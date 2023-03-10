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
        raise UserError(_("-----------------------"))

        pass
        # job_id = self.env['fleet.workshop']
        # if self.appointment_id:
        #     job_id.create({
        #         'client_id': self.appointment_id.client_id.id,
        #         'client_phone': self.appointment_id.client_id.phone,
        #         'partner_id': self.appointment_id.client_id.partner_id,
        #         'client_mobile': self.appointment_id.client_id.mobile,
        #         'service_advisor_id': self.user_id.id,
        #         'advisor_nots': self.nots,
        #         'appointment_description':self.appointment_id.description,
        #         'sequence': self.env['ir.sequence'].next_by_code('fleet.workshop') or _('New'),
        #         'fleet_repair_line': [
        #             (0, 0, {
        #                 'fleet_id': line.fleet_id.id,
        #                 'license_plate': line.license_plate,
        #                 'model_id': line.model_id.id,
        #                 'vin_sn': line.vin_sn,
        #                 'fuel_type': line.fuel_type,
        #                 'registration_no': line.registration_no,
        #
        #             }
        #              )
        #             for line in self.appointment_id.fleet_appointment_line]
        #
        #     }
        #     )
        #     self.appointment_id.write({'advisor_nots':self.nots,
        #                                'state':'done'})

