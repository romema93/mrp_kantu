# -*- coding: utf-8 -*-

from odoo import api, models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def _get_default_route_ids(self):
        if self.env.context.get('manufacture', False):
            return self.env.ref("mrp.route_warehouse0_manufacture")

    alto = fields.Float('Alto', (3, 2))
    ancho = fields.Float('Ancho', (3, 2))
    espesor = fields.Float('Espesor', (2, 2))
    bases_x_carro = fields.Integer('Bases por Carro')
    max_carros = fields.Integer('Número maximo de carros')
    metros_base = fields.Float(string='Metros Base', digits=(3, 2))
    disenador_id = fields.Many2one('hr.employee', 'Diseñador')
    numero_mallas = fields.Integer('Número Mallas')
    calculate_qty_op = fields.Boolean('Calcular cantidad?', default=False,
                                      help="Si esta habilitado, realizara el calculo de las piezas en las Ordenes de Produccion en función a la base que utiliza")
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Cantidad de adjuntos')
    route_ids = fields.Many2many(default=_get_default_route_ids)

    @api.multi
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'product.template'), ('res_id', 'in', self.ids), ('res_field', '=', False)], ['res_id'],
            ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for product in self:
            product.attachment_number = attachment.get(product.id, 0)

    @api.multi
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'product.template'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'product.template', 'default_res_id': self.id}
        return res
