from odoo import api, fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    is_car = fields.Selection([('is_car','Car '), ('is_spare','Spare'), ('is_labour','Labour')], 'Type ')
    product_alternatives_ids = fields.One2many('product.alternatives', 'product_id', 'Replacement/alternative Part NO')
    service_stander_time = fields.Float(string="Stander Time")
    vehicle_id = fields.Many2one('fleet.vehicle.model', string="Model Name")
    brand_id = fields.Many2one('fleet.vehicle.model.brand', string="Brand")
    part_number = fields.Char(string="Part number")
    model_year = fields.Integer(string="Model Year")



class ProductAlternatives(models.Model):
    _name = "product.alternatives"

    product_id = fields.Many2one('product.template', 'Alternative')
    name = fields.Char('Part Number', required=True)
    alternative_date = fields.Date('Date', required=True)
    alternative_qty = fields.Float('Qty')

