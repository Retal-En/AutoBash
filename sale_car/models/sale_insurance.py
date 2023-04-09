# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class SaleInsurance(models.Model):
    _name = 'sale.insurance'
    
    partner_id = fields.Many2one("res.partner", string='Customer')
    insurance_type = fields.Selection([
        ('customer', 'Customer Cars'),
        ('company', 'Company Cars'),
        ('used', 'Used Cars'), ], string="Insurance Type")
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('installment', 'Installment'),
        ('cfr', 'CFR')], string="Payment Method")
    insurance_state = fields.Selection([
        ('include', 'Include Insurance'),
        ('out', 'Non Include Insurance'),
        ('self', 'Self Insurance')], string="Insurance State")

    installment_end_date = fields.Date(string="Installment End Date")
    insurance_end_date = fields.Date(string="Insurance End Date")
    product_id = fields.Many2one('product.product', string="Product")
    update_price = fields.Float(string="Update Price")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_process', 'In Process'),
        ('done', ' Done'), ], default='draft')
    sale_id = fields.Many2one('sale.order')
