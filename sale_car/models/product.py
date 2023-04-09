# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import api, fields, models, _
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError, ValidationError



class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    # is_car = fields.Boolean('Is Car')
    # model_year = fields.Char('Model Year')
    # displacement = fields.Float('Displacement (L)')
    # transmission = fields.Selection([('manual', 'Manual'), ('automatic', 'Automatic')], 'Transmission', help='Transmission Used by the vehicle')

    drive_train = fields.Char('Drive Train')
    fuel = fields.Selection([
        ('benzene', 'Benzene'),
        ('gasoline', 'Gasoline'),
        ('diesel', 'Diesel'),
        ('lpg', 'LPG'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid')
        ], 'Fuel Type', help='Fuel Used by the vehicle')
    # brand = fields.Many2one('brand', 'Brand')
    # brand = fields.Many2one('fleet.vehicle.model.brand', 'Brand')
    insurance_price = fields.Monetary('Insurance Price', required=True, default=0.0)
    registration_price = fields.Monetary('Registration Price', required=True, default=0.0)
    crf_price = fields.Monetary('CRF Price', required=True, default=0.0)
    block_product = fields.Float()
    hold_product = fields.Float()


    is_car = fields.Selection([('is_car','Car '), ('is_spare','Spare'), ('is_labour','Labour')], 'Type ')
    brand_id = fields.Many2one('fleet.vehicle.model.brand', string="Brand")
    model_year = fields.Integer(string="Model Year")
    # transmission = fields.Selection([('manual', "Manual"),('automatic', "Automatic")], default=False, help="Transmission")


    # def _compute_block_hold_product(self):
    #     hold = 0
    #     is_block = 0
    #     read_group_res = self.env['stock.quant'].read_group(
    #         [('product_id', 'in', self.ids)],
    #         ['product_state'],)
    #     res = {i: {} for i in self.ids}
    #     print(read_group_res)
    #     for data in read_group_res:
    #         if res[data['product_state']] == 'hold':
    #             hold +=1
    #         if res[data['product_state']] == 'is_block':
    #             is_block += 1
    #     for product in self:
    #         # read_group_res = self.env['stock.quant'].serch([('product_id','=',product.id)])
    #         product.block_product = is_block
    #         product.hold_product = hold


class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    # car_color = fields.Char('Color')
    # displacement = fields.Float('Displacement (L)')
    # transmission = fields.Selection([('manual', 'Manual'), ('automatic', 'Automatic')], 'Transmission',
    #                                 help='Transmission Used by the vehicle')

    car_color = fields.Char('Color', compute='_get_color', store=True)
    displacement = fields.Float('Displacement (L)', compute='_get_displacement', store=True)
    transmission = fields.Selection([('manual', 'Manual'), ('automatic', 'Automatic')], 'Transmission',
                                    help='Transmission Used by the vehicle', compute='_get_transmission', store=True)

    @api.depends('product_template_attribute_value_ids')
    def _get_color(self):
        for product in self:
            for rec in product.product_template_attribute_value_ids:
                if rec.attribute_id.type == 'color':
                    product.car_color = rec.name

    @api.depends('product_template_attribute_value_ids')
    def _get_displacement(self):
        for product in self:
            for rec in product.product_template_attribute_value_ids:
                if rec.attribute_id.type == 'displacement':
                    product.displacement = rec.name

    @api.depends('product_template_attribute_value_ids')
    def _get_transmission(self):
        for product in self:
            for rec in product.product_template_attribute_value_ids:
                if rec.attribute_id.type == 'transmission':
                    if rec.name == 'manual' or rec.name == 'MT' or rec.name == 'Manual' or rec.name == 'mt':
                        product.transmission = 'manual'
                    elif rec.name == 'automatic' or rec.name == 'AT' or rec.name == 'Automatic' or rec.name == 'at':
                        product.transmission = 'automatic'

     
    # def name_get(self):
    #     # TDE: this could be cleaned a bit I think

    #     def _name_get(d):
    #         name = d.get('name', '')
    #         code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
    #         model_year = self._context.get('display_model_year', True) and d.get('model_year', False) or False
    #         if code:
    #             name = '[%s] %s' % (code,name)

    #         if model_year:
    #             name = '[%s] %s' % (model_year,name)
    #         return (d['id'], name)

    #     partner_id = self._context.get('partner_id')
    #     if partner_id:
    #         partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
    #     else:
    #         partner_ids = []

    #     # all user don't have access to seller and partner
    #     # check access and use superuser
    #     self.check_access_rights("read")
    #     self.check_access_rule("read")

    #     result = []

    #     # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
    #     # Use `load=False` to not call `name_get` for the `product_tmpl_id`
    #     self.sudo().read(['name', 'default_code', 'product_tmpl_id', 'product_template_attribute_value_ids', 'attribute_line_ids'], load=False)

    #     product_template_ids = self.sudo().mapped('product_tmpl_id').ids

    #     if partner_ids:
    #         supplier_info = self.env['product.supplierinfo'].sudo().search([
    #             ('product_tmpl_id', 'in', product_template_ids),
    #             ('name', 'in', partner_ids),
    #         ])
    #         # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
    #         # Use `load=False` to not call `name_get` for the `product_tmpl_id` and `product_id`
    #         supplier_info.sudo().read(['product_tmpl_id', 'product_id', 'product_name', 'product_code'], load=False)
    #         supplier_info_by_template = {}
    #         for r in supplier_info:
    #             supplier_info_by_template.setdefault(r.product_tmpl_id, []).append(r)
    #     for product in self.sudo():
    #         # display only the attributes with multiple possible values on the template
    #         variable_attributes = product.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 1).mapped('attribute_id')
    #         variant = product.product_template_attribute_value_ids._variant_name(variable_attributes)

    #         name = variant and "%s (%s)" % (product.name, variant) or product.name
    #         sellers = []
    #         if partner_ids:
    #             product_supplier_info = supplier_info_by_template.get(product.product_tmpl_id, [])
    #             sellers = [x for x in product_supplier_info if x.product_id and x.product_id == product]
    #             if not sellers:
    #                 sellers = [x for x in product_supplier_info if not x.product_id]
    #         if sellers:
    #             for s in sellers:
    #                 seller_variant = s.product_name and (
    #                     variant and "%s (%s)" % (s.product_name, variant) or s.product_name
    #                     ) or False
    #                 mydict = {
    #                           'id': product.id,
    #                           'name': seller_variant or name,
    #                           'default_code': s.product_code or product.default_code,
    #                           'model_year': product.model_year,
    #                           }
    #                 temp = _name_get(mydict)
    #                 if temp not in result:
    #                     result.append(temp)
    #         else:
    #             mydict = {
    #                       'id': product.id,
    #                       'name': name,
    #                       'default_code': product.default_code,
    #                       'model_year': product.model_year,
    #             }
    #             result.append(_name_get(mydict))
    #     return result


class Brand(models.Model):
    _name = 'brand'

    name = fields.Char('Brand', required=True)


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    lot_state = fields.Selection([
        ('normal', 'Normal'),
        ('hold', 'Hold'),
        ('is_block', 'Block')], string='Product State',
        copy=False, default='normal', required=True)
    engine_no = fields.Char('Engine No')
    # is_car = fields.Selection('Is Car', related='product_id.is_car', store=True)
    vehicle = fields.Many2one('fleet.vehicle', 'Vehicle')
    plate_number = fields.Char(string="Plate Number")


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    product_state = fields.Selection(related='lot_id.lot_state',store=True, default='normal')


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    payment_method = fields.Selection([('cash', 'Cash'), ('installment', 'Installment'),('crf','CFR')], 'Payment Method',default='cash')


class FleetVehicle(models.Model):
    _inherit = ['fleet.vehicle']

    fuel_type = fields.Selection([
        ('benzene', 'Benzene'),
        ('gasoline', 'Gasoline'),
        ('diesel', 'Diesel'),
        ('lpg', 'LPG'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid')
        ], 'Fuel Type', help='Fuel Used by the vehicle')
    sale_order = fields.Many2one('sale.order', 'Sale Order')

    @api.constrains('autobash_ownership','sale_order')
    def autobash_ownership_constrains(self):
        for rec in self:
            inv = rec.sale_order.invoice_ids.filtered(lambda r: r.residual != 0.0)
            if rec.sale_order and not rec.autobash_ownership and inv:
                raise ValidationError(_("You cannot change this vehicle ownership when have Amount Due !"))


# class JobOrder(models.Model):
#     _inherit = ['job.order']

#     sale_order = fields.Many2one('sale.order', 'Sale Order')


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    # YTI FIX ME: PLEASE RENAME ME INTO attribute_type
    type = fields.Selection([
        ('radio', 'Radio'),
        ('select', 'Select'),
        ('color', 'Color'),
        ('displacement', 'Displacement'),
        ('transmission', 'Transmission'),
    ], default='radio', required=True)
