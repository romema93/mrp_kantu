# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.exceptions import ValidationError


class MrpPago(models.Model):
    _name = "mrp.pago"

    """--------------------------------
               DEFAULT FUNCTIONS
       --------------------------------"""

    def _get_company_currency(self):
        return self.env.user.company_id.currency_id

    """/------------- DEFAULT FUNCTIONS"""

    """---------------------------
                FIELDS
    ------------------------------"""

    servicio_id = fields.Many2one('product.product', 'Servicio', domain=[('type', '=', 'service')], required=True)
    price = fields.Monetary(string='Precio', compute="_compute_price", store=True)
    empleado_id = fields.Many2one('hr.employee', 'Personal', required=True)
    workorder_id = fields.Many2one('mrp.workorder', 'Orden de Trabajo', ondelete="cascade")
    merma_id = fields.Many2one('mrp.merma', 'Merma', ondelete="cascade")
    production_id = fields.Many2one('mrp.production', 'Orden de Produccion', related='workorder_id.production_id',
                                    store=True)
    qty = fields.Integer('Cantidad de Productos')
    monto = fields.Monetary('Pago', store=True)
    currency_id = fields.Many2one('res.currency', default=_get_company_currency, readonly=True, string="Moneda")
    fecha_pago = fields.Date('Fecha del trabajo')
    periodo_id = fields.Many2one('mrp.periodo', 'Periodo de Producción', compute='_compute_periodo', store=True)
    """Modificaciones para la mejora"""
    # unit_factor = fields.Float('Unit Factor', compute="_compute_unit_factor", store=True)
    # price = fields.Float(string='Precio', compute="_compute_unit_factor", store=True)
    pay_group_compute_id = fields.Many2one('pay.group.compute')

    """/--------------------------- FIELDS"""

    """---------------------------------
            COMPUTE FUNCTIONS
    ---------------------------------"""

    @api.depends('fecha_pago')
    def _compute_periodo(self):
        for pago in self:
            if pago.fecha_pago:
                periodo = self.env['mrp.periodo'].search(
                    ['|', ('active', '=', True), ('active', '=', False), ('date_start', '<=', pago.fecha_pago),
                     ('date_finish', '>=', pago.fecha_pago)])
                if len(periodo) == 1:
                    pago.periodo_id = periodo

    @api.depends('servicio_id')
    def _compute_price(self):
        for pago in self:
            if pago.servicio_id:
                pago.price = pago.servicio_id.standard_price

    # @api.depends('workorder_id', 'servicio_id')
    # def _compute_unit_factor(self):
    #     for pago in self:
    #         if pago.servicio_id:
    #             bom = pago.workorder_id.production_id.bom_id
    #             bom_line_services = bom.bom_line_service_ids
    #             if bom_line_services:
    #                 service_line = bom_line_services.filtered(lambda x: x.product_id.id == pago.servicio_id.id and (
    #                         x.operation_id.name == pago.workorder_id.name or x.operation_id is False))
    #                 if len(service_line) > 1:
    #                     raise ValidationError('Se encontro más de un servicio de pago para la operacion')
    #                 if not service_line:
    #                     raise ValidationError('No se encontro un servicio de pago')
    #                 service = service_line.product_id
    #                 pago.unit_factor = service_line.product_qty / bom.product_qty
    #                 pago.price = service.uom_id._compute_price(service.standard_price, service_line.product_uom_id)
    #
    # @api.depends('workorder_id.pago_ids', 'servicio_id', 'price', 'qty')
    # def _compute_monto(self):
    #     for pago in self:
    #         if pago.workorder_id.pago_ids and pago.servicio_id and pago.qty and pago.price:
    #             employees_with_same_pay = len(
    #                 pago.workorder_id.pago_ids.filtered(lambda x: x.servicio_id.id == pago.servicio_id.id))
    #             pago.monto = (pago.qty * pago.unit_factor * pago.price) / employees_with_same_pay

    """/------------------- COMPUTE FUNCTIONS"""

    """-----------------------------
            ONCHANGE FUNCTIONS
    -----------------------------"""

    def get_service_line(self):
        bom = self.workorder_id.production_id.bom_id
        bom_line_services = bom.bom_line_service_ids
        if bom_line_services:
            service_line = bom_line_services.filtered(lambda x: x.product_id.id == self.servicio_id.id and (
                    x.operation_id.name == self.workorder_id.name or x.operation_id is False))
            if len(service_line) > 1:
                raise ValidationError('Se encontro más de un servicio de pago para la operacion')
            if not service_line:
                raise ValidationError('No se encontro un servicio de pago')
            return service_line

    @api.onchange('empleado_id')
    def onchange_empleado(self):
        possible_service_ids = self.production_id.bom_id.bom_line_service_ids.mapped('product_id').ids
        if self.empleado_id and self.workorder_id:
            suggested_service = self.search(
                [('empleado_id', '=', self.empleado_id.id), ('workorder_id.name', '=', self.workorder_id.name),
                 ('monto', '>=', 0), ('servicio_id.id', 'in', possible_service_ids)],
                limit=1).mapped('servicio_id')
            if suggested_service:
                self.servicio_id = suggested_service
            else:
                self.servicio_id = False
        return {'domain': {'servicio_id': [('id', 'in', possible_service_ids)]}}

    """/-------------- ONCHNAGE FUNCTIONS"""

    """------------------------------
            OTHER FUNCTIONS
    ------------------------------"""

    def _calcular_monto_pagar(self, nro_operarios):
        bom_line_id = (self.workorder_id.production_id.bom_id.bom_line_service_ids.filtered(
            lambda r: r.product_id.id == self.servicio_id.id))[0]
        factor = self.workorder_id.product_uom_id._compute_quantity(self.qty,
                                                                    self.workorder_id.production_id.bom_id.product_uom_id) / self.workorder_id.production_id.bom_id.product_qty
        unit_price = self.servicio_id.uom_id._compute_price(self.servicio_id.standard_price, bom_line_id.product_uom_id)
        monto_total = unit_price * bom_line_id.product_qty * factor
        monto_pagar = monto_total / nro_operarios
        return monto_pagar

    def _calcular_monto(self, servicio_id, product_uom_id, nro_operarios, product_qty, workorder_id=False):
        if workorder_id:
            factor = self.workorder_id.product_uom_id._compute_quantity(self.qty,
                                                                        self.workorder_id.production_id.bom_id.product_uom_id) / self.workorder_id.production_id.bom_id.product_qty
        else:
            factor = 1
        unit_price = servicio_id.uom_id._compute_price(servicio_id.standard_price, product_uom_id)
        monto_total = unit_price * product_qty * factor
        monto_pagar = monto_total / nro_operarios
        return monto_pagar

    """/-------------- OTHER FUNCTIONS"""

    class HrEmployee(models.Model):
        _inherit = "hr.employee"

        pago_ids = fields.One2many('mrp.pago', 'empleado_id', 'Pagos')
