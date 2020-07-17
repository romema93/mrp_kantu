# -*- coding: utf-8 -*-
from odoo import api, models, fields
import json

class MrpProduccion(models.Model):
    _inherit = "stock.move"
    se_produce = fields.Boolean('Puede Producirse?', compute="_compute_se_produce")
    product_stock = fields.Float(related="product_id.virtual_available", store=False)

    @api.depends('product_id')
    def _compute_se_produce(self):
        for move in self:
            if move.product_id.bom_ids:
                move.se_produce = True
            else:
                move.se_produce = False

    @api.multi
    def button_crear_op(self):
        self.ensure_one()
        return {
            'name': 'Crear Orden Producción',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.production',
            'view_id': self.env.ref('mrp.mrp_production_form_view').id,
            'type': 'ir.actions.act_window',
            'context': {
                'default_product_id': self.product_id.id,
                'qty_product': self.product_uom_qty,
            },
            'target': 'current',
        }

    @api.multi
    def button_transferir(self):
        self.ensure_one()
        return {
            'name': 'Transferir',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.production.transfer',
            'view_id': self.env.ref('mrp_kantu.production_transfer_wizard').id,
            'type': 'ir.actions.act_window',
            'context': {
                'default_origin': self.group_id.name,
                'default_product_id': self.product_id.id,
                'default_qty': self.product_uom_qty,
                'default_location_dest_id': self.location_id.id,
                'default_product_uom_id': self.product_uom.id,
            },
            'target': 'new',
        }

    def _calculateUnitFactor(self,p_qty):
        original_quantity = self.raw_material_production_id.product_qty - self.raw_material_production_id.qty_produced
        qty = self.product_qty + self.product_uom._compute_quantity(p_qty, self.product_id.uom_id)
        return qty/original_quantity

    def CreateMrpFromMove(self, values):
        procurements = self.env['procurement.order']
        original_quantity = self.raw_material_production_id.product_qty - self.raw_material_production_id.qty_produced
        if values['type'] == 'adicionar':
            #qty = self.product_qty + self.product_uom._compute_quantity(values['product_qty'], self.product_id.uom_id)
            qty = self.product_uom_qty + float(values['product_qty'])
        else:
            qty = values['product_qty']
        unit_factor = qty/original_quantity
        for move in self:
            qty_temp = move.product_uom_qty
            move.product_uom_qty = values['product_qty']
            procurements |= procurements.create(move._prepare_procurement_from_move())
            if values['type'] == 'adicionar':
                move.write({'product_uom_qty':qty_temp+values['product_qty'],'unit_factor':unit_factor})
            else:
                move.write({'product_uom_qty':values['product_qty'],'unit_factor':unit_factor})
        #if procurements:
            #procurements.run()
        op = self.env['mrp.production'].search([('origin','like',self.origin)],order='id desc',limit=1)
        return op.id

    def TransferQuantity(self,values):
        self.ensure_one()
        production = self.raw_material_production_id
        original_quantity = self.raw_material_production_id.product_qty - self.raw_material_production_id.qty_produced
        qty = float(values['product_uom_qty'])
        if (values['motivo'] == 'abastecimiento'):
            if self.product_uom_qty != qty:
                unit_factor = qty / original_quantity
                self.write({
                    'product_uom_qty': values.get('product_uom_qty'),
                    'unit_factor':unit_factor
                })
            self._done_transfer_qty(values)
            production.action_assign()
        elif (values['motivo'] == 'adicionar'):
            # Obtenemos el move que sera modificado
            qty = self.product_uom_qty + float(values['product_uom_qty'])
            unit_factor = qty / original_quantity
            self.write({
                'product_uom_qty': qty,
                'unit_factor': unit_factor,
            })
            # Transferir desde almacen
            self._done_transfer_qty(values)
            # Reserva la cantidad transferida al move del mrp.production
            #quants = self.env['stock.quant'].quants_get_preferred_domain(
            #    qty, self)
            #self.env['stock.quant'].quants_reserve(quants, self)
            production.action_assign()
        elif (values['motivo'] == 'devolucion'):
            self.do_unreserve()
            self._done_transfer_qty(values)
            self.write({
                'product_uom_qty': self.product_uom_qty - qty,
                'quantity_done_store': self.quantity_done_store - qty,
            })
            #quants = self.env['stock.quant'].quants_get_preferred_domain(
            #    self.product_uom_qty, self)
            #self.env['stock.quant'].quants_reserve(quants, self)
        return True

    def _done_transfer_qty(self,values):
        del values['motivo']
        self.ensure_one()
        values['move_dest_id'] = self.id
        move = self.env['stock.move'].create(values)
        quants = self.env['stock.quant'].quants_get_preferred_domain(
            move.product_qty, move)
        self.env['stock.quant'].quants_reserve(quants, move)
        move.action_done()