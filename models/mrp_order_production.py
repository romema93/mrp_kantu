# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError


class MrpOrderProduction(models.Model):
    _name = 'mrp.order.production'
    _description = 'Orden de Produccion'
    _inherit = ['mail.thread']

    @api.multi
    def _compute_state(self):
        for order in self:
            order_lines = order.order_line_ids
            if order_lines:
                confirmado = len(order_lines.filtered(lambda x: x.state == 'confirmed'))
                realizado = len(order_lines.filtered(lambda x: x.state == 'done'))
                nuevo = len(order_lines.filtered(lambda x: x.state == 'draft'))
                if confirmado == len(order_lines):
                    order.state = 'confirmed'
                elif realizado == len(order_lines):
                    order.state = 'done'
                elif nuevo == len(order_lines):
                    order.state = 'draft'
                else:
                    order.state = 'progress'
            else:
                order.state = 'draft'

    name = fields.Char(string='Descripcion')
    fecha_programacion = fields.Date(string='Fecha de Programacion',
                                     states={'draft': [('readonly', False)]}, readonly=True)
    order_line_ids = fields.One2many('mrp.order.line', 'order_id', 'Linea de Productos',
                                     states={'draft': [('readonly', False)]}, readonly=True)
    order_operation_ids = fields.One2many('mrp.order.operation', 'order_id', 'Orden Inicial',
                                          states={'draft': [('readonly', False)]}, readonly=True)
    state = fields.Selection(
        [('draft', 'Nuevo'), ('confirmed', 'Confirmado'), ('progress', 'En Proceso'), ('done', 'Realizado')],
        string='Estado', compute='_compute_state', default='draft')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Ya existe una orden de producción con este codigo')
    ]

    @api.multi
    def button_confirm(self):
        for production in self:
            production.order_operation_ids.create_detail()
            production.order_line_ids.write({'state': 'confirmed'})

    @api.model
    def create(self, values):
        if not values.get('name'):
            values['name'] = self.env['ir.sequence'].next_by_code('mrp.order.production') or 'Nuevo'
        order = super(MrpOrderProduction, self).create(values)
        return order

    @api.multi
    def unlink(self):
        for order in self:
            orders_in_process = order.order_line_ids.filtered(lambda x: x.state in ['progress', 'done'])
            if orders_in_process:
                raise UserError('No se puede eliminar una orden que se haya planificado')
            else:
                order.order_line_ids.unlink()
                super(MrpOrderProduction, order).unlink()


