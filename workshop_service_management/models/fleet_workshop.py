# -*- coding: utf-8 -*-
# Part of Preciseways See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from datetime import date, time, datetime
from odoo.exceptions import UserError, ValidationError, Warning


class FleetWorkshop(models.Model):
    _name = 'fleet.workshop'
    _rec_name = 'sequence'
    _inherit = ['mail.thread']
    _description = "Fleet Workshop"
    _order = 'id desc'
    #
    sequence = fields.Char(string='Sequence', required=True, readonly=True, default=lambda self: _('New'))
    client_id = fields.Many2one('res.partner', string='Customer Name', required=True)
    client_phone = fields.Char(string='Phone')
    client_mobile = fields.Char(string='Mobile')
    client_email = fields.Char(string='Email')
    partner_id = fields.Char(string="Client ID", required=True)
    drive_id = fields.Many2one('res.partner', string='Drive Name')
    receipt_date = fields.Date(string='Date of Receipt', default=datetime.today())
    delivery_date = fields.Date(string='Estimated delivery time', default=fields.Datetime.now)
    contact_name = fields.Char(string='Contact Name')
    phone = fields.Char(string='Contact Number')
    fleet_id = fields.Many2one('fleet.vehicle', 'Fleet')
    model_year = fields.Char(string="Model Year ")
    license_plate = fields.Char('License Plate',
                                help='License plate number of the vehicle (ie: plate number for a car)')
    vin_sn = fields.Char('Chassis Number', help='Unique number written on the vehicle motor (VIN/SN number)')
    model_id = fields.Many2one('fleet.vehicle.model', 'Model', help='Model of the vehicle')
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
    registration_no = fields.Char(string="Engine Number ")
    odometer = fields.Char(string='Last Odometer')
    guarantee = fields.Selection([('yes', 'On'), ('no', 'Off')], string='Guarantee?')
    guarantee_type = fields.Selection([('paid', 'payable'), ('free', 'No Cost')], string='Type')
    service_advisor_id = fields.Many2one('res.users', string='Service Advisor')
    user_id = fields.Many2one('res.users', string='Assigned to')
    advisor_id = fields.Many2one('res.users', string='Advisor')
    advisor_nots = fields.Text(string='Advisor Nots')
    appointment_description = fields.Text(string='Appointment Nots')
    priority = fields.Selection([('0', 'Low'), ('1', 'Normal'), ('2', 'High')], 'Priority')
    description = fields.Text(string='Notes')
    service_detail = fields.Text(string='Service Details')
    state = fields.Selection([
        ('reception', 'Reception'),
        ('repar', 'Repar'),
        ('quality_check', 'Quality Check'),
        ('delivery_invoicing', 'Delivery & Invoicing'),
        ('jet_bus', 'GitBuss'),
        ('follow_up', 'Follow Up'),
        ('closed', 'Closed'),
    ], 'Status', default="reception", readonly=True, copy=False, help="Gives the status of the fleet repairing.")
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, index=True,
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related="company_id.currency_id",
                                  help='The currency used to enter statement', string="Currency")
    task_line = fields.One2many('job.tasks.line', 'fleet_workshop_id', string="Workshop Lines")
    spare_part_ids = fields.One2many('spare.part.line', 'fleet_spare_id', string='Spare Parts Needed')
    fleet_repair_line = fields.One2many('fleet.workshop.line', 'fleet_repair_id', string="Workshop Lines")
    car_repair_line = fields.One2many('fleet.workshop.line', 'fleet_repair_id', string="Workshop Lines")
    purchase_order_line= fields.One2many('fleet.purchase.order', 'purchase_id', string="External Service")
    external_order_line= fields.One2many('external.purchase.order', 'purchase_id', string="External Service")
    purchase_count = fields.Integer(string='Purchase Count',compute="_comput_purchase_count",stor=True)
    spare_part_count = fields.Integer(string='Purchase Count',compute="_comput_purchase_count",stor=True)
    sale_id = fields.Many2one('sale.order',string="References")
    remark =fields.Text(string="")
    attachment_ids = fields.Many2many('ir.attachment', string='Attachment', required=True)
    payment_mode = fields.Selection([
        ('redo', 'Redo'),
        ('insurance', 'Insurance'),
        ('warranty', 'Warranty'),
        ('cash', 'Cash'),
        ('goodwill', 'Good Will'),
        ('workshop', 'Work Shop'),
        ('promotion', 'Promotion'),
        ('company_cars', 'Company Cars'),
        ('sales_used_cars', 'Sales & Used Cars'), ], default='cash',string= 'Payment Mode', required=True)

    #
    external_total = fields.Float(string='External Purchase', currency_field='company_currency_id', tracking=True ,compute='_compute_external_order_price', store=True)
    purchase_total = fields.Float(string='Purchase', currency_field='company_currency_id', tracking=True ,compute='_compute_purchase_order_price', store=True)
    spare_part = fields.Float(string='Spare Part', currency_field='company_currency_id', tracking=True ,compute='_compute_spear_order_price', store=True)
    job_tasks = fields.Float(string='Job Tasks', currency_field='company_currency_id',compute='_compute_job_tasks_price', store=True)
    total_tax = fields.Float(string='Total Taxes',compute='_compute_total_tax', store=True)
    #
    untaxed_amount_total = fields.Float(string='Untaxed Amount', currency_field='company_currency_id', tracking=True,compute='_compute_all_untaxed_order_price', store=True)
    amount_total = fields.Float(string='Total Amount', currency_field='company_currency_id', tracking=True,compute='_compute_all_order_price', store=True)
    #
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id,
                                 readonly=True)
    location_id = fields.Many2one('stock.location', 'Source Location')
    location_des_id = fields.Many2one('stock.location', 'Destination Location')


    def button_delivery_invoicing(self):
        invoice_lines =[]
        account_move = self.env['account.move']
        for task in self.task_line:
            invoice_lines.append((0, 0, {
                'name': task.product_id.name,
                'product_id': task.product_id.id,
                'quantity': 1,
                'price_unit': task.total,
            }))

        for purchase in self.purchase_order_line:
            invoice_lines.append((0, 0, {
                'name': purchase.product_id.name,
                'product_id': purchase.product_id.id,
                'product_uom_id': purchase.uom_id.id,
                'quantity': purchase.quantity,
                'price_unit': purchase.price_total,
                'tax_ids': purchase.taxes_id.id,

            }))
        for external in self.external_order_line:
            invoice_lines.append((0, 0, {
                'name': external.product_id.name,
                'product_id': external.product_id.id,
                'product_uom_id': external.uom_id.id,
                'tax_ids': external.taxes_id,

                'quantity': external.quantity,
                'price_unit': external.price_total,
            }))
        for spare in self.spare_part_ids:
            invoice_lines.append((0, 0, {
                'name': spare.product_id.name,
                'product_id': spare.product_id.id,
                'product_uom_id': spare.uom_id.id,
                'quantity': spare.quantity,
                'price_unit': spare.price_total,
            }))
        vals = {
            'partner_id': self.client_id.id,
            'payment_mode': self.payment_mode,
            'workshop_id': self.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': invoice_lines,

        }
        account_move.create(vals)

    def pickgin(self):

        if self.purchase_order_line:
            purchase_order = self.env['stock.picking'].create({
                'picking_type_id': self.env.ref('stock.picking_type_out').id,
                'location_id': self.env.ref('stock.stock_location_stock').id,
                'partner_id': self.client_id.id,
                'origin': self.sequence,
                'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                'move_lines': [(0, 0, {
                    'name': 'outgoing_shipment_avg_move',
                    'product_id': rec.product_id.id,
                    'product_uom_qty':rec.quantity,
                    'product_uom': rec.uom_id.id,
                    'location_id': self.env.ref('stock.stock_location_stock').id,
                    'location_dest_id': self.env.ref('stock.stock_location_customers').id})
                               for rec in self.purchase_order_line.filtered(lambda r: r.quantity > 0)
                               ]
            })
            purchase_order.write({'state': 'assigned'})
        if self.spare_part_ids:
            spare_part = self.env['stock.picking'].create({
                'picking_type_id': self.env.ref('stock.picking_type_out').id,
                'location_id': self.env.ref('stock.stock_location_stock').id,
                'partner_id': self.client_id.id,
                'origin': self.sequence,
                'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                'move_lines': [(0, 0, {
                    'name': 'outgoing_shipment_avg_move',
                    'product_id': rec.product_id.id,
                    'product_uom_qty': rec.quantity,
                    'product_uom': rec.uom_id.id,
                    'location_id': self.location_des_id.id,
                    'location_dest_id': self.env.ref('stock.stock_location_customers').id})
                               for rec in self.spare_part_ids.filtered(lambda r: r.quantity > 0)
                               ]
            })
            spare_part.write({'state': 'assigned'})


    @api.onchange('fleet_id')
    def onchange_fleet_id(self):
        fleet_id = self.fleet_id
        if fleet_id:
            self.license_plate = fleet_id.license_plate
            self.vin_sn = fleet_id.vin_sn
            self.fuel_type = fleet_id.fuel_type
            self.model_id = fleet_id.model_id.id
            self.model_year = fleet_id.model_year
            self.registration_no = fleet_id.registration_no or ''
            self.odometer = fleet_id.odometer

    @api.depends('external_total', 'purchase_total','spare_part', 'job_tasks')
    def _compute_all_untaxed_order_price(self):
        total = 0
        for line in self:
            total = (line.external_total + line.purchase_total + line.spare_part + line.job_tasks)
        self.untaxed_amount_total = total
    @api.depends('untaxed_amount_total', 'total_tax',)
    def _compute_all_order_price(self):
        total = 0
        for line in self:
            total = (line.total_tax + line.untaxed_amount_total)
        self.amount_total = total

    @api.depends('job_tasks')
    def _compute_total_tax(self):
        total_tax = 0
        for line in self.task_line:
            if self.payment_mode and self.payment_mode == 'cash':
                total_tax += line.total * (line.taxes_id.amount / 100)
        self.total_tax = total_tax




    @api.depends('external_order_line.price_total', )
    def _compute_external_order_price(self):
        total = 0
        for line in self.external_order_line:
            total += line.price_total
        self.external_total = total

    @api.depends('purchase_order_line.price_total', )
    def _compute_purchase_order_price(self):
        total = 0
        for line in self.purchase_order_line:
            total += line.price_total
        self.purchase_total = total

    @api.depends('spare_part_ids.price_total', )
    def _compute_spear_order_price(self):
        total = 0
        for line in self.spare_part_ids:
            total += line.price_total
        self.spare_part = total
    @api.depends('task_line.service_type', )
    def _compute_job_tasks_price(self):
        total = 0
        if not self.payment_mode:
            self.service_type = False
            raise UserError(_("You must specify the type of payment for the job"))
        for line in self.task_line:
            if self.payment_mode and self.payment_mode == 'cash':
                total += line.total
        self.job_tasks = total

    @api.model
    def create(self, vals):
        if vals.get('sequence', _('New')) == _('New'):
            vals['sequence'] = self.env['ir.sequence'].next_by_code(
                'fleet.workshop') or _('New')
        res = super(FleetWorkshop, self).create(vals)
        return res

    @api.depends('purchase_count')
    def _comput_purchase_count(self):
        for record in self:
            record.purchase_count  =100
            # record.purchase_count = self.env['purchase.order'].search_count([('workshop_id', '=', record.id)])
    def action_create_purchase_order(self):
        self.ensure_one()
        return {
            # 'name': _('%s Goals') % self.employee_id.name,
            'view_mode': 'form',
            'res_model': 'requisition.order',
            'type': 'ir.actions.act_window',
            'target': 'current',
            # 'domain': [('employee_id', '=', self.client_id.id)],
            'context': {'default_client_id': self.client_id.id,
                        'default_partner_id': self.partner_id,
                        'default_purchase_type': 'external_purchase',
                        'default_workshop_id': self.id,
                        },
        }

    def action_create_external_service(self):
        self.ensure_one()
        return {
            # 'name': _('%s Goals') % self.employee_id.name,
            'view_mode': 'form',
            'res_model': 'requisition.order',
            'type': 'ir.actions.act_window',
            'target': 'current',
            # 'domain': [('employee_id', '=', self.client_id.id)],
            'context': {'default_client_id': self.client_id.id,
                        'default_partner_id': self.partner_id,
                        'default_purchase_type': 'external_service',
                        'default_workshop_id': self.id,
                        },
        }

    def action_create_request_spare_part(self):
        return {
            # 'name': _('%s Goals') % self.employee_id.name,
            'view_mode': 'form',
            'res_model': 'spare.part.request',
            'type': 'ir.actions.act_window',
            'target': 'current',
            # 'domain': [('employee_id', '=', self.client_id.id)],
            'context': {'default_source_id': self.id,
                        'default_partner_id': self.partner_id,
                        'default_partner_id': self.client_id.id,
                        },
        }

    def action_purchase_order(self):
        if self.purchase_order_line:
            self.env['purchase.order'].sudo().create(
                {'partner_id': self.client_id.id,
                 'date_order': self.delivery_date,
                 'order_line': [(0, 0, {
                     'product_id': l.product_id.id,
                     'product_qty': l.quantity,
                     'price_unit': l.price_unit,
                 }) for l in self.purchase_order_line]}
            )

    def action_external_order(self):
        if self.purchase_order_line:
            self.env['purchase.order'].sudo().create(
                {'partner_id': self.client_id.id,
                 'date_order': self.delivery_date,
                 'order_line': [(0, 0, {
                     'product_id': l.product_id.id,
                     'product_qty': l.quantity,
                     'price_unit': l.price_unit,
                 }) for l in self.external_order_line]}
            )

    def action_open_purchase_order(self):
        pass
    def print_job_card(self):
        return self.env.ref('workshop_service_management.report_workshop_quotation').report_action(self)
    def button_pre_delivery(self):
        for x in self.task_line:
            if any(x.filtered(lambda task: task.state not in ('done', 'cancel'))):
                raise UserError(_('You cannot create a invoice which task is not done or cancel!'))
            self.write({'state': 'quality_check'})
    def button_repair(self):
        for line in self:
            line.write({'state':'repar'})

    def button_draft(self):
        for line in self:
            line.write({'state': 'reception'})

    def action_create_invoice(self):
        for line in self:
            line.write({'state': 'completed'})



    def button_cancel(self):
        for line in self:
            line.write({'state': 'closed'})


    def button_done(self):
        for line in self:
            line.write({'state': 'completed'})
    def button_quality(self):
        for line in self:
            line.write({'state': 'quality_check'})
    def button_followup(self):
        crm =  self.env['crm.lead']
        if self:
            crm.sudo().create(
            {
                'workshop_id': self.id,
                'name': self.sequence,
                'partner_id': self.client_id.id,
                'phone': self.client_phone,
                'fleet_id':self.fleet_id.id,
                'license_plate':self.fleet_id.license_plate,
                'vin_sn':self.fleet_id.vin_sn,
                'fuel_type':self.fleet_id.fuel_type,
                'model_id':self.fleet_id.model_id.id,
                'registration_no':self.fleet_id.registration_no,
                'model_year':self.fleet_id.model_year,
                'odometer':self.fleet_id.odometer
             })
            self.write({'state': 'follow_up'})

