import odoorpc
import logging
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

class OdooClient:
    """
    Client for interacting with Odoo API using OdooRPC.
    """
    
    def __init__(self, host: str, port: int, database: str, username: str, password: str):
        """
        Initialize the Odoo client with connection parameters.
        
        Args:
            host: Odoo server hostname or IP
            port: Odoo server port
            database: Odoo database name
            username: Odoo username
            password: Odoo password
        """
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.odoo = None
        self.connected = False
    
    def connect(self) -> bool:
        """
        Connect to the Odoo server.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            self.odoo = odoorpc.ODOO(self.host, port=self.port)
            self.odoo.login(self.database, self.username, self.password)
            self.connected = True
            logger.info(f"Successfully connected to Odoo server at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Odoo server: {str(e)}")
            self.connected = False
            return False
    
    def ensure_connection(self) -> bool:
        """
        Ensure that the connection to Odoo is active.
        
        Returns:
            bool: True if connection is active, False otherwise
        """
        if not self.connected or not self.odoo:
            return self.connect()
        return True
    
    def get_product_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """
        Get product information by SKU.
        
        Args:
            sku: Product SKU
            
        Returns:
            Optional[Dict[str, Any]]: Product information or None if not found
        """
        if not self.ensure_connection():
            return None
        
        try:
            product_ids = self.odoo.env['product.product'].search([('default_code', '=', sku)])
            if not product_ids:
                logger.warning(f"Product with SKU {sku} not found in Odoo")
                return None
            
            product = self.odoo.env['product.product'].browse(product_ids[0])
            return {
                'id': product.id,
                'name': product.name,
                'sku': product.default_code,
                'retail_price': product.list_price,
                'promo_price': product.lst_price if hasattr(product, 'lst_price') else None,
                'quantity': product.qty_available,
                'type': product.type,
            }
        except Exception as e:
            logger.error(f"Error getting product by SKU {sku}: {str(e)}")
            return None
    
    def get_all_products(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get all products from Odoo.
        
        Args:
            limit: Optional limit on the number of products to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of product information dictionaries
        """
        if not self.ensure_connection():
            return []
        
        try:
            product_ids = self.odoo.env['product.product'].search([])
            if limit:
                product_ids = product_ids[:limit]
            
            products = []
            for product in self.odoo.env['product.product'].browse(product_ids):
                products.append({
                    'id': product.id,
                    'name': product.name,
                    'sku': product.default_code,
                    'retail_price': product.list_price,
                    'promo_price': product.lst_price if hasattr(product, 'lst_price') else None,
                    'quantity': product.qty_available,
                    'type': product.type,
                })
            return products
        except Exception as e:
            logger.error(f"Error getting all products: {str(e)}")
            return []
    
    def create_sale_order(self, customer_data: Dict[str, Any], order_lines: List[Dict[str, Any]], 
                          external_order_id: str) -> Optional[int]:
        """
        Create a sales order in Odoo.
        
        Args:
            customer_data: Customer information
            order_lines: List of order line items
            external_order_id: External order ID (from Magento)
            
        Returns:
            Optional[int]: Odoo sale order ID if successful, None otherwise
        """
        if not self.ensure_connection():
            return None
        
        try:
            # Check if customer exists, create if not
            partner_ids = self.odoo.env['res.partner'].search([
                ('email', '=', customer_data.get('email'))
            ])
            
            if partner_ids:
                partner_id = partner_ids[0]
            else:
                # Create new customer
                partner_id = self.odoo.env['res.partner'].create({
                    'name': customer_data.get('name'),
                    'email': customer_data.get('email'),
                    'phone': customer_data.get('phone'),
                    'street': customer_data.get('street'),
                    'city': customer_data.get('city'),
                    'zip': customer_data.get('zip'),
                    'country_id': self._get_country_id(customer_data.get('country_code')),
                })
            
            # Prepare order lines
            sale_order_lines = []
            for line in order_lines:
                product_ids = self.odoo.env['product.product'].search([
                    ('default_code', '=', line.get('sku'))
                ])
                
                if not product_ids:
                    logger.warning(f"Product with SKU {line.get('sku')} not found in Odoo")
                    continue
                
                sale_order_lines.append((0, 0, {
                    'product_id': product_ids[0],
                    'product_uom_qty': line.get('quantity', 1),
                    'price_unit': line.get('price_unit'),
                }))
            
            if not sale_order_lines:
                logger.error("No valid order lines found, cannot create sale order")
                return None
            
            # Create sale order
            sale_order_vals = {
                'partner_id': partner_id,
                'client_order_ref': external_order_id,
                'order_line': sale_order_lines,
            }
            
            sale_order_id = self.odoo.env['sale.order'].create(sale_order_vals)
            logger.info(f"Created sale order with ID {sale_order_id} for external order {external_order_id}")
            return sale_order_id
        except Exception as e:
            logger.error(f"Error creating sale order: {str(e)}")
            return None
    
    def _get_country_id(self, country_code: str) -> Optional[int]:
        """
        Get country ID from country code.
        
        Args:
            country_code: ISO country code (e.g., 'US')
            
        Returns:
            Optional[int]: Country ID if found, None otherwise
        """
        if not self.ensure_connection():
            return None
        
        try:
            country_ids = self.odoo.env['res.country'].search([
                ('code', '=', country_code.upper())
            ])
            return country_ids[0] if country_ids else None
        except Exception as e:
            logger.error(f"Error getting country ID for code {country_code}: {str(e)}")
            return None
