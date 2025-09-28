"""
New FastAPI application with clean MVC architecture.

This replaces the old mcp_server/main.py with a cleaner structure:
- API routes separated into focused modules
- Business logic moved to service layer  
- Data access through repository pattern
- Clean dependency injection
"""
import logging
import logging.config
import os
import sys
import yaml
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add project root to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging from YAML file
def setup_logging():
    """Setup logging configuration from logging.yaml"""
    logging_config_path = os.path.join(os.path.dirname(__file__), '..', 'logging.yaml')
    if os.path.exists(logging_config_path):
        with open(logging_config_path, 'r') as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
        print(f"✅ Logging configured from {logging_config_path}")
    else:
        # Fallback to basic logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)-8s - %(name)s - %(message)s",
            handlers=[
                logging.FileHandler("logs/api_server.log"),
                logging.StreamHandler()
            ]
        )
        print("⚠️ Using fallback logging configuration")

# Setup logging before importing other modules
setup_logging()

# Import route modules
from guidelines_agent.api.routes.agent_routes import router as agent_router
from guidelines_agent.api.routes.session_routes import router as session_router
from guidelines_agent.api.routes.config_routes import router as config_router
from guidelines_agent.api.routes.mcp_routes import router as mcp_router

# Import services for startup
from guidelines_agent.services import AgentService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Server startup: Initializing AI agents...")
    
    try:
        # Initialize agent service (this will create agents on first use)
        agent_service = AgentService()
        logger.info("Server startup: AI agents initialized successfully.")
        
        yield
        
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        raise
    finally:
        logger.info("Server shutdown: Cleaning up...")


# Create FastAPI app
app = FastAPI(
    title="Guidelines Agent API",
    description="AI-powered investment guidelines extraction and querying system",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception in {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "details": str(exc) if app.debug else None
        }
    )


# Include routers
app.include_router(agent_router)
app.include_router(session_router)
app.include_router(config_router)  
app.include_router(mcp_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "success": True,
        "message": "Guidelines Agent API",
        "version": "2.0.0",
        "documentation": "/docs",
        "endpoints": {
            "agent": "/agent/* - High-level user-facing operations",
            "sessions": "/sessions/* - Session management",
            "config": "/config - System configuration and provider info", 
            "mcp": "/mcp/* - Internal tool endpoints for agents"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "success": True,
        "status": "healthy",
        "message": "Server is running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)