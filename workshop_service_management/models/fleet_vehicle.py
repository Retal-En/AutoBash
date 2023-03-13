from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp

class FleetVehicleModel(models.Model):
    _inherit = 'fleet.vehicle.model'

    parent_id = fields.Many2one('fleet.vehicle.model', string="Sub model")


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    job_card_no = fields.Float(string="Job Card No")
    service_advisor = fields.Many2one('res.partner', string="Service Advisor")
    service_technician = fields.Many2one('res.partner', string="Service Mechanic")
    registraiton_no = fields.Char('Vehicle Registraiton No')
    customer_part_number = fields.Char(string="Customer Part Number")
    part_price = fields.Float(string="Part Price")
    registration_no = fields.Char(string="Engine Number ")
    autobash_ownership = fields.Boolean(string="Autobash Ownership ")


class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    state = fields.Selection(selection_add=[('new', 'New'), ('confirm', 'Confirm'), ('invoice', 'Invoice')], default='new', copy=False, string="State")
    partner_id = fields.Many2one('res.partner', string="Customer")
    invoice_id = fields.Many2one('account.move')
    invoice_count = fields.Integer(string='# of Invoices', copy=False)
    services_lines_ids = fields.One2many('fleet.vehicle.log.line', 'services_id', string="Services Line")

    def action_view_invoice(self):
        return {
            'name': _('Account Invoices'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', '=', self.invoice_id.id)],
        }

    def button_confirm(self):
        self.write({'state': 'confirm'})

    @api.model
    def _prepare_invoce_lines(self, line):
        return {
            'product_id': line.product_id.id or False,
            'quantity': line.quantity or 1.0,
            'product_uom_id': line.product_uom.id or False,
            'price_unit' : line.price_unit or 0.0,
        }

    def button_invoice(self):
        lines = [(0, 0, self._prepare_invoce_lines(line)) for line in self.services_lines_ids]
        vals= {'partner_id':self.partner_id.id,'move_type':'out_invoice','invoice_line_ids':lines}
        invoice_id = self.env['account.move'].create(vals)
        self.invoice_id = invoice_id.id
        self.invoice_count = len(invoice_id)
        return {
                'name': _('Invoice'),
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('account.view_move_form').id,
                'res_model': 'account.move',
                'res_id': invoice_id.id,
                'type': 'ir.actions.act_window',
                'target': 'current',
        }

class FleetVehicleLogLine(models.Model):
    _name = 'fleet.vehicle.log.line'
    _description = 'Fleet Vehicle Log Line'
    _order = 'id desc'

    @api.depends('price_unit','quantity','product_id')
    def _compute_price(self):
        for rec in self:
            rec.price_subtotal = rec.quantity * rec.price_unit

    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', digits='UOM', default=1.0)
    product_uom = fields.Many2one('uom.uom', string='UOM')
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
    price_subtotal = fields.Float(string='Subtotal', compute='_compute_price')
    services_id = fields.Many2one('fleet.vehicle.log.services', string="Services")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            rec.name = rec.product_id.display_name
            rec.price_unit = rec.product_id.lst_price
            rec.product_uom = rec.product_id.uom_id.id
