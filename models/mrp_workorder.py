# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from collections import defaultdict
from odoo.tools import float_round


class MrpWorkorder(models.Model):
    merma_count = fields.Integer(compute='_compute_merma_count', string='Merma')
    _inherit = "mrp.workorder"

    merma_ids = fields.One2many('mrp.merma', 'wo_source_id', 'Mermas')
    qty_production = fields.Integer(compute='_compute_qty_production')
    qty_producing = fields.Integer(compute='_compute_qty_producing')
    pago_ids = fields.One2many('mrp.pago', 'workorder_id', 'Personal')
    state = fields.Selection(selection_add=[('supervisado', 'Supervisado')])
    base = fields.Many2one('product.product', string='Base', compute='_compute_base')
    qty_base = fields.Float('Cantidad de bases', compute='_compute_base')
    piezas_x_base = fields.Integer('Piezas por Base', compute='_compute_base')
    numero_pasadas = fields.Integer('Número de Pasadas', compute='_compute_numero_pasadas')
    puede_supervisar = fields.Boolean('Puede ser Supervisado', compute="_compute_puede_supervisar")
    puede_anular_supervision = fields.Boolean('Puede anular supervisión', compute="_compute_puede_anular_supervision")

    @api.multi
    def _compute_puede_supervisar(self):
        for workorder in self:
            prev_workorder = workorder.production_id.workorder_ids.filtered(
                lambda x: x.next_work_order_id.id == workorder.id)
            if prev_workorder.state == 'supervisado' or not prev_workorder:
                workorder.puede_supervisar = True

    @api.multi
    def _compute_puede_anular_supervision(self):
        for workorder in self:
            if (workorder.next_work_order_id.state not in (
                    'cancel', 'supervisado') or not workorder.next_work_order_id) and workorder.state == 'supervisado':
                workorder.puede_anular_supervision = True

    @api.multi
    def _compute_base(self):
        for workorder in self:
            production_id = workorder.production_id
            bom_line = production_id.move_raw_ids.filtered(lambda x: x.product_id.bases_x_carro)
            base = bom_line.mapped('product_id')
            if len(base) == 1:
                workorder.base = base
                workorder.piezas_x_base = production_id.product_qty / bom_line.product_uom_qty
                if workorder.base and workorder.qty_produced:
                    workorder.qty_base = workorder.qty_produced / workorder.piezas_x_base
                elif not workorder.qty_produced and workorder.qty_production:
                    workorder.qty_base = workorder.qty_production / workorder.piezas_x_base
                else:
                    workorder.qty_base = production_id.product_qty / workorder.piezas_x_base

    @api.multi
    def _compute_numero_pasadas(self):
        for workorder in self:
            bom_line = workorder.production_id.bom_id.bom_line_service_ids.filtered(
                lambda x: x.numero_pasadas and x.operation_id.name == workorder.operation_id.name)
            if bom_line:
                workorder.numero_pasadas = bom_line[0].numero_pasadas

    @api.one
    def _compute_merma_count(self):
        self.merma_count = len(self.merma_ids)

    @api.multi
    def _compute_qty_production(self):
        for order in self:
            production_id = order.production_id
            qty_production = production_id.product_qty
            prev_wo = production_id.workorder_ids.filtered(
                lambda x: x.next_work_order_id.id == order.id)
            if prev_wo and prev_wo.qty_produced:
                qty_production = prev_wo.qty_produced
            elif prev_wo:
                last_wo = order.production_id.workorder_ids.filtered(
                    lambda x: x.state == 'supervisado' and x.qty_produced)
                if last_wo:
                    qty_production = last_wo[-1].qty_produced
            order.qty_production = qty_production

    @api.one
    def _compute_qty_producing(self):
        if self.state == 'supervisado':
            self.qty_producing = 0
        else:
            if self.merma_ids:
                cant = 0
                for merma in self.merma_ids:
                    if merma.product_id.id == self.product_id.id:
                        cant += merma.qty
                    elif merma.alter_production:
                        cant += merma._calculate_qty()
                self.qty_producing = self.qty_production - cant
            else:
                self.qty_producing = self.qty_production

    @api.multi
    def action_cancel(self):
        for workorder in self:
            pago_to_delete = workorder.pago_ids.filtered(lambda x: x.monto == 0)
            pago_to_delete.unlink()
        return super(MrpWorkorder, self).action_cancel()

    @api.multi
    def button_merma(self):
        self.ensure_one()
        wo_ids = self.production_id.workorder_ids.filtered(lambda x: x.id <= self.id).mapped('id')
        return {
            'name': 'Registro Merma',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.merma',
            'view_id': self.env.ref('mrp_kantu.merma_form_view').id,
            'type': 'ir.actions.act_window',
            'context': {
                'default_wo_source_id': self.id,
                'default_wo_dest_id': self.id,
                'default_product_id': self.product_id.id,
                'default_product_uom_id': self.product_uom_id.id,
                'default_alter_production': True,
                'workorder_ids': wo_ids,
                'servicio_descuento_ids': self.production_id.bom_id.bom_line_service_ids.mapped('product_id').filtered(
                    lambda x: x.standard_price < 0).ids,
                'products_available': [self.product_id.id] + self.production_id.move_raw_ids.mapped('product_id').ids
            },

            'target': 'new',
        }

    @api.multi
    def record_production(self):
        self.button_finish()

    @api.multi
    def button_personal(self, show_error=True):
        for wo in self:
            # wo._asignar_pago()
            empleado_ids = wo._get_employees(show_error)
            service_id = wo._get_service_pay(show_error=show_error)
            if empleado_ids and service_id:
                wo._create_mrp_pago(empleado_ids, service_id)
        return True

    def _create_mrp_pago(self, empleado_ids, servicio_id):
        pago = self.env['mrp.pago']
        values = {
            'servicio_id': servicio_id.id,
            'workorder_id': self.id
        }
        for empleado in empleado_ids:
            values['empleado_id'] = empleado.id
            pago.create(values)

    def _get_employees(self, show_error):
        empleados = self.workcenter_id.employee_ids
        if empleados:
            return empleados
        elif show_error:
            raise UserError('No encontramos personal en el area de %s' % (self.workcenter_id.name))
        return False

    def _get_service_pay(self, service_id=False, show_error=True):
        if service_id:
            bom_line_id = self.production_id.bom_id.bom_line_service_ids.filtered(
                lambda r: r.product_id.id == service_id.id and (
                        r.operation_id.name == self.operation_id.name or r.operation_id.id == self.operation_id.id))
        else:
            bom_line_id = self.production_id.bom_id.bom_line_service_ids.filtered(
                lambda r: r.product_id.type == 'service' and r.operation_id and (
                        r.operation_id.id == self.operation_id.id or r.operation_id.name in (
                    self.operation_id.name, self.display_name)))
        if len(bom_line_id) >= 2:
            raise UserError(
                'Se encontro mas de un servicio de pago para la orden de trabajo %s' % self.display_name.upper())
        if bom_line_id and service_id:
            return bom_line_id[0]
        elif bom_line_id:
            return bom_line_id[0].product_id
        elif show_error:
            raise UserError('Necesitamos un servicio de pago para la operacion '
                            '%s en la lista de materiales de %s' % (self.name, self.product_id.name))
        return False

    def _crear_datos_pago(self, empleados, servicio_id, qty, merma_id, workorder=False):
        pago = self.env['mrp.pago']
        pago_ids = []
        values = {
            'servicio_id': servicio_id,
            'workorder_id': workorder,
            'qty': qty,
            'merma_id': merma_id,
            'fecha_pago': fields.Date.today()
        }
        for e in empleados:
            values['empleado_id'] = e.id
            pago_ids.append(pago.create(values))
        return pago_ids

    @api.one
    def button_supervisar(self):
        if self.pago_ids:
            pago_groups = self._group_by_service()
            for group in pago_groups:
                price = self._compute_qty_price(group)
                self._asignar_monto(group, price)
        return self._registrar_wo()

    def _group_by_service(self):
        groups = defaultdict(list)
        for obj in self.pago_ids:
            if obj.servicio_id.standard_price >= 0:
                groups[obj.servicio_id].append(obj)
        return groups.values()

    def _compute_qty_price(self, group):
        pago = group[0]
        bom_line_id = self._get_service_pay(service_id=pago.servicio_id)
        servicio_id = bom_line_id.product_id
        bom_id = self.production_id.bom_id
        factor = self.product_uom_id._compute_quantity(self.qty_producing, bom_id.product_uom_id) / bom_id.product_qty
        unit_price = servicio_id.uom_id._compute_price(servicio_id.standard_price, bom_line_id.product_uom_id)
        monto_total = unit_price * bom_line_id.product_qty * factor
        return (monto_total / len(group))

    def _asignar_monto(self, pago_ids, monto):
        values = {
            'monto': monto,
            'qty': self.qty_producing,
            'fecha_pago': fields.Date.today()
        }
        for pago in pago_ids:
            pago.write(values)

    def _registrar_wo(self):
        self.ensure_one()
        if self.qty_producing <= 0:
            raise UserError(_('Please set the quantity you produced in the Current Qty field. It can not be 0!'))

        if (self.production_id.product_id.tracking != 'none') and not self.final_lot_id:
            raise UserError(_('You should provide a lot for the final product'))

        # Update quantities done on each raw material line
        raw_moves = self.move_raw_ids.filtered(
            lambda x: (x.has_tracking == 'none') and (x.state not in ('done', 'cancel')) and x.bom_line_id)
        for move in raw_moves:
            if move.unit_factor:
                rounding = move.product_uom.rounding
                move.quantity_done += float_round(self.qty_producing * move.unit_factor, precision_rounding=rounding)

        # Transfer quantities from temporary to final move lots or make them final
        for move_lot in self.active_move_lot_ids:
            # Check if move_lot already exists
            if move_lot.quantity_done <= 0:  # rounding...
                move_lot.unlink()
                continue
            #if not move_lot.lot_id:
            #    raise UserError(_('You should provide a lot for a component'))
            # Search other move_lot where it could be added:
            lots = self.move_lot_ids.filtered(
                lambda x: (x.lot_id.id == move_lot.lot_id.id) and (not x.lot_produced_id) and (not x.done_move))
            if lots:
                lots[0].quantity_done += move_lot.quantity_done
                lots[0].lot_produced_id = self.final_lot_id.id
                move_lot.unlink()
            else:
                move_lot.lot_produced_id = self.final_lot_id.id
                move_lot.done_wo = True

        # One a piece is produced, you can launch the next work order
        if self.next_work_order_id.state == 'pending':
            self.next_work_order_id.state = 'ready'
        if self.next_work_order_id and self.final_lot_id and not self.next_work_order_id.final_lot_id:
            self.next_work_order_id.final_lot_id = self.final_lot_id.id

        self.move_lot_ids.filtered(
            lambda move_lot: not move_lot.done_move and not move_lot.lot_produced_id and move_lot.quantity_done > 0
        ).write({
            'lot_produced_id': self.final_lot_id.id,
            'lot_produced_qty': self.qty_producing
        })

        # If last work order, then post lots used
        # TODO: should be same as checking if for every workorder something has been done?
        if not self.next_work_order_id:
            production_move = self.production_id.move_finished_ids.filtered(
                lambda x: (x.product_id.id == self.production_id.product_id.id) and (x.state not in ('done', 'cancel')))
            if production_move.product_id.tracking != 'none':
                move_lot = production_move.move_lot_ids.filtered(lambda x: x.lot_id.id == self.final_lot_id.id)
                if move_lot:
                    move_lot.quantity += self.qty_producing
                else:
                    move_lot.create({'move_id': production_move.id,
                                     'lot_id': self.final_lot_id.id,
                                     'quantity': self.qty_producing,
                                     'quantity_done': self.qty_producing,
                                     'workorder_id': self.id,
                                     })
            else:
                production_move.quantity_done += self.qty_producing  # TODO: UoM conversion?
        # Update workorder quantity produced
        self.qty_produced += self.qty_producing
        self.state = 'supervisado'

    @api.model
    def attendance_start(self, id, action):
        wo = self.browse(id)
        if action == 'start':
            wo.button_start()
        elif action == 'stop':
            wo.button_pending()
        elif action == 'continue':
            wo.button_start()
        elif action == 'done':
            wo.record_production()
        return {
            'action':
                {
                    'type': 'ir.actions.client',
                    'name': 'Codigo Barras',
                    'tag': 'mrp_kantu_codigo_barras'
                }
        }

    @api.multi
    def button_anular_supervision(self):
        for workorder in self:
            workorder.state = 'done'
            workorder.qty_produced = 0
            if workorder.pago_ids:
                workorder.pago_ids.filtered(lambda x: x.monto > 0 and not x.merma_id).write({
                    'monto': 0,
                    'qty': 0
                })
            if workorder.next_work_order_id:
                if workorder.next_work_order_id.state == 'ready':
                    workorder.next_work_order_id.state = 'pending'
            else:
                product_finished_move = workorder.production_id.move_finished_ids.filtered(
                    lambda x: x.product_id == workorder.production_id.product_id and x.state == 'confirmed')
                if product_finished_move and len(product_finished_move) == 1:
                    product_finished_move.quantity_done = 0
                else:
                    raise UserError('¡No podemos anular la supervisión!, comunicate con el administrador del sistema')
        return True

    @api.multi
    def supervise_all_wo(self):
        for wo in self:
            if wo.state == 'done':
                wo.button_supervisar()
            else:
                raise UserError('La orden de trabajo "%s" no ha sido realizada' % wo.display_name)

    """@api.multi
    def supervise_all_wo(self):
        prev_workorder = self.env['mrp.workorder']
        can_supervise = self[0].puede_supervisar
        for wo in self.filtered(lambda x: x.state not in ('supervisado', 'cancel')):
            if can_supervise:
                prev_workorder += wo.button_supervisar()
                can_supervise = prev_workorder.
            else:
                raise UserError('No se puede supervisar la orden de trabajo "%s"' % self.display_name)"""