class MrpOrderOperation(models.Model):
    _name = "mrp.order.operation"
    _rec_name = 'product_id'

    @api.depends('order_id.order_line_ids')
    def _compute_data_from_lines(self):
        for order_operation in self:
            order_lines = order_operation.order_id.order_line_ids.filtered(
                lambda x: x.product_id == order_operation.product_id)
            order_operation.confirmed_pieces = sum(order_lines.mapped('num_piezas'))
            order_operation.qty_planned = sum(order_lines.mapped('num_piezas_ord'))
            order_operation.qty_produced = sum(order_lines.mapped('num_piezas_prod'))

    order_id = fields.Many2one('mrp.order.production')
    product_id = fields.Many2one('product.product', 'Producto', required=True)
    num_piezas = fields.Integer('Numero Piezas')
    location_dest_id = fields.Many2one('stock.location', 'Destino')
    confirmed_pieces = fields.Integer('Piezas Confirmadas', compute="_compute_data_from_lines")
    qty_planned = fields.Integer('Piezas Planificadas', compute="_compute_data_from_lines")
    qty_produced = fields.Integer('Piezas Producidas', compute="_compute_data_from_lines")
    observations = fields.Text(string="Observaciones")

    @api.multi
    def create_detail(self):
        for operation in self:
            product_id = operation.product_id
            if product_id.bom_ids and product_id.calculate_qty_op:
                bom = product_id.bom_ids[0]
                bom_line = bom.bom_line_ids.filtered(lambda x: x.product_id.bases_x_carro and x.product_id.max_carros)
                if bom_line:
                    base = bom_line.mapped('product_id')
                    bases_x_carro = base.bases_x_carro
                    max_carros = base.max_carros
                    pz_x_base = bom.product_qty / bom_line.product_qty
                    if bases_x_carro and max_carros:
                        num_pzs, carros = operation._get_num_pzs(bases_x_carro, pz_x_base, operation.num_piezas)
                        operation._create_order_line(max_carros, carros, num_pzs)
                else:
                    self.env['mrp.order.line'].create(operation._prepare_datos(operation.num_piezas))
            else:
                self.env['mrp.order.line'].create(operation._prepare_datos(operation.num_piezas))
        return True

    def _get_num_pzs(self, p_bases_x_carro, p_pz_x_base, p_product_qty):
        bases = p_product_qty / float(p_pz_x_base)
        a = bases - int(bases)
        bases = int(bases)
        if a >= 0.33:
            bases += 1
        carros = bases / float(p_bases_x_carro)
        b = carros - int(carros)
        carros = int(carros)
        if b >= 0.33:
            carros += 1
        num_piezas = carros * p_bases_x_carro * p_pz_x_base
        return num_piezas, carros

    def _create_order_line(self, p_max_carros, p_carros, p_num_pzs):
        order_line = self.env['mrp.order.line']
        min = p_max_carros
        max = (min - 1) * 2
        carros = p_carros
        piezas = p_num_pzs
        piezas_x_carro = piezas / carros
        if carros <= min:
            order_line.create(self._prepare_datos(piezas))
        else:
            while carros >= min:
                if carros > min and carros <= max:
                    temp = int(carros / 2)
                    pzs = temp * piezas_x_carro
                    order_line.create(self._prepare_datos(pzs))
                    temp += carros % 2
                    pzs = temp * piezas_x_carro
                    order_line.create(self._prepare_datos(pzs))
                    carros = 0
                else:
                    carros = carros - min
                    pzs = min * piezas_x_carro
                    order_line.create(self._prepare_datos(pzs))
            if carros > 0 and carros <= min:
                pzs = carros * piezas_x_carro
                order_line.create(self._prepare_datos(pzs))

    def _prepare_datos(self, p_num_pzs):
        return {
            'location_dest_id': self.location_dest_id.id or '',
            'num_piezas': p_num_pzs,
            'product_id': self.product_id.id,
            'order_id': self.order_id.id
        }


