{
    "name": "Custom Sale and Inventory Extension",
    "version": "1.0.1",
    "category": "Inventory/Inventory",
    "summary": "Adds a button to inventory header and special transfers menu",
    "depends": ["sale", "stock"],
    "data": [
        "views/stock_picking_views.xml",
        "views/stock_menu_views.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "AGPL-3",
}
