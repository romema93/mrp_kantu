# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class KantuProduccion(http.Controller):
    @http.route('/kantu/produccion/<production>', type='http', auth='user')
    def kantu_web(self,production):
        context = json.dumps(request.session.context)
        return request.render('mrp_kantu.index',{'production':production,'context':context})\

    @http.route('/kantu/produccion2/<production>', type='http', auth='user')
    def kantu_web2(self,production):
        context = json.dumps(request.session.context)
        return request.render('mrp_kantu.index2',{'production':production,'context':context})
#     @http.route('/kantu_produccion/kantu_produccion/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/kantu_produccion/kantu_produccion/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('kantu_produccion.listing', {
#             'root': '/kantu_produccion/kantu_produccion',
#             'objects': http.request.env['kantu_produccion.kantu_produccion'].search([]),
#         })

#     @http.route('/kantu_produccion/kantu_produccion/objects/<model("kantu_produccion.kantu_produccion"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('kantu_produccion.object', {
#             'object': obj
#         })