# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    brand_id = fields.Many2one('fleet.vehicle.model.brand', string="Brand")
    part_number = fields.Char(string="Part number")
    model_year = fields.Integer(string="Model Year")

    chassis_no = fields.Char()
    plate_number = fields.Char(string="Plate Number")
    registration = fields.Selection([
        ('include', 'Include Registration'),
        ('out', 'Non Include Registration'),
        ('self', 'Self Registration')], string="Registration")
    insurance = fields.Selection([
        ('include', 'Include Insurance'),
        ('out', 'Non Include Insurance'),
        ('self', 'Self Insurance')], string="Insurance")



    @api.onchange('product_id')
    def onchange_product_id(self):
        product_id = self.product_id
        if product_id:
            self.brand_id = product_id.brand_id.id
            self.model_year = product_id.model_year

