# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import math
import babel
import time
from odoo import tools


class TargetSaleEngineer(models.Model):
    _name = 'target.sale'
    _description = 'Assign Monthly Target For Sale Engineer'

    name = fields.Char(string='Reference')
    active = fields.Boolean(string="Active", default=True, track_visibility='onchange')
    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    user_line = fields.One2many('target.sale.line', 'target_line', string="Users List")
    commission_ids = fields.One2many('commission.amount', 'target_id', string="Commission List")
    crm_team_id = fields.Many2one('crm.team', string="Sale Team", )
    leader_user_id = fields.Many2one('res.users', string="Team Leader", related='crm_team_id.user_id', store=True)
    # total_target = fields.Float(string="Total Target", compute='_get_total_target_actual')
    total_target = fields.Float(string="Total Target", )
    # total_actual = fields.Float(string="Total Target", compute='_get_total_target_actual')
    total_actual = fields.Float(string="Total Target", )
    flag = fields.Boolean(string="Active", default=False, )
    # year = fields.Char(string='Year', compute='_get_year')
    year = fields.Char(string='Year', )
    commission_count = fields.Integer('Count', compute='_get_commission')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='draft')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('target.sale'))

    def _get_commission(self):
        for rec in self:
            rec.commission_count = len(rec.commission_ids)

    @api.onchange('from_date', 'to_date')
    def get_date(self):
        for x in self:
            if x.to_date and x.from_date:
                ttyme = datetime.fromtimestamp(time.mktime(time.strptime(str(x.from_date), "%Y-%m-%d")))
                ttyme2 = datetime.fromtimestamp(time.mktime(time.strptime(str(x.to_date), "%Y-%m-%d")))
                locale = self.env.context.get('lang', 'en_US')
                x.name = 'Sale Target From ' + ' ' + tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y',
                                                                                        locale=locale)) + ' ' + 'To' + ' ' + tools.ustr(
                    babel.dates.format_date(date=ttyme2, format='MMMM-y', locale=locale))

    @api.depends('user_line', 'user_line.target', 'user_line.actual')
    def _get_total_target_actual(self):
        # for rec in self:
        #     for line in rec.user_line:
        #         group = self.env.ref('is_sales_custmization.group_representative')
        #         actual = 0.0
        #         amount_total = 0.0
        #         if line.user_id in group.users:
        #             rec.total_target += line.target
        #             rec.total_actual += line.actual
        pass

    @api.depends('from_date', 'to_date')
    def _get_year(self):
        # for rec in self:
        #     if rec.to_date:
        #         date = datetime.strptime(str(rec.to_date), "%Y-%m-%d")
        #         rec.year = date.year
        pass

    def action_running(self):
        for rec in self:
            if rec.user_line.filtered(lambda x: x.target <= 0.0):
                raise UserError(_('Please Set Target First.'))
            rec.state = 'running'

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def get_rep_commission(self, user, from_date, to_date):
        commission_cal = 0.0
        sale_search = self.env['sale.approve'].search([
            ('salesman_id', '=', user),
            ('sale_order_id.state', '=', 'sale'),
            ('sale_order_id.confirmation_date', '>=', to_date),
            ('sale_order_id.confirmation_date', '<=', from_date)
        ])
        min_commis = self.env['incentive.category'].search([
            ('date_from', '<=', from_date), ('date_to', '>=', to_date),
        ], limit=1)
        cal1 = 0.0
        cal2 = 0.0
        cal3 = 0.0
        for sale in sale_search:
            commis_check = self.env['deal.commission'].search([
                ('category_id.date_from', '<=', from_date), ('category_id.date_to', '>=', to_date),
                ('payment_method', '=', sale.sale_order_id.payment_method)
            ], limit=1)
            deal_commisson = commis_check.percentage
            level_check = self.env['discount.matrix.line'].search([
                ('matrix_id.date_from', '<=', from_date), ('matrix_id.date_to', '>=', to_date),
                ('min_allowed', '<=', sale.total_discount), ('max_allowed', '>=', sale.total_discount)
            ], limit=1)
            discount_percentage = level_check.commission_percentage
            cal1 += sale.total_basic * (min_commis.com / 100)
            if commis_check.payment_method == 'installment':
                cal2 += cal1 * (min_commis.actual_com / 100)
            else:
                cal2 += sale.total_basic * (min_commis.com / 100)
            cal3 += cal2 * (min_commis.sales_rep / 100)
        commission_cal = cal3
        return commission_cal

    def get_above_target(self, user, from_date, to_date, commission_cal):
        filter = self.user_line.filtered(lambda x: x.user_id.id == user)
        commis = self.env['incentive.category'].search([
            ('date_from', '<=', from_date), ('date_to', '>=', to_date),
        ], limit=1)
        for line in filter:
            if line.actual > line.target:
                if line.actual_percentage > commis.achieved_target_than1 and line.actual_percentage < commis.achieved_target_than2:
                    return commission_cal * 20 / 100
                elif line.actual_percentage > commis.achieved_target_than2:
                    return commission_cal * 40 / 100
                else:
                    return 0.0

    def action_compute(self):
        for rec in self:
            if rec.to_date and rec.from_date:
                ttyme = datetime.fromtimestamp(time.mktime(time.strptime(str(rec.from_date), "%Y-%m-%d")))
                ttyme2 = datetime.fromtimestamp(time.mktime(time.strptime(str(rec.to_date), "%Y-%m-%d")))
                locale = self.env.context.get('lang', 'en_US')
                name = 'Sale Commission From ' + ' ' + tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y',
                                                                                          locale=locale)) + ' ' + 'To' + ' ' + tools.ustr(
                    babel.dates.format_date(date=ttyme2, format='MMMM-y', locale=locale))

            commission = self.env['commission.amount'].create({
                'name': name,
                'crm_team_id': rec.crm_team_id.id,
                'from_date': rec.from_date,
                'to_date': rec.to_date,
                'target_id': rec.id,
            })
            for user in rec.user_line:
                commission_cal = rec.get_rep_commission(user.user_id.id, rec.to_date, rec.from_date)
                above_target = rec.get_above_target(user.user_id.id, rec.to_date, rec.from_date, commission_cal)
                line_name = _('Sale Commission of %s from %s') % (user.user_id.name, tools.ustr(
                    babel.dates.format_date(date=ttyme, format='MMMM-y',
                                            locale=locale)) + ' ' + 'to' + ' ' + tools.ustr(
                    babel.dates.format_date(date=ttyme2, format='MMMM-y', locale=locale)))

                self.env['commission.amount.line'].create({
                    'name': line_name,
                    'from_date': rec.from_date,
                    'to_date': rec.to_date,
                    'user_id': user.user_id.id,
                    'amount': commission_cal,
                    # 'above_target': above_target,
                    'commission_id': commission.id,
                })
    #  
    # def action_compute(self):
    #     for rec in self:
    #         if rec.to_date and rec.from_date:
    #             ttyme = datetime.fromtimestamp(time.mktime(time.strptime(str(rec.from_date), "%Y-%m-%d")))
    #             ttyme2 = datetime.fromtimestamp(time.mktime(time.strptime(str(rec.to_date), "%Y-%m-%d")))
    #             locale = self.env.context.get('lang', 'en_US')
    #             name = 'Sale Commission From ' + ' ' + tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)) + ' ' + 'To' + ' ' + tools.ustr(babel.dates.format_date(date=ttyme2, format='MMMM-y', locale=locale))
    #
    #         commission = self.env['commission.amount'].create({
    #             'name': name,
    #             'crm_team_id': rec.crm_team_id.id,
    #             'from_date': rec.from_date,
    #             'to_date': rec.to_date,
    #             'target_id': rec.id,
    #         })
    #         for user in rec.user_line:
    #             if user.is_manager:
    #                 manager_ids = rec.user_line.filtered(lambda x: x.manager.id ==  user.user_id.id)
    #                 manager_commission_cal = 0.0
    #                 line_name = _('Sale Commission of %s from %s') % ( user.user_id.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)) + ' ' + 'to' + ' ' + tools.ustr(babel.dates.format_date(date=ttyme2, format='MMMM-y', locale=locale)))
    #                 for man in manager_ids:
    #                     manager_commission_cal += rec.get_rep_commission(man.user_id.id,man.actual_percentage, rec.to_date, rec.from_date)
    #                 commission_cal = (manager_commission_cal / len(manager_ids)) * 1.5
    #                 above_target = rec.get_above_target(user.user_id.id, rec.to_date, rec.from_date,commission_cal)
    #                 self.env['commission.amount.line'].create({
    #                     'name': line_name,
    #                     'from_date': rec.from_date,
    #                     'to_date': rec.to_date,
    #                     'user_id': user.user_id.id,
    #                     'amount': commission_cal,
    #                     'above_target': above_target,
    #                     'commission_id': commission.id,
    #                 })
    #
    #             else:
    #                 commission_cal = rec.get_rep_commission(user.user_id.id,user.actual_percentage, rec.to_date, rec.from_date)
    #                 above_target = rec.get_above_target(user.user_id.id, rec.to_date , rec.from_date,commission_cal)
    #                 line_name = _('Sale Commission of %s from %s') % ( user.user_id.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)) + ' ' + 'to' + ' ' + tools.ustr(babel.dates.format_date(date=ttyme2, format='MMMM-y', locale=locale)))
    #
    #                 self.env['commission.amount.line'].create({
    #                     'name': line_name,
    #                     'from_date': rec.from_date,
    #                     'to_date': rec.to_date,
    #                     'user_id': user.user_id.id,
    #                     'amount': commission_cal,
    #                     'above_target': above_target,
    #                     'commission_id': commission.id,
    #                 })


