# -*- coding: utf-8 -*-

from odoo import models, fields, api ,_
from odoo.exceptions import UserError, Warning
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from datetime import datetime,date
from dateutil.relativedelta import relativedelta
import math
import babel
import time
from odoo import tools
import math


class DiscountMatrix (models.Model):
    _name = 'discount.matrix'
    _inherit = ['mail.thread']

    name = fields.Char('Reference', required=True)
    date_from = fields.Date(string='Date From',  required=True,
        default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    date_to = fields.Date(string='Date To', required=True,
        default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))
    # date_from = fields.Datetime.to_string(fields.datetime.now() + timedelta(days=365))
    level_line_ids = fields.One2many('discount.matrix.line', 'matrix_id', 'Levels')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('discount.matrix'))
    discount_account_id = fields.Many2one("account.account", string="Discount Account", domain=[('deprecated', '=', False)],help="Account used for Discount")
    income_account_id = fields.Many2one("account.account", string="Income Account", domain=[('deprecated', '=', False)],help="Account used for Discount")
    payment_type = fields.Selection([('cash', 'Cash'), ('installment', 'Installment'),('crf','CFR')], 'Payment Type',required=True, default='cash')

    @api.onchange('date_from','date_to')
    def get_date(self):
        for x in self:
            if x.date_to and x.date_from:
                ttyme = datetime.fromtimestamp(time.mktime(time.strptime(str(x.date_from), "%Y-%m-%d")))
                ttyme2 = datetime.fromtimestamp(time.mktime(time.strptime(str(x.date_to), "%Y-%m-%d")))
                locale = self.env.context.get('lang', 'en_US')
                x.name = x.payment_type +' Discount Matrix From ' + ' ' + tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)) + ' ' + 'To' + ' ' + tools.ustr(babel.dates.format_date(date=ttyme2, format='MMMM-y', locale=locale))

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Discount Matrix Already Exists In This Period!"),

    ]


class DiscountMatrixLine (models.Model):
    _name = 'discount.matrix.line'
    _inherit = ['mail.thread']

     
    @api.constrains('name', 'position_id')
    def _check_position_level(self):
        for level in self :
            level_check = self.env['discount.matrix.line'].search([
                ('matrix_id', '=', level.matrix_id.id),
                ('name', '=', level.name),('position_id', '=', level.position_id.id),
                ('id', '!=', level.id),
            ])
            if level.name and level.position_id and level_check:
                raise ValidationError(_("this position is already have level."))

    name = fields.Char(string='Discount Level', track_visibility='onchange' , required=True)
    position_id = fields.Many2one('hr.job', 'Jop Position', required=True)
    min_allowed = fields.Float(string='Min Allowed Discount (%) ', required=True, track_visibility='onchange')
    max_allowed = fields.Float(string='Max Allowed Discount (%) ', required=True, track_visibility='onchange')
    commission_percentage = fields.Float(string="Rep's Due Commission Percentage (%)", track_visibility='onchange',required=True,)
    matrix_id = fields.Many2one('discount.matrix', 'Discount Matrix')
    payment_method = fields.Selection([('cash', 'Cash'), ('installment', 'Installment'),('crf','CFR')], 'Payment Method',default='cash')

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('discount.matrix.line'))


class IncentiveCategory(models.Model):
    _name = 'incentive.category'
    _inherit = ['mail.thread']

    name = fields.Char('Reference', required=True)
    commission_ids = fields.One2many('deal.commission', 'category_id', 'Deal Commission')
    date_from = fields.Date(string='Date From',  required=True,
        default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    date_to = fields.Date(string='Date To', required=True,
        default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))

    com = fields.Float(string="Commission (%)", track_visibility='onchange')
    actual_com = fields.Float(string="Actual Commission (%)", track_visibility='onchange')
    sales_rep = fields.Float(string="Sale Rep (%)", track_visibility='onchange')
    supervision_com = fields.Float(string="Superviser (%)", track_visibility='onchange')
    admin_mark_com = fields.Float(string="Admin + Marketing (%)", track_visibility='onchange')
    manager = fields.Float(string="Manager(%)", track_visibility='onchange')
    sale_market = fields.Float(string="Sales & Marketing (%)", track_visibility='onchange')

    achieved_target = fields.Float(string="Achieved Target (%)", track_visibility='onchange')
    achieved_target_than1 = fields.Float(string="Achieved Target (more than 150 %)", track_visibility='onchange')
    achieved_target_than2 = fields.Float(string="Achieved Target (more than 200%)", track_visibility='onchange')
    unachieved_target = fields.Float(string="Min Target (%)", track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('incentive.category'))

    @api.onchange('date_from','date_to')
    def get_date(self):
        for x in self:
            if x.date_to and x.date_from:
                ttyme = datetime.fromtimestamp(time.mktime(time.strptime(str(x.date_from), "%Y-%m-%d")))
                ttyme2 = datetime.fromtimestamp(time.mktime(time.strptime(str(x.date_to), "%Y-%m-%d")))
                locale = self.env.context.get('lang', 'en_US')
                x.name = 'Commission Policy From ' + ' ' + tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)) + ' ' + 'To' + ' ' + tools.ustr(babel.dates.format_date(date=ttyme2, format='MMMM-y', locale=locale))

                # x.name = _('Commission Policy for %s To %s ') % (
                #     tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)) %
                #     tools.ustr(babel.dates.format_date(date=ttyme2, format='MMMM-y', locale=locale)))