class PurchaseOrderLine(models.Model):
    _name = 'external.purchase.order'
    _description = "purchase order line"
    _order = 'id desc'
    vendor_id = fields.Many2one('res.partner', string='Vendor ', required=True)
    product_id = fields.Many2one('product.product', string='Service', domain=[('detailed_type', '=', 'service')])
    name = fields.Char(string='Description')
    expected_time = fields.Datetime(
        'Expected Time',
         copy=False)
    default_code = fields.Char(string='Product Code')
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    quantity = fields.Float(string='Quantity', required=True, default=1)
    price_unit = fields.Float(string='Unit Price')
    taxes_id = fields.Many2many('account.tax', string='Taxes',
                                domain=['|', ('active', '=', False), ('active', '=', True)])
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    price_total = fields.Float(string='Total', compute='_compute_price' ,store=True)
    purchase_id = fields.Many2one('fleet.workshop', string='fleet Workorder')



    @api.depends('quantity','price_unit')
    def _compute_price(self):
        for line in self:
            line.price_total =(line.price_unit * line.quantity)


    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if self.product_id:
            res = {'default_code': self.product_id.default_code, 'price_unit': self.product_id.lst_price,
                   'uom_id': self.product_id.uom_id.id}
        return {'value': res}




class JobTasks(models.Model):
    _name = 'job.tasks.line'
    _description = "Job Tasks"
    _order = 'id desc'
    _rec_name = "product_id"

    user_id = fields.Many2one('hr.employee', string='Assigned To',domain=[('mechanic', '=',True)], required=True)
    fleet_workshop_id = fields.Many2one('fleet.workshop')
    product_id = fields.Many2one('product.product', string='Name', domain=[('detailed_type', '=', 'service'),('is_car', '=', 'is_labour')],
                                 required=True)
    company_currency_id = fields.Many2one('res.currency', related="fleet_workshop_id.currency_id", string="Currency")
    duration_expected = fields.Float(
        'Expected Duration', digits=(16, 2), default=60.0,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help="Expected duration (in minutes)" , related="product_id.service_stander_time")
    duration = fields.Char(string='Real Duration', tracking=True, compute='_compute_task_time', store=True)

    state = fields.Selection([
        ('ready', 'Ready'),
        ('progress', 'In Progress'),
        ('Pause', 'Pause'),
        ('done', 'Finished'),
        ('cancel', 'Cancelled')], string='Status',
        store=True,
        default='ready', copy=False, readonly=True, index=True)
    price_unit = fields.Float(related="product_id.list_price")
    stander_time = fields.Float(related="product_id.service_stander_time")
    date_finished = fields.Datetime(string="Time", )
    taxes_id = fields.Many2one('account.tax', string='Taxes')
    price_subtotal = fields.Monetary(string='Subtotal', compute="_compute_price_subtotal",
                                     currency_field='company_currency_id', tracking=True)
    date_start = fields.Datetime(
        'Start Date',
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        store=True, copy=False)
    date_pause = fields.Datetime(
        'Pause Date',
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        store=True, copy=False)

    service_type = fields.Selection([
        ('regular_maintenance', 'Regular Maintenance'),
        ('general_repair', 'General Repair'),
        ('initial_maintenance', 'Initial Maintenance'),
        ('stock_maintenance', 'Stock  Maintenance'),
        ('pdi', 'PDI')], 'Service Type', required=True)
    total = fields.Monetary(string='Total', compute="_compute_price_total",
                                     currency_field='company_currency_id', tracking=True)


    @api.depends('price_unit','total')
    def _compute_price_subtotal(self):
        for rec in self:
            rec.price_subtotal = (rec.price_unit * rec.total)

    @api.depends('price_unit','stander_time')
    def _compute_price_total(self):
        for rec in self:
            if rec.stander_time <= 0:
                rec.total = rec.price_unit
            else:
                rec.total = (rec.price_unit * rec.stander_time)




    def button_start(self):
        start_date = datetime.now()
        for line in self:
            available_mechanic = self.env['available.technician.line'].search([('employee_id', '=', line.user_id.id), ('today_date', '=', start_date.date())])
            if not available_mechanic:
                raise ValidationError(_('%s is not available today') % self.user_id.name)
            elif available_mechanic.busy == True:
                raise ValidationError(_('%s is busy now') % self.user_id.name)
            else:
                line.date_start = fields.Datetime.now()
                line.state = 'progress'
                available_mechanic.write({
                    'busy': True,
                    'fleet_workshop_id': line.fleet_workshop_id.id
                })



    def button_pending(self):
        pending_date = datetime.now()
        duration = 0.0
        for lin in self:
            vals = {
                'state': 'Pause',
                'date_pause': pending_date,
            }
            return lin.write(vals)




        pass
    def button_finish(self):
        pass
    def button_block(self):
        today = fields.Datetime.now()
        for line in self:
            available_mechanic = self.env['available.technician.line'].search([('employee_id', '=', line.user_id.id), ('today_date', '=', today.date())])
            available_mechanic.write({
                'busy': False,
            })
            available_mechanic.employee_id.write({ 'mechanic_status' :'ready'})
            # line.fleet_workshop_id = False
            line.state = 'cancel'

    @api.depends('date_start', 'date_pause')
    def _compute_task_time(self):
        for line in self:
            if line.date_start and line.date_pause:
                line.duration = (line.date_pause - line.date_start)


