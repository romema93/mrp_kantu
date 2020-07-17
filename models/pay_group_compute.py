# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PaidGroupCompute(models.Model):
    _name = "pay.group.compute"

    employee_id = fields.Many2one('hr.employee', string="Empleado")
    workdays = fields.Float(string='Dias trabajados')
    mrp_pago_ids = fields.One2many('mrp.pago', 'pay_group_compute_id')
    group_pay_id = fields.Many2one('mrp.group.pay')
    percentage = fields.Float(compute="_compute_percentage", string="Porcentage(%)")

    @api.depends('group_pay_id')
    def _compute_percentage(self):
        total_workdays = sum(self[0].group_pay_id.pay_group_compute_ids.mapped('workdays'))
        for item in self:
            item.percentage = (item.workdays * 100) / total_workdays
