from odoo import models, fields, api
import requests
import json
import logging
import random
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class ApiProduct(models.Model):
    _name = "api.product"
    _description = "API Product Data"
    _order = "name"  # Updated order to only sort by name

    api_id = fields.Integer("API ID", required=True)
    name = fields.Char("Name", required=True)
    date = fields.Date("Date")
    design = fields.Char("Design")
    fast_ship = fields.Boolean("Fast Ship", default=False)
    quantity = fields.Integer("Quantity", default=1)
    email = fields.Char("Email")

    # New state field with selection options
    state = fields.Selection(
        [
            ("all_products", "All Products"),
            ("processing", "Processing"),
            ("approving", "Approving"),
            ("not_approved", "Not Approved"),
            ("done", "Done"),
        ],
        string="Status",
        default="all_products",
        tracking=True,
    )

    # Priority field for sorting (computed based on tags)
    priority = fields.Integer(
        string="Priority", compute="_compute_priority", store=True
    )

    @api.depends("fast_ship", "quantity", "design")
    def _compute_priority(self):
        for record in self:
            # Default priority = 0
            priority = 0

            # Priority 3 (highest): Urgent (fast_ship)
            if record.fast_ship:
                priority = 10
            # Priority 2: Bulk Order (quantity > 10)
            elif record.quantity > 10:
                priority = 2
            # Priority 1: Custom design
            elif record.design:
                priority = 1

            record.priority = priority

    @api.model
    def create(self, vals):
        # Set default state if not provided
        if "state" not in vals:
            vals["state"] = "all_products"
        return super(ApiProduct, self).create(vals)

    @api.model
    def fetch_and_store_api_data(self):
        """Fetch data from local API and store it in the database"""
        try:
            # Try different hostnames for different environments
            hostnames = [
                "http://host.docker.internal:8000",
            ]

            response = None
            exception = None

            for hostname in hostnames:
                try:
                    url = f"{hostname}/api/get_data"
                    _logger.info(f"Trying to connect to API at: {url}")
                    response = requests.get(url, timeout=3)
                    if response.status_code == 200:
                        _logger.info(f"Successfully connected to API at: {url}")
                        break
                except requests.exceptions.RequestException as e:
                    exception = e
                    continue

            if not response or response.status_code != 200:
                raise exception or ValueError("Could not connect to any API endpoint")

            # Parse JSON response
            api_data = response.json()
            _logger.info(f"API response data: {api_data}")

        except (requests.exceptions.RequestException, ValueError) as e:
            _logger.error(f"Could not connect to API: {str(e)}")
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "API Connection Error",
                    "message": f"Could not connect to API: {str(e)}",
                    "sticky": True,
                    "type": "danger",
                },
            }

        if api_data.get("status") == "success" and "data" in api_data:
            try:
                # Track how many products were added and updated
                added_count = 0
                updated_count = 0

                for product_data in api_data["data"]:
                    # Make sure we have a valid product name
                    product_name = product_data.get("product")
                    if not product_name:  # Add explicit check for empty product name
                        _logger.warning(
                            f"Skipping product with no name: {product_data}"
                        )
                        continue

                    try:
                        # Check if a product with the same API ID already exists
                        api_id = product_data.get("id")
                        existing_product = self.search(
                            [("api_id", "=", api_id)], limit=1
                        )

                        product_values = {
                            "api_id": api_id,
                            "name": product_name,
                            "date": product_data.get("date"),
                            "design": product_data.get("design", ""),
                            "fast_ship": product_data.get("fastShip") == "True",
                            "quantity": product_data.get("quantity", 1),
                            "email": product_data.get("mail", ""),
                        }

                        if not existing_product:
                            # Create new product
                            api_product = self.create(product_values)
                            _logger.info(
                                f"Created API product: {api_product.name}, ID: {api_product.api_id}"
                            )
                            added_count += 1

                    except Exception as e:
                        _logger.error(f"Error processing API product: {e}")

                # Update success message to show counts
                message = f"API products imported successfully: {added_count} added, {updated_count} updated"
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": "API Import",
                        "message": message,
                        "sticky": False,
                        "type": "success",
                    },
                }
            except Exception as e:
                _logger.error(f"Error in fetch_and_store_api_data: {e}", exc_info=True)
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": "Error",
                        "message": f"Error processing API data: {str(e)}",
                        "sticky": False,
                        "type": "danger",
                    },
                }
        else:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "API Error",
                    "message": f"Invalid response format from API: {api_data}",
                    "sticky": False,
                    "type": "danger",
                },
            }
