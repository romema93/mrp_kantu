# -*- coding: utf-8 -*-
from odoo import api, models, fields

class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    load_default_employees = fields.Boolean(string="Cargar empleados automaticamente",default=True,
                                            help="Al planificar la orden de producción, se cargara automaticamente a todos los empleados configurados en el centro de producción.")