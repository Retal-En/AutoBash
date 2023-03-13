
from odoo import fields, models, api, tools, _
from datetime import date, time, datetime

class PurchaseTasks(models.Model):
    _name = "purchase.task"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Purchase Order"
    _order = 'priority desc, id desc'






class PurchaseTaskeLine(models.Model):
    _name = 'purchase.task.line'
    _description = 'Purchase Task Line'
    _order = 'order_id, sequence, id'

    name = fields.Text(string='Description', required=True)