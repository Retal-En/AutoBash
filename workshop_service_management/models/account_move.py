from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
class SparePartRequest(models.Model):
    _inherit = 'account.move'
    payment_mode = fields.Selection([
        ('redo', 'Redo'),
        ('insurance', 'Insurance'),
        ('warranty', 'Warranty'),
        ('cash', 'Cash'),
        ('goodwill', 'Good Will'),
        ('workshop', 'Work Shop'),
        ('promotion', 'Promotion'),
        ('company_cars', 'Company Cars'),
        ('sales_used_cars', 'Sales & Used Cars'), ], string='Payment Mode')
    workshop_id = fields.Many2one('fleet.workshop', string='Workshop')

    def action_post(self):
        if self.workshop_id:
            self.workshop_id.write({'state':'jet_bus'})

        return super(SparePartRequest, self).action_post()