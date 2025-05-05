import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import FastAPI app
from app.main import app

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", "8000"))
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
