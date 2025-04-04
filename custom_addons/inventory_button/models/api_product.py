from odoo import models, fields, api
import requests
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class ApiProduct(models.Model):
    _name = "api.product"
    _description = "API Product Data"
    _order = "is_fast_ship desc, quantity desc, is_custom_label desc, name"

    api_id = fields.Integer("API ID", required=True, readonly=True)
    name = fields.Char("Name", required=True, readonly=True)
    date = fields.Date("Date", readonly=True)
    design = fields.Char("Design", readonly=True)
    is_fast_ship = fields.Boolean("Fast Shipping", readonly=True)
    quantity = fields.Integer("Quantity", readonly=True)
    is_custom_label = fields.Boolean("Custom Label", readonly=True)
    is_converted = fields.Boolean("Converted", default=False, readonly=True)
    status_label = fields.Char("Status", compute="_compute_status_label", store=False, readonly=True)
    delivery_status = fields.Char("Delivery Status", compute="_compute_delivery_status", store=False)

    category = fields.Selection([
        ('clothing', 'Clothing'),
        ('accessories', 'Accessories'),
        ('other', 'Other')
    ], string='Category', default='clothing', readonly=True)

    state = fields.Selection([
        ('to_do', 'To Do'),
        ('in_process', 'In Process'),
        ('done', 'Done'),
        ('delivered', 'Delivered')
    ], string='Status', default='to_do', tracking=True, group_expand='_expand_state_groups')


    @api.model
    def _expand_state_groups(self, states, domain, order):
        """Force display of all states in the specified order"""
        return ['to_do', 'in_process', 'done', 'delivered']
    
    def action_set_in_process(self):
        self.ensure_one()
        self.write({'state': 'in_process'})  # Use write to respect workflow
        _logger.info(f"Set state to 'in_process' for {self.name}")
    
    def action_set_done(self):
        self.ensure_one()
        self.write({'state': 'done'})
        _logger.info(f"Set state to 'done' for {self.name}")
    
    def action_set_delivered(self):
        self.ensure_one()
        self.write({'state': 'delivered'})
        _logger.info(f"Set state to 'delivered' for {self.name}")

    @api.depends("is_converted")
    def _compute_status_label(self):
        for record in self:
            if record.is_converted:
                record.status_label = "✅ Delivered"
            else:
                record.status_label = "🔄 Ready for Delivery"

    @api.depends("is_converted")
    def _compute_delivery_status(self):
        for record in self:
            if record.is_converted:
                record.delivery_status = "Already Delivered"
            else:
                record.delivery_status = "Ready for Delivery"

    @api.model
    def fetch_and_store_api_data(self):
        """Fetch data from local API and store it in the database"""
        _logger.info("Starting fetch_and_store_api_data")
        try:
            api_url = "http://host.docker.internal:8000/api/get_data"
            _logger.info(f"Attempting to fetch data from API: {api_url}")
            try:
                response = requests.get(api_url, timeout=10)
                _logger.warning("*** The response is 200, getting data from API ***")
                if response.status_code == 200:
                    data = response.json()
                    _logger.info(f"API returned data: {data}")
                    if data.get("status") == "success":
                        _logger.info(f"Returning data in fetch_and_store_api_data: {data}")
                        return self._process_api_data(data)
                
                _logger.warning("API request failed or invalid response. Falling back to local JSON.")
                return self._fetch_from_local_json()

            except requests.RequestException as e:
                _logger.error(f"API request error: {str(e)}")
                _logger.info("*** The response is not valid, not getting data from API ***")
                return self._fetch_from_local_json()

        except Exception as e:
            _logger.error(f"API processing error: {str(e)}")
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Processing Error",
                    "message": f"Error processing API data: {str(e)}",
                    "sticky": True,
                    "type": "danger",
                },
            }

    def _fetch_from_local_json(self):
        """Fetch a random selection of 1-5 items from the local data array"""
        _logger.info("Entering _fetch_from_local_json")
        try:
            import random
            # Note: 'data' is not defined here; assuming it's a placeholder for a local array
            # Replace with actual data source if available
            data = []  # Placeholder; replace with your local data source
            num_items = random.randint(1, 5)
            _logger.info(f"Selecting {num_items} random items from local data")
            selected_data = random.sample(data, min(num_items, len(data)))
            _logger.info(f"Selected local data: {selected_data}")
            return self._process_api_data(selected_data)
        except Exception as e:
            _logger.error(f"Error processing local data array: {str(e)}")
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Error",
                    "message": f"Failed to process local data: {str(e)}",
                    "sticky": True,
                    "type": "danger",
                },
            }

    def _process_api_data(self, data):
        """Process API data and create or update products"""
        _logger.info("*** Processing api data method _process_api_data ***")
        if isinstance(data, list):
            _logger.info("Data is a list (local source)")
            products = data
        else:
            _logger.info("*** The data is API response method: _process_api_data ***")
            products = data.get("data", [])
        
        created_count = 0
        updated_count = 0
        _logger.info(f"Got data to process: {products}")
    
        for product in products:
            existing = self.search([("api_id", "=", product.get("id"))])
            vals = {
                "api_id": product.get("id"),
                "name": product.get("name"),
                "date": product.get("date"),
                "design": product.get("design"),
                "quantity": int(product.get("quantity")),
                "is_fast_ship": bool(product.get("is_fast_ship", False)),
                "is_custom_label": bool(product.get("is_custom_label", False))
            }
            if not existing:
                _logger.info(f"*** Creating new record with vals: {vals} ***")
                record = self.create(vals)
                _logger.info(f"Created record with ID {record.id}, quantity: {record.quantity}")
                created_count += 1
            else:
                _logger.info(f"*** Updating existing record with api_id {product.get('id')} with vals: {vals} ***")
                existing.write(vals)
                _logger.info(f"Updated record with ID {existing.id}, quantity: {existing.quantity}")
                updated_count += 1
    
        source = "API" if isinstance(data, dict) and data.get("source") != "local" else "local file"
        _logger.info(f"Processed {created_count} new and {updated_count} updated records from {source}")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Success",
                "message": f"Successfully fetched {created_count} new and updated {updated_count} existing products from {source}",
                "sticky": False,
                "type": "success",
            },
        }

    def create_delivery_order(self):
        """Create a delivery order for a single API product"""
        self.ensure_one()
        _logger.info(f"Creating delivery order for {self.name} (api_id: {self.api_id})")
        
        if self.is_converted:
            _logger.warning(f"Product {self.name} already converted")
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Warning",
                    "message": f"Product {self.name} has already been converted to a delivery order",
                    "sticky": False,
                    "type": "warning",
                },
            }

        warehouse = self.env["stock.warehouse"].search([], limit=1)
        if not warehouse:
            _logger.error("No warehouse found")
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Error",
                    "message": "No warehouse found to create delivery",
                    "sticky": True,
                    "type": "danger",
                },
            }

        product = self.env["product.product"].search([("name", "=", self.name)], limit=1)
        if not product:
            _logger.info(f"Creating new product: {self.name}")
            product = self.env["product.product"].create({
                "name": self.name,
                "type": "product",
                "categ_id": self.env.ref("product.product_category_all").id,
            })
            _logger.info(f"Created product with ID {product.id}")

        picking_type = self.env["stock.picking.type"].search(
            [("warehouse_id", "=", warehouse.id), ("code", "=", "outgoing")], limit=1
        )
        if not picking_type:
            _logger.error("No outgoing picking type found")
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Error",
                    "message": "No outgoing operation type found",
                    "sticky": True,
                    "type": "danger",
                },
            }

        location_src = picking_type.default_location_src_id or warehouse.lot_stock_id
        location_dest = picking_type.default_location_dest_id or self.env.ref(
            "stock.stock_location_customers", raise_if_not_found=False
        )
        if not location_dest:
            _logger.info("Creating customer location")
            location_dest = self.env["stock.location"].create({
                "name": "Customers",
                "usage": "customer",
                "company_id": self.env.company.id,
            })

        if not location_src or not location_dest:
            _logger.error("Invalid stock locations")
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Error",
                    "message": "Could not determine appropriate stock locations",
                    "sticky": True,
                    "type": "danger",
                },
            }

        try:
            picking = self.env["stock.picking"].create({
                "partner_id": self.env.user.partner_id.id,
                "picking_type_id": picking_type.id,
                "location_id": location_src.id,
                "location_dest_id": location_dest.id,
                "origin": f"API Product {self.api_id}",
                "scheduled_date": self.date or fields.Date.today(),
            })
            _logger.info(f"Created picking with ID {picking.id}")

            self.env["stock.move"].create({
                "name": self.name,
                "product_id": product.id,
                "product_uom_qty": self.quantity,
                "product_uom": product.uom_id.id,
                "picking_id": picking.id,
                "location_id": location_src.id,
                "location_dest_id": location_dest.id,
            })
            _logger.info(f"Created stock move with quantity {self.quantity}")

            self.write({"is_converted": True})
            _logger.info(f"Marked {self.name} as converted")

            return {
                "type": "ir.actions.act_window",
                "res_model": "stock.picking",
                "res_id": picking.id,
                "view_mode": "form",
                "target": "current",
            }
        except Exception as e:
            _logger.error(f"Error creating delivery order: {str(e)}")
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Error",
                    "message": f"Failed to create delivery order: {str(e)}",
                    "sticky": True,
                    "type": "danger",
                },
            }

    def create_delivery_orders(self):
        """Create delivery orders for multiple selected API products"""
        _logger.info("Starting create_delivery_orders")
        products_to_convert = self.filtered(lambda p: not p.is_converted)
        if not products_to_convert:
            _logger.warning("No products to convert")
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Warning",
                    "message": "All selected products have already been converted to delivery orders",
                    "sticky": False,
                    "type": "warning",
                },
            }

        created_pickings = self.env["stock.picking"]
        for api_product in products_to_convert:
            try:
                result = api_product.create_delivery_order()
                if isinstance(result, dict) and result.get("res_model") == "stock.picking" and result.get("res_id"):
                    created_pickings += self.env["stock.picking"].browse(result["res_id"])
                    _logger.info(f"Added picking ID {result['res_id']} to created_pickings")
            except Exception as e:
                _logger.error(f"Error creating delivery for {api_product.name}: {str(e)}")

        if not created_pickings:
            _logger.warning("No delivery orders created")
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Warning",
                    "message": "No delivery orders were created",
                    "sticky": False,
                    "type": "warning",
                },
            }

        if len(created_pickings) == 1:
            _logger.info(f"Returning single picking view for ID {created_pickings.id}")
            return {
                "type": "ir.actions.act_window",
                "res_model": "stock.picking",
                "res_id": created_pickings.id,
                "view_mode": "form",
                "target": "current",
            }

        _logger.info(f"Returning multiple pickings view for IDs {created_pickings.ids}")
        return {
            "type": "ir.actions.act_window",
            "name": "Created Delivery Orders",
            "res_model": "stock.picking",
            "domain": [("id", "in", created_pickings.ids)],
            "view_mode": "tree,form",
            "target": "current",
        }
    
    @api.model
    def create(self, vals):
        return super(ApiProduct, self).create(vals)

    def write(self, vals):
            """Restrict updates to specific fields only"""
            protected_fields = [
                'api_id', 'name', 'date', 'design', 'quantity', 
                'is_fast_ship', 'is_custom_label', 'category'
            ]
            # Check if any protected field is in vals
            if any(field in vals for field in protected_fields):
                _logger.warning(f"Attempt to modify protected fields: {vals}")
                # Remove protected fields from vals to prevent changes
                for field in protected_fields:
                    vals.pop(field, None)
            
            # Handle is_converted and state updates as allowed
            if "is_converted" in vals and vals["is_converted"]:
                to_convert = self.filtered(lambda r: not r.is_converted)
                result = super(ApiProduct, self).write(vals)
                if to_convert:
                    _logger.info(f"Converting {len(to_convert)} records")
                    for product in to_convert:
                        try:
                            product.create_delivery_order()
                            _logger.info(f"Created delivery for {product.name}")
                        except Exception as e:
                            _logger.error(f"Failed to create delivery for {product.name}: {str(e)}")
                return result
            else:
                return super(ApiProduct, self).write(vals)