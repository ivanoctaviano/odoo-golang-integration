from odoo import http
from odoo.http import request
from datetime import datetime
from . import helper
from .helper import JsonControllerMixin
import json

import logging
_logger = logging.getLogger(__name__)

class SaleOrder(http.Controller):
    JsonControllerMixin.patch_for_json("/order")

    @http.route('/order', auth='public', csrf=False, methods=['POST'])
    def action_create_order(self):
        auth = helper.parse_header()
        token = request.env['ir.config_parameter'].sudo().get_param('static_token')

        if auth == token:
            body = json.loads(request.httprequest.data.decode("utf-8"))

            invalid_payload = self.check(body)
            if invalid_payload:
                return helper.response(code=400, success=False, data=invalid_payload)

            sale_obj = request.env['sale.order'].sudo()
            
            exist_order = sale_obj.search([('origin','=',body.get('name'))])
            if exist_order:
                return helper.response(code=409, success=False, data={'name': "Already exists"})

            order_line = [(0, 0, line) for line in body.get('order_line')]
            vals = {
                "origin": body.get('name'),
                "partner_id": body.get('partner_id'),
                "date_order": body.get('date_order'),
                "company_id": body.get('company_id'),
                "order_line": order_line
            }
            try:
                sale_obj.create(vals)
                return helper.response(code=200, success=True, message='Success')
            except Exception as e:
                _logger.info("Failed to create order : %s", e)
                return helper.response(code=500, success=False, message='Internal Server Error')
        else:
            return helper.response(code=401, success=False, message='Token Not Found')

    @http.route('/order/<int:order_id>', auth='public', csrf=False, methods=['GET'])
    def action_get_order_detail(self, order_id):
        auth = helper.parse_header()
        token = request.env['ir.config_parameter'].sudo().get_param('static_token')

        if auth == token:
            sale_obj = request.env['sale.order'].sudo()
            
            exist_order = sale_obj.search([('id','=',order_id)])
            if not exist_order:
                return helper.response(code=400, success=False, message='order id not found')

            try:
                request.env.cr.execute("""
                    WITH partner AS (
                        SELECT 
                            so.id AS so_id,
                            jsonb_agg(
                                json_build_object(
                                        'partner_id', rp.id,
                                        'name', rp.name,
                                        'address', rp.street
                                    )
                            ) AS data
                        FROM sale_order so
                        JOIN res_partner rp ON so.partner_id = rp.id
                        WHERE so.id = %(order_id)s
                        GROUP BY so.id
                    ), company AS (
                        SELECT 
                            so.id as so_id,
                            jsonb_agg(
                                json_build_object(
                                        'id', rc.id,
                                        'name', rc.name,
                                        'description', rp.street
                                    )
                            ) AS data
                        FROM sale_order so
                        JOIN res_company rc ON so.company_id = rc.id
                        JOIN res_partner rp ON rc.partner_id = rp.id
                        WHERE so.id = %(order_id)s
                        GROUP BY so.id
                    )
                    SELECT 
                        so.origin AS name,
                        so.partner_id,
                        TO_CHAR(so.date_order, 'YYYY-MM-DD HH:MM:SS') AS date_order,
                        so.company_id,
                        json_build_object(
                            'partner', p.data,
                            'product', jsonb_agg(
                                    json_build_object(
                                        'id', pp.id,
                                        'name', pt.name,
                                        'description', pt.description,
                                        'price', sol.price_unit
                                    )
                            ),
                            'company', c.data,
                            'uom', jsonb_agg(
                                    json_build_object(
                                        'id', uu.id,
                                        'name', uu.name,
                                        'description', uu.uom_type
                                    )
                            ),
                            'order_line', jsonb_agg(
                                    json_build_object(
                                        'price_unit', sol.price_unit,
                                        'product_id', pp.id,
                                        'product_uom_qty', sol.product_uom_qty,
                                        'product_uom', uu.id
                                    )
                            )
                        ) AS relationship
                    FROM sale_order so
                    JOIN sale_order_line sol ON so.id = sol.order_id
                    JOIN partner p ON so.id = p.so_id
                    JOIN company c ON so.id = c.so_id
                    JOIN product_product pp ON sol.product_id = pp.id
                    JOIN product_template pt ON pp.product_tmpl_id = pt.id
                    JOIN uom_uom uu ON sol.product_uom = uu.id
                    WHERE so.id = %(order_id)s
                    GROUP BY so.id, p.data, c.data
                """, {'order_id': order_id}
                )
                data = request.env.cr.dictfetchall()[0]
                return helper.response(code=200, success=True, message='Data found', data=data)
            except Exception as e:
                _logger.info("Failed to get order detail : %s", e)
                return helper.response(code=500, success=False, message='Internal Server Error')
        else:
            return helper.response(code=401, success=False, message='Token Not Found')
    
    @http.route('/order/<int:order_id>', auth='public', csrf=False, methods=['PUT'])
    def action_update_order(self, order_id):
        auth = helper.parse_header()
        token = request.env['ir.config_parameter'].sudo().get_param('static_token')

        if auth == token:
            body = json.loads(request.httprequest.data.decode("utf-8"))

            invalid_payload = self.check(body)
            if invalid_payload:
                return helper.response(code=400, success=False, data=invalid_payload)

            sale_obj = request.env['sale.order'].sudo()
            
            exist_order = sale_obj.search([('id','=',order_id)])
            if not exist_order:
                return helper.response(code=400, success=False, data={'name': "order id not found"})

            exist_order_reference = sale_obj.search([('id','!=',order_id),('origin','=',body.get('name'))])
            if exist_order_reference:
                return helper.response(code=409, success=False, data={'name': "Already exists"})

            exist_order.write({'order_line': [(5, 0, 0)]})

            order_line = [(0, 0, line) for line in body.get('order_line')]
            vals = {
                "origin": body.get('name'),
                "partner_id": body.get('partner_id'),
                "date_order": body.get('date_order'),
                "company_id": body.get('company_id'),
                "order_line": order_line
            }
            try:
                exist_order.write(vals)
                return helper.response(code=200, success=True, message='Success')
            except Exception as e:
                _logger.info("Failed to update order : %s", e)
                return helper.response(code=500, success=False, message='Internal Server Error')
        else:
            return helper.response(code=401, success=False, message='Token Not Found')

    def check(self, body):
        data = {}

        if not body.get('name'):
            data['name'] = "Required"
        elif not isinstance(body.get('name'), str):
            data['name'] = "Is not string"

        if not body.get('partner_id'):
            data['partner_id'] = "Required"
        elif not isinstance(body.get('partner_id'), int):
            data['partner_id'] = "Is not integer"
        else:
            partner_id = request.env['res.partner'].sudo().search([('id','=',body.get('partner_id'))])
            if not partner_id:
                data['partner_id'] = "Not found"

        if not body.get('date_order'):
            data['date_order'] = "Required"
        elif not isinstance(body.get('date_order'), str):
            data['date_order'] = "Is not string"
        else:
            try:
                datetime.strptime(body.get('date_order'), "%Y-%m-%d %H:%M:%S")
            except:
                data['date_order'] = "Invalid format date"

        if not body.get('company_id'):
            data['company_id'] = "Required"
        elif not isinstance(body.get('company_id'), int):
            data['company_id'] = "Is not integer"
        else:
            company_id = request.env['res.company'].sudo().search([('id','=',body.get('company_id'))])
            if not company_id:
                data['company_id'] = "Not found"

        if not body.get('order_line'):
            data['order_line'] = "Required"
        elif not isinstance(body.get('order_line'), list):
            data['order_line'] = "Is not array"
        else:
            count = 0
            for line in body.get('order_line'):
                
                if not line.get('product_id'):
                    data['order_line.'+str(count)+'.product_id'] = "Required"
                elif not isinstance(line.get('product_id'), int):
                    data['order_line.'+str(count)+'.product_id'] = "Is not integer"

                if not line.get('product_uom_qty'):
                    data['order_line.'+str(count)+'.product_uom_qty'] = "Required"
                elif not isinstance(line.get('product_id'), int):
                    data['order_line.'+str(count)+'.product_uom_qty'] = "Is not integer"
                
                if not line.get('product_uom'):
                    data['order_line.'+str(count)+'.product_uom'] = "Required"
                elif not isinstance(line.get('product_id'), int):
                    data['order_line.'+str(count)+'.product_uom'] = "Is not integer"

                if not line.get('price_unit'):
                    data['order_line.'+str(count)+'.price_unit'] = "Required"
                elif not isinstance(line.get('product_id'), int):
                    data['order_line.'+str(count)+'.price_unit'] = "Is not integer"

                count += 1

        return data