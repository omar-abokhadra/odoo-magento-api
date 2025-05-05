#!/bin/bash

# Create a zip file of the project
echo "Creating project archive..."
cd /home/ubuntu
zip -r odoo_magento_middleware.zip odoo_magento_middleware -x "odoo_magento_middleware/venv/*"
echo "Archive created: odoo_magento_middleware.zip"