class MrpOrderLine(models.Model):
    _name = 'mrp.order.line'
    _rec_name = 'product_id'
    _order = 'order_id DESC, id'

    @api.depends('num_piezas', 'num_piezas_ord', 'num_piezas_prod')
    def _compute_qty_remaining(self):
        for order_line in self:
            order_line.qty_remaining = order_line.num_piezas - order_line.num_piezas_ord

    @api.depends('order_production_ids.production_id.progress')
    def _compute_progress(self):
        for order_line in self:
            progress = 0
            for order_production_rel in order_line.order_production_ids:
                production_progress = order_production_rel.production_id.progress
                qty_order_percentage = order_production_rel.product_uom_qty * 100.0 / order_line.num_piezas / 100.0
                progress += int(production_progress * qty_order_percentage)
            order_line.progress = progress

    @api.depends('order_production_ids.production_id.state')
    def _compute_state(self):
        for order_line in self:
            order_production_ids = order_line.order_production_ids
            orders_planned = any(order_production_ids.filtered(lambda x: x.production_id.state == 'planned'))
            orders_progress = any(order_production_ids.filtered(lambda x: x.production_id.state == 'progress'))
            orders_confirmed = any(order_production_ids.filtered(lambda x: x.production_id.state == 'confirmed'))
            qty_orders_done = len(order_production_ids.filtered(
                lambda x: x.production_id.state == 'done')) if order_production_ids else False
            if not order_production_ids:
                if order_line.order_id.state in ['confirmed', 'progress']:
                    order_line.state = 'confirmed'
                else:
                    order_line.state = 'draft'
            if orders_confirmed:
                order_line.state = 'confirmed'
            if orders_planned:
                order_line.state = 'planned'
            if orders_progress:
                order_line.state = 'process'
            if order_production_ids and qty_orders_done == len(order_production_ids):
                order_line.state = 'done'

    product_id = fields.Many2one('product.product', 'Producto', required=True)
    num_piezas = fields.Integer('Piezas Ordenadas')
    num_piezas_ord = fields.Integer('Piezas Planificadas', default=0)
    num_piezas_prod = fields.Integer('Piezas Producidas', compute='_compute_pzs_prod')
    order_id = fields.Many2one('mrp.order.production', 'Órden de Producción', ondelete='cascade')
    order_production_ids = fields.One2many('mrp.order.production.rel', 'order_line_id', 'Ordenes Programadas')
    location_dest_id = fields.Many2one('stock.location', 'Destino')
    state = fields.Selection(
        [('draft', 'Nuevo'), ('confirmed', 'Confirmado'), ('planned', 'Planificado'), ('process', 'En Proceso'),
         ('done', 'Realizado'), ('cancel', 'Cancelado')],
        string='Estado', default='draft', compute="_compute_state", store=True)
    workorders = fields.Text(string="Proceso(s) Actual(es)", compute="_compute_workorders")
    qty_remaining = fields.Integer('Piezas Restantes', compute='_compute_qty_remaining')
    progress = fields.Integer('Progreso', compute='_compute_progress', store=True, group_operator="avg")

    @api.one
    @api.depends("order_production_ids.production_id.workorder_ids")
    def _compute_workorders(self):
        if self.order_production_ids:
            self.workorders = ", ".join(self.order_production_ids.mapped('production_id.workorder_ids') \
                                        .filtered(lambda x: x.state in ('ready', 'progress')).mapped('name'))

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id,
                 u"[%s] %s / %s" % (str(record.id), record.order_id.name, record.location_dest_id.name or '')
                 ))
        return result

    @api.one
    @api.depends('order_production_ids.production_id.check_to_done')
    def _compute_pzs_prod(self):
        executed_orders = self.order_production_ids.filtered(lambda x: x.production_id.check_to_done)
        if executed_orders:
            self.num_piezas_prod = sum(
                executed_orders.mapped('production_id.move_finished_ids').filtered(
                    lambda x: x.state != 'cancel').mapped('quantity_done'))
        else:
            self.num_piezas_prod = 0

    def show_workorders(self):
        workorder_ids = self.order_production_ids.mapped('production_id.workorder_ids').ids
        return {
            'name': 'Ordenes de Trabajo',
            'res_model': 'mrp.workorder',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('id', 'in', workorder_ids)],
        }


class MrpOrderLineProduction(models.Model):
    _name = 'mrp.order.production.rel'
    _rec_name = 'production_id'

    order_line_id = fields.Many2one('mrp.order.line', 'Orden de Producción', required=True)
    production_id = fields.Many2one('mrp.production', 'Ficha de Producción', ondelete='cascade')
    product_uom_qty = fields.Integer('Cantidad')

    @api.onchange('production_id')
    def onchange_production_id(self):
        print self.production_id.order_line_production_ids.mapped('order_line_id')

    @api.onchange('order_line_id')
    def _onchange_order(self):
        if self.order_line_id:
            if not self.order_line_id.num_piezas_prod:
                self.product_uom_qty = self.order_line_id.num_piezas - self.order_line_id.num_piezas_ord
            else:
                self.product_uom_qty = self.order_line_id.num_piezas - self.order_line_id.num_piezas_prod

    @api.model
    def create(self, vals):
        new_record = super(MrpOrderLineProduction, self).create(vals)
        new_record.order_line_id.sudo().num_piezas_ord += new_record.product_uom_qty
        return new_record

    @api.multi
    def unlink(self):
        for order_production_rel in self:
            order_production_rel.order_line_id.sudo().num_piezas_ord -= order_production_rel.product_uom_qty
            super(MrpOrderLineProduction, order_production_rel).unlink()

    @api.constrains('product_uom_qty')
    def _check_product_uom_qty(self):
        for x in self:
            order_qty = (x.order_line_id.num_piezas - x.order_line_id.num_piezas_ord)
            if x.product_uom_qty > order_qty:
                if order_qty == 0:
                    raise ValidationError(
                        'La orden de produccion "%s" ya se encuentra planificada en su totalidad o existe mas de una referencia a la misma' % x.order_line_id.display_name)
                raise ValidationError(
                    'La cantidad solicitada para la orden de produccion "%s" no debe exceder de %s' % (
                        x.order_line_id.display_name, str(order_qty)))
            if x.product_uom_qty < 1:
                raise ValidationError('La cantidad solicitada debe ser mayor a 0')
