
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.auth.router import router as auth_router
from src.bot_builder.router import router as bot_router
from src.whatsapp.router import router as whatsapp_router
from src.shared.database import init_db

# Create FastAPI app instance
app = FastAPI(
    title="ChatBoost Backend API",
    description="A comprehensive backend system with authentication and WhatsApp bot builder",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(bot_router)
app.include_router(whatsapp_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    await init_db()


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    
    Returns:
        dict: Welcome message and API information
    """
    return {
        "message": "Welcome to ChatBoost Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "modules": ["Authentication", "Bot Builder", "WhatsApp"]
    }



@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Health status
    """
    return {"status": "healthy", "message": "API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
