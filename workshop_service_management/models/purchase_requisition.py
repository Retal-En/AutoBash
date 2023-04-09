# -*- coding: utf-8 -*-
# Part of Preciseways See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from datetime import date, time, datetime
from odoo.exceptions import UserError, ValidationError, Warning


class PurchaseRequisition(models.Model):
    _name = 'purchase.requisition'
    _rec_name = 'sequence'
    _inherit = ['mail.thread']
    _description = "Fleet Workshop"
    _order = 'id desc'
    sequence = fields.Char(string='Sequence', required=True, readonly=True, default=lambda self: _('New'))
    client_id = fields.Many2one('res.partner', string='Customer', required=True)
    client_phone = fields.Char(string='Phone')
    client_mobile = fields.Char(string='Mobile')
    client_email = fields.Char(string='Email')
    partner_id = fields.Char(string="Customer ID", required=True)
    receipt_date = fields.Date(string='Date of Receipt', default=datetime.today())
    delivery_date = fields.Date(string='Estimated delivery time', default=fields.Datetime.now)
    contact_name = fields.Char(string='Contact Name')
    phone = fields.Char(string='Contact Number')
    fleet_id = fields.Many2one('fleet.vehicle', 'Fleet')
    license_plate = fields.Char('License Plate',
                                help='License plate number of the vehicle (ie: plate number for a car)')
    vin_sn = fields.Char('Chassis Number', help='Unique number written on the vehicle motor (VIN/SN number)')
    model_id = fields.Many2one('fleet.vehicle.model', 'Model', help='Model of the vehicle')
    purchase_type = fields.Selection(
        [('external_service', 'External Service'), ('external_purchase', 'External Purchase'),
        ('parts_requisition', 'partd Requisition')], 'Purchase Type')
    fuel_type = fields.Selection(
        [('gasoline', 'Gasoline'), ('diesel', 'Diesel'), ('electric', 'Electric'), ('hybrid', 'Hybrid')], 'Fuel Type',
        help='Fuel Used by the vehicle')
    guarantee = fields.Selection([('yes', 'On'), ('no', 'Off')], string='Guarantee?')
    job_controller_id = fields.Many2one('res.users', string='Job Controller', default=lambda self: self.env.user)
    supplier_quotation = fields.Binary(string="Supplier Quotations")
    department_id = fields.Many2one('hr.department', string='Department')
    price_ratio = fields.Float(string="Price Ratio")
    quality_ratio = fields.Float(string="Quality Ratio")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'To Approved'),
        ('department_manager', ' Approved By Department Manager'),
        ('purchase_officer', ' Approved By Purchase Officer'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], 'Status', default="draft", readonly=True, copy=False, help="Gives the status of the fleet repairing.")
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, index=True,
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related="company_id.currency_id",
                                  help='The currency used to enter statement', string="Currency")
    workshop_id = fields.Many2one('fleet.workshop', string="Source Document" ,readonly=True)
    requisition_line_ids = fields.One2many('purchase.requisition.line', 'purchase_id', string="Purchase")
    total = fields.Float( compute='_compute_all_price' ,store=True)
    nots = fields.Text(string='Nots')


    @api.depends('requisition_line_ids.price_total',)
    def _compute_all_price(self):
        total=0
        for line in self.requisition_line_ids:
            total += line.price_total
        self.total = total

    @api.model
    def create(self, vals):
        if vals.get('sequence', _('New')) == _('New'):
            vals['sequence'] = self.env['ir.sequence'].next_by_code(
                'purchase.requisition') or _('New')
        res = super(PurchaseRequisition, self).create(vals)
        return res

    def button_confirm(self):
        for lin in self:
            lin.write({
                'state':'confirm'
            })

    def button_department_manager(self):
        for line in self:
            line.write({
                'state': 'department_manager'
            })
    def button_purchase(self):
        for lin in self:
            lin.write({
                'state':'draft'
            })




    def button_purchase_officer(self):
        line_ids = []
        for line in self.requisition_line_ids:
            line_ids.append((0, 0, {
            'product_id': line.product_id.id or False,
            'product_qty': line.quantity or 1.0,
            'price_unit': line.price_unit or 0.0,
            }))
        vals = {'partner_id': self.client_id.id, 'date_order': self.receipt_date, 'partner_ref': self.sequence,
                'requisition_id':self.id,
                'workshop_id':self.workshop_id.id,
                'order_line': line_ids}
        self.env['purchase.order'].sudo().create(vals)

        self.write({
                'state':'purchase_officer'
            })
    def button_concel(self):
        for lin in self:
            lin.write({
                'state': 'cancel'
            })


    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    ('You cannot delete purchase requisition orders which is not draft or cancelled.'))
        return super(PurchaseRequisition, self).unlink()



class PurchaseRequisitionLine(models.Model):
    _name = 'purchase.requisition.line'
    _description = "purchase order line"
    _order = 'id desc'

    product_id = fields.Many2one('product.product', string='Name', domain=[('detailed_type', '=', 'service')])
    purchase_id = fields.Many2one('purchase.requisition', string='fleet Purchase')
    name = fields.Text(string='Description')
    default_code = fields.Char(string='Product Code')
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    quantity = fields.Float(string='Quantity', required=True, default=1)
    price_unit = fields.Float(string='Unit Price')
    product_qty = fields.Float(string='Quantity Available')
    taxes_id = fields.Many2many('account.tax', string='Taxes',
                                domain=['|', ('active', '=', False), ('active', '=', True)])
    price_total = fields.Float(string='Total', compute='_compute_price' ,store=True)

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if self.product_id:
            res = {'default_code': self.product_id.default_code, 'price_unit': self.product_id.lst_price,
                   'product_qty': self.product_id.qty_available,
                   'uom_id': self.product_id.uom_id.id}
        return {'value': res}

    @api.depends('quantity', 'price_unit')
    def _compute_price(self):
        for line in self:
            line.price_total = (line.quantity * line.price_unit)






class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    workshop_id = fields.Many2one('fleet.workshop', string="Source Document" ,readonly=True)
    requisition_id = fields.Many2one('purchase.requisition', string="Source Document" ,readonly=True)

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        if self.requisition_id and  self.requisition_id.purchase_type =='external_service':
            for line in self.order_line:
                self.workshop_id.write({'external_order_line':[(0, 0, {
                    'vendor_id': line.partner_id.id ,
                    'product_id': line.product_id.id or False,
                    'uom_id': line.product_uom.id or False,
                    'price_unit': line.price_unit or 0.0,
                    'quantity': line.product_qty or 0.0,
                })]})
        else:
            for line in self.order_line:
                self.workshop_id.write({'purchase_order_line': [(0, 0, {
                    'vendor_id': line.partner_id.id,
                    'product_id': line.product_id.id or False,
                    'uom_id': line.product_uom.id or False,
                    'price_unit': line.price_unit or 0.0,
                    'quantity': line.product_qty or 0.0,
                })]})
        self.requisition_id.write({'state':'done'})
        return  res

    # def button_cancel(self):
    #     res = super(PurchaseOrder, self).button_cancel()
    #     if self.workshop_id:
        #     self.workshop_id.external_order_line =  [(5,0,0)]
        # return res
