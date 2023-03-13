from odoo import fields, models, api, _
from datetime import date, time, datetime
from odoo.exceptions import UserError, ValidationError


class fleet_appointment(models.Model):
    _name = 'fleet.appointment'
    _description = 'Fleet Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_name = "sequence"

    sequence = fields.Char(string='Sequence', required=True, readonly=True, default=lambda self: _('New'),
                           tracking=True)
    id_type = fields.Selection([
        ('passport', 'Passport'),
        ('id_card', 'ID Card')
    ], string="ID Type")
    client_id = fields.Many2one('res.partner', ondelete='restrict',
                                string="Customer Name", required=True)
    partner_id = fields.Char(string="ID Number", tracking=True)
    client_phone = fields.Char("Phone")
    client_mobile = fields.Char(string="Mobile")
    coll_date = fields.Datetime(string="Coll Date", default=fields.Datetime.now, required=True, readonly=True)
    complaint_date = fields.Date(string="Appointment Date", default=fields.Date.today(), required=True)
    priority = fields.Selection([('0', 'Low'), ('1', 'Normal'), ('2', 'High')], 'Priority')
    company_id = fields.Many2one('res.company', ondelete='restrict',
                                 string='Company',
                                 required=True, default=lambda self: self.env.company)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('create_job', 'Create Job'),
        ('cancel', 'Cancelled'),
        ('done', 'Done'),
    ], 'Status', default="draft", readonly=True, copy=False, help="Gives the status of the fleet appointment.",
        tracking=True)
    description = fields.Text(string='Appointment Description', tracking=True)
    advisor_nots = fields.Text(string='Advisor Nots', tracking=True)

    #
    fleet_id = fields.Many2one('fleet.vehicle', ondelete='restrict', string='Fleet')
    license_plate = fields.Char('License Plate',
                                help='License plate number of the vehicle (ie: plate number for a car)')
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
    model_id = fields.Many2one('fleet.vehicle.model', ondelete='restrict', string='Model', help='Model of the vehicle')
    model_year = fields.Char(string="Model Year ")
    registration_no = fields.Char(string="Engine Number ")
    odometer = fields.Char(string='Last Odometer')

    @api.onchange('fleet_id')
    def onchange_fleet_id(self):
        fleet_id = self.fleet_id
        if fleet_id:
            pass
            self.license_plate = fleet_id.license_plate
            self.vin_sn = fleet_id.vin_sn
            self.fuel_type = fleet_id.fuel_type
            self.model_id = fleet_id.model_id.id
            self.model_year = fleet_id.model_year
            self.odometer = fleet_id.odometer
            self.registration_no = fleet_id.registration_no or ''

    #

    def button_confirm(self):
        for rec in self:
            if not rec.fleet_id:
                raise ValidationError(_('You cannot create appointment  without fleet......'))
            rec.write({'state': 'confirm'})

    def button_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})

    def button_concel(self):
        for rec in self:
            rec.write({'state': 'cancel'})

    @api.onchange('client_id')
    def onchange_partner_id(self):
        addr = {}
        if self.client_id:
            addr = self.client_id.address_get(['contact'])
            addr['client_phone'] = self.client_id.phone
            addr['partner_id'] = self.client_id.partner_id
            addr['client_mobile'] = self.client_id.mobile
            addr['id_type'] = self.client_id.id_type
        return {'value': addr}

    @api.model
    def create(self, vals):

        if not self.client_id.partner_id:
            if vals.get('partner_id'):
                partner = self.env['res.partner'].browse(vals.get('client_id'))
                if partner:
                    partner.write({'partner_id': vals['partner_id']})
            else:
                raise UserError(_("Please enter the customer identification number"))
        if not vals.get('fleet_id'):
            raise ValidationError(_('You cannot create appointment  without fleet......'))

        if vals.get('sequence', _('New')) == _('New'):
            vals['sequence'] = self.env['ir.sequence'].next_by_code(
                'fleet.appointment') or _('New')
        res = super(fleet_appointment, self).create(vals)
        return res

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(('You cannot delete fleet appointment which is not draft or cancelled.'))
        return super(fleet_appointment, self).unlink


# class FleetAppointmentLine(models.Model):
#     _name = 'fleet.appointment.line'
#     _description = "Fleet Appointment Lines"
#     _order = 'id desc'
#     _rec_name = 'fleet_id'
#     fleet_id = fields.Many2one('fleet.vehicle',  ondelete='restrict',string='Fleet')
#     fleet_appointment_id = fields.Many2one('fleet.appointment',ondelete='restrict', string='Appointment')
#     license_plate = fields.Char('License Plate',
#                                 help='License plate number of the vehicle (ie: plate number for a car)')
#     vin_sn = fields.Char('Chassis Number', help='Unique number written on the vehicle motor (VIN/SN number)')
#     fuel_type = fields.Selection(
#         [('gasoline', 'Gasoline'), ('diesel', 'Diesel'), ('electric', 'Electric'), ('hybrid', 'Hybrid')],
#         'Fuel Type', help='Fuel Used by the vehicle')
#     model_id = fields.Many2one('fleet.vehicle.model',ondelete='restrict',string='Model', help='Model of the vehicle')
#     model_year = fields.Char(string="Model Year ")
#     registration_no = fields.Char(string="Engine Number ")
#     odometer= fields.Char(string='Last Odometer')
#
#
#     @api.onchange('fleet_id')
#     def onchange_fleet_id(self):
#         fleet_id = self.fleet_id
#         if fleet_id:
#             self.license_plate = fleet_id.license_plate
#             self.vin_sn = fleet_id.vin_sn
#             self.fuel_type = fleet_id.fuel_type
#             self.model_id = fleet_id.model_id.id
#             self.model_id = fleet_id.model_year.id
#             self.odometer = fleet_id.odometer
#             self.registration_no = fleet_id.registration_no or ''
