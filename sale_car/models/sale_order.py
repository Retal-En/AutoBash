# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from odoo.addons import decimal_precision as dp
from werkzeug.urls import url_encode


class SaleOrder(models.Model):
    _inherit = "sale.order"

    client_id = fields.Char(string="Customer ID")  # Need Review
    mobile = fields.Char(string="Mobile")
    email = fields.Char(string="Email")
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('installment', 'Installment'),
        ('cfr', 'CFR')], string="Payment Method", default='cash')
    total_down_payment = fields.Float(string="Total Down Payment", compute="_compute_down_payment", store=True)
    total_monthly_installment = fields.Float(string="Total Monthly Installment", compute="_compute_monthly_installment",
                                             store=True)
    remaining_amount = fields.Float(string="Total Remaining Amount", compute="_compute_remaining_amount", store=True)

    state = fields.Selection(selection_add=[
        ('approval', 'Approval Sent'),
        ('approved', 'Approved'),
        ('insurance', 'Insurance and Registration'),
        ('pdi', 'IN PDI'),
        ('contract', 'Contract'),
        ('contracted', 'Contract is Done'),
        ('delivery', 'Delivery'), ])
    approval_id = fields.Many2one('sale.order.approval')
    contract_id = fields.Many2one('sale.contract')
    # pdi_id = fields.Many2one('')  #Needed Woorkshop Madule
    approval_count = fields.Integer(compute="compute_approval_count")
    contract_count = fields.Integer(compute="compute_contract_count")
    pdi_count = fields.Integer(compute="compute_pdi_count")
    installment_count = fields.Integer(compute="compute_installment_count")

    insurance_count = fields.Integer()  # 2-3-2023

    bank_name = fields.Char(string="Bank Name")
    bank_branch = fields.Char(string="Bank Branch")
    date_start = fields.Date(string="Frist Installment Date Start")
    pdc_number = fields.Char(string="Frist Installment Cheque Number")

    installment_ids = fields.Many2one('sale.installment')
    # pdc_ids = fields.Many2one('pdc.payment')
    down_payment_percentage = fields.Float(string="Down Payment Percentage")  # 22-2-2023
    fixed_down_payment = fields.Boolean(string="Fixed Down Payment")  # 22-2-2023
    down_payment_fixed = fields.Float(string="Down Payment Fixed")  # 22-2-2023
    number_of_installment = fields.Integer(string="Number of Installment")  # 22-2-2023

    amount_registration = fields.Monetary(string='Registration Amount', store=True, readonly=True,
                                          compute='_amount_registration', track_visibility='onchange', track_sequence=5)
    amount_insurance = fields.Monetary(string='Insurance Amount', store=True, readonly=True,
                                       compute='_amount_registration', track_visibility='onchange', track_sequence=5)
    approve_line = fields.One2many('sale.order.approval', 'sale_id', string='Approves', copy=True, auto_join=True)

    down_payment = fields.Monetary('Total Down Payment', compute='_amount_down_payment')
    no_ofmanth = fields.Monetary('Number of Month', compute='_number_of_month')
    monthly_installment = fields.Monetary('Total Monthly Installment', compute='_amount_monthly_installment')
    choose = fields.Boolean('Choose', default=False)



    discount_amount = fields.Float('Discount Amount', digits=dp.get_precision('Account'))
    finance_amount = fields.Float('Finance Amount', digits=dp.get_precision('Account'))

    order_type = fields.Selection([('car', "Car Order"), ('order', "Workshop Order"), ], default='order',
                                   help="Technical field for UX purpose.")
    @api.model
    def _default_finance(self):
        product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_finance_product_id')
        return self.env['product.product'].browse(int(product_id)).exists()

    @api.model
    def _default_finance_account_id(self):
        return self._default_finance().property_account_income_id or self._default_finance().categ_id.property_account_income_categ_id.id


    finance_id = fields.Many2one('product.product', string='Finance', domain=[('type', '=', 'service')],
                                 default=_default_finance
                                 )
    discount_amount = fields.Float('Discount Amount', digits=dp.get_precision('Account'))
    finance_amount = fields.Float('Finance Amount', digits=dp.get_precision('Account'))
    finance_account_id = fields.Many2one("account.account", string="Income Account",
                                         domain=[('deprecated', '=', False)],
                                         help="Account used for deposits",
                                         default=_default_finance_account_id
                                        )
    #  1-3-2023
    def _default_registration_product(self):

        config = self.env['service.config'].search([], order='date DESC', limit=1)
        return config.rec_product.id

    @api.depends('order_line.down_payment')
    def _amount_down_payment(self):
        """
        Compute the total down payment  of the SO.
        """
        for order in self:
            down_payment = 0.0
            for line in order.order_line:
                down_payment += line.down_payment * line.product_uom_qty
            order.update({
                'down_payment': down_payment,
            })
        #  1-3-2023

    @api.depends('order_line.no_ofmanth')
    def _number_of_month(self):
        """
        Compute the total number of month  in the SO.
        """
        for order in self:
            max_no_ofmanth = 0
            for line in order.order_line:
                if line.no_ofmanth > max_no_ofmanth:
                    max_no_ofmanth = line.no_ofmanth
            no_ofmanth = max_no_ofmanth
            order.update({
                'no_ofmanth': no_ofmanth,
            })

    @api.depends('order_line.monthly_installment')
    def _amount_monthly_installment(self):
        """
        Compute the total monthly installment  of the SO.
        """
        for order in self:
            monthly_installment = 0.0
            for line in order.order_line:
                monthly_installment += line.monthly_installment
            order.update({
                'monthly_installment': monthly_installment,
            })

    @api.depends('order_line.registration', 'order_line.registration_price', 'order_line.insurance',
                 'order_line.insurance_price')
    def _amount_registration(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_registration = 0.0
            amount_insurance = 0.0
            for line in order.order_line:
                amount_registration += line.registration_price
                amount_insurance += line.insurance_price
            
            self.amount_registration= amount_registration
            self.amount_insurance= amount_insurance
           

    @api.onchange('pricelist_id')  # 22-2-2023
    def compute_pricelist_filds(self):
        self.down_payment_percentage = self.pricelist_id.down_payment_percentage
        self.number_of_installment = self.pricelist_id.number_of_installment

    def create_installment(self):  # 22-2-2023 update fields periods
        # self.write({'installments_is': True})
        installment_obj = self.env['pdc.payment']
        due_date = self.date_start + relativedelta(months=+1)
        start_date = self.date_start + relativedelta(months=+1)
        cheque_number = int(self.pdc_number)
        # cheque_number_inst = cheque_number+1
        journal = self.env['account.journal'].search([('is_pdc', '=', True)], limit=1)
        periods = self.number_of_installment
        ranges = periods + 1
        for pr in self:
            for i in range(1, ranges, ):
                installment_id = installment_obj.create({
                    'payment_amount': self.total_monthly_installment,
                    'partner_id': self.partner_id.id,
                    'due_date': due_date,
                    'bank': self.bank_name,
                    'payment_journal': journal.id,
                    'pdc_ref': cheque_number,
                    'sale_id': self.id,
                    'payment_type': 'receive',
                    'state': 'registered',
                })
                due_date = due_date + relativedelta(months=+1)
                cheque_number = int(cheque_number + 1)
        # duration = due_date.year- start_date.year
        # self.write({'installment_start_date':start_date,
        #             'installment_end_date':due_date,
        #             'contract_duration':str(duration)+' Years'})

    def get_installment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales Order Installment',
            'view_mode': 'tree,form,calendar',
            'res_model': 'pdc.payment',
            'domain': [('sale_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def compute_installment_count(self):
        for record in self:
            record.installment_count = self.env['pdc.payment'].search_count(
                [('sale_id', '=', self.id)])

    @api.depends('amount_total', 'down_payment_percentage', 'down_payment_fixed')
    def _compute_down_payment(self):  # 22-2-2023 update fields
        for sdp in self:
            if sdp.payment_method == 'installment' or 'cfr':
                if sdp.fixed_down_payment == True:
                    if sdp.amount_total:
                        sdp.total_down_payment = sdp.down_payment_fixed
                elif sdp.fixed_down_payment == False:
                    if sdp.amount_total:
                        sdp.total_down_payment = sdp.amount_total * sdp.down_payment_percentage / 100
            else:
                sdp.total_down_payment = sdp.amount_total


    @api.depends('total_down_payment', 'down_payment_percentage', 'down_payment_fixed')
    def _compute_remaining_amount(self):
        for srm in self:
            if srm.payment_method == 'installment' or 'cfr':
                if srm.total_down_payment:
                    srm.remaining_amount = srm.amount_total - srm.total_down_payment

    @api.depends('remaining_amount', 'number_of_installment')
    def _compute_monthly_installment(self):  # 22-2-2023 update fields
        for smi in self:
            if smi.payment_method == 'installment' or 'cfr':
                if smi.remaining_amount:
                    smi.total_monthly_installment = smi.remaining_amount / smi.number_of_installment

    @api.constrains('payment_method', 'pricelist_id.is_installment')
    def _installment_constrains(self):
        for rec in self:
            if rec.payment_method == 'installment':
                if rec.pricelist_id.is_installment == False:
                    raise ValidationError(_('Sorry, Price List Must be Installment Type or Ceck Payment Method...'))
                else:
                    pass

    # @api.constrains('payment_method', 'pricelist_id.is_installment')
    # def _cfr_constrains(self):
    #     for rec in self:
    #         if rec.payment_method == 'cfr':
    #             if rec.pricelist_id.is_installment == False:
    #                 raise ValidationError(_('Sorry, Price List Must be Installment Type or CFR or Ceck Payment Method...'))
    #             else:
    #                 pass

    @api.constrains('payment_method', 'pricelist_id.is_installment')
    def _cash_constrains(self):
        for rec in self:
            if rec.payment_method == 'cash':
                if rec.pricelist_id.is_installment == True:
                    raise ValidationError(_('Sorry, Price List Must be Cash or Ceck Payment Method...'))
                else:
                    pass

    def action_to_approve(self):
        approve_obj = self.env['sale.order.approval']
        for rec in self:
            # if rec.payment_type and rec.payment_type =='receive':
            approve_id = approve_obj.create({
                'order_reference': self.name,
                'customer': rec.partner_id.id,
                'payment_method': rec.payment_method,
                'salesperson': rec.user_id.id,
                'order_date': rec.date_order,
                'sale_id': self.id,
            })

            # move_id.state = 'posted'
            self.write({'state': 'approval'})

    def send_to_approve(self):
        for rec in self:
            if rec.approve_line.filtered(lambda r: r.state != 'cancel'):
                raise UserError(_(
                    'An approve order already exists.'))
            config = self.env['service.config'].search([], order='date DESC', limit=1)
            # registration_product = rec.order_line.filtered(lambda line: line.product_id == config.rec_product)
            # insurance_product = rec.order_line.filtered(lambda line: line.product_id == config.ins_product)
            # if rec.order_line.filtered(
            #         lambda line: line.registration in ['out', 'include']) and not registration_product:
            #     raise UserError(_(
            #         'please add registration in SO.'))
            # if rec.order_line.filtered(lambda line: line.insurance in ['out', 'include']) and not insurance_product:
            #     raise UserError(_(
            #         'please add insurance in SO.'))
            finance_amount = 0.0
            if not rec.order_line:
                raise UserError(_(
                    'There is no invoiceable line,please make sure that a product has been selected.'))
            approve = self.env['sale.order.approval'].create({
                'sale_id': rec.id,
                'order_reference': self.name,
                'customer': rec.partner_id.id,
                'payment_method': rec.payment_method,
                'salesperson': rec.user_id.id,
                'order_date': rec.date_order,
            })
            print('approveghkgh', approve)
            """ Registration  and  Insurance Price """
            for line in rec.order_line:
                if line.product_id.is_car == 'is_car':
                    registration_price = 0.0
                    insurance_price = 0.0
                    finance = 0.0
                    down_payment = 0.0
                    discount = 0.0
                    discount_amount = 0.0
                    finance_value = self.env['finance.config'].search([], order='id DESC', limit=1).value

                    product = line.product_id.with_context(
                        lang=line.order_id.partner_id.lang,
                        partner=line.order_id.partner_id,
                        quantity=line.product_uom_qty,
                        date=line.order_id.date_order,
                        pricelist=line.order_id.pricelist_id.id,
                        uom=line.product_uom.id
                    )
                    if line.registration == 'include':
                        registration_price = line.product_id.registration_price * line.product_uom_qty
                    elif line.registration in ['out', 'self']:
                        registration_price = 0.0

                    if line.insurance == 'include':
                        insurance_price = line.product_id.insurance_price * line.product_uom_qty
                    elif line.insurance in ['out', 'self']:
                        insurance_price = 0.0
                    # print('ins', insurance_price,rec.registration,line.product_id.insurance_price)

                    """ Unit Price , Vat and  Showroom Price"""
                    # showroom_price = line.product_id.lst_price*line.product_uom_qty
                    showroom_price = (
                        self.env['account.tax']._fix_tax_included_price_company(line._get_cash_price(product),
                                                                                product.taxes_id, line.tax_id,
                                                                                line.company_id))
                    selling_price = line.price_unit * line.product_uom_qty
                    unit_price = selling_price / 1.17
                    vat = unit_price * 0.17

                    if rec.payment_method == 'cash':
                        """ Discount """

                        if (showroom_price / 1.17) - unit_price > 0:
                            discount_amount = (showroom_price / 1.17) - unit_price
                            # print(showroom_price / 1.17, unit_price, discount_amount , 'ggggghhhhhhwwwwww')
                            discount = (discount_amount / (showroom_price / 1.17)) * 100
                        if registration_price > 0.0 and insurance_price > 0.0:
                            discount_amount2 = registration_price + insurance_price
                            discount_amount += discount_amount2
                            # print(discount_amount)
                            discount2 = (discount_amount2 / (showroom_price + discount_amount2)) * 100
                            discount += discount2
                        vals = {
                            'name': self.name,
                            'order_id': self.id,
                            'approve_id': approve.id,
                            'product_id': line.product_id.id or False,
                            'brand_id': line.product_id.brand_id.id,
                            'model_year': line.product_id.model_year,
                            'product_qty': line.product_uom_qty,
                            'showroom_price': showroom_price,
                            'selling_price': selling_price,
                            'unit_price': unit_price,
                            'vat': vat,
                            'discount_amount': discount_amount,
                            'discount': discount,
                            'insurance': insurance_price,
                            'registration': registration_price,
                            'line_id': line.id,
                        }
                        self.env['sale.approve.line'].create(vals)

                    elif rec.payment_method == 'installment':
                        # cash_price = (self.env['account.tax']._fix_tax_included_price_company(line._get_cash_price(product),product.taxes_id, line.tax_id, line.company_id))*line.product_uom_qty
                        cash_price = line.product_id.lst_price * line.product_uom_qty
                        finance2 = selling_price - cash_price - insurance_price - registration_price
                        finance = selling_price - cash_price
                        if finance <= 0:
                            finance = 0.0
                        else:
                            finance_amount += finance
                        unit_price = (selling_price - finance) / 1.17
                        vat = unit_price * 0.17
                        down_payment = (line.down_payment * line.product_uom_qty) / (unit_price + vat) * 100

                        """ Discount """
                        basic_finance = ((
                                                 cash_price / line.product_uom_qty - line.down_payment) * line.finance * line.no_ofmanth) * line.product_uom_qty
                        if basic_finance - finance2 > 0:
                            discount_amount = basic_finance - finance2
                            discount = (discount_amount / (cash_price + basic_finance)) * 100
                            if insurance_price > 0.0 or registration_price > 0.0:
                                discount = (discount_amount / (
                                        cash_price + basic_finance + insurance_price + registration_price)) * 100
                        else:
                            discount_amount = 0.0

                        vals = {
                            'name': self.name,
                            'order_id': self.id,
                            'approve_id': approve.id,
                            'product_id': line.product_id.id or False,
                            'brand_id': line.product_id.brand_id.id,
                            'model_year': line.product_id.model_year,
                            'product_qty': line.product_uom_qty,
                            'showroom_price': cash_price,
                            'selling_price': selling_price,
                            'unit_price': unit_price,
                            'vat': vat,
                            'discount_amount': discount_amount,
                            'discount': discount,
                            'insurance': insurance_price,
                            'registration': registration_price,
                            'finance': finance,
                            'down_payment': down_payment,
                            'no_ofmanth': line.no_ofmanth,
                            'line_id': line.id,
                        }
                        self.env['sale.approve.line'].create(vals)

                    elif rec.payment_method == 'crf':
                        crf_price = self.env['account.tax']._fix_tax_included_price_company(
                            line._get_display_price(product), product.taxes_id, line.tax_id,
                            line.company_id) * line.product_uom_qty
                        if (crf_price - selling_price) > 0:
                            discount_amount = crf_price - selling_price
                            discount = (discount_amount / crf_price) * 100
                        else:
                            discount_amount = 0.0
                            discount = 0.0
                        vals = {
                            'name': self.name,
                            'order_id': self.id,
                            'approve_id': approve.id,
                            'product_id': line.product_id.id or False,
                            'brand_id': line.product_id.brand_id.id,
                            'model_year': line.product_id.model_year,
                            'product_qty': line.product_uom_qty,
                            'crf_price': crf_price,
                            'selling_price': selling_price,
                            'discount_amount': discount_amount,
                            'discount': discount,
                            'line_id': line.id,
                        }
                        self.env['sale.approve.line'].create(vals)
                rec.state = 'approval'
                rec.finance_amount = finance_amount

     
    # def send_to_approve(self):
    #     for rec in self:
    #         if rec.approve_line.filtered(lambda r: r.state != 'cancel'):
    #             raise UserError(_(
    #                 'An approve order already exists.'))

    #         config = self.env['service.config'].search([], order='date DESC', limit=1)
    #         # registration_product = rec.order_line.filtered(lambda line: line.product_id == config.rec_product)
    #         # insurance_product = rec.order_line.filtered(lambda line: line.product_id == config.ins_product)
    #         # if rec.order_line.filtered(lambda line: line.registration in ['out', 'include']) and not registration_product:
    #         #     raise UserError(_(
    #         #         'please add registration in SO.'))
    #         # if rec.order_line.filtered(lambda line: line.insurance in ['out', 'include']) and not insurance_product:
    #         #     raise UserError(_(
    #         #         'please add insurance in SO.'))
    #         finance_amount = 0.0
    #         if not rec.order_line:
    #             raise UserError(_(
    #                 'There is no invoiceable line,please make sure that a product has been selected.'))
    #         approve = self.env['sale.order.approval'].create({
    #             'sale_id': rec.id,
    #             'order_reference': self.name,
    #             'customer': rec.partner_id.id,
    #             'payment_method': rec.payment_method,
    #             'salesperson': rec.user_id.id,
    #         })
    #         print('approveghkgh',approve)
    #         """ Registration  and  Insurance Price """
    #         for line in rec.order_line:
    #             if line.product_id.is_car == 'is_car':
    #                 registration_price = 0.0
    #                 insurance_price = 0.0
    #                 finance = 0.0
    #                 down_payment = 0.0
    #                 discount = 0.0
    #                 discount_amount = 0.0
    #                 finance_value = self.env['finance.config'].search([], order='id DESC', limit=1).value

    #                 product = line.product_id.with_context(
    #                     lang=line.order_id.partner_id.lang,
    #                     partner=line.order_id.partner_id,
    #                     quantity= line.product_uom_qty,
    #                     date=line.order_id.date_order,
    #                     pricelist=line.order_id.pricelist_id.id,
    #                     uom=line.product_uom.id
    #                 )
    #                 if line.registration == 'include':
    #                     registration_price = line.product_id.registration_price*line.product_uom_qty
    #                 elif line.registration in ['out', 'self']:
    #                     registration_price = 0.0

    #                 if line.insurance == 'include':
    #                     insurance_price = line.product_id.insurance_price*line.product_uom_qty
    #                 elif line.insurance in ['out', 'self']:
    #                     insurance_price = 0.0
    #                 # print('ins', insurance_price,rec.registration,line.product_id.insurance_price)

    #                 """ Unit Price , Vat and  Showroom Price"""
    #                 # showroom_price = line.product_id.lst_price*line.product_uom_qty
    #                 showroom_price = (self.env['account.tax']._fix_tax_included_price_company(line._get_display_price(product),product.taxes_id, line.tax_id, line.company_id))
    #                 selling_price = line.price_unit*line.product_uom_qty
    #                 unit_price = selling_price / 1.17
    #                 vat = unit_price * 0.17

    #                 if rec.payment_method == 'cash':
    #                     """ Discount """

    #                     if (showroom_price / 1.17) - unit_price > 0:
    #                         discount_amount = (showroom_price / 1.17) - unit_price
    #                         # print(showroom_price / 1.17, unit_price, discount_amount , 'ggggghhhhhhwwwwww')
    #                         discount = (discount_amount / (showroom_price / 1.17))*100
    #                     if registration_price > 0.0 and insurance_price > 0.0:
    #                         discount_amount2 = registration_price + insurance_price
    #                         discount_amount += discount_amount2
    #                         # print(discount_amount)
    #                         discount2 = (discount_amount2 / (showroom_price + discount_amount2))*100
    #                         discount += discount2
    #                     vals = {
    #                         'name': self.name,
    #                         'order_id': self.id,
    #                         'approve_id': approve.id,
    #                         'product_id': line.product_id.id or False,
    #                         'brand': line.product_id.brand.id,
    #                         'model_year': line.product_id.model_year,
    #                         'product_qty': line.product_uom_qty,
    #                         'showroom_price': showroom_price,
    #                         'selling_price': selling_price,
    #                         'unit_price': unit_price,
    #                         'vat': vat,
    #                         'discount_amount': discount_amount,
    #                         'discount': discount,
    #                         'insurance': insurance_price,
    #                         'registration': registration_price,
    #                         'line_id': line.id,
    #                         'registration_type': line.registration,
    #                         'insurance_type': line.insurance,
    #                     }
    #                     self.env['sale.approve.line'].create(vals)

    #                 elif rec.payment_method == 'installment':
    #                     cash_price = (self.env['account.tax']._fix_tax_included_price_company(line._get_display_price(product),product.taxes_id, line.tax_id, line.company_id))*line.product_uom_qty
    #                     # cash_price = line.product_id.lst_price*line.product_uom_qty
    #                     finance2 = selling_price - cash_price - insurance_price - registration_price
    #                     finance = selling_price - cash_price
    #                     if finance <= 0:
    #                         finance = 0.0
    #                     else:
    #                         finance_amount += finance
    #                     unit_price = (selling_price - finance) / 1.17
    #                     vat = unit_price * 0.17
    #                     down_payment = (line.down_payment*line.product_uom_qty) / (unit_price + vat) * 100

    #                     """ Discount """
    #                     basic_finance = ((cash_price/line.product_uom_qty - line.down_payment) * (line.installment_policy.profit / line.no_ofmanth / 100) * line.no_ofmanth)*line.product_uom_qty
    #                     print(basic_finance,finance2,'finance2',cash_price,(cash_price/line.product_uom_qty - line.down_payment),line.installment_policy.profit,line.no_ofmanth,line.product_uom_qty)
    #                     if basic_finance - finance2 > 0:
    #                         discount_amount = basic_finance - finance2
    #                         discount = (discount_amount / (cash_price + basic_finance))*100
    #                         if insurance_price > 0.0 or registration_price > 0.0:
    #                             discount = (discount_amount / (cash_price + basic_finance + insurance_price + registration_price)) * 100
    #                     else:
    #                         discount_amount = 0.0

    #                     vals = {
    #                         'name': self.name,
    #                         'order_id': self.id,
    #                         'approve_id': approve.id,
    #                         'product_id': line.product_id.id or False,
    #                         'brand': line.product_id.brand.id,
    #                         'model_year': line.product_id.model_year,
    #                         'product_qty': line.product_uom_qty,
    #                         'showroom_price': cash_price,
    #                         'selling_price': selling_price,
    #                         'unit_price': unit_price,
    #                         'vat': vat,
    #                         'discount_amount': discount_amount,
    #                         'discount' : discount,
    #                         'insurance': insurance_price,
    #                         'registration': registration_price,
    #                         'finance': finance,
    #                         'down_payment': down_payment,
    #                         'no_ofmanth': line.no_ofmanth,
    #                         'line_id': line.id,
    #                         'registration_type': line.registration,
    #                         'insurance_type': line.insurance,
    #                     }
    #                     self.env['sale.approve.line'].create(vals)

    #                 elif rec.payment_method == 'crf':
    #                     crf_price = self.env['account.tax']._fix_tax_included_price_company(line._get_display_price(product), product.taxes_id, line.tax_id, line.company_id)*line.product_uom_qty
    #                     if(crf_price - selling_price) > 0:
    #                         discount_amount = crf_price - selling_price
    #                         discount = (discount_amount/crf_price)*100
    #                     else:
    #                         discount_amount = 0.0
    #                         discount = 0.0
    #                     vals = {
    #                         'name': self.name,
    #                         'order_id': self.id,
    #                         'approve_id': approve.id,
    #                         'product_id': line.product_id.id or False,
    #                         'brand': line.product_id.brand.id,
    #                         'model_year': line.product_id.model_year,
    #                         'product_qty': line.product_uom_qty,
    #                         'crf_price': crf_price,
    #                         'selling_price': selling_price,
    #                         'discount_amount': discount_amount,
    #                         'discount': discount,
    #                         'line_id':line.id,
    #                     }
    #                     self.env['sale.approve.line'].create(vals)
    #             rec.state = 'sent_approve'
    #             vals = {
    #                 'name': rec.name,
    #                 'sale_order_id': rec.id,
    #                 'state': rec.state,
    #                 'date': fields.Datetime.now(),
    #             }
    #             self.env['sale.history'].sudo().create(vals)
    #             rec.finance_amount = finance_amount

    def action_to_pdi(self):

        pdi_obj = self.env['fleet.workshop']
        for rec in self.order_line:
            pdi_id = pdi_obj.create({
                'partner_id': self.partner_id.partner_id,
                'client_id': self.partner_id.id,
                'partner_id': self.partner_id.id,
                'sale_id': self.id,
                'car_repair_line': [(0, 0, {
                    'product_id': self.order_line.product_id.id,
                    'brand_id': self.order_line.brand_id.id,
                    'model_year': self.order_line.model_year,
                    # 'fuel_type': self.order_line.product_id.fuel,
                })]
            })
        # self.write({'state':'pdi'}) #From Workshop Madule    Neeed Review

    def action_to_contract(self):
        contract_obj = self.env['sale.contract']
        for rec in self:
            for line in rec.order_line:
                contracts_id = contract_obj.create({
                    'order_reference': self.name,
                    'customer': rec.partner_id.id,
                    # 'payment_method': rec.payment_method,
                    # 'salesperson' : rec.user_id.id,
                    'down_payment_amount': rec.total_down_payment,
                    'sale_id': self.id,
                    'total_amount': line.price_subtotal,
                    # 'down_payment_amount': line.price_subtotal,
                    'product_id': line.product_id.name,
                })
        self.write({'state': 'contract'})

    def get_approval(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales Order Approval',
            'view_mode': 'tree,form',
            'res_model': 'sale.order.approval',
            'domain': [('sale_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def compute_approval_count(self):
        for record in self:
            record.approval_count = self.env['sale.order.approval'].search_count(
                [('sale_id', '=', self.id)])

    def get_contract(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales Contract',
            'view_mode': 'tree,form',
            'res_model': 'sale.contract',
            'domain': [('sale_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def compute_contract_count(self):
        for record in self:
            record.contract_count = self.env['sale.contract'].search_count(
                [('sale_id', '=', self.id)])

    def get_pdi(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales Order PDI Job',
            'view_mode': 'tree,form',
            'res_model': 'fleet.workshop',
            'domain': [('sale_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def compute_pdi_count(self):
        for record in self:
            record.pdi_count = self.env['fleet.workshop'].search_count(
                [('sale_id', '=', self.id)])

    def get_insurance(self):
        pass


class SaleOrderApproval(models.Model):
    _name = "sale.order.approval"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "rec_name"

    sequence = fields.Char(string='Reference', required=True, copy=False, readonly=True, index=True,
                           default=lambda self: _('New'))
    description = fields.Char(string="Description")
    order_date = fields.Datetime(string="Order Date")
    order_reference = fields.Char(string="Order Reference")
    salesperson = fields.Many2one('res.users', string="Salesperson")
    customer = fields.Many2one('res.partner', string="Customer")
    payment_method = fields.Char(string="Payment Method")
    total_discount_amount = fields.Float(string="Total Discount Amount")
    #  1-3-2023
    approve_lines = fields.One2many('sale.approve.line', 'approve_id', string='Approves')
    total_discount = fields.Float('Total Discount Amount', compute='_get_total_discount', digits=(12, 3),store=True)
    total_amount = fields.Float('Total Amount', compute='_get_total', digits=(12, 3),store=True)
    total_discount_pre = fields.Float('Discount Percentage %', compute='_get_total_amount_discount', digits=(12, 3),store=True)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'sale.order.approval'))

    state = fields.Selection([
        ('draft', 'Draft'),
        ('discount', 'Discount Approve'),
        ('sales_sp', 'Sales SP'),
        ('sales_m', 'Sales M'),
        ('credit_controller', 'CREDIT CONTROLLER'), ], default="draft")
    sale_id = fields.Many2one('sale.order')
    rec_name = fields.Char(compute="_compute_rec_name")

    @api.depends('approve_lines.discount_amount')
    def _get_total_discount(self):
        for rec in self:
            for line in rec.approve_lines:
                rec.total_discount += line.discount_amount

    @api.depends('approve_lines.discount')
    def _get_total_amount_discount(self):
        for rec in self:
            for line in rec.approve_lines:
                rec.total_discount_pre += line.discount

    @api.depends('approve_lines.selling_price', 'approve_lines.vat')
    def _get_total(self):
        for rec in self:
            vat = 0.0
            total_selling = 0.0
            for line in rec.approve_lines:
                total_selling += line.selling_price
                vat += line.vat
            rec.total_amount = total_selling - vat

    @api.model
    def create(self, vals):
        res = super(SaleOrderApproval, self).create(vals)
        res.update({'sequence': self.env['ir.sequence'].next_by_code('sale.order.approval') or _('New')})
        return res

    @api.model
    def _compute_rec_name(self):
        if self.id:
            self.rec_name = self.order_reference + "/" + self.sequence

    def action_discount_approve(self):
        self.write({'state': 'discount'})

    def action_sales_sp_approve(self):
        self.write({'state': 'sales_sp'})

    def action_sales_m_approve(self):
        self.write({'state': 'sales_m'})

    def action_credit_controller(self):
        self.sale_id.write({'state': 'approved'})
        self.write({'state': 'credit_controller'})

    # class MuneefAccountPayment(models.Model):
    # _inherit = 'account.payment.employee'

    # service_id = fields.Many2one('end.service',string="End OF Service")

    # def action_post(self):
    #     record = super(MuneefAccountPayment, self).action_post()
    #     if self.service_id:
    #         self.service_id.state = 'paid'
    #         self.service_id.payment_id = self.id
    #     return record


class SaleApproveLine(models.Model):
    _name = "sale.approve.line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Sales Approve Line'
    _order = 'order_id, id'

    name = fields.Text(string='Description', )
    order_id = fields.Many2one('sale.order', string='Order Reference', ondelete='cascade',
                               index=True, copy=False)
    line_id = fields.Many2one('sale.order.line', string='Line Reference', ondelete='cascade',
                              index=True, copy=False)
    approve_id = fields.Many2one('sale.order.approval', string='Order Reference', ondelete='cascade',
                                 index=True, copy=False)
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)],
                                 change_default=True, ondelete='restrict')
    brand_id = fields.Many2one('fleet.vehicle.model.brand', related='product_id.brand_id', string='Brand',
                               readonly=True,
                               store=True)
    model_year = fields.Integer('Model Year', related='product_id.model_year', readonly=True, store=True)
    product_qty = fields.Float(string='Ordered Quantity', default=1.0)
    showroom_price = fields.Float('Showroom Price', default=0.0)
    selling_price = fields.Float('Selling Price ', default=0.0)
    unit_price = fields.Float('Unit Price ', default=0.0)
    vat = fields.Float('VAT', default=0.0)
    insurance = fields.Float('Insurance', default=0.0)
    registration = fields.Float('Registration ', default=0.0)
    discount_amount = fields.Float('Discount ', default=0.0)
    discount = fields.Float('Discount %', default=0.0, digits=(12, 3))
    finance = fields.Float('Finance ', default=0.0)
    down_payment = fields.Float('Down Payment %', default=0.0, digits=(12, 3))
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('sale.approve.line'))
    crf_price = fields.Float('CRF Price ', default=0.0)
    no_ofmanth = fields.Integer('No.of Month')

#
# class FinanceConfig(models.Model):
#     _name = "finance.config"
#     _inherit = ['mail.thread', 'mail.activity.mixin']
#     _rec_name = 'value'
#
#     value = fields.Float(string="Value", required=True, track_visibility='onchange', default=0.0166, digits=(12, 4))
#     company_id = fields.Many2one('res.company', 'Company',
#                                  default=lambda self: self.env['res.company']._company_default_get(
#                                      'finance.config'))
