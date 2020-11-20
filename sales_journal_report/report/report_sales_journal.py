# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError


class ReportSalesJournal(models.AbstractModel):
    _name = 'report.sales_journal_report.report_sales_journal'
    _description = 'Account Sales Journal Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        sales_journal = self.env['ir.actions.report']._get_report_from_name('sales_journal_report.report_sales_journal')

        from_date = data['form']['from_date']
        to_date = data['form']['to_date']
        company_id = data['form']['company_id']

        acMove = self.env['account.move'].search(
            [('journal_id.type', '=', 'sale'),
            ('state', '=', 'posted'),
            ('date', '>=', from_date),
            ('date', '<=', to_date),
            ('company_id', '=', company_id[0])], order='id desc')

        return {
            'doc_model': sales_journal.model,
            'doc_ids': self.ids,
            'docs': self.ids,
            'get_month': data['month'],
            'get_month_name': data['month_name'],
            'get_year': data['year'],
            'get_folio': data['folio'],
            'get_from_date': data['form']['from_date'],
            'get_to_date': data['form']['to_date'],
            'get_move': acMove,
        }
