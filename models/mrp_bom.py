# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    bom_line_service_ids = fields.One2many('mrp.bom.line', 'bom_service_id', 'BoM Service Lines', copy=True)

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id,
                 u"%s (%s)" % (record.product_tmpl_id.name, record.routing_id.name or '')
                 ))
        return result

    @api.onchange('routing_id')
    def onchange_routing(self):
        self.bom_line_service_ids.update({
            'operation_id': False
        })


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    bom_id = fields.Many2one('mrp.bom', required=False)
    bom_service_id = fields.Many2one('mrp.bom', 'Parent BoM', ondelete='cascade', required=True)
    numero_pasadas = fields.Integer('Numero de Pasadas')
