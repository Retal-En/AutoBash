from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SparePartRequest(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = "spare.part.request"
    name = fields.Char('Reference', required=True, index=True, copy=False, default='New')
    partner_id = fields.Many2one('res.partner', 'Partner')
    stock_picking_id = fields.Many2one('stock.picking.type', string="Operation Type",
                                       domain="[('code','=','internal')]")
    location_id = fields.Many2one('stock.location', 'Source Location')
    location_des_id = fields.Many2one('stock.location', 'Destination Location')
    state = fields.Selection([('draft', 'Draft'),
                              ('spare_part', 'Spare Part Order'), ('approved', 'Approved'),
                              ('done', 'Done'),
                              ('cancel', 'Cancel')], default="draft",
                             string="Status")
    request_date = fields.Datetime(string="Scheduled Date", default=fields.Datetime.now)
    responsible_id = fields.Many2one('res.users', string='Responsible ',
                                     default=lambda self: self.env.user)
    spare_ids = fields.One2many('spare.request.line', 'line_id')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    source_id = fields.Many2one('fleet.workshop', string="Source Document")
    picking_ids = fields.One2many('stock.picking', 'spare_request_id', string="stock")

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'spare.part.request') or _('New')
        res = super(SparePartRequest, self).create(vals)
        return res

    @api.onchange('stock_picking_id')
    def onchange_stock_picking_location_id(self):
        if self.stock_picking_id:
            self.location_id = self.stock_picking_id.default_location_src_id
            self.location_des_id = self.stock_picking_id.default_location_dest_id

    def action_spare_part_order(self):
        for rec in self:
            if not rec.spare_ids:
                raise UserError(_("The application cannot be approved without entering a quantity of aspirin"))
            rec.write({'state': 'spare_part'})

    def action_spare_part_approved(self):
        line_ids = []
        if self.source_id:
            spare = self.source_id
            spare.write({
                'location_id': self.location_id.id,
                'location_des_id': self.location_des_id.id,
                'spare_part_ids': [(0, 0, {
                'product_id':line.product_id.id,
                'uom_id':line.product_uom.id,
                'quantity':line.quantity_done,
                'price_unit':line.product_id.standard_price
                                                    })
                        for line in self.spare_ids.filtered(lambda r: r.quantity_done > 0)]

                         })
        if self.stock_picking_id:
            picking_id =self.stock_picking_id
        else:
            picking_id = self.env.ref('stock.picking_type_internal').id,


        values_for_create = {
            'location_id': self.location_id.id,
            'location_dest_id': self.location_des_id.id,
            'partner_id': self.partner_id.id,
            'spare_request_id': self.id,
            'origin': self.name,
            'picking_type_id': picking_id,
            'move_ids_without_package': [(0, 0, {
                # 'spare_request_line_id': rec.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_des_id.id,
                'product_id': line.product_id.id,
                'name': line.product_id.name,
                'product_uom': line.product_id.uom_id.id,
                'product_uom_qty': line.quantity_done,
            }) for line in self.spare_ids.filtered(lambda r:r.quantity_done > 0)]

        }
        self.write({'state': 'approved'})
        self.env['stock.picking'].sudo().create(values_for_create)

    def action_spare_part_order_cancel(self):
        for rec in self:
            rec.write({'state': 'cancel'})

    def action_spare_part_drift(self):
        for rec in self:
            rec.write({'state': 'draft'})

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    ('You cannot delete spare part requisition orders which is not draft or cancelled.'))
        return super(SparePartRequest, self).unlink()


class SparePartRequestLine(models.Model):
    _name = "spare.request.line"
    _description = 'spare part line Detail'
    line_id = fields.Many2one('spare.part.request')
    product_id = fields.Many2one('product.product', domain=[('is_car', '=', 'is_spare')], string='product')
    description_picking = fields.Char(string="Description")
    product_uom = fields.Many2one('uom.uom', related='product_id.uom_id', string="Unit of Measure")
    product_qty = fields.Float(string='Quantity Available')
    quantity_done = fields.Float(string='Quantity')

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if self.product_id:
            res = {
                'product_qty': self.product_id.qty_available,
                'uom_id': self.product_id.uom_id.id,
            }
        return {'value': res}


class FleetStockPicking(models.Model):
    _inherit = 'stock.picking'
    spare_request_id = fields.Many2one('spare.part.request', string="spare")

    def button_validate(self):
        source_id = self.spare_request_id.source_id
        workshop = self.env['fleet.workshop']
        record = super(FleetStockPicking, self).button_validate()
        self.spare_request_id.write({'state': 'done'})
        return record
        # if self.move_ids_without_package:
            # workshop_id = workshop.browse(source_id.id)
            # raise  UserError(_(workshop_id.id))
            # line_ids = []
            # for line in self.move_ids_without_package:
            #     if line and line.quantity_done > 0.0:
            #         line_ids.append((0, 0, {
            #             'product_id': line.product_id.id or False,
            #             'uom_id': line.product_uom.id or False,
            #             'quantity': line.quantity_done
            #         }))
                    # line_ids.append({
                    #     'product_id': line.product_id.id,
                    #     'workorder_id': workshop_id.id,
                    #     'uom_id': line.product_uom.id,
                    # })
                    # source_id.spare_part_ids.write({
                    #     'product_id':lin.product_id.id,
                    #     'uom_id':lin.product_uom.id,
                    #     'quantity':lin.quantity_done
                    # })
            # vals = {'spare_part_ids': line_ids}
            # work = self.env['spare.part.line']
            # azam = work.create({
            #             'product_id': 1,
            #             'workorder_id': 18,
            #             'uom_id':1,
            #         })
            # if azam:
            #     raise UserError(_(azam.id))
            # else:
            #     raise UserError(_('Error'))
            # workshop_id.write(vals)
            # raise  UserError(_(workshop))
            # if workshop_id:
            #     raise UserError(_(workshop.id))
            # else:
            #     raise UserError(_('Error'))
            # raise UserError(_(azam))

        # self.spare_request_id.write({'state': 'done'})
        # return record


class FleetStockMove(models.Model):
    _inherit = 'stock.move'
    spare_request_line_id = fields.Many2one('spare.request.line', string="spare line")
