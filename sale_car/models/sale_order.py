# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta


class SaleOrder(models.Model):
    _inherit = "sale.order"

    client_id = fields.Char(string="Customer ID")  # Need Review
    mobile = fields.Char(string="Mobile")
    email = fields.Char(string="Email")
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('installment', 'Installment'),
        ('cfr', 'CFR')], string="Payment Method")
    total_down_payment = fields.Float(string="Total Down Payment", compute="_compute_down_payment", store=True)
    total_monthly_installment = fields.Float(string="Total Monthly Installment", compute="_compute_monthly_installment",
                                             store=True)
    remaining_amount = fields.Float(string="Total Remaining Amount", compute="_compute_remaining_amount", store=True)

    state = fields.Selection(selection_add=[
        ('approval', 'Approval Sent'),
        ('approved', 'Approved'),
        ('insurance', 'Insurance and Registration'),
        ('pdi', 'IN PDI'),
        ('contract', 'Contract'),
        ('contracted', 'Contract is Done'),
        ('delivery', 'Delivery'), ])
    approval_id = fields.Many2one('sale.order.approval')
    contract_id = fields.Many2one('sale.contract')
    # pdi_id = fields.Many2one('')  #Needed Woorkshop Madule
    approval_count = fields.Integer(compute="compute_approval_count")
    contract_count = fields.Integer(compute="compute_contract_count")
    pdi_count = fields.Integer(compute="compute_pdi_count")
    installment_count = fields.Integer(compute="compute_installment_count")

    bank_name = fields.Char(string="Bank Name")
    bank_branch = fields.Char(string="Bank Branch")
    date_start = fields.Date(string="Frist Installment Date Start")
    pdc_number = fields.Char(string="Frist Installment Cheak Number")

    installment_ids = fields.Many2one('sale.installment')

    # pdc_ids = fields.Many2one('pdc.payment')

    def create_installment(self):
        # self.write({'installments_is': True})
        installment_obj = self.env['pdc.payment']
        due_date = self.date_start + relativedelta(months=+1)
        start_date = self.date_start + relativedelta(months=+1)
        cheque_number = int(self.pdc_number)
        # cheque_number_inst = cheque_number+1
        journal = self.env['account.journal'].search([('is_pdc', '=', True)], limit=1)
        periods = self.pricelist_id.number_of_installment
        ranges = periods + 1
        for pr in self:
            for i in range(1, ranges, ):
                installment_id = installment_obj.create({
                    'payment_amount': self.total_monthly_installment,
                    'partner_id': self.partner_id.id,
                    'due_date': due_date,
                    'bank': self.bank_name,
                    'payment_journal': journal.id,
                    'pdc_ref': cheque_number,
                    'sale_id': self.id,
                    'payment_type': 'receive',
                    'state': 'registered',
                })
                due_date = due_date + relativedelta(months=+1)
                cheque_number = int(cheque_number + 1)
        # duration = due_date.year- start_date.year
        # self.write({'installment_start_date':start_date,
        #             'installment_end_date':due_date,
        #             'contract_duration':str(duration)+' Years'})

    def get_installment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales Order Installment',
            'view_mode': 'tree,form,calendar',
            'res_model': 'pdc.payment',
            'domain': [('sale_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def compute_installment_count(self):
        for record in self:
            record.installment_count = self.env['pdc.payment'].search_count(
                [('sale_id', '=', self.id)])

    @api.depends('amount_total')
    def _compute_down_payment(self):
        for sdp in self:
            if sdp.payment_method == 'installment' or 'cfr':
                if sdp.amount_total:
                    sdp.total_down_payment = sdp.amount_total * sdp.pricelist_id.down_payment_percentage / 100

    @api.depends('total_down_payment')
    def _compute_remaining_amount(self):
        for srm in self:
            if srm.payment_method == 'installment' or 'cfr':
                if srm.total_down_payment:
                    srm.remaining_amount = srm.amount_total - srm.total_down_payment

    @api.depends('remaining_amount')
    def _compute_monthly_installment(self):
        for smi in self:
            if smi.payment_method == 'installment' or 'cfr':
                if smi.remaining_amount:
                    smi.total_monthly_installment = smi.remaining_amount / smi.pricelist_id.number_of_installment

    @api.constrains('payment_method', 'pricelist_id.is_installment')
    def _installment_constrains(self):
        for rec in self:
            if rec.payment_method == 'installment':
                if rec.pricelist_id.is_installment == False:
                    raise ValidationError(_('Sorry, Price List Must be Installment Type or Ceck Payment Method...'))
                else:
                    pass

    # @api.constrains('payment_method', 'pricelist_id.is_installment')
    # def _cfr_constrains(self):
    #     for rec in self:
    #         if rec.payment_method == 'cfr':
    #             if rec.pricelist_id.is_installment == False:
    #                 raise ValidationError(_('Sorry, Price List Must be Installment Type or CFR or Ceck Payment Method...'))
    #             else:
    #                 pass

    @api.constrains('payment_method', 'pricelist_id.is_installment')
    def _cash_constrains(self):
        for rec in self:
            if rec.payment_method == 'cash':
                if rec.pricelist_id.is_installment == True:
                    raise ValidationError(_('Sorry, Price List Must be Cash or Ceck Payment Method...'))
                else:
                    pass

    def action_to_approve(self):
        approve_obj = self.env['sale.order.approval']
        for rec in self:
            # if rec.payment_type and rec.payment_type =='receive':
            approve_id = approve_obj.create({
                'order_reference': self.name,
                'customer': rec.partner_id.id,
                'payment_method': rec.payment_method,
                'salesperson': rec.user_id.id,
                'order_date': rec.date_order,
                'sale_id': self.id,
            })

            # move_id.state = 'posted'
            self.write({'state': 'approval'})

    def action_to_pdi(self):
        line_ids = []
        pdi_obj = self.env['fleet.workshop']
        for line in self.order_line:
            vals = {'client_id': self.partner_id.id, 'sale_id': self.id,
                    'partner_id': self.partner_id.partner_id,
                    'car_repair_line': [(0, 0, {'product_id': line.product_id.id,'model_year': line.model_year,'brand_id': line.brand_id.id} )]}
            pdi_obj.sudo().create(vals)
        self.write({'state':'pdi'}) #From Workshop Madule    Neeed Review

    def action_to_contract(self):
        contract_obj = self.env['sale.contract']
        for rec in self:
            contracts_id = contract_obj.create({
                'order_reference': self.name,
                'customer': rec.partner_id.id,
                # 'payment_method': rec.payment_method,
                # 'salesperson' : rec.user_id.id,
                'down_payment_amount': rec.total_down_payment,
                'sale_id': self.id,
            })
        self.write({'state': 'contract'})

    def get_approval(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales Order Approval',
            'view_mode': 'tree,form',
            'res_model': 'sale.order.approval',
            'domain': [('sale_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def compute_approval_count(self):
        for record in self:
            record.approval_count = self.env['sale.order.approval'].search_count(
                [('sale_id', '=', self.id)])

    def get_contract(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales Contract',
            'view_mode': 'tree,form',
            'res_model': 'sale.contract',
            'domain': [('sale_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def compute_contract_count(self):
        for record in self:
            record.contract_count = self.env['sale.contract'].search_count(
                [('sale_id', '=', self.id)])

    def get_pdi(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales Order PDI Job',
            'view_mode': 'tree,form',
            'res_model': 'fleet.workshop',
            'domain': [('sale_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def compute_pdi_count(self):
        for record in self:
            record.pdi_count = self.env['fleet.workshop'].search_count(
                [('sale_id', '=', self.id)])


class SaleOrderApproval(models.Model):
    _name = "sale.order.approval"
    _rec_name = "rec_name"

    sequence = fields.Char(string='Reference', required=True, copy=False, readonly=True, index=True,
                           default=lambda self: _('New'))
    description = fields.Char(string="Description")
    order_date = fields.Datetime(string="Order Date")
    order_reference = fields.Char(string="Order Reference")
    salesperson = fields.Many2one('res.users', string="Salesperson")
    customer = fields.Many2one('res.partner', string="Customer")
    payment_method = fields.Char(string="Payment Method")
    total_discount_amount = fields.Float(string="Total Discount Amount")
    product_ids = fields.Char()  # need review
    state = fields.Selection([
        ('draft', 'Draft'),
        ('discount', 'Discount Approve'),
        ('sales_sp', 'Sales SP'),
        ('sales_m', 'Sales M'),
        ('credit_controller', 'CREDIT CONTROLLER'), ], default="draft")
    sale_id = fields.Many2one('sale.order')
    rec_name = fields.Char(compute="_compute_rec_name")

    @api.model
    def create(self, vals):
        res = super(SaleOrderApproval, self).create(vals)
        res.update({'sequence': self.env['ir.sequence'].next_by_code('sale.order.approval') or _('New')})
        return res

    @api.model
    def _compute_rec_name(self):
        if self.id:
            self.rec_name = self.order_reference + "/" + self.sequence

    def action_discount_approve(self):
        self.write({'state': 'discount'})

    def action_sales_sp_approve(self):
        self.write({'state': 'sales_sp'})

    def action_sales_m_approve(self):
        self.write({'state': 'sales_m'})

    def action_credit_controller(self):
        self.sale_id.write({'state': 'approved'})
        self.write({'state': 'credit_controller'})

    # class MuneefAccountPayment(models.Model):
    # _inherit = 'account.payment.employee'

    # service_id = fields.Many2one('end.service',string="End OF Service")

    # def action_post(self):
    #     record = super(MuneefAccountPayment, self).action_post()
    #     if self.service_id:
    #         self.service_id.state = 'paid'
    #         self.service_id.payment_id = self.id
    #     return record
