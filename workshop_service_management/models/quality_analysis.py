# -*- coding: utf-8 -*-
# Part of Preciseways See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from datetime import date, time, datetime
from odoo.exceptions import UserError, ValidationError, Warning


class FleetQualityAnalysis(models.Model):
    _name = 'fleet.quality.analysis'
    _rec_name = 'sequence'
    _inherit = ['mail.thread']
    _description = "Fleet Quality Analysis"
    _order = 'id desc'

    sequence = fields.Char(string='Sequence', required=True, readonly=True, default=lambda self: _('New'))
    request_date = fields.Date(string='Date of request', default=datetime.today())
    fleet_id = fields.Many2one('fleet.vehicle', 'Fleet')
    license_plate = fields.Char('License Plate',
                                help='License plate number of the vehicle (ie: plate number for a car)')
    vin_sn = fields.Char('Chassis Number', help='Unique number written on the vehicle motor (VIN/SN number)')
    model_id = fields.Many2one('fleet.vehicle.model', 'Model', help='Model of the vehicle')
    model_year = fields.Char(string="Model Year ")

    quality_type = fields.Selection([
        ('car', 'Car'),
        ('spare_check', 'Spare Check'),
        ('paints_and_plumbing', 'Paints & Plumbing'),
    ], string="Quality Type", required=True)
    fuel_type = fields.Selection(
        [('gasoline', 'Gasoline'), ('diesel', 'Diesel'), ('electric', 'Electric'), ('hybrid', 'Hybrid')], 'Fuel Type',
        help='Fuel Used by the vehicle')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('diagnosis', 'In Inspection'),
        ('cancel', 'Cancel'),
        ('done', 'Done')], 'Status', default="draft", readonly=True, copy=False,
        help="Gives the status of the fleet Inspection.")
    user_id = fields.Many2one('res.users', string='Assigned to')
    quality_analysis_line = fields.One2many('quality.analysis.line', 'analysis_id', string="Quality")

    @api.model
    def create(self, vals):
        # raise UserError(_(vals.get('check_type')))
        if vals.get('sequence', _('New')) == _('New'):
            vals['sequence'] = self.env['ir.sequence'].next_by_code(
                'quality.analysis') or _('New')
        res = super(FleetQualityAnalysis, self).create(vals)
        return res
    def button_confirm(self):
        pass

    def button_draft(self):
        pass
    def button_concel(self):
        pass


class FleetQualityAnalysisLine(models.Model):
    _name = 'quality.analysis.line'
    _description = "Fleet Quality Analysis"
    _order = 'id desc'

    analysis_id = fields.Many2one('fleet.quality.analysis', string='quality analysis')
    check = fields.Boolean(string="Check")
    quality_id = fields.Many2one('fleet.quality', string='Check Name',domain=[('quality_type', '=', 'analysis_id.quality_type')])
    nots = fields.Text(string='Nots')

    # @api.onchange('quality_id')
    # def onchange_product_id(self):
    #     if self.quality_id:
    #         domain = [('quality_type', '=', self.analysis_id.quality_type)]
    #     return {'domain': {'quality_id': domain}}
    #
    #





