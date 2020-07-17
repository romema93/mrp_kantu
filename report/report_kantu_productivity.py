# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.sql import drop_view_if_exists


class ReportKantuProductivity(models.Model):
    _name = "report.kantu.productivity"
    _description = "Reporte de Productividad"
    _auto = False
    _order = "production_id,id"

    workcenter_id = fields.Many2one('mrp.workcenter', 'Centro de Producción', readonly=True)
    production_id = fields.Many2one('mrp.production', 'Ficha de Producción', readonly=True)
    workorder = fields.Char('Orden de Trabajo', readonly=True)
    base_id = fields.Many2one('product.product', 'Base', readonly=True)
    product_qty = fields.Integer('Piezas', readonly=True)
    base_qty = fields.Float('Bases', readonly=True)
    merma_src_qty = fields.Integer('Piezas Merma', readonly=True)
    merma_base_src_qty = fields.Float('Bases Merma', readonly=True)
    meters_qty = fields.Float('Metros', readonly=True)
    diff_meters = fields.Float('Diferencia Metros', readonly=True)

    @api.model_cr
    def init(self):
        drop_view_if_exists(self._cr, 'report_kantu_productivity')
        self._cr.execute("""
                    create or replace view report_kantu_productivity as (
                        SELECT
                            workorder."id" AS ID,
                            workcenter."id" AS workcenter_id,
                            production."id" AS production_id,
                            UPPER(workorder."name") AS workorder,
                            productbase."id" AS base_id,
                            workorder.qty_produced AS product_qty,
                            workorder.qty_produced / (
                                production.product_qty / ldm.product_uom_qty
                            ) AS base_qty,
                            SUM (
                                CASE
                                WHEN mermasrc.product_id = production.product_id THEN
                                    mermasrc.qty
                                WHEN mermasrc.product_id = productbase."id" THEN
                                    mermasrc.qty * (
                                        production.product_qty / ldm.product_uom_qty
                                    )
                                END
                            ) AS merma_src_qty,
                            SUM (
                                CASE
                                WHEN mermasrc.product_id = productbase."id" THEN
                                    mermasrc.qty
                                WHEN mermasrc.product_id = production.product_id THEN
                                    mermasrc.qty / (
                                        production.product_qty / ldm.product_uom_qty
                                    )
                                END
                            ) AS merma_base_src_qty,
                            AVG (
                                CASE
                                WHEN templatebase.metros_base IS NOT NULL THEN
                                    workorder.qty_produced / (
                                        production.product_qty / ldm.product_uom_qty
                                    ) / templatebase.metros_base
                                ELSE
                                    0
                                END
                            ) AS meters_qty,
                            (
                                AVG (
                                    CASE
                                    WHEN templatebase.metros_base IS NOT NULL THEN
                                        prev_workorder.qty_produced / (
                                            production.product_qty / ldm.product_uom_qty
                                        ) / templatebase.metros_base
                                    ELSE
                                        0
                                    END
                                ) - AVG (
                                    CASE
                                    WHEN templatebase.metros_base IS NOT NULL THEN
                                        workorder.qty_produced / (
                                            production.product_qty / ldm.product_uom_qty
                                        ) / templatebase.metros_base
                                    ELSE
                                        0
                                    END
                                )
                            ) AS diff_meters
                        FROM
                            mrp_workorder workorder
                        INNER JOIN mrp_production production ON production."id" = workorder.production_id
                        INNER JOIN mrp_workcenter workcenter ON workcenter."id" = workorder.workcenter_id
                        INNER JOIN resource_resource resource ON resource."id" = workcenter.resource_id
                        INNER JOIN stock_move ldm ON ldm.raw_material_production_id = production."id"
                        INNER JOIN product_product productbase ON productbase."id" = ldm.product_id
                        INNER JOIN product_template templatebase ON templatebase."id" = productbase.product_tmpl_id
                        AND templatebase.bases_x_carro IS NOT NULL
                        LEFT JOIN mrp_merma mermasrc ON mermasrc.wo_source_id = workorder."id"
                        LEFT JOIN mrp_workorder prev_workorder ON prev_workorder.next_work_order_id = workorder."id"
                        WHERE
                            workorder."state" = 'supervisado'
                        GROUP BY
                            workcenter."id",
                            production."id",
                            workorder."id",
                            productbase."id",
                            workorder.qty_produced,
                            base_qty,
                            workorder."id"
                    )""")
