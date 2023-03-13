from odoo.exceptions import UserError, ValidationError

from odoo import models, fields, api, _
class FleetQuality(models.Model):
    _name = 'fleet.quality'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "sequence,id"

    _description = 'fleet quality'
    name = fields.Char(string ="Name")
    quality_type = fields.Selection([
        ('car', 'Car'),
        ('spare_check', 'Spare Check'),
        ('paints_and_plumbing', 'Paints & Plumbing'),
    ], string="Quality Type" ,required=True)
    sequence = fields.Integer(default=1,string="sequence")
