{
    "name": "Custom Sale and Inventory Extension",
    "version": "16.0.1.0.0",
    "depends": ["sale", "stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order_views.xml",
        "views/stock_picking_views.xml",
        "views/stock_menu_views.xml",
    ],
    "external_dependencies": {
        "python": ["requests"],
    },
}
