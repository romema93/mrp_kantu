# -*- coding: utf-8 -*-
from odoo import api, models, fields

class ResUsers(models.Model):
    _inherit = "res.users"

    picking_type_ids = fields.Many2many('stock.picking.type',string='Tipos de Operacion')

class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    res_users_ids = fields.Many2many('res.users',string='Responsables')

