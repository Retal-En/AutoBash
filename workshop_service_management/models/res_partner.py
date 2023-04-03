# -*- coding: utf-8 -*-
from odoo import models,fields,api

class Partner(models.Model):
    _inherit = "res.partner"

    partner_id = fields.Char(string=" ID Number")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ])
    id_type = fields.Selection([
        ('passport', 'Passport'),
        ('id_card', 'ID Card')
    ],string="ID Type")
    last_name = fields.Char(string="Last Name")
    age = fields.Integer(string="Age")
    insurance_companies = fields.Integer(string="Insurance Companies")
    bank_ac_name = fields.Char('Bank Ac Name')
    bank_ac_no = fields.Char('Bank Ac No')
    account_type = fields.Char('Account type')
    ifsc_code = fields.Char('IFSC Code')
    branch = fields.Char('Branch')

    def name_get(self):
        recs = []
        for record in self:
            name = record.name
            if record.last_name:
                name = record.name + ' ' + record.last_name
            recs.append((record.id, name))
        return recs

    _sql_constraints = [
        ('partner_id_uniq', 'unique (partner_id)',
         "Customer ID already in use."),
    ]


