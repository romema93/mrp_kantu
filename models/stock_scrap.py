# -*- coding: utf-8 -*-
# Modulo para definir el modelo stock.scrap como una posible merma

from odoo import api, fields, models


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    type_id = fields.Many2one('mrp.merma.type', 'Motivo')
    workorder_dest_id = fields.Many2one('mrp.workorder', 'Orden de Trabajo')
    servicio_id = fields.Many2one('product.product', 'Servicio Descuento', domain=[('type', '=', 'service'),
                                                                                   ('standard_price', '<=', 0)])
