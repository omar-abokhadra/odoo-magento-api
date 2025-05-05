import logging
from typing import Dict, List, Any, Optional
import time

logger = logging.getLogger(__name__)

class ProductSynchronizer:
    """
    Handles synchronization of product data between Odoo and Magento.
    """
    
    def __init__(self, odoo_client, magento_client):
        """
        Initialize the product synchronizer.
        
        Args:
            odoo_client: Odoo client instance
            magento_client: Magento client instance
        """
        self.odoo_client = odoo_client
        self.magento_client = magento_client
    
    def sync_product(self, sku: str) -> Dict[str, Any]:
        """
        Synchronize a single product from Odoo to Magento.
        
        Args:
            sku: Product SKU
            
        Returns:
            Dict[str, Any]: Result of synchronization
        """
        try:
            # Get product from Odoo
            odoo_product = self.odoo_client.get_product_by_sku(sku)
            if not odoo_product:
                return {
                    "success": False,
                    "message": f"Product with SKU {sku} not found in Odoo",
                    "sku": sku
                }
            
            # Check if product exists in Magento
            magento_product = self.magento_client.get_product_by_sku(sku)
            if not magento_product:
                return {
                    "success": False,
                    "message": f"Product with SKU {sku} not found in Magento",
                    "sku": sku
                }
            
            # Update stock quantity
            stock_result = self.magento_client.update_product_stock(
                sku=sku,
                quantity=odoo_product["quantity"]
            )
            
            # Update regular price (retail price)
            price_result = self.magento_client.update_product_price(
                sku=sku,
                price=odoo_product["retail_price"]
            )
            
            # Update special price (promo price) if available
            special_price_result = True
            if odoo_product["promo_price"] and odoo_product["promo_price"] < odoo_product["retail_price"]:
                special_price_result = self.magento_client.update_product_special_price(
                    sku=sku,
                    special_price=odoo_product["promo_price"]
                )
            
            if stock_result and price_result and special_price_result:
                return {
                    "success": True,
                    "message": f"Product {sku} synchronized successfully",
                    "sku": sku
                }
            else:
                failed_operations = []
                if not stock_result:
                    failed_operations.append("stock update")
                if not price_result:
                    failed_operations.append("price update")
                if not special_price_result:
                    failed_operations.append("special price update")
                
                return {
                    "success": False,
                    "message": f"Product {sku} synchronization failed for: {', '.join(failed_operations)}",
                    "sku": sku
                }
        except Exception as e:
            logger.error(f"Error synchronizing product {sku}: {str(e)}")
            return {
                "success": False,
                "message": f"Error synchronizing product {sku}: {str(e)}",
                "sku": sku
            }
    
    def sync_all_products(self) -> Dict[str, Any]:
        """
        Synchronize all products from Odoo to Magento.
        
        Returns:
            Dict[str, Any]: Result of synchronization
        """
        try:
            # Get all products from Odoo
            odoo_products = self.odoo_client.get_all_products()
            
            results = {
                "total": len(odoo_products),
                "successful": 0,
                "failed": 0,
                "failed_skus": []
            }
            
            for product in odoo_products:
                sku = product["sku"]
                if not sku:
                    logger.warning(f"Product ID {product['id']} has no SKU, skipping")
                    results["failed"] += 1
                    continue
                
                result = self.sync_product(sku)
                if result["success"]:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["failed_skus"].append(sku)
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.5)
            
            return {
                "success": True,
                "message": f"Synchronized {results['successful']} products successfully, {results['failed']} failed",
                "results": results
            }
        except Exception as e:
            logger.error(f"Error synchronizing all products: {str(e)}")
            return {
                "success": False,
                "message": f"Error synchronizing all products: {str(e)}"
            }


class OrderSynchronizer:
    """
    Handles synchronization of order data between Magento and Odoo.
    """
    
    def __init__(self, odoo_client, magento_client):
        """
        Initialize the order synchronizer.
        
        Args:
            odoo_client: Odoo client instance
            magento_client: Magento client instance
        """
        self.odoo_client = odoo_client
        self.magento_client = magento_client
    
    def sync_order(self, magento_order_id: str) -> Dict[str, Any]:
        """
        Synchronize a single order from Magento to Odoo.
        
        Args:
            magento_order_id: Magento order ID
            
        Returns:
            Dict[str, Any]: Result of synchronization
        """
        try:
            # Get order from Magento
            magento_order = self.magento_client.get_order_by_id(magento_order_id)
            if not magento_order:
                return {
                    "success": False,
                    "message": f"Order with ID {magento_order_id} not found in Magento",
                    "orders_synced": []
                }
            
            # Extract customer data
            billing_address = magento_order.get("billing_address", {})
            customer_data = {
                "name": f"{billing_address.get('firstname', '')} {billing_address.get('lastname', '')}".strip(),
                "email": magento_order.get("customer_email", ""),
                "phone": billing_address.get("telephone", ""),
                "street": billing_address.get("street", [""])[0] if isinstance(billing_address.get("street", []), list) else billing_address.get("street", ""),
                "city": billing_address.get("city", ""),
                "zip": billing_address.get("postcode", ""),
                "country_code": billing_address.get("country_id", "")
            }
            
            # Extract order lines
            order_lines = []
            for item in magento_order.get("items", []):
                order_lines.append({
                    "sku": item.get("sku", ""),
                    "quantity": item.get("qty_ordered", 1),
                    "price_unit": item.get("price", 0)
                })
            
            # Create sale order in Odoo
            odoo_order_id = self.odoo_client.create_sale_order(
                customer_data=customer_data,
                order_lines=order_lines,
                external_order_id=magento_order_id
            )
            
            if odoo_order_id:
                return {
                    "success": True,
                    "message": f"Order {magento_order_id} synchronized successfully to Odoo order {odoo_order_id}",
                    "orders_synced": [magento_order_id]
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to create Odoo order for Magento order {magento_order_id}",
                    "orders_synced": []
                }
        except Exception as e:
            logger.error(f"Error synchronizing order {magento_order_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Error synchronizing order {magento_order_id}: {str(e)}",
                "orders_synced": []
            }
    
    def sync_new_orders(self) -> Dict[str, Any]:
        """
        Synchronize all new orders from Magento to Odoo.
        
        Returns:
            Dict[str, Any]: Result of synchronization
        """
        try:
            # Get new orders from Magento
            new_orders = self.magento_client.get_new_orders()
            
            results = {
                "total": len(new_orders),
                "successful": 0,
                "failed": 0,
                "failed_orders": [],
                "synced_orders": []
            }
            
            for order in new_orders:
                order_id = order.get("entity_id", "")
                if not order_id:
                    logger.warning("Order has no entity_id, skipping")
                    results["failed"] += 1
                    continue
                
                result = self.sync_order(order_id)
                if result["success"]:
                    results["successful"] += 1
                    results["synced_orders"].append(order_id)
                else:
                    results["failed"] += 1
                    results["failed_orders"].append(order_id)
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.5)
            
            return {
                "success": True,
                "message": f"Synchronized {results['successful']} orders successfully, {results['failed']} failed",
                "orders_synced": results["synced_orders"],
                "results": results
            }
        except Exception as e:
            logger.error(f"Error synchronizing new orders: {str(e)}")
            return {
                "success": False,
                "message": f"Error synchronizing new orders: {str(e)}",
                "orders_synced": []
            }
