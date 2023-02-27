from odoo import api, fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    is_car = fields.Selection([('is_car','Car '), ('is_spare','Spare')], 'Type ')

    service_stander_time = fields.Float(string="Service Stander Time")
    vehicle_id = fields.Many2one('fleet.vehicle.model', string="Model Name")
    brand_id = fields.Many2one('fleet.vehicle.model.brand', string="Brand")
    part_number = fields.Char(string="Part number")
    model_year = fields.Integer(string="Model Year")

