# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.exceptions import UserError


class MrpPedidoProduccion(models.Model):
    _name = 'mrp.pedido.produccion'

    name = fields.Char(string='Descripcion')
    fecha_programacion = fields.Date(string='Fecha de Programacion',
                                     states={'nuevo': [('readonly', False)]}, readonly=True)
    pedido_line_ids = fields.One2many('mrp.pedido.line', 'pedido_id', 'Detalle del Pedido',
                                      states={'nuevo': [('readonly', False)]}, readonly=True)
    state = fields.Selection(
        [('nuevo', 'Nuevo'), ('confirmado', 'Confirmado'), ('proceso', 'En Proceso'), ('realizado', 'Realizado')],
        string='Estado', compute='_compute_state', default='nuevo')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Ya existe un pedido de produccion con este codigo!')
    ]

    @api.multi
    def _compute_state(self):
        for pedido in self:
            pedido_lines = pedido.pedido_line_ids
            if pedido_lines:
                confirmado = len(pedido_lines.filtered(lambda x: x.state == 'confirmado'))
                realizado = len(pedido_lines.filtered(lambda x: x.state == 'realizado'))
                nuevo = len(pedido_lines.filtered(lambda x: x.state == 'nuevo'))
                if confirmado == len(pedido_lines):
                    pedido.state = 'confirmado'
                elif realizado == len(pedido_lines):
                    pedido.state = 'realizado'
                elif nuevo == len(pedido_lines):
                    pedido.state = 'nuevo'
                else:
                    pedido.state = 'proceso'
            else:
                pedido.state = 'nuevo'

    @api.multi
    def button_confirm(self):
        for production in self:
            production.pedido_line_ids.write({'state': 'confirmado'})

    @api.model
    def create(self, values):
        if not values.get('name'):
            values['name'] = self.env['ir.sequence'].next_by_code('mrp.pedido.produccion') or 'Nuevo'
        pedido = super(MrpPedidoProduccion, self).create(values)
        return pedido

    @api.multi
    def unlink(self):
        for pedido in self:
            pedidosEnProceso = pedido.pedido_line_ids.filtered(lambda x: x.state in ['proceso', 'realizado'])
            if pedidosEnProceso:
                raise UserError('No se puede eliminar un pedido que se haya planificado')
            else:
                pedido.pedido_line_ids.unlink()
                super(MrpPedidoProduccion, self).unlink()

    @api.multi
    def button_add_detail(self):
        return {
            'name': 'Agregar Detalle',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pedido.line.wizard',
            'view_id': self.env.ref('mrp_kantu.pedidio_line_wizard').id,
            'type': 'ir.actions.act_window',
            'context': {
                'default_pedido_id': self.id
            },
            'target': 'new',
        }


class MrpPedidoLine(models.Model):
    _name = 'mrp.pedido.line'
    _rec_name = 'pedido_id'

    product_id = fields.Many2one('product.product', 'Producto')
    num_piezas = fields.Integer('Numero Piezas Pedidas')
    num_piezas_ord = fields.Integer('Numero Piezas Ordenadas', default=0)
    num_piezas_prod = fields.Integer('Numero Piezas Producidas', compute='_compute_pzs_prod')
    pedido_id = fields.Many2one('mrp.pedido.produccion', 'Pedido de Produccion', ondelete='cascade')
    pedido_production_ids = fields.One2many('mrp.pedido.production.rel', 'pedido_line_id', 'Ordenes Programadas')
    location_dest_id = fields.Many2one('stock.location', 'Destino')
    state = fields.Selection(
        [('nuevo', 'Nuevo'), ('confirmado', 'Confirmado'), ('proceso', 'En Proceso'), ('realizado', 'Realizado')],
        string='Estado', default='nuevo')
    workorders = fields.Text(string="Proceso(s) Actual(es)", compute="_compute_workorders")

    @api.one
    @api.depends("pedido_production_ids.production_id.workorder_ids")
    def _compute_workorders(self):
        if self.pedido_production_ids:
            self.workorders = ", ".join(self.pedido_production_ids.mapped('production_id.workorder_ids') \
                                        .filtered(lambda x: x.state in ('ready', 'progress')).mapped('name'))

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id,
                 u"%s (%s) %s" % (record.pedido_id.name, str(record.num_piezas), record.location_dest_id.name or '')
                 ))
        return result

    @api.one
    @api.depends('pedido_production_ids')
    def _compute_pzs_prod(self):
        pedidosRealizados = self.pedido_production_ids.filtered(lambda x: x.state == 'realizado')
        if pedidosRealizados:
            self.num_piezas_prod = sum(pedidosRealizados.mapped('product_uom_qty'))
        else:
            self.num_piezas_prod = 0

    def _compute_state(self):
        if self.num_piezas_ord != 0 and self.num_piezas_prod >= round(self.num_piezas - self.num_piezas * 0.10):
            self.state = 'realizado'
        elif self.num_piezas_ord != 0:
            self.state = 'proceso'
        else:
            self.state = 'confirmado'