class FleetRepairLine(models.Model):
    _name = 'fleet.workshop.line'
    _description ="Fleet Workshop Lines"
    _order = 'id desc'
    _rec_name = 'fleet_id'

    fleet_id = fields.Many2one('fleet.vehicle','Fleet')
    product_id = fields.Many2one('product.product','Vehicle ')
    brand_id = fields.Many2one('fleet.vehicle.model.brand', string="Brand")
    model_year = fields.Integer(string="Model Year")
    license_plate = fields.Char('License Plate', help='License plate number of the vehicle (ie: plate number for a car)')
    vin_sn= fields.Char('Chassis Number', help='Unique number written on the vehicle motor (VIN/SN number)')
    model_id= fields.Many2one('fleet.vehicle.model', 'Model', help='Model of the vehicle')
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
    odometer= fields.Char(string='Last Odometer')
    registration_no = fields.Char(string='Registration no')
    guarantee= fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Under Guarantee?')
    guarantee_type= fields.Selection([('paid', 'Paid'), ('free', 'Free')], string='Guarantee Type')
    fleet_repair_id= fields.Many2one('fleet.workshop', string='fleet', copy=False)
    service_detail= fields.Text(string='Service Details')
    diagnose_id= fields.Many2one('fleet.inspection', string='fleet Diagnose', copy=False)
    workorder_id= fields.Many2one('fleet.workshop', string='fleet Work Order', copy=False)
    source_line_id= fields.Many2one('fleet.workshop.line', string='Source')
    # service_type= fields.Many2one('service.type', string='Nature of Service')
    # diagnostic_result= fields.Text(string='Diagnostic Result')
    registration_no = fields.Char(string="Engine Number ")
    model_year = fields.Char(string="Model Year ")
    model_id = fields.Many2one('fleet.vehicle.model',ondelete='restrict',string='Model', help='Model of the vehicle')


    # est_ser_hour= fields.Float(string='Estimated Sevice Hours')
    # service_product_id= fields.Many2one('product.product', string='Service Product')
    # service_product_price= fields.Float('Service Product Price')
    state= fields.Selection([
            ('draft', 'Draft'),
            ('diagnosis', 'In Inspection'),
            ('done', 'Done')], 'Status', default="draft", readonly=True, copy=False, help="Gives the status of the fleet Inspection.")

    def action_start(self):
        pass

    def name_get(self):
        reads = self.read(['fleet_id', 'license_plate'])
        res = []
        for record in reads:
            name = record['license_plate']
            if record['fleet_id']:
                name = record['fleet_id'][1]
            res.append((record['id'], name))
        return res

    def action_add_fleet_diagnosis_result(self):
        for obj in self:
            self.write({'state': 'done'})
        return True

    @api.model
    def fields_view_get(self, view_id=None, binding_view_types='form', toolbar=False, submenu=False):
        res = super(FleetRepairLine,self).fields_view_get(view_id, binding_view_types, toolbar=toolbar, submenu=submenu)
        return res

    @api.onchange('fleet_id')
    def onchange_fleet_id(self):
        fleet_id = self.fleet_id
        if fleet_id:
            self.license_plate = fleet_id.license_plate
            self.vin_sn = fleet_id.vin_sn
            self.fuel_type = fleet_id.fuel_type
            self.model_id = fleet_id.model_id.id
            self.model_year = fleet_id.model_year
            self.registration_no = fleet_id.registration_no or ''
            self.odometer = fleet_id.odometer

