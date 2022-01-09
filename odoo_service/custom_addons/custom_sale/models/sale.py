from odoo import api, models
import requests
import json

import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        url = self.env['ir.config_parameter'].sudo().get_param('webhook_url')
        token = self.env['ir.config_parameter'].sudo().get_param('webhook_token')

        headers = {
            'Content-Type' : 'application/json',
            'Authorization' : token 
        }

        data = {
            'event' : 'service.sales_order_created',
            'payload' : vals
        }

        try:
            requests.post(url, headers=headers, data=json.dumps(data))
        except Exception as e:
            _logger.info('Failed to send webhook notif sale order created : ', e)

        return res

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        url = self.env['ir.config_parameter'].sudo().get_param('webhook_url')
        token = self.env['ir.config_parameter'].sudo().get_param('webhook_token')

        headers = {
            'Content-Type' : 'application/json',
            'Authorization' : token 
        }

        data = {
            'event' : 'service.sales_order_updated',
            'payload' : vals
        }

        try:
            requests.post(url, headers=headers, data=json.dumps(data))
        except Exception as e:
            _logger.info('Failed to send webhook notif sale order updated : ', e)

        return res