# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.exceptions import UserError


class MrpPago(models.Model):
    _name = "mrp.periodo"
    _order = "date_start desc"

    name = fields.Char('Nombre', required=True)
    date_start = fields.Date("Fecha Inicio", required=True)
    date_finish = fields.Date("Fecha Final", required=True)
    active = fields.Boolean(default=True)
    prev_periodo = fields.Many2one('mrp.periodo', compute="_compute_related_periodo")
    next_periodo = fields.Many2one('mrp.periodo', compute="_compute_related_periodo")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Ya existe un periodo con este nombre !"),
    ]

    @api.one
    def _compute_related_periodo(self):
        next_periodos = self.search(
            ['|', ('active', '=', False), ('active', '=', True), ('date_start', '>', self.date_finish)])
        prev_periodos = self.search(
            ['|', ('active', '=', False), ('active', '=', True), ('date_finish', '<', self.date_start)])
        if next_periodos:
            self.next_periodo = next_periodos[-1]
        if prev_periodos:
            self.prev_periodo = prev_periodos[0]

    @api.onchange('date_start', 'date_finish')
    def _onchange_date(self):
        if self.date_start and self.date_finish:
            if fields.Date.from_string(self.date_start) > fields.Date.from_string(self.date_finish):
                raise UserError('La fecha final tiene que ser mayor a la fecha de inicio')

    @api.model
    def create(self, vals):
        if self._find_same_interval_dates(vals):
            raise UserError('Fechas invalidas, existen periodos en el intervalo de estas fechas')
        active_periodo = self.search([('active', '=', True)])
        if len(active_periodo) == 1:
            if fields.Date.from_string(active_periodo.date_start) > fields.Date.from_string(vals['date_start']):
                vals['active'] = False
            else:
                active_periodo.write({
                    'active': False
                })
        elif len(active_periodo) > 1:
            raise UserError('Existe mas de un periodo activo')
        return super(MrpPago, self).create(vals)

    @api.one
    def write(self, vals):
        if self._find_same_interval_dates(vals):
            raise UserError('Fechas invalidas, existen periodos en el intervalo de estas fechas')
        return super(MrpPago, self).write(vals)

    @api.one
    def update_pagos(self):
        pagos = self.env['mrp.pago'].search(
            [('fecha_pago', '>=', self.date_start), ('fecha_pago', '<=', self.date_finish)])
        pagos.write({
            'periodo_id': self.id
        })
        return True

    def _find_same_interval_dates(self, vals):
        periodo_in_same_date_start = False
        periodo_in_same_date_finish = False
        date_start = vals.get('date_start')
        date_finish = vals.get('date_finish')
        domain1 = ['|', ('active', '=', False), ('active', '=', True)]
        domain2 = ['|', ('active', '=', False), ('active', '=', True)]
        if self.id:
            domain1.append(('id', '!=', self.id))
            domain2.append(('id', '!=', self.id))
        if date_start:
            domain1.append(('date_start', '<=', date_start))
            domain1.append(('date_finish', '>=', date_start))
            periodo_in_same_date_start = self.search(domain1)
        if date_finish:
            domain2.append(('date_start', '<=', date_finish))
            domain2.append(('date_finish', '>=', date_finish))
            periodo_in_same_date_finish = self.search(domain2)
        if periodo_in_same_date_start or periodo_in_same_date_finish:
            return True
        else:
            return False