class MrpPedidoLineProduccion(models.Model):
    _name = 'mrp.pedido.production.rel'
    _rec_name = 'production_id'

    pedido_line_id = fields.Many2one('mrp.pedido.line', 'Pedido')
    production_id = fields.Many2one('mrp.production', 'Orden de Produccion', ondelete='cascade')
    product_uom_qty = fields.Integer('Cantidad')
    state = fields.Selection([('confirmado', 'Confirmado'), ('realizado', 'Realizado')], default='confirmado')

    @api.onchange('pedido_line_id')
    def _onchange_pedido(self):
        if self.pedido_line_id:
            if not self.pedido_line_id.num_piezas_prod:
                self.product_uom_qty = self.pedido_line_id.num_piezas - self.pedido_line_id.num_piezas_ord
            else:
                self.product_uom_qty = self.pedido_line_id.num_piezas - self.pedido_line_id.num_piezas_prod

    @api.model
    def create(self, vals):
        new_record = super(MrpPedidoLineProduccion, self).create(vals)
        new_record.pedido_line_id.sudo().num_piezas_ord += new_record.product_uom_qty
        new_record.pedido_line_id.sudo()._compute_state()
        return new_record

    @api.multi
    def unlink(self):
        for pedidoRel in self:
            pedidoRel.pedido_line_id.sudo().num_piezas_ord -= pedidoRel.product_uom_qty
            pedidoRel.pedido_line_id.sudo()._compute_state()
            super(MrpPedidoLineProduccion, pedidoRel).unlink()


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    pedido_line_production_ids = fields.One2many('mrp.pedido.production.rel', 'production_id',
                                                 string='Pedidos de Produccion')

    @api.multi
    def action_cancel(self):
        for production in self:
            pedidos = production.pedido_line_production_ids
            pedidos.unlink()
            super(MrpProduction, production).action_cancel()
        return True

    @api.onchange('pedido_line_production_ids')
    def _onchange_pedido(self):
        if self.pedido_line_production_ids:
            if not self.move_raw_ids:
                qty_unit_products = sum(self.pedido_line_production_ids.mapped('product_uom_qty'))
                self.product_qty = self.product_id.uom_id._compute_quantity(qty_unit_products, self.product_uom_id)
        # if self.pedido_line_production_ids:
        #    if not self.move_raw_ids:
        #        self.product_qty = sum(self.pedido_line_production_ids.mapped('product_uom_qty'))
        # elif not self.move_raw_ids:
        #    self.product_qty = 0

    @api.multi
    def button_mark_done(self):
        self.ensure_one()
        super(MrpProduction, self).button_mark_done()
        if self.pedido_line_production_ids:
            self._update_pedidos()
        return True

    def _update_pedidos(self):
        move_finish = self.move_finished_ids[0]
        qty = move_finish.quantity_done
        if qty:
            pedidos = self.pedido_line_production_ids.sorted(
                key=lambda x: x.pedido_line_id.pedido_id.fecha_programacion)
            for p in pedidos:
                values = {}
                if p.product_uom_qty > qty:
                    values['product_uom_qty'] = qty
                values['state'] = 'realizado'
                p.write(values)
                p.pedido_line_id._compute_state()
                qty -= p.product_uom_qty
