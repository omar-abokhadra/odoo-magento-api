import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_odoo_connection():
    """Test connection to Odoo server"""
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.odoo import OdooClient
        
        odoo_client = OdooClient(
            host=os.getenv("ODOO_HOST", "localhost"),
            port=int(os.getenv("ODOO_PORT", "8069")),
            database=os.getenv("ODOO_DB", "odoo"),
            username=os.getenv("ODOO_USER", "admin"),
            password=os.getenv("ODOO_PASSWORD", "admin")
        )
        
        connected = odoo_client.connect()
        if connected:
            logger.info("✅ Successfully connected to Odoo")
            return True
        else:
            logger.error("❌ Failed to connect to Odoo")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing Odoo connection: {str(e)}")
        return False

def test_magento_connection():
    """Test connection to Magento server"""
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.magento import MagentoClient
        
        magento_client = MagentoClient(
            base_url=os.getenv("MAGENTO_URL", "http://localhost"),
            username=os.getenv("MAGENTO_USER", "admin"),
            password=os.getenv("MAGENTO_PASSWORD", "admin123")
        )
        
        token = magento_client._get_token()
        if token:
            logger.info("✅ Successfully connected to Magento")
            return True
        else:
            logger.error("❌ Failed to connect to Magento")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing Magento connection: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Testing connections to Odoo and Magento...")
    
    odoo_success = test_odoo_connection()
    magento_success = test_magento_connection()
    
    if odoo_success and magento_success:
        logger.info("✅ All connections successful!")
    else:
        logger.warning("⚠️ Some connections failed. Please check your configuration.")
    
    logger.info("Connection test completed.")