class TargetLine(models.Model):
    _name = 'target.sale.line'
    _description = 'Sales Person Target'

    user_id = fields.Many2one('res.users', string="Sales Person")
    manager = fields.Many2one('res.users', string="Manager")
    is_manager = fields.Boolean('IS Manager')
    target = fields.Float(string="Target")
    actual = fields.Float(string="Achieved Target", compute='_get_total_target_actual')
    achieved_target_percentage = fields.Float(string="Achieved Target Percentage % ",
                                              compute='_get_achieved_target_percentage')
    actual_percentage = fields.Float(string="Percentage % ", compute='_get_target_percentage')
    # amount_total = fields.Float(string="Actual",compute='_get_total_target_actual')
    pending = fields.Float(string="Pending", compute='_get_total_target_actual')
    target_line = fields.Many2one('target.sale', string="Target Id")
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('target.sale.line'))

    @api.onchange('user_id')
    def _get_manager(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)], limit=1)
        self.manager = employee.parent_id.user_id.id

    @api.depends('user_id', 'manager')
    def _get_total_target_actual(self):  # 4-3-2023 need review groups
        for rec in self:
            if rec.target_line.state == 'running':
                group = self.env.ref('is_sales_custmization.group_representative')
                actual = 0.0
                if rec.user_id in group.users:
                    sale_search = self.env['sale.order'].search([
                        ('user_id', '=', rec.user_id.id),
                        ('state', '=', 'sale'),
                        ('order_type', '=', 'car'),
                        ('confirmation_date', '>=', rec.target_line.from_date),
                        ('confirmation_date', '<=', rec.target_line.to_date)
                    ])
                    if sale_search:
                        for sale in sale_search:
                            for line in sale.order_line:
                                if line.product_id.is_car:
                                    actual += line.product_uom_qty
                        rec.actual = actual
                        manager_ids = self.search([('user_id', '=', rec.manager.id)])
                        for man in manager_ids:
                            man.actual += rec.actual

                else:
                    manager_ids = self.search(
                        [('manager', '=', rec.user_id.id), ('target_line', '=', rec.target_line.id)])
                    actual = 0.0
                    for man in manager_ids:
                        actual += man.actual
                    if manager_ids:
                        rec.is_manager = True
                    rec.actual = actual

    @api.depends('actual', 'target')
    def _get_target_percentage(self):
        for rec in self:
            if rec.target:
                rec.actual_percentage = rec.actual / rec.target * 100

    @api.depends('actual', 'target')
    def _get_achieved_target_percentage(self):
        for rec in self:
            if rec.target:
                achieved_commis = self.env['incentive.category'].search([
                    ('date_from', '<=', rec.target_line.from_date), ('date_to', '>=', rec.target_line.to_date),
                ], limit=1)
                rec.achieved_target_percentage = achieved_commis.achieved_target


