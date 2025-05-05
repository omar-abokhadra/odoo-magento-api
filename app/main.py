from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging
import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Import Odoo and Magento clients
from app.odoo import OdooClient
from app.magento import MagentoClient
from app.middleware.sync import ProductSynchronizer, OrderSynchronizer

# Create FastAPI app
app = FastAPI(
    title="Odoo-Magento Middleware",
    description="FastAPI middleware for synchronizing data between Odoo 16 and Magento 2.4.7",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables for configuration
ODOO_HOST = os.getenv("ODOO_HOST", "localhost")
ODOO_PORT = int(os.getenv("ODOO_PORT", "8069"))
ODOO_DB = os.getenv("ODOO_DB", "odoo")
ODOO_USER = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

MAGENTO_URL = os.getenv("MAGENTO_URL", "http://localhost")
MAGENTO_USER = os.getenv("MAGENTO_USER", "admin")
MAGENTO_PASSWORD = os.getenv("MAGENTO_PASSWORD", "admin123")

# Dependency to get Odoo client
def get_odoo_client():
    client = OdooClient(
        host=ODOO_HOST,
        port=ODOO_PORT,
        database=ODOO_DB,
        username=ODOO_USER,
        password=ODOO_PASSWORD,
    )
    if not client.connect():
        logger.error("Failed to connect to Odoo")
        raise HTTPException(status_code=500, detail="Failed to connect to Odoo")
    return client

# Dependency to get Magento client
def get_magento_client():
    client = MagentoClient(
        base_url=MAGENTO_URL,
        username=MAGENTO_USER,
        password=MAGENTO_PASSWORD,
    )
    if not client._get_token():
        logger.error("Failed to authenticate with Magento")
        raise HTTPException(status_code=500, detail="Failed to authenticate with Magento")
    return client

# Dependency to get product synchronizer
def get_product_synchronizer(
    odoo_client: OdooClient = Depends(get_odoo_client),
    magento_client: MagentoClient = Depends(get_magento_client),
):
    return ProductSynchronizer(odoo_client, magento_client)

# Dependency to get order synchronizer
def get_order_synchronizer(
    odoo_client: OdooClient = Depends(get_odoo_client),
    magento_client: MagentoClient = Depends(get_magento_client),
):
    return OrderSynchronizer(odoo_client, magento_client)

# Request and response models
class ProductSyncRequest(BaseModel):
    sku: str = Field(..., description="Product SKU to synchronize")

class ProductSyncResponse(BaseModel):
    success: bool
    message: str
    sku: str

class OrderSyncRequest(BaseModel):
    order_id: Optional[str] = Field(None, description="Specific Magento order ID to synchronize (optional)")
    sync_all_new: bool = Field(False, description="Whether to sync all new orders")

class OrderSyncResponse(BaseModel):
    success: bool
    message: str
    orders_synced: List[str] = []

class HealthCheckResponse(BaseModel):
    status: str
    odoo_connected: bool
    magento_connected: bool

# Routes
@app.get("/", response_model=dict)
async def root():
    return {
        "message": "Odoo-Magento Middleware API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "sync_product": "/sync/product",
            "sync_all_products": "/sync/products/all",
            "sync_order": "/sync/order",
            "sync_all_orders": "/sync/orders/all",
        }
    }

@app.get("/health", response_model=HealthCheckResponse)
async def health_check(
    odoo_client: OdooClient = Depends(get_odoo_client),
    magento_client: MagentoClient = Depends(get_magento_client),
):
    odoo_connected = odoo_client.connected
    magento_connected = magento_client._get_token() is not None
    
    status = "healthy" if odoo_connected and magento_connected else "unhealthy"
    
    return {
        "status": status,
        "odoo_connected": odoo_connected,
        "magento_connected": magento_connected,
    }

@app.post("/sync/product", response_model=ProductSyncResponse)
async def sync_product(
    request: ProductSyncRequest,
    synchronizer: ProductSynchronizer = Depends(get_product_synchronizer),
):
    result = synchronizer.sync_product(request.sku)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.post("/sync/products/all", response_model=Dict[str, Any])
async def sync_all_products(
    background_tasks: BackgroundTasks,
    synchronizer: ProductSynchronizer = Depends(get_product_synchronizer),
):
    # Start sync in background
    background_tasks.add_task(synchronizer.sync_all_products)
    
    return {
        "success": True,
        "message": "Product synchronization started in background",
    }

@app.post("/sync/order", response_model=OrderSyncResponse)
async def sync_order(
    request: OrderSyncRequest,
    synchronizer: OrderSynchronizer = Depends(get_order_synchronizer),
):
    if request.order_id:
        result = synchronizer.sync_order(request.order_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    elif request.sync_all_new:
        result = synchronizer.sync_new_orders()
        return result
    else:
        raise HTTPException(status_code=400, detail="Either order_id or sync_all_new must be provided")

@app.post("/sync/orders/all", response_model=Dict[str, Any])
async def sync_all_orders(
    background_tasks: BackgroundTasks,
    synchronizer: OrderSynchronizer = Depends(get_order_synchronizer),
):
    # Start sync in background
    background_tasks.add_task(synchronizer.sync_new_orders)
    
    return {
        "success": True,
        "message": "Order synchronization started in background",
    }

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
