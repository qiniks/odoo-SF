from odoo import models, fields, api
import requests
import json
import logging
import socket

_logger = logging.getLogger(__name__)


class ApiProduct(models.Model):
    _name = "api.product"
    _description = "Products from External API"
    _order = "priority desc, date desc"

    api_id = fields.Integer(string="API ID")
    name = fields.Char(string="Name")
    date = fields.Date(string="Date")
    design = fields.Char(string="Design")
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High')
    ], string="Priority", default='1')

    @api.model
    def fetch_and_store_api_data(self):
        try:
            # When running in Docker, use host.docker.internal to access the host
            # For Linux-based Docker, you might need to use the actual host IP
            response = requests.get(
                "http://host.docker.internal:8000/api/get_data", timeout=10
            )
            response.raise_for_status()  # Raise exception for HTTP errors

            # Parse JSON response
            api_data = response.json()

            if api_data.get("status") == "success" and "data" in api_data:
                # Clear existing records
                self.search([]).unlink()

                # Create new records
                products_to_create = []
                for product in api_data["data"]:
                    products_to_create.append(
                        {
                            "api_id": product.get("id"),
                            "name": product.get("name"),
                            "date": product.get("date"),
                            "design": product.get("design"),
                        }
                    )

                if products_to_create:
                    self.create(products_to_create)

                # Return an action to display the products
                return {
                    "name": "API Products",
                    "type": "ir.actions.act_window",
                    "res_model": "api.product",
                    "view_mode": "list,form",
                    "domain": [],
                    "context": {"create": False},
                }
            else:
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": "API Error",
                        "message": "Invalid response format from API",
                        "sticky": False,
                        "type": "danger",
                    },
                }

        except requests.exceptions.RequestException as e:
            _logger.error(f"Error fetching API data: {e}")
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "API Error",
                    "message": f"Failed to fetch data from API: {str(e)}",
                    "sticky": False,
                    "type": "danger",
                },
            }
