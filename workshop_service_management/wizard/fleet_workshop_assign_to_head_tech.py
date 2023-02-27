# -*- coding: utf-8 -*-
# Part of Preciseways See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _


class fleet_workshop_assign_to_head_tech(models.TransientModel):
    _name = 'fleet.workshop.assignto.headtech'
    _description = "Fleet Workshop headtech"
    _order = 'id desc'

    user_id = fields.Many2one('res.users', string='Head Mechanic', required=True)

    def do_assign_ht(self):
        if self.user_id and self._context.get('active_id'):
            self.pool.get('fleet.workshop').write(self._context.get('active_id'), {'user_id': self.user_id.id, 'state': 'confirm'})
        return {'type': 'ir.actions.act_window_close'}
