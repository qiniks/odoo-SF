from odoo import models, fields, api
import requests
import json
import logging
import random
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class ApiProduct(models.Model):
    _name = "api.product"
    _description = "Products from External API"

    api_id = fields.Integer(string="API ID")
    name = fields.Char(string="Name")
    date = fields.Date(string="Date")
    design = fields.Char(string="Design")

    @api.model
    def create_delivery_from_api_product(self, api_product):
        """Create a delivery order from an API product"""
        # Get warehouse and picking type
        warehouse = self.env["stock.warehouse"].search([], limit=1)
        if not warehouse:
            raise ValueError("No warehouse found!")

        picking_type = self.env["stock.picking.type"].search(
            [("code", "=", "outgoing"), ("warehouse_id", "=", warehouse.id)], limit=1
        )

        if not picking_type:
            raise ValueError("No outgoing picking type found!")

        # Get a customer
        partner = self.env["res.partner"].search([("customer_rank", ">", 0)], limit=1)
        if not partner:
            partner = self.env.ref("base.res_partner_1")  # Use demo data partner

        # Create product if it doesn't exist
        product = self.env["product.product"].search(
            [("name", "=", api_product.name), ("sale_ok", "=", True)], limit=1
        )

        if not product:
            try:
                # Try with detailed_type for Odoo 18.0
                product = self.env["product.product"].create(
                    {
                        "name": api_product.name,
                        "detailed_type": "product",  # Try with detailed_type
                        "sale_ok": True,
                        "description": f"Design: {api_product.design}",
                        "default_code": f"API-{api_product.api_id}",
                    }
                )
            except ValueError:
                # If detailed_type fails, try a different approach (Odoo 18.0 specific)
                try:
                    # Create a basic product with minimal fields first
                    product = self.env["product.product"].create(
                        {
                            "name": api_product.name,
                            "sale_ok": True,
                            "default_code": f"API-{api_product.api_id}",
                        }
                    )

                    # Then update its description separately
                    product.write(
                        {
                            "description": f"Design: {api_product.design}",
                        }
                    )
                except Exception as e:
                    _logger.error(f"Failed to create product: {e}", exc_info=True)
                    # Fall back to an existing product
                    product = self.env["product.product"].search(
                        [("sale_ok", "=", True)], limit=1
                    )
                    if not product:
                        raise ValueError(f"Could not create or find a product: {e}")

        # Create picking (delivery order)
        delivery_date = api_product.date or fields.Date.today()
        picking_vals = {
            "partner_id": partner.id,
            "picking_type_id": picking_type.id,
            "location_id": picking_type.default_location_src_id.id,
            "location_dest_id": picking_type.default_location_dest_id.id,
            "scheduled_date": delivery_date,
            "origin": f"API Import - {api_product.api_id}",
            "note": f"Created from API product: {api_product.name}, Design: {api_product.design}",
        }

        picking = self.env["stock.picking"].create(picking_vals)

        # Add move line (the product to deliver)
        self.env["stock.move"].create(
            {
                "name": product.name,
                "product_id": product.id,
                "product_uom_qty": random.randint(1, 5),  # Random quantity
                "product_uom": product.uom_id.id,
                "picking_id": picking.id,
                "location_id": picking_type.default_location_src_id.id,
                "location_dest_id": picking_type.default_location_dest_id.id,
            }
        )

        return picking

    @api.model
    def fetch_and_store_api_data(self):
        try:
            # Try different hostnames for different environments
            hostnames = [
                "http://127.0.0.1:8000",
                "http://localhost:8000",
                "http://host.docker.internal:8000",
                "http://172.17.0.1:8000",  # Common Docker host IP
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

        except (requests.exceptions.RequestException, ValueError) as e:
            _logger.warning(f"Could not connect to API, using fallback data: {str(e)}")
            # Fallback data in case the API is not available
            api_data = {
                "status": "success",
                "data": [
                    {
                        "id": 1,
                        "name": "Fallback Product 1",
                        "date": "2025-04-01",
                        "design": "Modern",
                    },
                    {
                        "id": 2,
                        "name": "Fallback Product 2",
                        "date": "2025-04-01",
                        "design": "Classic",
                    },
                    {
                        "id": 3,
                        "name": "Fallback Product 3",
                        "date": "2025-04-01",
                        "design": "Minimal",
                    },
                ],
            }

        created_pickings = self.env["stock.picking"]

        if api_data.get("status") == "success" and "data" in api_data:
            try:
                # First store the API data
                existing_products = self.search([])
                existing_products.unlink()

                api_products = self.env["api.product"]
                for product_data in api_data["data"]:
                    api_product = self.create(
                        {
                            "api_id": product_data.get("id"),
                            "name": product_data.get("name"),
                            "date": product_data.get("date"),
                            "design": product_data.get("design"),
                        }
                    )
                    api_products += api_product

                    try:
                        # Create a delivery order for each API product
                        picking = self.create_delivery_from_api_product(api_product)
                        created_pickings += picking
                    except Exception as e:
                        _logger.error(
                            f"Error creating delivery for product {api_product.name}: {e}"
                        )

                # Return an action to show the created pickings
                if created_pickings:
                    return {
                        "name": "Deliveries from API",
                        "type": "ir.actions.act_window",
                        "res_model": "stock.picking",
                        "view_mode": "list,form",
                        "domain": [("id", "in", created_pickings.ids)],
                        "context": {"create": True},
                    }
                else:
                    return {
                        "type": "ir.actions.client",
                        "tag": "display_notification",
                        "params": {
                            "title": "API Import",
                            "message": "API products imported but no deliveries could be created",
                            "sticky": False,
                            "type": "warning",
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
                    "message": "Invalid response format from API",
                    "sticky": False,
                    "type": "danger",
                },
            }