class CommissionAmount(models.Model):
    _name = 'commission.amount'

    name = fields.Char(string='Reference')
    active = fields.Boolean(string="Active", default=True, track_visibility='onchange')
    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    commission_line = fields.One2many('commission.amount.line', 'commission_id', string="Commission")
    crm_team_id = fields.Many2one('crm.team', string="Sale Team", )
    target_id = fields.Many2one('target.sale', string="Target", )
    leader_user_id = fields.Many2one('res.users', string="Team Leader", related='crm_team_id.user_id', store=True)
    # total_commission = fields.Float(string="Total Commissions (SDG)", compute='_get_total')
    total_commission = fields.Float(string="Total Commissions (SDG)", )
    # total_sale = fields.Float(string="Total Sales (SDG)", compute='_get_total')
    total_sale = fields.Float(string="Total Sales (SDG)", )
    # percentage = fields.Float(string="Percentage (%)", compute='_get_total')
    percentage = fields.Float(string="Percentage (%)", )
    flag = fields.Boolean(string="Active", default=False, )
    # year = fields.Char(string='Year', compute='_get_year')
    year = fields.Char(string='Year', )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='draft')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('commission.amount'))

    @api.onchange('from_date', 'to_date')
    def get_date(self):
        for x in self:
            if x.to_date and x.from_date:
                ttyme = datetime.fromtimestamp(time.mktime(time.strptime(str(x.from_date), "%Y-%m-%d")))
                ttyme2 = datetime.fromtimestamp(time.mktime(time.strptime(str(x.to_date), "%Y-%m-%d")))
                locale = self.env.context.get('lang', 'en_US')
                x.name = 'Sale Commission From ' + ' ' + tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y',
                                                                                            locale=locale)) + ' ' + 'To' + ' ' + tools.ustr(
                    babel.dates.format_date(date=ttyme2, format='MMMM-y', locale=locale))

    @api.depends('commission_line', 'commission_line.final_commission')
    def _get_total(self):
        for rec in self:
            for line in rec.commission_line:
                rec.total_commission += line.final_commission

    @api.depends('from_date', 'to_date')
    def _get_year(self):
        for rec in self:
            if rec.to_date:
                date = datetime.strptime(str(rec.to_date), "%Y-%m-%d")
                rec.year = date.year

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_compute(self):
        for rec in self:
            rec.commission_line.unlink()
            for user in rec.target_id.user_line:
                commission_cal = rec.target_id.get_rep_commission(user.user_id.id, rec.to_date, rec.from_date)
                above_target = rec.target_id.get_above_target(user.user_id.id, rec.to_date, rec.from_date,
                                                              commission_cal)
                ttyme = datetime.fromtimestamp(time.mktime(time.strptime(str(rec.from_date), "%Y-%m-%d")))
                ttyme2 = datetime.fromtimestamp(time.mktime(time.strptime(str(rec.to_date), "%Y-%m-%d")))
                locale = self.env.context.get('lang', 'en_US')
                line_name = _('Sale Commission of %s from %s') % (user.user_id.name, tools.ustr(
                    babel.dates.format_date(date=ttyme, format='MMMM-y',
                                            locale=locale)) + ' ' + 'to' + ' ' + tools.ustr(
                    babel.dates.format_date(date=ttyme2, format='MMMM-y', locale=locale)))

                self.env['commission.amount.line'].create({
                    'name': line_name,
                    'from_date': rec.from_date,
                    'to_date': rec.to_date,
                    'user_id': user.user_id.id,
                    'amount': commission_cal,
                    # 'above_target': above_target,
                    'commission_id': rec.id,
                })
    #  
    # def action_compute(self):
    #     for rec in self:
    #         rec.commission_line.unlink()
    #         for user in rec.target_id.user_line:
    #             if user.is_manager:
    #                 manager_ids = rec.target_id.user_line.filtered(lambda x: x.manager.id == user.user_id.id)
    #                 manager_commission_cal = 0.0
    #                 ttyme = datetime.fromtimestamp(time.mktime(time.strptime(str(rec.from_date), "%Y-%m-%d")))
    #                 ttyme2 = datetime.fromtimestamp(time.mktime(time.strptime(str(rec.to_date), "%Y-%m-%d")))
    #                 locale = self.env.context.get('lang', 'en_US')
    #                 line_name = _('Sale Commission of %s from %s') % (user.user_id.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)) + ' ' + 'to' + ' ' + tools.ustr(babel.dates.format_date(date=ttyme2, format='MMMM-y', locale=locale)))
    #                 for man in manager_ids:
    #                     manager_commission_cal += rec.target_id.get_rep_commission(man.user_id.id,man.actual_percentage, rec.to_date, rec.from_date)
    #                 commission_cal = (manager_commission_cal / len(manager_ids)) * 1.5
    #                 above_target = rec.target_id.get_above_target(user.user_id.id, rec.to_date, rec.from_date,commission_cal)
    #                 self.env['commission.amount.line'].create({
    #                     'name': line_name,
    #                     'from_date': rec.from_date,
    #                     'to_date': rec.to_date,
    #                     'user_id': user.user_id.id,
    #                     'amount': commission_cal,
    #                     'above_target': above_target,
    #                     'commission_id': rec.id,
    #                 })
    #
    #             else:
    #                 commission_cal = rec.target_id.get_rep_commission(user.user_id.id,user.actual_percentage, rec.to_date, rec.from_date)
    #                 above_target = rec.target_id.get_above_target(user.user_id.id, rec.to_date , rec.from_date,commission_cal)
    #                 ttyme = datetime.fromtimestamp(time.mktime(time.strptime(str(rec.from_date), "%Y-%m-%d")))
    #                 ttyme2 = datetime.fromtimestamp(time.mktime(time.strptime(str(rec.to_date), "%Y-%m-%d")))
    #                 locale = self.env.context.get('lang', 'en_US')
    #                 line_name = _('Sale Commission of %s from %s') % ( user.user_id.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)) + ' ' + 'to' + ' ' + tools.ustr(babel.dates.format_date(date=ttyme2, format='MMMM-y', locale=locale)))
    #
    #                 self.env['commission.amount.line'].create({
    #                     'name': line_name,
    #                     'from_date': rec.from_date,
    #                     'to_date': rec.to_date,
    #                     'user_id': user.user_id.id,
    #                     'amount': commission_cal,
    #                     'above_target': above_target,
    #                     'commission_id': rec.id,
    #                 })


