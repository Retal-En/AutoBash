# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class PdcPayment(models.Model):
    """pdc payment in"""
    _name = 'pdc.payment'
    _rec_name = 'sequence'


    sequence = fields.Char(string='PDC Reference', required=True, copy=False, readonly=True, index=True,
                            default=lambda self: _('New'))
    payment_type = fields.Selection([('receive','Receive'),('send','Send')], string='Payment Type', readonly=True)
    partner_id = fields.Many2one("res.partner", string='Partner', required=True)
    payment_date = fields.Date(string='Payment Date', required=True, default=fields.date.today())
    cheque_payment_date = fields.Date(string='Cheque Payment Date')
    due_date = fields.Date(string='Due Date', required=True)
    payment_amount = fields.Float(string='Payment Amount', required=True)
    payment_journal = fields.Many2one("account.journal", string='Payment Journal', required=True )
    bank_journal = fields.Many2one("account.journal", string='Bank Journal')
    pdc_ref = fields.Char(required=True)
    memo = fields.Char()
    bank = fields.Char()
    attachment_ids = fields.Many2many(
        'ir.attachment', 'pdc_ir_attachments_rel',
        'pdc_id', 'attachment_id', 'Attachments')
    state = fields.Selection([('draft','Draft'), ('registered','Registered'),('deposited','Deposited'),('done','Done'),('bounced','Bounced'),
        ('cancelled','Cancelled'),('reconciled','Reconciled')], default='draft')
    pdc_move_lines_ids = fields.One2many("account.move.line", "pdc_in_id", string="PDC Move Line")
    move_id = fields.Many2one("account.move")
    sale_id = fields.Many2one("sale.order")


    @api.model
    def create(self, vals):
        res =super(PdcPayment, self).create(vals)
        if res.payment_type == 'receive':
            res.update({'sequence':self.env['ir.sequence'].next_by_code('pdc.payment') or _('New')})
        else:
            res.update({'sequence':self.env['ir.sequence'].next_by_code('pdc.payment.out') or _('New')})

        return res


    def action_test():
        pass

    @api.constrains('due_date', 'payment_date')
    def date_constrains(self):
        for rec in self:
            if rec.due_date < rec.payment_date:
                raise ValidationError(_('Sorry, DUE DATE Must be greater Than or Equal PAYMENT DATE...'))

    @api.constrains('due_date', 'cheque_payment_date')
    def cheque_payment_date_constrains(self):
        for rec in self:
            if rec.cheque_payment_date:
                if rec.cheque_payment_date < rec.due_date:
                    raise ValidationError(_('Sorry, CHEQUE PAYMENT DATE Must be greater Than or Equal DUE DATE...'))



    def action_registered(self):
            self.write({'state': 'registered'})

    cost_compute = fields.Boolean()
    def action_deposited(self):
        move_obj = self.env['account.move']
        for rec in self:
            if rec.payment_type and rec.payment_type =='receive':
                move_id = move_obj.create({
                'ref':rec.sequence,
                'journal_id':rec.payment_journal.id,
                'date': rec.payment_date,
                'pdc_id':self.id
                })
                self.env['account.move.line'].with_context(check_move_validity=False).create({
                    'move_id':move_id.id,
                    'account_id':rec.payment_journal.payment_debit_account_id.id,
                    'debit':rec.payment_amount,
                    'credit':0.0,
                    })
                self.env['account.move.line'].with_context(check_move_validity=False).create({
                    'move_id':move_id.id,
                    'account_id':rec.partner_id.property_account_receivable_id.id,
                    'partner_id':rec.partner_id.id,
                    'debit':0.0,
                    'credit':rec.payment_amount,

                    })
            elif rec.payment_type and rec.payment_type =='send':

                move_id = move_obj.create({
                'ref':rec.sequence,
                'journal_id':rec.payment_journal.id,
                'date': rec.payment_date,
                'pdc_id':self.id
                })
                self.env['account.move.line'].with_context(check_move_validity=False).create({
                    'move_id':move_id.id,
                    'account_id':rec.payment_journal.payment_credit_account_id.id,
                    'debit':0.0,
                    'credit':rec.payment_amount,
                    })
                self.env['account.move.line'].with_context(check_move_validity=False).create({
                    'move_id':move_id.id,
                    'account_id':rec.partner_id.property_account_payable_id.id,
                    'partner_id':rec.partner_id.id,
                    'debit':rec.payment_amount,
                    'credit':0.0,

                    })

            move_id.state = 'posted'
            self.write({'state': 'deposited'})

    def action_done(self):
        move_obj = self.env['account.move']

        for rec in self:
            if rec.payment_type and rec.payment_type =='receive':
                move_id = move_obj.create({
                'ref':rec.sequence,
                'journal_id':rec.payment_journal.id,
                'date': rec.payment_date,
                'pdc_id':self.id
                })
                self.env['account.move.line'].with_context(check_move_validity=False).create({
                    'move_id':move_id.id,
                    'account_id':rec.payment_journal.payment_debit_account_id.id,
                    'debit':0.0,
                    'credit':rec.payment_amount,
                    })
                self.env['account.move.line'].with_context(check_move_validity=False).create({
                    'move_id':move_id.id,
                    'account_id':rec.bank_journal.payment_debit_account_id.id,
                    'debit':rec.payment_amount,
                    'credit':0.0,

                    })
            elif rec.payment_type and rec.payment_type =='send':
                move_id = move_obj.create({
                'ref':rec.sequence,
                'journal_id':rec.payment_journal.id,
                'date': rec.payment_date,
                'pdc_id':self.id
                })
                self.env['account.move.line'].with_context(check_move_validity=False).create({
                    'move_id':move_id.id,
                    'account_id':rec.payment_journal.payment_credit_account_id.id,
                    'debit':rec.payment_amount,
                    'credit':0.0,
                    })
                self.env['account.move.line'].with_context(check_move_validity=False).create({
                    'move_id':move_id.id,
                    'account_id':rec.bank_journal.payment_credit_account_id.id,
                    'debit':0.0,
                    'credit':rec.payment_amount,

                    })
            move_id.state = 'posted'
            self.write({'state': 'done'})

    def action_bounced(self):
        move_ids = self.env['account.move'].search([('pdc_id','=',self.id)])
        account_reversal = self.env['account.move.reversal']
        if move_ids:
            vals ={ 'date_mode':'custom',
            # 'date' : self.cheque_payment_date,
            }
            account_reversal_id = account_reversal.with_context({'active_model':'account.move','active_ids':move_ids.id}).create(vals)
            account_reversal_id.reverse_moves()
            self.write({'state': 'bounced'})

    def reset_to_draft(self):
            self.write({'state': 'draft'})

       
class PdcMoveLine(models.Model):
    """inherited move line"""
    _inherit = 'account.move.line'

    pdc_in_id = fields.Many2one("pdc.payment", string='PDC IN')

class PdcMove(models.Model):
    """inherited move"""
    _inherit = 'account.move'
    pdc_id = fields.Many2one("pdc.payment")

class PdcJournal(models.Model):
    """inherited journal"""
    _inherit = 'account.journal'


    is_pdc = fields.Boolean(string='IS PDC')
    payment_debit_account_id = fields.Many2one('account.account', string="Income Receipts Account")
    payment_credit_account_id = fields.Many2one('account.account', string="Out Payments Account")