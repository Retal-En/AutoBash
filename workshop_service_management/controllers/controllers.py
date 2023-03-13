# -*- coding: utf-8 -*-
# from odoo import http


# class WorkshopServiceManagement(http.Controller):
#     @http.route('/workshop_service_management/workshop_service_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/workshop_service_management/workshop_service_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('workshop_service_management.listing', {
#             'root': '/workshop_service_management/workshop_service_management',
#             'objects': http.request.env['workshop_service_management.workshop_service_management'].search([]),
#         })

#     @http.route('/workshop_service_management/workshop_service_management/objects/<model("workshop_service_management.workshop_service_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('workshop_service_management.object', {
#             'object': obj
#         })
