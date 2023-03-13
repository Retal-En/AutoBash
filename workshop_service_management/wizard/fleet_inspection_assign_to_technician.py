# -*- coding: utf-8 -*-
# Part of Preciseways See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

class fleet_diagnose_assignto_technician(models.TransientModel):
    _name = 'fleet.inspection.assignto.technician'
    _description = "Fleet Inspection Mechanic"
    _order = 'id desc'

    user_id = fields.Many2one('res.users', string='Mechanic', required=True)

    def do_assign_technician(self):
        if self.user_id and self._context.get('active_id'):
            self.env['fleet.inspection'].browse(self._context.get('active_id')).write({'user_id': self.user_id.id, 'state': 'in_progress'})
        return {'type': 'ir.actions.act_window_close'}
