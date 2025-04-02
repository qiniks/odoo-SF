{
    "name": "Hello World",
    "version": "16.0.1.0.0",
    "category": "Tools",
    "summary": "Simple Hello World module for testing",
    "author": "Your Name",
    "depends": ["base", "stock"],  # Added 'stock' dependency for Inventory
    "data": [
        "views/inventory_views.xml",
    ],
    "installable": True,
    "application": True,
}
