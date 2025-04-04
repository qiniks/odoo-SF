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
            _logger.warning(f"Could not connect to API, using fallback data: {str(e)}")
            # Fallback data in case the API is not available
            api_data = {
                "status": "success",
                "data": [
                    {
                        "id": 1,
                        "product": "Shirt",
                        "date": "2025-04-01",
                        "design": "Modern",
                        "fastShip": "True",
                        "quantity": 10,
                        "mail": "user123@gmail.com",
                    },
                    {
                        "id": 2,
                        "product": "T-Shirt",
                        "date": "2025-04-02",
                        "design": "Classic",
                        "fastShip": "False",
                        "quantity": 5,
                        "mail": "user456@yahoo.com",
                    },
                    {
                        "id": 3,
                        "product": "Shirt",
                        "date": "2025-04-03",
                        "design": "Minimal",
                        "fastShip": "True",
                        "quantity": 3,
                        "mail": "user789@hotmail.com",
                    },
                ],
            }

        if api_data.get("status") == "success" and "data" in api_data:
            try:
                # First clear existing products
                existing_products = self.search([])
                existing_products.unlink()

                for product_data in api_data["data"]:
                    # Make sure we have a valid product name
                    product_name = product_data.get("product")
                    if not product_name:  # Add explicit check for empty product name
                        _logger.warning(
                            f"Skipping product with no name: {product_data}"
                        )
                        continue

                    try:
                        # Handle the new API response format - use 'product' instead of 'name'
                        api_product = self.create(
                            {
                                "api_id": product_data.get("id"),
                                "name": product_name,  # Use product name directly
                                "date": product_data.get("date"),
                                "design": product_data.get("design", ""),
                                "fast_ship": product_data.get("fastShip") == "True",
                                "quantity": product_data.get("quantity", 1),
                                "email": product_data.get("mail", ""),
                            }
                        )

                        # Log the new product data
                        _logger.info(
                            f"Created API product: {api_product.name}, ID: {api_product.api_id}"
                        )

                    except Exception as e:
                        _logger.error(f"Error creating API product: {e}")

                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": "API Import",
                        "message": "API products imported successfully",
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
