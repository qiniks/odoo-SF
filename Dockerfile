FROM odoo:18.0

# Expose Cloud Run’s port
EXPOSE 8080

# Start Odoo on port 8080 and bind to all interfaces
CMD odoo --db_host=$DB_HOST --db_user=$DB_USER --db_password=$DB_PASSWORD --http-port=8080 --http-interface=0.0.0.0