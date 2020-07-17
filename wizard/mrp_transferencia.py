# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class WorkorderRecicle(models.TransientModel):
    _name = "mrp.production.transfer"
    _description = "Lanza una ventana de transferencia"

    location_id = fields.Many2one('stock.location','Ubicacion origen',required='True')
    location_dest_id = fields.Many2one('stock.location','Ubicacion destino',required='True')
    origin = fields.Char('Documento Origen')
    product_id = fields.Many2one(
        'product.product', 'Producto',
        required=True)
    qty = fields.Float(string='Cantidad')
    product_uom_id = fields.Many2one('product.uom', 'Unidad de medida', required=True)
    transfer_type = fields.Selection([
        ('abastecimiento','Abastecimiento'),
        ('aumento','Falta de material'),
        ('devolucion','Devolucion'),
    ],string='Motivo de transferencia',default='abastecimiento',required='True')

    # @api.onchange('product_id')
    # def onchange_product_id(self):
    #     if self.product_id:
    #         self.product_uom_id = self.product_id.uom_id.id
    #     active_id = self.env.context.get('active_id', False)
    #     production = self.env[self.env.context.get('active_model')].search([('id', '=', active_id)])
    #     move = self._get_move(production,'confirmed')
    #     if move:
    #         self.qty = move.product_uom_qty
    #     else:
    #         self.qty = 0


    @api.multi
    def button_transfer(self):
        self.ensure_one()
        active_id = self.env.context.get('active_id', False)
        order = self.env[self.env.context.get('active_model')].search([('id', '=', active_id)])
        production = order.raw_material_production_id
        if(self.transfer_type=='abastecimiento'):
            #if(self._get_move(production,['confirmed'])):
            self._done_transfer()
            production.action_assign()
            #else: raise UserError('No se puede abastecer una orden en proceso')
        elif(self.transfer_type=='aumento'):
            # Obtenemos el move que sera modificado
            move_affected = self._get_move(production,['assigned'])
            move_affected.write({
                'product_uom_qty':move_affected.product_uom_qty+self.qty,
                'quantity_done_store':move_affected.quantity_done_store+self.qty,
                                 })
            # Transferir desde almacen
            self._done_transfer()
            # Reserva la cantidad transferida al move del mrp.production
            quants = self.env['stock.quant'].quants_get_preferred_domain(
                self.qty, move_affected)
            self.env['stock.quant'].quants_reserve(quants, move_affected)
        elif(self.transfer_type=='devolucion'):
            move_affected = self._get_move(production, ['assigned'])
            move_affected.do_unreserve()
            self._done_transfer()
            move_affected.write({
                'product_uom_qty': move_affected.product_uom_qty - self.qty,
                'quantity_done_store': move_affected.quantity_done_store - self.qty,
            })
            quants = self.env['stock.quant'].quants_get_preferred_domain(
                move_affected.product_uom_qty, move_affected)
            self.env['stock.quant'].quants_reserve(quants, move_affected)

    def _prepare_move_values(self):
        self.ensure_one()
        return {
            'name': self.origin,
            'origin': self.origin,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': self.qty,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id
        }
    def _get_move(self,production,estado):
        move = production.move_raw_ids.filtered(lambda x: x.product_id.id == self.product_id.id and x.state in estado)
        return move

    def _done_transfer(self):
        self.ensure_one()
        move = self.env['stock.move'].create(self._prepare_move_values())
        quants = self.env['stock.quant'].quants_get_preferred_domain(
            move.product_qty, move)
        self.env['stock.quant'].quants_reserve(quants, move)
        move.action_done()
