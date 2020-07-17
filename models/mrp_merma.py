# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MrpMerma(models.Model):
    _name = 'mrp.merma'

    name = fields.Char('Motivo')
    type_id = fields.Many2one('mrp.merma.type', string='Tipo de merma')
    wo_source_id = fields.Many2one('mrp.workorder', required=True)
    wo_dest_id = fields.Many2one('mrp.workorder', 'Orden de Trabajo', required=True)
    product_id = fields.Many2one('product.product', 'Producto', required=True)
    product_uom_id = fields.Many2one('product.uom', 'Unidad de medida', required=True)
    qty = fields.Float('Cantidad', default=1.0)
    alter_production = fields.Boolean('Alterar Cantidad de Producción')
    servicio_id = fields.Many2one('product.product', 'Servicio Descuento', domain=[('type', '=', 'service'),
                                                                                   ('standard_price', '<=', 0)])
    scrap_location_id = fields.Many2one('stock.location', 'Ubicacion de Desecho')
    lot_id = fields.Many2one(
        'stock.production.lot', 'Lote', domain="[('product_id', '=', product_id)]")
    lot_available = fields.Boolean(compute="_compute_lot_available")
    discount_required = fields.Boolean(related='type_id.discount_required')

    @api.multi
    def name_get(self):
        return [(merma.id, '%s %s' % (
        merma.name, '[' + merma.wo_source_id.name + ']' if merma.wo_source_id != merma.wo_dest_id else '')) for merma in
                self]

    @api.onchange('product_id')
    def _compute_lot_available(self):
        if self.product_id.tracking == 'lot':
            self.lot_available = True
        else:
            self.lot_available = False

    @api.onchange('product_id')
    def _load_lots(self):
        if self.product_id:
            move = self.wo_dest_id.production_id.move_raw_ids.filtered(lambda x: x.product_id == self.product_id)
            lot_ids = move.active_move_lot_ids.mapped('lot_id.id')
            domain = {'lot_id': [('id', '=', lot_ids)]}
            return {'domain': domain}

    @api.model
    def create(self, vals):
        del vals['discount_required']
        merma_type = self.env['mrp.merma.type'].browse([vals['type_id']])
        vals['name'] = merma_type.name
        merma = super(MrpMerma, self).create(vals)
        merma._do_merma()
        merma._create_payment()
        return merma

    @api.multi
    def action_done(self):
        return {'type': 'ir.actions.act_window_close'}

    # Actualizar modelos relacionados a la merma
    @api.multi
    def _do_merma(self):
        for merma in self:
            if merma.scrap_location_id:
                merma._create_move()
                merma._alter_move()
                # raw_moves = merma.wo_source_id.move_raw_ids.filtered(
                #     lambda x: (x.has_tracking == 'none') and (x.state not in ('done', 'cancel')) and x.bom_line_id)
                # for move in raw_moves:
                #     if move.unit_factor:
                #         rounding = move.product_uom.rounding
                #         qty = self.wo_source_id.production_id.product_qty-merma.wo_source_id.qty_production+merma.qty
                #         move.quantity_done += float_round(qty * move.unit_factor,
                #                                           precision_rounding=rounding)

    def _create_move(self):
        if self.product_id.tracking == 'lot' and not self.lot_id:
            raise UserError('Debe Seleccionar un lote(Palet) para este producto')
        move = self.env['stock.move'].create(self._prepare_move_values())
        quants = self.env['stock.quant'].quants_get_preferred_domain(
            move.product_qty, move,
            domain=[
                ('qty', '>', 0),
                ('lot_id', '=', self.lot_id.id)])
        if any([not x[0] for x in quants]):
            raise UserError(_(
                'You cannot scrap a move without having available stock for %s. You can correct it with an inventory adjustment.') % move.product_id.name)
        self.env['stock.quant'].quants_reserve(quants, move)
        move.action_done()

    def _alter_move(self):
        production = self.wo_source_id.production_id
        move = production.move_raw_ids.filtered(lambda x: x.product_id == self.product_id and x.scrapped == False)[0]
        active_lot = move.active_move_lot_ids.filtered(lambda x: x.lot_id == self.lot_id)
        qty_merma = self.product_uom_id._compute_quantity(self.qty, move.product_uom)
        qty = move.product_uom_qty - qty_merma
        unit_factor = qty / production.product_qty
        active_lot.write({
            'quantity_done': active_lot.quantity_done - qty_merma,
            'quantity': active_lot.quantity - qty_merma
        })
        move.write({
            'product_uom_qty': qty,
            'quantity_done': move.quantity_done - qty_merma,
            'unit_factor': unit_factor
        })

    def _prepare_move_values(self):
        self.ensure_one()
        values = {
            'name': self.name,
            'origin': self.wo_source_id.production_id.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': self.qty,
            'location_id': self.wo_source_id.production_id.location_src_id.id,
            'location_dest_id': self.scrap_location_id.id,
            'restrict_lot_id': self.lot_id.id,
            # 'raw_material_production_id': self.wo_source_id.production_id.id,
            # 'production_id': self.wo_source_id.production_id.id,
            'scrapped': True
        }
        return values

    def _calculate_qty(self):
        # # convertimos la unidad de medida a la del BoM
        # from_uom = self.product_uom_id
        # bom = self.wo_source_id.production_id.bom_id
        # bom_line = bom.bom_line_ids.filtered(
        #     lambda x: x.product_id.id == self.product_id.id)
        # to_uom = bom_line.product_uom_id  # obtiene la uom de la bom
        # qty = from_uom._compute_quantity(self.qty, to_uom)
        # return (qty * bom.product_qty) / bom_line.product_qty

        # convertimos la unidad de medida a la del BoM
        from_uom = self.product_uom_id
        production_id = self.wo_source_id.production_id
        move_raw = production_id.move_raw_ids.filtered(
            lambda x: x.product_id.id == self.product_id.id and x.state != 'cancel')
        to_uom = move_raw.product_uom  # obtiene la uom de la bom
        qty = from_uom._compute_quantity(self.qty, to_uom)
        return (qty * production_id.product_qty) / move_raw.product_uom_qty

    @api.multi
    def _create_payment(self):
        for merma in self:
            if merma.servicio_id:
                empleados = merma.wo_dest_id.pago_ids.mapped('empleado_id')
                qty = merma.qty
                if merma.product_id != self.wo_source_id.product_id:
                    qty = merma._calculate_qty()
                pago_ids = merma.wo_dest_id._crear_datos_pago(
                    empleados, merma.servicio_id.id, qty, merma.id, merma.wo_dest_id.id)
                if pago_ids:
                    monto = pago_ids[0]._calcular_monto_pagar(len(pago_ids))
                    # pago_ids.write({'monto':monto})
                    for p in pago_ids:
                        p.monto = monto
                else:
                    raise UserError('No se asigno personal a la orden de trabajo: ' + self.wo_dest_id.name)


class MrpMermaType(models.Model):
    _name = 'mrp.merma.type'

    name = fields.Char('Descripcion')
    discount_required = fields.Boolean('Se requiere descuento?')
