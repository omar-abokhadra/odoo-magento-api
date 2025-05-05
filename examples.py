from app.odoo import OdooClient
from app.magento import MagentoClient
from app.middleware import ProductSynchronizer, OrderSynchronizer
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def run_product_sync_example():
    """
    Example of how to use the ProductSynchronizer to sync a product.
    """
    try:
        # Create Odoo client
        odoo_client = OdooClient(
            host=os.getenv("ODOO_HOST", "localhost"),
            port=int(os.getenv("ODOO_PORT", "8069")),
            database=os.getenv("ODOO_DB", "odoo"),
            username=os.getenv("ODOO_USER", "admin"),
            password=os.getenv("ODOO_PASSWORD", "admin")
        )
        
        # Create Magento client
        magento_client = MagentoClient(
            base_url=os.getenv("MAGENTO_URL", "http://localhost"),
            username=os.getenv("MAGENTO_USER", "admin"),
            password=os.getenv("MAGENTO_PASSWORD", "admin123")
        )
        
        # Connect to Odoo
        if not odoo_client.connect():
            logger.error("Failed to connect to Odoo")
            return
        
        # Create product synchronizer
        product_sync = ProductSynchronizer(odoo_client, magento_client)
        
        # Example: Sync a product with SKU "EXAMPLE-SKU"
        # Replace with an actual SKU from your system
        result = product_sync.sync_product("EXAMPLE-SKU")
        
        if result["success"]:
            logger.info(f"Product sync successful: {result['message']}")
        else:
            logger.error(f"Product sync failed: {result['message']}")
            
    except Exception as e:
        logger.error(f"Error in product sync example: {str(e)}")

def run_order_sync_example():
    """
    Example of how to use the OrderSynchronizer to sync an order.
    """
    try:
        # Create Odoo client
        odoo_client = OdooClient(
            host=os.getenv("ODOO_HOST", "localhost"),
            port=int(os.getenv("ODOO_PORT", "8069")),
            database=os.getenv("ODOO_DB", "odoo"),
            username=os.getenv("ODOO_USER", "admin"),
            password=os.getenv("ODOO_PASSWORD", "admin")
        )
        
        # Create Magento client
        magento_client = MagentoClient(
            base_url=os.getenv("MAGENTO_URL", "http://localhost"),
            username=os.getenv("MAGENTO_USER", "admin"),
            password=os.getenv("MAGENTO_PASSWORD", "admin123")
        )
        
        # Connect to Odoo
        if not odoo_client.connect():
            logger.error("Failed to connect to Odoo")
            return
        
        # Create order synchronizer
        order_sync = OrderSynchronizer(odoo_client, magento_client)
        
        # Example: Sync all new orders
        result = order_sync.sync_new_orders()
        
        if result["success"]:
            logger.info(f"Order sync successful: {result['message']}")
            logger.info(f"Synced orders: {result['orders_synced']}")
        else:
            logger.error(f"Order sync failed: {result['message']}")
            
    except Exception as e:
        logger.error(f"Error in order sync example: {str(e)}")

if __name__ == "__main__":
    logger.info("Running examples...")
    
    # Uncomment to run examples
    # run_product_sync_example()
    # run_order_sync_example()
    
    logger.info("Examples completed.")