class spare_part_line(models.Model):
        _name = 'spare.part.line'
        _description = "spare part line"
        _order = 'id desc'

        product_id = fields.Many2one('product.product', string='Part No:', domain=[('is_car', '=', 'is_spare')] ,required=True)
        fleet_spare_id = fields.Many2one('fleet.workshop')

        name = fields.Char(string='Description')
        default_code = fields.Char(string='Product Code')
        workorder_id = fields.Many2one('fleet.workshop', string='fleet Workorder')
        company_currency_id = fields.Many2one('res.currency', related="workorder_id.currency_id", string="Currency")
        description = fields.Text(string='Description')
        remark = fields.Text(string='Remarks')

        uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
        quantity = fields.Float(string='Quantity', required=True, default=1)
        price_unit = fields.Float(string='Unit Price')
        taxes_id = fields.Many2many('account.tax', string='Taxes',
                                    domain=['|', ('active', '=', False), ('active', '=', True)])
        parts_advisor_id = fields.Many2one('res.users', string='Parts Advisor ',
                                         default=lambda self: self.env.user)
        price_total = fields.Float(string='Total', tracking=True,compute='_compute_price', store=True)

        @api.depends('quantity', 'price_unit')
        def _compute_price(self):
            for line in self:
                line.price_total = (line.price_unit * line.quantity)

        @api.onchange('product_id')
        def onchange_product_id(self):
            res = {}
            if self.product_id:
                res = {'default_code': self.product_id.default_code, 'price_unit': self.product_id.lst_price,
                       'uom_id': self.product_id.uom_id.id}
            return {'value': res}

        @api.depends('price_unit', 'quantity', 'product_id')
        def _compute_price(self):
            for rec in self:
                rec.price_total = rec.quantity * rec.price_unit


