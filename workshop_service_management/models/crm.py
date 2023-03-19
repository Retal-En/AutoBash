from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
class SparePartRequest(models.Model):
    _inherit = 'crm.lead'

    workshop_id = fields.Many2one('fleet.workshop', string="Workshop")
    workshop_count = fields.Integer(string='Workshop Count',compute="_comput_workshop_count",stor=True)
    fleet_id = fields.Many2one('fleet.vehicle', 'Fleet')
    model_id = fields.Many2one('fleet.vehicle.model',ondelete='restrict',string='Model', help='Model of the vehicle')
    model_year = fields.Char(string="Model Year ")
    license_plate = fields.Char('License Plate', help='License plate number of the vehicle (ie: plate number for a car)')
    vin_sn = fields.Char('Chassis Number', help='Unique number written on the vehicle motor (VIN/SN number)')
    fuel_type = fields.Selection([
        ('diesel', 'Diesel'),
        ('gasoline', 'Gasoline'),
        ('hybrid', 'Hybrid Diesel'),
        ('full_hybrid_gasoline', 'Hybrid Gasoline'),
        ('plug_in_hybrid_diesel', 'Plug-in Hybrid Diesel'),
        ('plug_in_hybrid_gasoline', 'Plug-in Hybrid Gasoline'),
        ('cng', 'CNG'),
        ('lpg', 'LPG'),
        ('hydrogen', 'Hydrogen'),
        ('electric', 'Electric')],
        'Fuel Type', help='Fuel Used by the vehicle')
    registration_no = fields.Char(string="Engine Number ")
    odometer = fields.Char(string='Last Odometer')






    @api.depends('workshop_id')
    def _comput_workshop_count(self):
        for record in self:
            record.workshop_count = self.env['crm.lead'].search_count([('id', '=', record.workshop_id.id)])
