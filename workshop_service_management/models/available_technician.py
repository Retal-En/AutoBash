from odoo.exceptions import UserError, ValidationError
from datetime import date, time, datetime
from odoo import models, fields, api, _
class AvailableTechnician(models.Model):
    _name = 'available.technician'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Available Technician'
    _rec_name = "request_date"

    request_date = fields.Date(string='Date of request', default=datetime.today())
    sign_in = fields.Datetime(string="Sign In", default=datetime.now().replace(hour=5, minute=00, second=00))
    sign_out = fields.Datetime(string="Sign Out", default=datetime.now().replace(hour=2, minute=30,second=00))
    breakfast_start = fields.Datetime(string="Breakfast Break Start",default=datetime.now().replace(hour=8, minute=00,second=00))
    breakfast_end = fields.Datetime(string="Breakfast Break End",default=datetime.now().replace(hour=8, minute=30,second=00))
    dhuhr_start = fields.Datetime(string="dhuhr Prayer Break Start",default=datetime.now().replace(hour=10, minute=30,second=00))
    dhuhr_end = fields.Datetime(string=" Dhuhr Prayer Break End",default=datetime.now().replace(hour=10, minute=45,second=00))
    asr_end = fields.Datetime(string="Asr prayer  Break End")
    asr_start = fields.Datetime(string="Asr Prayer Break Start",
                                     default=datetime.now().replace(hour=1, minute=30, second=00))
    asr_end = fields.Datetime(string="Asr Prayer Break End",
                                   default=datetime.now().replace(hour=1, minute=45, second=00))
    line_ids = fields.One2many('available.technician.line','technician_id', string='Technician Available Line')

    def _compute_time_state(self):
        if self.request_date:
            raise UserError(_("---------------------"))
    def action_available_technician(self):
        attendance = self.env['hr.attendance']
        technician = self.env['available.technician']
        if self.request_date:
            attendance_ids = attendance.search([('check_in','>=',self.request_date)])
            if attendance_ids:
                available_technician_id = technician.browse(self.id)
                if available_technician_id.line_ids:
                    available_technician_id.line_ids.unlink()
                for l in attendance_ids:
                    available_technician_id.line_ids.create({
                        'technician_id': self.id,
                        'employee_id': l.employee_id.id,
                        'sign_in': self.sign_in,
                        'sign_out': self.sign_out,
                        'breakfast_start': self.breakfast_start,
                        'breakfast_end': self.breakfast_end,
                        'dhuhr_start': self.dhuhr_start,
                        'dhuhr_end': self.dhuhr_end,
                        'asr_start': self.asr_start,
                        'asr_end': self.asr_end,
                        'available': True,
                    }

                    )







class AvailableTechnicianLine(models.Model):
    _name = 'available.technician.line'
    _description = 'Available Technician Line'
    _rec_name = "employee_id"

    employee_id = fields.Many2one('hr.employee', string='Technician')
    technician_id = fields.Many2one('available.technician', string='Technician Available')
    today_date = fields.Date('Today',related='technician_id.request_date')
    fleet_workshop_id = fields.Many2one('fleet.workshop')
    available = fields.Boolean(string="Available")
    busy = fields.Boolean(string="Busy")
    sign_in = fields.Datetime(string="Sign In")
    sign_out = fields.Datetime(string="Sign Out")
    breakfast_start = fields.Datetime(string="Breakfast Break Start")
    breakfast_end = fields.Datetime(string="Breakfast Break  End")
    dhuhr_start = fields.Datetime(string="Dhohr prayer Break Start")
    dhuhr_end = fields.Datetime(string="Dhohr prayer  Break End")
    asr_start = fields.Datetime(string="Asr prayer Break Start")
    asr_end = fields.Datetime(string="Asr prayer  Break End")



