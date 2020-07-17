# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    def predict_next_sequence(self):
        if not self.use_date_range:
            if self.implementation == 'standard':
                number_next = self.number_next_actual
                return self.get_next_char(number_next)
            else:
                return False