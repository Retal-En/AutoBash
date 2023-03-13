from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    mechanic_status = fields.Selection([
        ('working', 'Working'),
        ('ready', 'Ready'),
        ('out_of_service', 'Out Of Service'),
    ], default='ready', string="Mechanic Status")

    mechanic = fields.Boolean(string="Is Mechanic")