class AmountCommissionLine(models.Model):
    _name = 'commission.amount.line'
    _description = 'Sales Person Commission'

    name = fields.Char(string='Reference')
    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    user_id = fields.Many2one('res.users', string="Sales Person")
    manager = fields.Many2one('res.users', string="Manager")
    amount = fields.Float(string="Amount")
    above_target = fields.Float(string="Above Target")
    additional_amount = fields.Float(string="Additional Amount")
    final_commission = fields.Float(string="Final Commission", compute='_get_final_commission')
    commission_id = fields.Many2one('commission.amount', string="commission Id")
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'commission.amount.line'))

    @api.onchange('from_date', 'to_date')
    def get_date(self):
        for x in self:
            if x.to_date and x.from_date:
                ttyme = datetime.fromtimestamp(time.mktime(time.strptime(str(x.from_date), "%Y-%m-%d")))
                ttyme2 = datetime.fromtimestamp(time.mktime(time.strptime(str(x.to_date), "%Y-%m-%d")))
                locale = self.env.context.get('lang', 'en_US')
                x.name = _('Sale Commission of %s from %s') % (user.user_id.name, tools.ustr(
                    babel.dates.format_date(date=ttyme, format='MMMM-y',
                                            locale=locale)) + ' ' + 'to' + ' ' + tools.ustr(
                    babel.dates.format_date(date=ttyme2, format='MMMM-y', locale=locale)))

    @api.onchange('user_id')
    def _get_manager(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)], limit=1)
        self.manager = employee.parent_id.user_id.id

    @api.depends('additional_amount', 'above_target', 'amount')
    def _get_final_commission(self):
        for rec in self:
            rec.final_commission = rec.amount + rec.above_target + rec.additional_amount
