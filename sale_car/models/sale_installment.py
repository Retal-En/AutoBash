# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class SalePricelists(models.Model):
    _inherit = "product.pricelist"
    
    is_installment = fields.Boolean(string="Is Installment")
    is_cfr = fields.Boolean(string="Is CFR")
    down_payment_percentage = fields.Float(string="Down Payment Percentage")
    number_of_installment = fields.Integer(string="Number of Installment")


class SaleInstallment(models.Model):
    """Sale Installment"""
    _name = 'sale.installment'
    # _rec_name = 'sequence'


    # sequence = fields.Char(string='PDC Reference', required=True, copy=False, readonly=True, index=True,
    #                         default=lambda self: _('New'))
    # payment_type = fields.Selection([('receive','Receive'),('send','Send')], string='Payment Type', readonly=True)
    partner_id = fields.Many2one("res.partner", string='Partner')
    
    payment_date = fields.Date(string='Payment Date', default=fields.date.today())
    due_date = fields.Date(string='Due Date',)
    # cheque_payment_date = fields.Date(string='Cheque Payment Date')

    payment_amount = fields.Float(string='Payment Amount',)
    # payment_journal = fields.Many2one("account.journal", string='Payment Journal', required=True )
    # bank_journal = fields.Many2one("account.journal", string='Bank Journal')
    cheque_ref = fields.Char()
    memo = fields.Char()
    bank = fields.Char()
    # attachment_ids = fields.Many2many(
    #     'ir.attachment', 'pdc_ir_attachments_rel',
    #     'pdc_id', 'attachment_id', 'Attachments')
    state = fields.Selection([
        ('draft','Draft'), 
        ('registered','Registered'),
        ('cancelled','Cancelled'),], default='draft')
    # pdc_move_lines_ids = fields.One2many("account.move.line", "pdc_in_id", string="PDC Move Line")
    # move_id = fields.Many2one("account.move")

    sale_id = fields.Many2one('sale.order')