class DealCommission(models.Model):
    _name = 'deal.commission'
    _rec_name = 'payment_method'

    payment_method = fields.Selection([('cash', 'Cash'), ('installment', 'Installment'),('crf','CFR')], 'Payment Method',default='cash')
    percentage = fields.Float(string="Commission Percentage (%)",track_visibility='onchange')
    category_id = fields.Many2one('incentive.category', 'Incentive Category')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('deal.commission'))


class ThirdPartyPercentage(models.Model):
    _name = 'third.party.percentage'
    _inherit = ['mail.thread']
    _rec_name = 'category_id'

    min = fields.Float('Min', required=1)
    max = fields.Float('Max', required=1)
    percentage = fields.Float(string="Commission Percentage (%)", required=True, track_visibility='onchange')
    category_id = fields.Many2one('incentive.category', 'Incentive Category')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('third.party.percentage'))


class ServiceConfig (models.Model):
    _name = 'service.config'
    _inherit = ['mail.thread']
    _rec_name = 'date'

    date = fields.Date(string='Date',  required=True,
        default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    rec_product = fields.Many2one('product.product','Registration Service', required=True)
    rec_price = fields.Float('Registration Price')
    ins_product = fields.Many2one('product.product','Insurance Service', required=True)
    ins_price = fields.Float('Insurance Price')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('service.config'))
    rec_locaton = fields.Many2one('stock.location', "Registration Location")
    pdi_locaton = fields.Many2one('stock.location', "PDI Location", required=True)


class DownPaymentConfig(models.Model):
    _name = 'down.payment.config'
    _inherit = ['mail.thread']
    _rec_name = 'percentage'

    date = fields.Date(string='Date', required=True,default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    percentage = fields.Float(string="Down Payment (%)", required=True, track_visibility='onchange', digits=(12,5))
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('down.payment.config'))


class FinanceConfig(models.Model):
    _name = 'finance.config'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'value'

    value = fields.Float(string="Value", required=True, track_visibility='onchange', default=0.0166, digits=(12,4))
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('finance.config'))


class InstallmentConfig(models.Model):
    _name = 'installment.config'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Reference', required=True)
    model = fields.Many2one('product.template', "Model", track_visibility='onchange', required=True)
    finance = fields.Float(string="Value", track_visibility='onchange', default=0.0166, digits=(12,4))
    no_ofmanth = fields.Integer('No.of Month', default=12, track_visibility='onchange', required=True)
    down_payment = fields.Float('Down Payment', track_visibility='onchange', required=True)
    profit = fields.Float('Finance(%)', track_visibility='onchange')
    active = fields.Boolean('Active', default=True, help="Available for the customers when active")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('installment.config'))
    payment_method = fields.Selection([('cash', 'Cash'), ('installment', 'Installment'),('crf','CFR')], 'Payment Method',required=True, default='cash')

    def truncate(self ,f, n):
        # math.floor(f * 10 ** n) multiply the number by 10000(10**n) (n is number of 0s) to get a integer number
        # after that divide it by 10000
        return math.floor(f * 10 ** n) / 10 ** n

    @api.onchange('profit','no_ofmanth')
    def _onchange_profit(self):
        # finance = self.profit / 12 /100
        # self.finance =  '%.2f' %finance
        test = 0.0
        if self.no_ofmanth:
            test = self.profit / self.no_ofmanth / 100
        # raise UserError(self.truncate(test, 4))
        self.finance = self.truncate(test, 4)