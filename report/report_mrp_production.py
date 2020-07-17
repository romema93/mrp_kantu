# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.sql import drop_view_if_exists
from odoo.exceptions import ValidationError


class CustomMrpProductionReport(models.AbstractModel):
    _name = "report.mrp.report_mrporder"

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('mrp.report_mrporder')
        model_name = report.model
        model_data = self.env[model_name].browse(docids)
        for model in model_data:
            if model.routing_id and not model.workorder_ids:
                raise ValidationError('La ficha "%s" no se encuentra planificada' % model.display_name)
        docargs = {
            'doc_ids': docids,
            'doc_model': model_name,
            'docs': model_data,
        }
        return report_obj.render('mrp.report_mrporder', docargs)


class ReportMrpProduction(models.Model):
    _name = "report.mrp.production"
    _description = "Reporte de las Ordenes de Produccion"
    _auto = False
    _order = "production_id,pago_id"

    production_id = fields.Many2one('mrp.production', 'Ficha de Producción', readonly=True)
    product_id = fields.Many2one('product.template', 'Producto', readonly=True)
    mrp_workorder_name = fields.Char('Orden de Trabajo', readonly=True)
    workcenter_id = fields.Many2one('mrp.workcenter', 'Centro de Producción', readonly=True)
    qty = fields.Float('# Productos', readonly=True, group_operator='avg')
    price = fields.Float('Precio', readonly=True, group_operator='avg')
    employee_id = fields.Many2one('hr.employee', 'Personal', readonly=True)
    service_id = fields.Many2one('product.template', 'Servicio', readonly=True)
    monto = fields.Float('Pago', readonly=True)
    pago_id = fields.Many2one('mrp.pago', 'Pago', readonly=True)
    merma = fields.Char(string='Merma', readonly=True)
    fecha_pago = fields.Date(string="Fecha de Pago", readonly=True)
    periodo_id = fields.Many2one('mrp.periodo', 'Periodo', readonly=True)
    base = fields.Many2one('product.product', 'Base', readonly=True)
    total_bases = fields.Float(string="Bases", readonly=True, group_operator='avg')
    pasadas = fields.Integer(string="# Pasadas", readonly=True)
    ayudante = fields.Many2one('hr.employee', 'Ayudante', readonly=True)

    @api.model_cr
    def init(self):
        drop_view_if_exists(self._cr, 'report_mrp_production')
        self._cr.execute("""
                create or replace view report_mrp_production as (
                    SELECT
                        mrp_p."id" AS ID,
                        mrp_production."id" AS production_id,
                        pt."id" AS product_id,
                        mrp_wo."name" AS mrp_workorder_name,
                        wc."id" AS workcenter_id,
                        mrp_p.qty AS qty,
                        mrp_p.empleado_id AS employee_id,
                        pt2."id" AS service_id,
                        mrp_p.price AS price,
                        mrp_p.monto AS monto,
                        mrp_p."id" AS pago_id,
                        merma."name" AS merma,
                        mrp_p."fecha_pago" AS fecha_pago,
                        mrp_p.periodo_id AS periodo_id,
                        stock_move.product_id AS base,
                        mbl.numero_pasadas AS pasadas,
                        mrp_p.qty / (
                            mrp_production.product_qty / stock_move.product_uom_qty
                        ) AS total_bases,
                        pagoayudante.empleado_id AS ayudante
                    FROM
                        mrp_pago mrp_p
                    INNER JOIN product_template pt2 ON pt2."id" = mrp_p.servicio_id
                    LEFT JOIN mrp_workorder mrp_wo ON mrp_wo."id" = mrp_p.workorder_id
                    LEFT JOIN mrp_production ON mrp_production."id" = mrp_wo.production_id
                    LEFT JOIN mrp_bom ON mrp_bom."id" = mrp_production.bom_id
                    LEFT JOIN product_template pt ON pt."id" = mrp_production.product_id
                    LEFT JOIN mrp_workcenter wc ON wc."id" = mrp_wo.workcenter_id
                    LEFT JOIN mrp_merma merma ON merma."id" = mrp_p.merma_id
                    LEFT JOIN stock_move ON stock_move.raw_material_production_id = mrp_production."id"
                    AND stock_move.product_id IN (
                        SELECT
                            product_move."id"
                        FROM
                            product_product product_move
                        INNER JOIN product_template template_move ON template_move."id" = product_move.product_tmpl_id
                        WHERE
                            template_move.bases_x_carro IS NOT NULL
                    )
                    LEFT JOIN mrp_bom_line mbl ON mbl.bom_service_id = mrp_bom."id"
                    AND mbl.operation_id = mrp_wo.operation_id
                    AND mbl.product_id = mrp_p.servicio_id
                    LEFT JOIN mrp_pago pagoayudante ON pagoayudante.workorder_id = mrp_p.workorder_id
                    AND pagoayudante.servicio_id != mrp_p.servicio_id
                    AND pagoayudante.price > 0
                    AND mrp_p.price > 0
                    WHERE
                        mrp_p.qty IS NOT NULL
                    ORDER BY mrp_p."id"
                )""")


