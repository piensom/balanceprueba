# -*- coding: utf-8 -*-

import xlwt
from xlwt import *
import base64
from datetime import timedelta, date
from io import BytesIO
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SalesJournalReportWizard(models.TransientModel):
    _name = 'sales.journal.report.wizard'
    _description = 'Sales Journal Report Wizard'

    from_date = fields.Date('From Date', default=fields.Date.today(), required=True)
    to_date = fields.Date('To Date', default=fields.Date.today(), required=True)
    company_id = fields.Many2one('res.company', string='Company')
    folio = fields.Char(string="Folio")

    def print_report(self):
        self.ensure_one()
        [data] = self.read()

        datas = {
            # 'ids': [],
            'form': data,
            'month': self.from_date.strftime("%m"),
            'month_name': self.from_date.strftime("%B"),
            'year': self.from_date.strftime("%Y"),
            'folio': self.folio,
        }
        return self.env.ref('sales_journal_report.action_report_sales_journal').report_action(self, data=datas)
