# Odoo-Magento Middleware

A FastAPI middleware application for integrating Odoo 16 and Magento 2.4.7, providing real-time synchronization of product data and orders.

## Features

- **Product Synchronization**: Update Magento product quantity, price, and advanced price from Odoo
- **Order Synchronization**: Fetch Magento orders and create corresponding Odoo sales orders
- **Real-time Updates**: Immediate synchronization between systems
- **Error Handling**: Notification and retry mechanism for failed operations
- **Background Processing**: Long-running tasks are processed in the background

## Requirements

- Python 3.10+
- Odoo 16 (odoo.sh)
- Magento 2.4.7
- Windows Server (for deployment)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/odoo-magento-middleware.git
cd odoo-magento-middleware
```

2. Create a virtual environment:

```bash
python -m venv venv
```

3. Activate the virtual environment:

```bash
# On Windows
venv\Scripts\activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Create a `.env` file based on the example:

```bash
copy .env.example .env
```

6. Update the `.env` file with your Odoo and Magento credentials.

## Configuration

Edit the `.env` file to configure your Odoo and Magento connections:

```
ODOO_HOST=your-odoo-host
ODOO_PORT=8069
ODOO_DB=your-odoo-database
ODOO_USER=your-odoo-username
ODOO_PASSWORD=your-odoo-password

MAGENTO_URL=https://your-magento-url
MAGENTO_USER=your-magento-admin-username
MAGENTO_PASSWORD=your-magento-admin-password
```

## Running the Application

Start the FastAPI application:

```bash
python main.py
```

The API will be available at `http://localhost:8000`.

## API Endpoints

### Health Check

- `GET /health`: Check the health of the application and connections to Odoo and Magento

### Product Synchronization

- `POST /sync/product`: Synchronize a single product by SKU
- `POST /sync/products/all`: Synchronize all products (background task)

### Order Synchronization

- `POST /sync/order`: Synchronize a specific order or all new orders
- `POST /sync/orders/all`: Synchronize all new orders (background task)

## API Documentation

Once the application is running, you can access the interactive API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Error Handling

The middleware implements error handling with:

- Detailed error logging
- Admin notifications for failed operations
- Automatic retry mechanism

## Deployment

For deployment on a Windows server:

1. Install Python 3.10+ on the server
2. Clone the repository and follow the installation steps
3. Consider using a service like NSSM (Non-Sucking Service Manager) to run the application as a Windows service

## Data Mapping

- Odoo SKU → Magento SKU
- Odoo retail price → Magento price
- Odoo promo price → Magento advanced price

## License

This project is licensed under the MIT License - see the LICENSE file for details.
