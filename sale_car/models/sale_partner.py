# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP


class ResPartner(models.Model):
    _inherit = 'res.partner'

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], default="male", string='Gender')

    age_range = fields.Selection([
        ('youth', 'Less than 25'),
        ('adults', '25-60'),
        ('seniors', 'more than 60'),
    ], default="adults", string='Age Range')

    age = fields.Integer(string='Age')

    id_type = fields.Selection([
        ('id_card', 'ID Card'),
        ('passport', 'Passport'),
    ], default="id_card", string='ID type')

    id_no = fields.Char(string='ID No')

    company_type_advance = fields.Selection(string='Partner Type',
                                            selection=[('person', 'Individual'), ('company', 'Company'),
                                                       ('labor_assocuiation', 'Labor Assocuiation')], default='person')

    is_labor = fields.Boolean(string='Is a Labor Assocuiation', default=False, )

    is_person = fields.Boolean(string='Is a Person', default=False, )

    @api.model
    def _commercial_fields(self):
        return super(ResPartner, self)._commercial_fields() + \
            ['id_no', 'id_type', 'age', 'age_range', 'gender', 'is_person', 'is_person', 'company_type_advance']

    @api.depends('age')
    def _compute_id_type(self):
        for rec in self:
            if rec.age < 25:
                rec.age_range = 'youth'
            elif rec.age >= 25 and rec.age <= 60:
                rec.age_range = 'adults'
            elif rec.age > 60:
                rec.age_range = 'seniors'

    @api.onchange('company_type_advance')
    def onchange_company_type(self):
        self.is_labor = (self.company_type_advance == 'labor_assocuiation')
        self.is_company = (self.company_type_advance == 'company')
        self.is_person = (self.company_type_advance == 'person')
        if self.company_type_advance == 'company' or self.company_type_advance == 'labor_assocuiation':
            self.company_type = 'company'
        else:
            self.company_type = 'person'
