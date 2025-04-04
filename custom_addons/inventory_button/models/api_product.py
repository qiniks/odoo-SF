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
    _order = "is_converted, name"  # Default sort by conversion status then name

    api_id = fields.Integer("API ID", required=True)
    name = fields.Char("Name", required=True)
    date = fields.Date("Date")
    design = fields.Char("Design")
    is_converted = fields.Boolean("Converted to Delivery", default=False)
    delivery_status = fields.Char(
        "Status", compute="_compute_delivery_status", store=False
    )

    @api.depends("is_converted")
    def _compute_delivery_status(self):
        for record in self:
            if record.is_converted:
                record.delivery_status = "✅ Delivered"
            else:
                record.delivery_status = "🔄 Ready for Delivery"

    @api.model
    def create_delivery_from_api_product(self, api_product, quantity=None):
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

        # Use quantity from API if provided, otherwise use random quantity between 1-5
        product_qty = quantity if quantity is not None else random.randint(1, 5)

        # Add move line (the product to deliver)
        self.env["stock.move"].create(
            {
                "name": product.name,
                "product_id": product.id,
                "product_uom_qty": product_qty,  # Use API quantity or random quantity
                "product_uom": product.uom_id.id,
                "picking_id": picking.id,
                "location_id": picking_type.default_location_src_id.id,
                "location_dest_id": picking_type.default_location_dest_id.id,
            }
        )

        api_product.is_converted = True

        return picking

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

            # Parse JSON response - THIS WAS THE PROBLEM
            api_data = response.json()  # <-- Fixed this line
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

        created_pickings = self.env["stock.picking"]

        if api_data.get("status") == "success" and "data" in api_data:
            try:
                # First clear existing products
                existing_products = self.search([])
                existing_products.unlink()

                api_products = self.env["api.product"]
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
                                # Could save additional fields if needed
                                # "fast_ship": product_data.get("fastShip") == "True",
                                # "quantity": product_data.get("quantity", 1),
                                # "email": product_data.get("mail", ""),
                            }
                        )
                        api_products += api_product

                        # Log the new product data
                        _logger.info(
                            f"Created API product: {api_product.name}, ID: {api_product.api_id}"
                        )

                        # If you want to show the extra data in the logs
                        _logger.info(
                            f"Additional data - fastShip: {product_data.get('fastShip')}, "
                            f"quantity: {product_data.get('quantity')}, "
                            f"email: {product_data.get('mail')}"
                        )

                        try:
                            # Create a delivery order for each API product
                            # When creating the delivery, use the quantity from API
                            picking = self.create_delivery_from_api_product(
                                api_product, quantity=product_data.get("quantity", 1)
                            )
                            created_pickings += picking
                        except Exception as e:
                            _logger.error(
                                f"Error creating delivery for product {api_product.name}: {e}"
                            )
                    except Exception as e:
                        _logger.error(f"Error creating API product: {e}")

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
                    "message": f"Invalid response format from API: {api_data}",
                    "sticky": False,
                    "type": "danger",
                },
            }

    def write(self, vals):
        """Override write to handle kanban changes"""
        # Check if is_converted is being changed from False to True
        if "is_converted" in vals and vals["is_converted"]:
            # Get records that are being converted (that weren't converted before)
            to_convert = self.filtered(lambda r: not r.is_converted)

            # Call super to perform the write operation
            result = super(ApiProduct, self).write(vals)

            # Create delivery orders for newly converted products
            if to_convert:
                for product in to_convert:
                    try:
                        self.create_delivery_from_api_product(product)
                    except Exception as e:
                        _logger.error(
                            f"Failed to create delivery for {product.name}: {str(e)}"
                        )
                        # Show a notification to the user
                        self.env.user.notify_warning(
                            title="Error Creating Delivery",
                            message=f"Could not create delivery for {product.name}: {str(e)}",
                            sticky=True,
                        )
            return result
        else:
            return super(ApiProduct, self).write(vals)

    def create_delivery_order(self):
        """Create a delivery order for the current product"""
        self.ensure_one()

        if self.is_converted:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Already Converted",
                    "message": f"Product {self.name} has already been converted to a delivery",
                    "sticky": False,
                    "type": "warning",
                },
            }

        try:
            picking = self.env["api.product"].create_delivery_from_api_product(self)

            return {
                "name": "Delivery Order",
                "type": "ir.actions.act_window",
                "res_model": "stock.picking",
                "view_mode": "form",
                "res_id": picking.id,
                "context": {"create": False},
            }
        except Exception as e:
            _logger.error(f"Error creating delivery order: {str(e)}")
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Error",
                    "message": f"Failed to create delivery: {str(e)}",
                    "sticky": True,
                    "type": "danger",
                },
            }
