# -*- coding: utf-8 -*-
from odoo import api, models, fields


class MrpGroupPay(models.Model):
    _name = "mrp.group.pay"

    name = fields.Char('Referencia')
    mrp_production_ids = fields.One2many('mrp.production', 'group_pay_id')
    pay_group_compute_ids = fields.One2many('pay.group.compute', 'group_pay_id')
    mrp_periodo_id = fields.Many2one('mrp.periodo', string='Periodo')
