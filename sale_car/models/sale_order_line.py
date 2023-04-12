# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta, date
from functools import partial
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from odoo.tools.float_utils import float_round
from odoo.tools import pycompat
from odoo.http import request

from odoo.addons import decimal_precision as dp
from werkzeug.urls import url_encode


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _default_product(self):
        # print(self._context.get('default_display_type'))
        if self._context.get('default_display_type2') == 'line_registration':
            config = self.env['service.config'].search([], order='date DESC',limit=1)
            return config.rec_product.id
        if self._context.get('default_display_type2') == 'line_insurance':
            config = self.env['service.config'].search([], order='date DESC',limit=1)
            return config.ins_product.id

    def _get_default_rec_ins(self):
        # print(self._context.get('default_display_type'))
        if self._context.get('default_display_type2') == 'line_registration':
            return False
        elif self._context.get('default_display_type2') == 'line_insurance':
            return False
        else:
            return 'out'

    def _get_default_policy(self):
        if not self._context.get('default_display_type2'):
            config = self.env['installment.config'].search([('model', '=', self.product_id.product_tmpl_id.id)], order='id DESC', limit=1)
            return config.id

    @api.depends('product_uom_qty', 'registration', 'insurance')
    def _compute_reg_ins_amount(self):
        """
        Compute the amounts of the registration and  insurance.
        """
        for line in self:
            rec_price = 0.0
            rec_ins = 0.0
            if line.registration == 'out':
                rec_price = line.product_id.registration_price * line.product_uom_qty
            if line.insurance == 'out':
                rec_ins = line.product_id.insurance_price * line.product_uom_qty
            line.update({
                'registration_price': rec_price,
                'insurance_price': rec_ins,
            })

    @api.depends('product_id', 'order_id.state', 'qty_invoiced', 'qty_delivered','order_id.order_type')
    def _compute_product_updatable(self):
        for line in self:
            if line.order_id.order_type == 'car':
                if line.state in ['sale_order','insurance_registration','pdi','contract','done', 'cancel'] or (line.state in ['sale_order','insurance_registration','pdi','contract','done', 'cancel'] and (line.qty_invoiced > 0 or line.qty_delivered > 0)):
                    line.product_updatable = False
                else:
                    line.product_updatable = True
            else:
                if line.state in ['done', 'cancel'] or (line.state == 'sale' and (line.qty_invoiced > 0 or line.qty_delivered > 0)):
                    line.product_updatable = False
                else:
                    line.product_updatable = True

    @api.depends('order_id.amount_registration', 'order_id.amount_insurance', 'product_id', 'display_type2')
    def _get_ins_reg_price(self):
        config = self.env['service.config'].search([], order='date DESC', limit=1)
        for rec in self:
            if config.rec_product.id == rec.product_id.id:
                rec._onchange_rec_in_price()
                rec.update({
                    'rec_in_price': rec.order_id.amount_registration,
                })
                # print('amount_registration',rec.price_unit)
            elif config.ins_product.id == rec.product_id.id:
                rec._onchange_rec_in_price()
                rec.update({
                    'rec_in_price': rec.order_id.amount_insurance,
                })

    def invoice_line_create_vals(self, invoice_id, qty):
        for line in self:
            vals_list = super(SaleOrderLine, self).invoice_line_create_vals(invoice_id, qty)
            if line.order_id.payment_method == 'installment':
                approve_line = self.env['sale.approve.line'].search([('line_id','=',line.id),('approve_id.state','=','approve')], limit=1)
                if approve_line:
                    vals_list[0]['price_unit'] = approve_line.showroom_price/approve_line.product_qty
            return vals_list

    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict', default=_default_product)
    brand = fields.Many2one('fleet.vehicle.model.brand',related='product_id.brand_id',string='Brand',readonly=True,store=True)
    display_type2 = fields.Selection([('line_registration', "Registration"),('line_insurance', "Insurance"),], default=False, help="Technical field for UX purpose.")
    model_year = fields.Integer('Model Year',related='product_id.model_year',readonly=True,store=True)
    engine_number = fields.Char('Engine Number')
    registration_price = fields.Monetary('Registration Price',compute='_compute_reg_ins_amount',readonly=False,store=True)
    insurance_price = fields.Monetary('Insurance Price',compute='_compute_reg_ins_amount',readonly=False,store=True)
    discount_price = fields.Monetary('Discount Amount',readonly=False,store=True)
    down_payment = fields.Monetary('Down Payment')
    no_ofmanth = fields.Integer('No.of Month')
    profit = fields.Float('Profit(%)', track_visibility='onchange')
    monthly_installment = fields.Monetary('Monthly Installment',compute='_compute_monthly_installment')
    installment_policy = fields.Many2one('installment.config', string='Installment Policy',default=_get_default_policy)
    lot_id = fields.Many2one('stock.production.lot', 'Chassis No')
    registration = fields.Selection(
        [('include', 'Include Registration'), ('out', 'Not Include Registration'), ('self', 'Self Registration')],
        'Registration', default=_get_default_rec_ins)
    insurance = fields.Selection(
        [('include', 'Include Insurance'), ('out', 'Not Include Insurance'), ('self', 'Self Insurance')], 'Insurance',
        default=_get_default_rec_ins)
    rec_in_price = fields.Float('Price2', digits=dp.get_precision('Product Price'), default=0.0,compute='_get_ins_reg_price',store=True)
    other_price = fields.Float('other Price', digits=dp.get_precision('Product Price'), default=0.0)
    # registered = fields.Boolean('Registered',default=False,readonly=True,translate=True)
    # move_to_pdi = fields.Boolean('To PDI',default=False,readonly=True,translate=True)
    product_location = fields.Many2one('stock.location', "Product Location" , compute="_get_product_location",store=True)
    order_type = fields.Selection([('car', "Car Order"),('order', "Workshop Order"),],related='order_id.order_type',store=True)
    finance = fields.Float(string="Value", track_visibility='onchange')
    approve_line = fields.Many2one('sale.approve.line', string='Approve Reference',  ondelete='cascade',
                               index=True, copy=False)
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sent_approve', 'Approval Sent'),
        ('sale_order', 'Sales Order'),
        ('insurance_registration', 'Insurance and Registration'),
        ('pdi', 'PDI'),
        ('contract', 'Contract'),
        ('sale', 'Delivery'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')

    show_add_reg_ins = fields.Boolean('Show Payment Method',default=False,compute='_compute_show_add_reg_ins', store=True)
    plate_number = fields.Char("Plate Number")

     
    @api.depends('order_type')
    def _compute_show_add_reg_ins(self):
        for line in self:
            if line.order_type == 'car':
                print('order_type',line.order_type)
                line.show_add_reg_ins = True

    @api.onchange('rec_in_price','order_id.amount_registration','order_id.amount_insurance')
    def _onchange_rec_in_price(self):
        config = self.env['service.config'].search([], order='date DESC', limit=1)
        if config.rec_product.id == self.product_id.id:
            self.price_unit = self.order_id.amount_registration
            self.down_payment = self.order_id.amount_registration
        elif config.ins_product.id == self.product_id.id:
            self.price_unit = self.order_id.amount_insurance
            self.down_payment = self.order_id.amount_insurance

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        production = self.env['stock.production.lot'].search([('id','=',self.lot_id.id)], order='id DESC', limit=1)
        self.engine_number = production.engine_no

    @api.onchange('installment_policy')
    def _onchange_installment_policy(self):
        if self.installment_policy:
            policy = self.env['installment.config'].search([('model', '=', self.product_id.product_tmpl_id.id)])
            policy_ids = []
            for pol in policy:
                policy_ids.append(pol.id)
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id
            )
            finance_value = self.env['finance.config'].search([], order='id DESC', limit=1).value
            self.down_payment = self.installment_policy.down_payment
            self.no_ofmanth = self.installment_policy.no_ofmanth
            self.finance = self.installment_policy.finance
            self.profit = self.installment_policy.profit
            cash_price = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product),product.taxes_id, self.tax_id, self.company_id) * self.product_uom_qty
            # cash_price = self.product_id.lst_price * self.product_uom_qty
            finance = 0.0
            if self.profit and self.no_ofmanth:
                finance = (cash_price - self.down_payment) * (self.profit / self.no_ofmanth / 100) * self.no_ofmanth
            self.price_unit = finance + cash_price
            domain = {'installment_policy': [('id', 'in',policy_ids)]}
            return {'domain': domain}

    @api.onchange('product_id')
    def _onchange_product_id_with_display_type(self):
        if self._context.get('default_display_type2') == 'line_registration':
            config = self.env['service.config'].search([], order='date DESC',limit=1)
            domain = {'product_id': [('id', '=', config.rec_product.id)]}
            return {'domain': domain}
        if self._context.get('default_display_type2') == 'line_insurance':
            config = self.env['service.config'].search([], order='date DESC',limit=1)
            domain = {'product_id': [('id', '=', config.ins_product.id)]}
            return {'domain': domain}

    @api.onchange('order_id.choose')
    def _onchange_state(self):
        quants = self.env['stock.quant'].search([('location_id.usage','=', 'internal'),('product_id', '=', self.product_id.id),('quantity','>',0),('product_state','not in', ['hold','is_block'])])
        lot_ids = []
        for quant in quants:
            lot_ids.append(quant.lot_id.id)
        domain = {'lot_id': [('id', 'in',lot_ids)]}
        return {'domain': domain}

    @api.onchange('price_unit','discount_price','product_uom_qty','down_payment')
    def _onchange_price_unit(self):
        self.other_price = self.price_unit

    @api.onchange('other_price')
    def _onchange_other_price(self):
        if self.order_id.pricelist_id and self.product_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id
            )
            if self.order_id.payment_method == 'installment':
                finance_value = self.env['finance.config'].search([], order='id DESC', limit=1).value
                cash_price = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product),product.taxes_id, self.tax_id, self.company_id)
                print("cash_pricepppp",cash_price,self._get_display_price(product))
                # cash_price = self.product_id.lst_price
                no_ofmanth = self.installment_policy.no_ofmanth
                profit = self.installment_policy.profit
                down_payment = self.installment_policy.down_payment
                finance = 0.0
                if profit and no_ofmanth and finance == 0.0:
                    print('counter','finance',finance,'cash_price',cash_price,'self.down_payment',self.down_payment)
                    finance = (cash_price - self.down_payment) * (profit / no_ofmanth / 100) * no_ofmanth
                if finance <= 0.0:
                    finance = 0.0
                price_unit = finance + cash_price
                print('price_unittttttt','price_unit',price_unit,'self.price_unit',self.price_unit,'finance',finance,'no_ofmanth',no_ofmanth,profit)
                if self.product_id.is_car:
                    if price_unit > self.other_price:
                        self.discount_price = price_unit - self.other_price
                    else:
                        self.discount_price = 0.0
            else:
                print('hhhhh',self._get_display_price(product))
                price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
                if price_unit > self.other_price:
                    self.discount_price = price_unit - self.other_price
                else:
                    self.discount_price = 0.0

    @api.onchange('discount_price')
    def _onchange_discount_price(self):
        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )
        if self.order_id.payment_method == 'installment':
            finance_value = self.env['finance.config'].search([], order='id DESC', limit=1).value
            cash_price = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product),product.taxes_id, self.tax_id, self.company_id)
            # cash_price = self.product_id.lst_price
            no_ofmanth = self.installment_policy.no_ofmanth
            profit = self.installment_policy.profit
            finance = 0.0
            if profit and no_ofmanth and finance == 0.0:
                finance = (cash_price - self.down_payment) * (profit / no_ofmanth / 100) * no_ofmanth
            price_unit = finance + cash_price
            print('price_unit12323','price_unit', price_unit,'finance', finance, 'cash_price', cash_price,'self.profit', self.profit,'self.no_ofmanth', self.no_ofmanth,'self.down_payment',self.down_payment)
            self.price_unit = price_unit - self.discount_price
        else:
            price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
            self.price_unit = price_unit - self.discount_price

     
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        # remove the is_custom values that don't belong to this template
        for pacv in self.product_custom_attribute_value_ids:
            if pacv.attribute_value_id not in self.product_id.product_tmpl_id._get_valid_product_attribute_values():
                self.product_custom_product_template_attribute_value_ids -= pacv

        # remove the no_variant attributes that don't belong to this template
        for ptav in self.product_no_variant_attribute_value_ids:
            if ptav.product_attribute_value_id not in self.product_id.product_tmpl_id._get_valid_product_attribute_values():
                self.product_no_variant_attribute_value_ids -= ptav

        vals = {}
        quants = self.env['stock.quant'].search([('location_id.usage','=', 'internal'),('product_id', '=', self.product_id.id),('quantity','>',0),('product_state','not in', ['hold','is_block'])])
        policy = self.env['installment.config'].search([('model','=', self.product_id.product_tmpl_id.id)])
        lot_ids = []
        policy_ids = []
        for quant in quants:
            lot_ids.append(quant.lot_id.id)
        for pol in policy:
            policy_ids.append(pol.id)

        print('lot_ids',lot_ids)
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)],'lot_id': [('id', 'in', lot_ids)] , 'installment_policy': [('id', 'in', policy_ids)]}
        # domain = {'lot_id': [('product_qty', '>', 0),('product_state','not in', ['hold','normal',False]),('location_id.usage','=', 'internal')]}
        print('domain',domain)
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = self.product_uom_qty or 1.0

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        result = {'domain': domain}

        name = self.get_sale_order_line_multiline_description_sale(product)

        vals.update(name=name)

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            if self.order_id.payment_method == 'installment':
                finance_value = self.env['finance.config'].search([], order='id DESC', limit=1).value
                installment_config = self.env['installment.config'].search([('model', '=', self.product_id.product_tmpl_id.id),('active','=',True)], order='id DESC', limit=1)
                vals['installment_policy'] = installment_config.id
                cash_price = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product),product.taxes_id, self.tax_id,self.company_id) * self.product_uom_qty
                # cash_price = self.product_id.lst_price * self.product_uom_qty
                no_ofmanth = self.installment_policy.no_ofmanth
                profit = self.installment_policy.profit
                finance = 0.0
                if profit and no_ofmanth:
                    finance = (cash_price - self.down_payment) * (profit / no_ofmanth / 100) * no_ofmanth
                print('finance',finance,cash_price,'self.down_payment',self.down_payment,installment_config.finance,installment_config.no_ofmanth,installment_config,self.product_id.product_tmpl_id.id)
                vals['price_unit'] = finance + cash_price
            else:
                vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)

        self.update(vals)
        vals['other_price'] = self.price_unit
        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False

        return result

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            if self.order_id.payment_method == 'installment':
                finance_value = self.env['finance.config'].search([], order='id DESC', limit=1).value
                cash_price = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product),product.taxes_id, self.tax_id,self.company_id)
                # cash_price = self.product_id.lst_price
                no_ofmanth = self.installment_policy.no_ofmanth
                profit = self.installment_policy.profit
                finance = 0.0
                if profit and no_ofmanth:
                    finance = (cash_price - self.down_payment)* (profit / no_ofmanth / 100) * no_ofmanth
                if finance > 0.0:
                    self.price_unit = finance + cash_price
                else:
                    finance = 0.0
                    self.price_unit = finance + cash_price
            else:
                self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)

    @api.onchange('down_payment')
    def down_payment_change(self):
        if self.order_id.pricelist_id and self.order_id.partner_id and self.order_id.pricelist_id.payment_method == 'installment':
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            finance_value = self.env['finance.config'].search([], order='id DESC', limit=1).value
            cash_price = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product),product.taxes_id, self.tax_id,self.company_id)
            # cash_price = self.product_id.lst_price
            no_ofmanth = self.installment_policy.no_ofmanth
            profit = self.installment_policy.profit
            finance = 0.0
            print('self.down_payment',self.down_payment)
            if profit and no_ofmanth:
                finance = (cash_price - self.down_payment) * (profit / no_ofmanth / 100) * no_ofmanth
            self.price_unit = finance + cash_price

    @api.depends('down_payment','price_unit','no_ofmanth')
    def _compute_monthly_installment(self):
        for rec in self:
            if rec.product_id.is_car and rec.no_ofmanth:
                rec.monthly_installment = (rec.price_total - (rec.down_payment * rec.product_uom_qty)) / rec.no_ofmanth

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            if line.order_id.order_type == 'car':
                if line.order_id.payment_method == 'installment':
                    product = line.product_id.with_context(
                        lang=line.order_id.partner_id.lang,
                        partner=line.order_id.partner_id,
                        quantity=line.product_uom_qty,
                        date=line.order_id.date_order,
                        pricelist=line.order_id.pricelist_id.id,
                        uom=line.product_uom.id,
                        fiscal_position=line.env.context.get('fiscal_position')
                    )
                    print()
                    cash_price = line.env['account.tax']._fix_tax_included_price_company(line._get_display_price(product), product.taxes_id, line.tax_id,line.company_id)
                    # finance = (cash_price - self.down_payment) * 0.0166 * self.order_id.no_ofmanth
                    # cash_price = line.product_id.lst_price
                    finance = line.price_unit*line.product_uom_qty - cash_price*line.product_uom_qty
                    # discount = (line.discount_price / cash_price) * 100
                    if finance <= 0.0:
                        finance = 0.0
                        price = line.price_unit
                    else:
                        price = cash_price
                    taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
                    line.update({
                        'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                        'price_total': taxes['total_included'] + finance,
                        'price_subtotal': taxes['total_excluded'] + finance,
                    })
                else:
                    price = line.price_unit
                    taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                                    product=line.product_id, partner=line.order_id.partner_shipping_id)

                    line.update({
                        'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                        'price_total': taxes['total_included'],
                        'price_subtotal': taxes['total_excluded'],
                    })
            else:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                                product=line.product_id, partner=line.order_id.partner_shipping_id)

                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })

    @api.depends('product_id','lot_id')
    # @api.depends('product_id','lot_id','registered','move_to_pdi')
    def _get_product_location(self):
        for rec in self:
            if rec.lot_id and rec.product_id.is_car:
                quant = self.env['stock.quant'].search([('lot_id','=',rec.lot_id.id)], order='id DESC',limit=1)
                rec.product_location = quant.location_id.id
                # print('rec.product_location',rec.product_location)

     
    def _get_cash_price(self, product):
        Pricelist = self.env['product.pricelist'].search([('payment_method','=','cash')], order='id DESC',limit=1)
        no_variant_attributes_price_extra = [
            ptav.price_extra for ptav in self.product_no_variant_attribute_value_ids.filtered(
                lambda ptav:
                    ptav.price_extra and
                    ptav not in product.product_template_product_template_attribute_value_ids
            )
        ]
        if no_variant_attributes_price_extra:
            product = product.with_context(
                no_variant_attributes_price_extra=no_variant_attributes_price_extra
            )

        if Pricelist.discount_policy == 'with_discount':
            return product.with_context(pricelist=Pricelist.id).price
        product_context = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order, uom=self.product_uom.id)

        final_price, rule_id = Pricelist.with_context(product_context).get_product_price_rule(self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
        base_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.product_uom_qty, self.product_uom, self.order_id.pricelist_id.id)
        if currency != Pricelist.currency_id:
            base_price = currency._convert(
                base_price, Pricelist.currency_id,
                self.order_id.company_id or self.env.user.company_id, self.order_id.date_order or fields.Date.today())
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)
