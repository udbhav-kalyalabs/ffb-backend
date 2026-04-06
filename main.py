"""
AgriAI - Agricultural Analysis API
Main application entry point
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from routes.analysis import router as analysis_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Validate settings on startup
try:
    settings.validate()
    logger.info("Configuration validated successfully")
except ValueError as e:
    logger.error(f"Configuration error: {str(e)}")
    raise

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analysis_router)

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    logger.info(f"AWS Region: {settings.AWS_REGION}")
    logger.info(f"Bedrock Model: {settings.BEDROCK_MODEL_ID}")
    logger.info(f"S3 Bucket: {settings.S3_BUCKET_NAME}")
    logger.info(f"MongoDB Database: {settings.MONGO_DATABASE}")
    
    # Connect to MongoDB
    from services.mongodb_service import mongodb_service
    try:
        await mongodb_service.connect()
        logger.info("MongoDB connection established")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        logger.warning("Application starting without MongoDB - storage features will fail")
    
    # Verify S3 bucket access
    from services.s3_service import s3_service
    try:
        if s3_service.check_bucket_exists():
            logger.info("S3 bucket access verified")
        else:
            logger.warning("S3 bucket not accessible - storage features may fail")
    except Exception as e:
        logger.error(f"S3 verification failed: {str(e)}")
    
    logger.info("API documentation available at /docs")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Shutting down AgriAI API")
    
    # Disconnect from MongoDB
    from services.mongodb_service import mongodb_service
    try:
        await mongodb_service.disconnect()
        logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "AgriAI - Agricultural Analysis API",
        "version": settings.API_VERSION,
        "status": "operational",
        "docs": "/docs",
        "features": [
            "AI-powered crop analysis using AWS Bedrock",
            "Object detection with YOLO/Roboflow",
            "Image storage in S3",
            "Analysis data persistence in MongoDB",
            "Presigned URLs for secure image access"
        ],
        "endpoints": {
            "analysis": {
                "analyze_file": "/api/v1/analyze",
                "analyze_base64": "/api/v1/analyze-base64",
                "health": "/api/v1/health",
                "supported_crops": "/api/v1/supported-crops"
            },
            "data_retrieval": {
                "get_analysis": "/api/v1/analysis/{image_id}",
                "get_user_analyses": "/api/v1/analyses/user/{user_uuid}",
                "get_all_analyses": "/api/v1/analyses/all",
                "statistics": "/api/v1/statistics"
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
