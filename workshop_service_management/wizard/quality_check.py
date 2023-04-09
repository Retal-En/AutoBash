# -*- coding: utf-8 -*-
# Part of Preciseways See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError, Warning


class QualityCheck(models.TransientModel):
    _name = 'fleet.quality.check'
    _description = "Fleet Inspection Mechanic"
    _order = 'id desc'

    user_id = fields.Many2one('res.users', string='Mechanic', default=lambda self: self.env.user, required=True)
    car = fields.Boolean(string="Car")
    spare_check = fields.Boolean(string="Spare")
    paints_and_plumbing = fields.Boolean(string="Paints & Plumbing")
    workshop_id = fields.Many2one('fleet.workshop', string='Workshop')
    def action_quality_check(self):
        if self.workshop_id:
            workshop =self.workshop_id
            quality = self.env['fleet.quality.analysis']
            vals = { }
            if self.car:
                vals = {
                        'fleet_id': workshop.fleet_id.id,
                        'license_plate': workshop.fleet_id.license_plate,
                        'vin_sn': workshop.fleet_id.vin_sn,
                        'fuel_type': workshop.fleet_id.fuel_type,
                        'model_id': workshop.fleet_id.model_id.id,
                        # 'registration_no': workshop.fleet_id.registration_no,
                        'model_year': workshop.fleet_id.model_year,
                        'quality_type': 'car',
                        'workshop_id': workshop.id,
                    }
                quality.create(vals)


            if self.spare_check:
                vals = {
                    'fleet_id': workshop.fleet_id.id,
                    'license_plate': workshop.fleet_id.license_plate,
                    'vin_sn': workshop.fleet_id.vin_sn,
                    'fuel_type': workshop.fleet_id.fuel_type,
                    'model_id': workshop.fleet_id.model_id.id,
                    # 'registration_no': workshop.fleet_id.registration_no,
                    'model_year': workshop.fleet_id.model_year,
                    'quality_type': 'spare_check',
                }
                quality.create(vals)


            if self.paints_and_plumbing:
                vals = {
                    'fleet_id': workshop.fleet_id.id,
                    'license_plate': workshop.fleet_id.license_plate,
                    'vin_sn': workshop.fleet_id.vin_sn,
                    'fuel_type': workshop.fleet_id.fuel_type,
                    'model_id': workshop.fleet_id.model_id.id,
                    # 'registration_no': workshop.fleet_id.registration_no,
                    'model_year': workshop.fleet_id.model_year,
                    'quality_type': 'paints_and_plumbing',
                }
                quality.create(vals)
        self.workshop_id.write({'state': 'delivery_invoicing'})


