# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class SaleContract(models.Model):
    _name = "sale.contract"
    _rec_name = 'sequence'

    sequence = fields.Char(string='Reference', required=True, copy=False, readonly=True, index=True,
                            default=lambda self: _('New'))
    contract_day_name = fields.Char(string="Contract Day",)
    contract_date = fields.Date(string="Contract Date", default=datetime.today())
    order_reference = fields.Char(string="Order Reference")
    company_id = fields.Many2one('res.company', string="Company")
    customer = fields.Many2one('res.partner', string="Customer")

    agent_company_employee = fields.Many2one('hr.employee', string="Company Agent")

    is_agent = fields.Boolean(string="Is Agent")
    agent_of_customer = fields.Many2one('res.partner', string="Customer Agent")
    poa_agent_number = fields.Char(string="Power Of Attorney Number")
    poa_agent_date = fields.Date(string="Power Of Attorney Date")
    poa_agent_city = fields.Char(string="Power Of Attorney City")
    lawyer_id = fields.Many2one('res.partner', string="Lawyer")

    product_id = fields.Char() #need reviwe

    total_amount = fields.Float(string="Total Amount")
    down_payment_amount = fields.Float(string="Down Payment Amount")
    number_of_installment = fields.Integer(string="Number of Installment")

    first_witness = fields.Many2one('res.partner', string="First Witness")
    second_witness = fields.Many2one('res.partner', string="Second Witness")
    first_witness_identify = fields.Char()
    second_witness_identify = fields.Char()
    first_witness_id_date = fields.Date()
    second_witness_id_date = fields.Date()
    first_witness_id_place = fields.Char()
    second_witness_id_place = fields.Char()




    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('done', 'Contract is Done'),], default="draft")
    sale_id = fields.Many2one('sale.order')

    # def _compute_day(self):
    #     if self.contract_date:
    #         contract_day_name = fields.Datetime.from_string(self.contract_date).weekday()
    #         return str(contract_day_name)



    @api.model
    def create(self, vals):
        res =super(SaleContract, self).create(vals)
        res.update({'sequence':self.env['ir.sequence'].next_by_code('sale.contract') or _('New')})
        return res



    def action_confirm(self):
        self.write({'state':'confirm'})


    def action_done(self):
        self.sale_id.write({'state':'contracted'})
        self.write({'state':'done'})