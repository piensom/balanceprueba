# -*- coding: utf-8 -*-

import xlwt
from xlwt import *
import base64
from datetime import timedelta, date
from io import BytesIO
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class journalItemReportWizard(models.TransientModel):
    _name = 'journal.items.report.wizard'
    _description = 'Journal Item Report Wizard'

    from_date = fields.Date('From Date', default=fields.Date.today(), required=True)
    to_date = fields.Date('To Date', default=fields.Date.today(), required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    excel_file = fields.Binary('Excel File')

    # Journal Report:
    def print_jurnal_report_xls(self):
        if self.id:
            filename = 'Account Report.xls'
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet('Account Report', cell_overwrite_ok=True)
            # style
            styleHeader = xlwt.easyxf(
                'font: name Calibri, bold True, color_index 0, height 260; align: horiz center; borders: top_color 0, bottom_color 0, right_color 0, left_color 0, left medium, right medium, top medium, bottom medium;')
            styleLable = xlwt.easyxf(
                'font: name Calibri, bold True, color_index 0, height 190; align: horiz center; borders: top_color 0, bottom_color 0, right_color 0, left_color 0, left medium, right medium, top medium, bottom medium;')
            styleLableSum = xlwt.easyxf(
                'font: name Calibri, bold True, color_index 0, height 210; align: horiz left; borders: top_color 0, bottom_color 0, right_color 0, left_color 0, left medium, right medium, top medium, bottom medium;')
            styleSum = xlwt.easyxf(
                'font: name Calibri, bold True, color_index 0, height 210; align: horiz right; borders: top_color 0, bottom_color 0, right_color 0, left_color 0, left medium, right medium, top medium, bottom medium;')
            styleVals = xlwt.easyxf(
                'font: name Calibri, bold True, color_index 0, height 160; align: horiz right; borders: top_color 0, bottom_color 0, right_color 0, left_color 0, left medium, right medium, top medium, bottom medium;')

            worksheet.write_merge(0, 1, 0, 8, 'Account Report Details', styleHeader)
            worksheet.write_merge(3, 3, 0, 1, 'From Dtae:  ' + str(self.from_date), styleLableSum)
            worksheet.write(3, 2, 'To Dtae:  ' + str(self.to_date), styleLableSum)
            worksheet.col(0).width = 3000
            worksheet.col(1).width = 4000
            worksheet.col(2).width = 8000
            worksheet.col(3).width = 8000
            worksheet.col(4).width = 9900
            worksheet.col(5).width = 6000
            worksheet.col(6).width = 6000
            worksheet.col(7).width = 6000
            worksheet.col(8).width = 6000

            worksheet.write(5, 0, "No.", styleLable)
            worksheet.write(5, 1, "Code", styleLable)
            worksheet.write(5, 2, "Account", styleLable)
            worksheet.write(5, 3, "Vat", styleLable)
            worksheet.write(5, 4, "Customer", styleLable)
            worksheet.write(5, 5, "Initial Balance", styleLable)
            worksheet.write(5, 6, "Debit", styleLable)
            worksheet.write(5, 7, "Credit", styleLable)
            worksheet.write(5, 8, "Total Balance", styleLable)

            self._cr.execute('''
                SELECT aa.code As ac_code,
                    aa.name As ac_name,
                    rp.vat As vat,
                    rp.name As partner_name,
                    sum(aml.debit) As debit,
                    sum(aml.credit) As credit
                FROM account_move_line aml
                    JOIN account_account aa ON aa.id = aml.account_id
                    JOIN res_partner rp ON aml.partner_id = rp.id
                WHERE aml.parent_state = 'posted' AND aml.date >= %s AND aml.date <= %s AND aml.company_id = %s OR aml.partner_id IS NULL
                GROUP BY aa.code, aa.name, rp.vat, rp.name
                ORDER BY aa.code, rp.name
                ''', [str(self.from_date), str(self.to_date), self.company_id.id])
            accountMoveLineDict = self.env.cr.dictfetchall()

            moveLineUsed = self.env['account.move.line'].search(
                    [('date','>=', str(self.from_date)),('date','<=', str(self.to_date)),
                    ('parent_state','=', 'posted'),('company_id', '=', self.company_id.id)])
            moveLineUsedIds = [x.id for x in moveLineUsed if x.partner_id]
            moveLineUsedPartnerIds = [x.partner_id.id for x in moveLineUsed if x.partner_id]

            dataDict = {}
            if accountMoveLineDict:
                for data in accountMoveLineDict:
                    balance_init = 0
                    initial_lines = self.env['account.move.line'].search(
                                        [('date','<', self.from_date),
                                        ('parent_state','=', 'posted'),
                                        ('account_id.code','=', data['ac_code']),
                                        ('partner_id.name','=', data['partner_name'])])
                    if initial_lines:
                        balance_init = sum(initial_lines.mapped('balance'))
                    balance_end = balance_init + data['debit'] - data['credit']

                    dataDict.setdefault(data['ac_code'],[])
                    dataDict[data['ac_code']].append({
                                                    'ac_code': data['ac_code'],
                                                    'ac_name': data['ac_name'],
                                                    'vat': data['vat'],
                                                    'partner_name': data['partner_name'],
                                                    'balance_init': balance_init,
                                                    'debit': data['debit'],
                                                    'credit': data['credit'],
                                                    'balance_end': balance_end
                                                })

                row = 6
                for acCode in dataDict:
                    number = 1
                    sumInit = 0.0
                    sumDebit = 0.0
                    sumCredit = 0.0
                    sumEnd = 0.0
                    acName = ''
                    for line in dataDict[acCode]:
                        worksheet.write(row, 0, number, styleVals)
                        worksheet.write(row, 1, line['ac_code'], styleVals)
                        worksheet.write(row, 2, line['ac_name'], styleVals)
                        worksheet.write(row, 3, line['vat'], styleVals)
                        worksheet.write(row, 4, line['partner_name'], styleVals)
                        worksheet.write(row, 5, line['balance_init'], styleVals)
                        worksheet.write(row, 6, line['debit'], styleVals)
                        worksheet.write(row, 7, line['credit'], styleVals)
                        worksheet.write(row, 8, line['balance_end'], styleVals)
                        # sumInit += line['balance_init']
                        # sumDebit += line['debit']
                        # sumCredit += line['credit']
                        # sumEnd += line['balance_end']
                        acName = line['ac_name']
                        number += 1
                        row += 1

                    self._cr.execute('''
                        SELECT aa.code As ac_code,
                            aa.name As ac_name,
                            rp.vat As vat,
                            rp.name As partner_name,
                            sum(aml.balance) As balance
                        FROM account_move_line aml
                            JOIN account_account aa ON aa.id = aml.account_id
                            JOIN res_partner rp ON aml.partner_id = rp.id
                        WHERE aml.parent_state = 'posted' AND aml.date < %s
                        AND aml.company_id = %s AND aa.code = %s AND rp.id NOT IN %s
                        GROUP BY aa.code, aa.name, rp.vat, rp.name
                        ORDER BY aa.code, rp.name
                        ''', [str(self.from_date), self.company_id.id, acCode, tuple(moveLineUsedPartnerIds),])
                    accountMoveLineRemain = self.env.cr.dictfetchall()

                    for rline in accountMoveLineRemain:
                        worksheet.write(row, 0, number, styleVals)
                        worksheet.write(row, 1, rline['ac_code'], styleVals)
                        worksheet.write(row, 2, rline['ac_name'], styleVals)
                        worksheet.write(row, 3, rline['vat'], styleVals)
                        worksheet.write(row, 4, rline['partner_name'], styleVals)
                        worksheet.write(row, 5, rline['balance'], styleVals)
                        worksheet.write(row, 6, 0, styleVals)
                        worksheet.write(row, 7, 0, styleVals)
                        worksheet.write(row, 8, 0, styleVals)
                        # sumInit += rline['balance']
                        number += 1
                        row += 1

                    otherMoveLine = self.env['account.move.line'].search(
                        [('id', 'not in', moveLineUsedIds),('account_id.code', '=', acCode),
                        ('date', '<', str(self.from_date)),('company_id', '=', self.company_id.id),
                        ('parent_state', '=', 'posted'),('partner_id', '=', False)])
                    print("otherMoveLine===============",otherMoveLine)
                    for x in otherMoveLine:
                        print('id:::::::::::::::',x.id)
                        print('balance:::::::::::::::',x.balance)
                    if otherMoveLine:
                        otherMoveInitBalance = sum(otherMoveLine.mapped('balance'))
                        worksheet.write(row, 0, number, styleVals)
                        worksheet.write(row, 1, acCode, styleVals)
                        worksheet.write(row, 2, acName, styleVals)
                        worksheet.write(row, 3, '-', styleVals)
                        worksheet.write(row, 4, 'Undefined', styleVals)
                        worksheet.write(row, 5, otherMoveInitBalance, styleVals)
                        worksheet.write(row, 6, 0, styleVals)
                        worksheet.write(row, 7, 0, styleVals)
                        worksheet.write(row, 8, 0, styleVals)
                        # sumInit += rline['balance']
                        number += 1
                        row += 1

                    # worksheet.write(row, 0, 'SUM', styleLableSum)
                    # worksheet.write(row, 1, ' ', styleLableSum)
                    # worksheet.write(row, 2, ' ', styleLableSum)
                    # worksheet.write(row, 3, ' ', styleLableSum)
                    # worksheet.write(row, 4, ' ', styleLableSum)
                    # worksheet.write(row, 5, sumInit, styleSum)
                    # worksheet.write(row, 6, sumDebit, styleSum)
                    # worksheet.write(row, 7, sumCredit, styleSum)
                    # worksheet.write(row, 8, sumEnd, styleSum)
                    row += 2

            fp = BytesIO()
            workbook.save(fp)

            fp.seek(0)
            excel_file = base64.encodestring(fp.read())
            fp.close()
            self.write({'excel_file': excel_file})

            if self.excel_file:
                active_id = self.ids[0]
                return {
                    'type': 'ir.actions.act_url',
                    'url': 'web/content/?model=journal.items.report.wizard&download=true&field=excel_file&id=%s&filename=%s' % (
                        active_id, filename),
                    'target': 'new',
                }
