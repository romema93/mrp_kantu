# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class MrpProduction(models.Model):
    _inherit = "mrp.production"
    """----------------------------------------
            DEFAULT FUNCTIONS FIELDS
    ----------------------------------------"""

    def get_orders_from_context(self):
        order_ids = self.env.context.get('order_ids', False)
        order_line_ids = False
        product_id = False
        if order_ids:
            order_line_ids = self.env['mrp.order.line'].browse(order_ids)
            product_id = order_line_ids.mapped('product_id')[0]
            order_line_ids = order_line_ids.filtered(lambda x: x.product_id.id == product_id.id)
        return order_line_ids, product_id

    def default_order_lines(self):
        order_line_production_ids = self.env['mrp.order.production.rel']
        order_line_ids, product_id = self.get_orders_from_context()
        if order_line_ids:
            for order in order_line_ids:
                if order.qty_remaining > 0 and order.state in ['confirmed', 'process']:
                    vals = {
                        'order_line_id': order.id,
                        'product_uom_qty': order.qty_remaining
                    }
                    order_line_production_ids += order_line_production_ids.new(vals)
        return order_line_production_ids

    def default_product(self):
        order_line_ids, product_id = self.get_orders_from_context()
        return product_id

    def default_product_qty(self):
        order_line_ids, product_id = self.get_orders_from_context()
        return sum(order_line_ids.mapped('qty_remaining')) if order_line_ids else 0

    """-----------------------------DEFAULT FUNCTIONS FIELD"""

    """-----------------------------
                FIELDS
    -----------------------------"""

    qty_product = fields.Float(compute='_compute_qty_product')
    name = fields.Char('Reference', copy=False, readonly=True, default=lambda x: _('New'),
                       states={'confirmed': [('readonly', False)]})
    employee_ids = fields.Many2one('hr.employee', string="Pintor")
    location_id = fields.Many2one('stock.location', string="Destino")
    order_line_production_ids = fields.One2many('mrp.order.production.rel', 'production_id',
                                                string='Órdenes de Producción', default=default_order_lines)
    product_id = fields.Many2one('product.product', default=default_product)
    product_qty = fields.Float(default=default_product_qty)
    progress = fields.Integer(string="Progreso", compute="_compute_progress", store=True)
    current_workorder = fields.Char(string='Proceso Actual', compute='_compute_current_workorder', store=True)
    mrp_periodo_id = fields.Many2one('mrp.periodo', string="Periodo")
    group_pay_id = fields.Many2one('mrp.group.pay', string="Grupo de pago")

    """/-----------------------FIELDS"""

    """------------------------------------------
                COMPUTE FUNCTIONS
    ---------------------------------------------"""

    @api.depends('workorder_ids.state', 'check_to_done')
    def _compute_current_workorder(self):
        for production in self:
            workorders = production.workorder_ids
            current_workorder = False
            if workorders:
                current_wos = workorders.filtered(lambda x: x.state in ('done', 'progress', 'supervisado'))
                if not production.check_to_done and current_wos:
                    current_workorder = current_wos[-1].name
                elif not production.check_to_done and not current_wos:
                    current_workorder = workorders[0].name
                elif production.check_to_done:
                    current_workorder = 'Supervisado'
            production.current_workorder = current_workorder

    @api.multi
    @api.depends('product_qty')
    def _compute_qty_product(self):
        if self._context.get('qty_product'):
            self.qty_product = float(self._context.get('qty_product'))
            self.product_qty = self.qty_product

    @api.depends('workorder_ids.state')
    def _compute_progress(self):
        for production in self:
            workorders = production.workorder_ids
            if workorders:
                available_wo = workorders.filtered(lambda x: x.state in ('progress', 'done', 'supervisado'))
                current_wo = available_wo[-1] if available_wo else False
                if current_wo:
                    level_wo = workorders.ids.index(current_wo.id) + 1
                    if current_wo.state == 'progress':
                        level_wo = (level_wo * 2) - 1
                    else:
                        level_wo *= 2
                    production.progress = int((level_wo * 100.0) / (len(workorders) * 2))

    """/----------- COMPUTE FUNCTIONS"""

    """------------------------------------------
                    CONSTRAINS
    ---------------------------------------------"""

    @api.constrains('order_line_production_ids')
    def _check_order_line_production_ids(self):
        order_line_ids = []
        for production in self:
            order_qty = sum(production.order_line_production_ids.mapped('product_uom_qty'))
            if order_qty > production.product_qty:
                raise ValidationError('La cantidad de las ordenes no debe exceder a la cantidad de la ficha')
            for x in production.order_line_production_ids:
                if x.order_line_id.id in order_line_ids:
                    raise ValidationError('Existe mas de una referencia a la OP "%s"' % x.order_line_id.display_name)
                order_line_ids.append(x.order_line_id.id)

    """/------------CONSTRAINS"""

    """------------------------------------------
                        ONCHANGE
        ---------------------------------------------"""

    @api.onchange('picking_type_id')
    def onchange_picking_type_id(self):
        if self.picking_type_id:
            predict_sequence_char = self.picking_type_id.sequence_id.predict_next_sequence()
            if predict_sequence_char:
                self.name = predict_sequence_char

    @api.onchange('order_line_production_ids')
    def _onchange_order(self):
        if self.order_line_production_ids and self.product_id:
            if not self.move_raw_ids:
                qty_unit_products = sum(self.order_line_production_ids.mapped('product_uom_qty'))
                self.product_qty = self.product_id.uom_id._compute_quantity(qty_unit_products, self.product_uom_id)

    """/------------ ONCHANGE"""

    """------------------------------------------
                    CRUD
    ---------------------------------------------"""

    @api.model
    def create(self, values):
        self._check_order_line_production_ids()
        next_code = self.env['stock.picking.type'].browse(values['picking_type_id']).sequence_id.predict_next_sequence()
        if values['name'] == next_code:
            if values.get('picking_type_id'):
                values['name'] = self.env['stock.picking.type'].browse(
                    values['picking_type_id']).sequence_id.next_by_id()
            else:
                values['name'] = self.env['ir.sequence'].next_by_code('mrp.production') or _('New')
        production = super(MrpProduction, self).create(values)
        return production

    """/------------ CRUD"""

    """------------------------------------------
                    BUTTON ACTIONS
    ---------------------------------------------"""

    @api.multi
    def button_transfer(self):
        self.ensure_one()
        products = (
                self.move_raw_ids.filtered(
                    lambda x: x.state not in ('done', 'cancel')) | self.move_finished_ids.filtered(
            lambda x: x.state == 'done')).mapped('product_id').ids
        return {
            'name': 'Transferir',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.production.transfer',
            'view_id': self.env.ref('mrp_kantu.production_transfer_wizard').id,
            'type': 'ir.actions.act_window',
            'context': {
                'default_origin': self.name,
                'product_ids': products
            },
            'target': 'new',
        }

    @api.multi
    def button_mark_done(self):
        self.ensure_one()
        if not self.routing_id:
            for move in self.move_raw_ids:
                if not move.quantity_done:
                    move.quantity_done = move.product_uom_qty
            for move in self.move_finished_ids:
                move.quantity_done = move.product_uom_qty
        return super(MrpProduction, self).button_mark_done()

    @api.multi
    def button_plan(self):
        res = super(MrpProduction, self).button_plan()
        for order in self:
            if order.routing_id and order.workorder_ids:
                operations_to_load_employees = order.routing_id.operation_ids.filtered(
                    lambda x: x.load_default_employees == True).mapped('name')
                if operations_to_load_employees:
                    workorders_to_load_employees = order.workorder_ids.filtered(
                        lambda x: x.name in operations_to_load_employees)
                    if workorders_to_load_employees:
                        workorders_to_load_employees.button_personal(show_error=False)
        return res

    @api.multi
    def button_mark_done(self):
        self.ensure_one()
        super(MrpProduction, self).button_mark_done()
        if self.order_line_production_ids:
            self._update_orders()
        return True

    """/------------BUTTON ACTIONS"""

    @api.multi
    @api.depends('workorder_ids.state', 'move_finished_ids')
    def _get_produced_qty(self):
        for production in self:
            done_moves = production.move_finished_ids.filtered(
                lambda x: x.state != 'cancel' and x.product_id.id == production.product_id.id)
            qty_produced = sum(done_moves.mapped('quantity_done'))
            wo_done = True
            if any([x.state not in ('supervisado', 'cancel') for x in production.workorder_ids]):
                wo_done = False
            production.check_to_done = done_moves and (qty_produced >= production.product_qty) and (
                        production.state not in ('done', 'cancel')) and wo_done
            production.qty_produced = qty_produced
        return True

    @api.multi
    @api.depends('workorder_ids.state')
    def _compute_workorder_done_count(self):
        data = self.env['mrp.workorder'].read_group([
            ('production_id', 'in', self.ids),
            ('state', '=', 'supervisado')], ['production_id'], ['production_id'])
        count_data = dict((item['production_id'][0], item['production_id_count']) for item in data)
        for production in self:
            production.workorder_done_count = count_data.get(production.id, 0)

    def obtain_materials(self, op):
        materials = []
        for raw in op.move_raw_ids:
            if raw.se_produce:
                temp = {
                    'id': raw.id,
                    'product': raw.product_id.name,
                    'product_uom_qty': raw.product_uom_qty,
                    'product_uom': raw.product_uom.name,
                }
                materials.append(temp)
        return materials

    @api.multi
    def _generate_moves(self):
        for production in self:
            production._generate_finished_moves()
            if self.bom_id:
                factor = production.product_uom_id._compute_quantity(production.product_qty,
                                                                     production.bom_id.product_uom_id) / production.bom_id.product_qty
                boms, lines = production.bom_id.explode(production.product_id, factor,
                                                        picking_type=production.bom_id.picking_type_id)
                production._generate_raw_moves(lines)
            # Check for all draft moves whether they are mto or not
            production._adjust_procure_method()
            production.move_raw_ids.action_confirm()
        return True

    def _generate_custom_moves(self, moves, production):
        for move in moves:
            values = {
                'name': production.name,
                'date': production.date_planned_start,
                'date_expected': production.date_planned_start,
                'product_id': move.product_id,
                'product_uom_qty': move.product_uom_qty,
                'product_uom': move.product_uom_id,
                'location_id': production.picking_type_id.default_location_src_id.id,
                'location_dest_id': production.picking_type_id.default_location_dest_id.id,
                'raw_material_production_id': production.id,
                'company_id': production.company_id.id,
                'procure_method': 'make_to_stock',
                'origin': production.name,
                'warehouse_id': production.picking_type_id.default_location_src_id.get_warehouse().id,
                'group_id': production.procurement_group_id.id,
                'propagate': production.propagate
            }
            self.env['stock.move'].create(values)
        return True

    @api.multi
    def action_cancel(self):
        for production in self:
            orders = production.order_line_production_ids
            orders.unlink()
            super(MrpProduction, production).action_cancel()
        return True

    def _update_orders(self):
        move_finish = self.move_finished_ids[0]
        qty = move_finish.quantity_done
        if qty:
            orders = self.order_line_production_ids.sorted(
                key=lambda x: x.order_line_id.order_id.fecha_programacion)
            for p in orders:
                values = {}
                if p.product_uom_qty > qty:
                    values['product_uom_qty'] = qty
                values['state'] = 'realizado'
                p.write(values)
                qty -= p.product_uom_qty