class PurchaseOrderLine(models.Model):
    _name = 'fleet.purchase.order'
    _description = 'Purchase Order Line'
    _order = 'id desc'
    vendor_id = fields.Many2one('res.partner', string='Vendor ', required=True)
    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)])
    name = fields.Char(string='Description')
    purchase_id = fields.Many2one('fleet.workshop', string='fleet Workorder')
    description = fields.Text(string='Description')
    default_code = fields.Char(string='Product Code')
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    quantity = fields.Float(string='Quantity', required=True, default=1)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    price_unit = fields.Float(string='Unit Price')
    company_currency_id = fields.Many2one('res.currency', related="purchase_id.currency_id", string="Currency")
    taxes_id = fields.Many2many('account.tax', string='Taxes',
                                domain=['|', ('active', '=', False), ('active', '=', True)])
    price_total = fields.Monetary(string='Subtotal',
                                     currency_field='company_currency_id', tracking=True,compute='_compute_price', store=True)

    @api.depends('quantity', 'price_unit')
    def _compute_price(self):
        for line in self:
            line.price_total = (line.price_unit * line.quantity)


    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if self.product_id:
            res = {'default_code': self.product_id.default_code, 'price_unit': self.product_id.lst_price,
                   'uom_id': self.product_id.uom_id.id}
        return {'value': res}

