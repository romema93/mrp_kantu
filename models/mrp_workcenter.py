# -*- coding: utf-8 -*-
import datetime
from odoo import api, models, fields


class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    employee_ids = fields.Many2many('hr.employee', 'employee_workcenter_rel', 'workcenter_id', 'employee_id',
                                    string='Personal')
    workorder_done_count = fields.Integer('# Ordenes Terminadas', compute='_compute_workorder_count')

    @api.depends('order_ids.duration_expected', 'order_ids.workcenter_id', 'order_ids.state',
                 'order_ids.date_planned_start')
    def _compute_workorder_count(self):
        super(MrpWorkcenter, self)._compute_workorder_count()
        MrpWorkorder = self.env['mrp.workorder']
        result = {wid: {} for wid in self.ids}
        res = MrpWorkorder.read_group(
            [('workcenter_id', 'in', self.ids), ('state', 'not in', ('supervisado', 'cancel'))],
            ['workcenter_id', 'state'], ['workcenter_id', 'state'],
            lazy=False)
        for res_group in res:
            result[res_group['workcenter_id'][0]][res_group['state']] = res_group['__count']
        for workcenter in self:
            workcenter.workorder_count = sum(count for state, count in result[workcenter.id].items())
            workcenter.workorder_done_count = result[workcenter.id].get('done', 0)

        """MrpWorkorder = self.env['mrp.workorder']
        result = {wid: {} for wid in self.ids}
        result_duration_expected = {wid: 0 for wid in self.ids}
        # Count Late Workorder
        data = MrpWorkorder.read_group([('workcenter_id', 'in', self.ids), ('state', 'in', ('pending', 'ready')),
                                        ('date_planned_start', '<', datetime.datetime.now().strftime('%Y-%m-%d'))],
                                       ['workcenter_id'], ['workcenter_id'])
        count_data = dict((item['workcenter_id'][0], item['workcenter_id_count']) for item in data)
        # Count All, Pending, Ready, Progress Workorder
        res = MrpWorkorder.read_group(
            [('workcenter_id', 'in', self.ids)],
            ['workcenter_id', 'state', 'duration_expected'], ['workcenter_id', 'state'],
            lazy=False)
        for res_group in res:k
            result[res_group['workcenter_id'][0]][res_group['state']] = res_group['__count']
            if res_group['state'] in ('pending', 'ready', 'progress'):
                result_duration_expected[res_group['workcenter_id'][0]] += res_group['duration_expected']
        for workcenter in self:
            workcenter.workorder_count = sum(
                count for state, count in result[workcenter.id].items() if state not in ('supervisado', 'cancel'))
            workcenter.workorder_pending_count = result[workcenter.id].get('pending', 0)
            workcenter.workcenter_load = result_duration_expected[workcenter.id]
            workcenter.workorder_ready_count = result[workcenter.id].get('ready', 0)
            workcenter.workorder_progress_count = result[workcenter.id].get('progress', 0)
            workcenter.workorder_done_count = result[workcenter.id].get('done', 0)
            workcenter.workorder_late_count = count_data.get(workcenter.id, 0)"""