"""
SELECT
                        mrp_p."id" AS ID,
                        mrp_production. ID AS production_id,
                        pt."id" AS product_id,
                        mrp_wo."name" AS mrp_workorder_name,
                        wc."id" AS workcenter_id,
                        mrp_p.qty AS qty,
                        hr_employee. ID AS employee_id,
                        pt2."id" AS service_id,
                        mrp_p.price AS price,
                        mrp_p.monto AS monto,
                        mrp_p."id" AS pago_id,
                        merma."name" AS merma,
                        mrp_p."fecha_pago" AS fecha_pago,
                        mrp_p.periodo_id AS periodo_id,
                        (
                            SELECT
                                "sum" (mbl2.numero_pasadas)
                            FROM
                                mrp_bom_line mbl2
                            WHERE
                                mbl2.bom_service_id = mrp_bom."id"
                            AND mrp_p.servicio_id = mbl2.product_id
                            AND mbl2.operation_id = mrp_wo.operation_id
                        ) AS pasadas,
                        mrp_p.qty / (
                            SELECT
                                mrp_bom.product_qty / mbl.product_qty
                            FROM
                                mrp_bom_line mbl
                            INNER JOIN product_product mbl_pp ON mbl_pp."id" = mbl.product_id
                            INNER JOIN product_template mbl_pt ON mbl_pt."id" = mbl_pp.product_tmpl_id
                            WHERE
                                mbl.bom_id = mrp_bom."id"
                            AND mbl_pt.bases_x_carro IS NOT NULL
                        ) AS total_bases,
                        (
                            SELECT
                                mrp_p2.empleado_id
                            FROM
                                mrp_pago mrp_p2
                            INNER JOIN product_product pp2 ON pp2."id" = mrp_p2.servicio_id
                            INNER JOIN product_template pt3 ON pt3."id" = pp2.product_tmpl_id
                            WHERE
                                mrp_p2.workorder_id = mrp_p.workorder_id
                            AND pp2."id" != mrp_p.servicio_id and pt3."name" ILIKE '%ayudante%'
                        ) as ayudante
                    FROM
                        mrp_pago mrp_p
                    INNER JOIN product_template pt2 ON pt2."id" = mrp_p.servicio_id
                    INNER JOIN hr_employee ON hr_employee."id" = mrp_p.empleado_id
                    INNER JOIN mrp_workorder mrp_wo ON mrp_wo."id" = mrp_p.workorder_id
                    INNER JOIN mrp_production ON mrp_production."id" = mrp_wo.production_id
                    INNER JOIN mrp_bom ON mrp_bom."id" = mrp_production.bom_id
                    INNER JOIN product_template pt ON pt."id" = mrp_production.product_id
                    INNER JOIN mrp_workcenter wc ON wc."id" = mrp_wo.workcenter_id
                    LEFT JOIN mrp_merma merma ON merma."id" = mrp_p.merma_id
                    WHERE
                        mrp_p.qty IS NOT NULL
"""
