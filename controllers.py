
import json
import logging

_logger = logging.getLogger(__name__)

from odoo import http

"""statuses:[
    "Pickup_Requested"
    "Assigned_for_Pickup"
    "Picked"
    "Pickup_Failed"
    "Pickup_Cancelled"
    "At_the_Sorting_HUB"
    "In_Transit"
    "Received_at_Last_Mile_HUB"
    "Assigned_for_Delivery"
    "Delivered"
    "Partial_Delivery"
    "Return"
    "Delivery_Failed"
    "On_Hold"
    "Payment_Invoice"
    ]"""


class pathao_WebHook(http.Controller):
    @http.route('/pathao_status', auth='public', type="json", website=False)
    def pathao_notification_post(self, **post):
        try:
            pathao_signature = http.request.httprequest.headers.get('X-PATHAO-Signature')
            if pathao_signature != "use_pathao_webhook_secrect_here":
                return self.error_response_builder(401, "wrong_webhook_secret",
                                                   "webhook secret is wrong. please provide correct one.")

            data = json.loads(http.request.httprequest.data)
            _logger.info("Pathao Webhook Info  {}".format(json.dumps(data)))
            order_name = data.get("merchant_order_id", None)
            if not order_name:
                return self.error_response_builder(400, "merchant_order_id_not_found", "Merchant Order ID is required.")

            order = http.request.env["sale.order"].sudo().search([("name", "=", order_name)], limit=1, order="id desc")
            if not order:
                return self.error_response_builder(400, "order_not_found",
                                                   "No Order is found by the given Merchant Order ID")
        except Exception as e:
            _logger.error("Error!!!  {}".format(e))
            return self.error_response_builder(500, "order_update_error2", str(e))
        try:
            order.write({
                "pathao_state": data['order_status'],
                "pathao_last_update_time": data['updated_at']

            })
            if 'reason' in data:
                order.write({
                    "pathao_reason": data['reason']
                })
        except Exception as e:
            _logger.error("Error!!!  {}".format(e))
            return self.error_response_builder(500, "order_update_error", str(e))

        return self.success_response_builder(200, data)

    def success_response_builder(self, status, data):
        resp = {
            "status": status,
            'success': True,
            'result': data,
        }

        return resp

    def error_response_builder(self, status, error, error_descp):
        resp = {
            "status": status,
            'error': error,
            'description': error_descp,

        }

        return resp
