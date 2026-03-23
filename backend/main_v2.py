"""
Music Text Generator - v2.0
Refactored with clean architecture.

Run with: uvicorn main:app --host 0.0.0.0 --port 8001
"""
import logging
import sys

# Configure logging BEFORE any other imports
# This prevents isatty errors in windowed mode
class NoTTYHandler(logging.Handler):
    def emit(self, record):
        pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(name)s:%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)] if sys.stdout else [NoTTYHandler()]
)
logging.getLogger('uvicorn').handlers = []

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from services.job_service import JobService
from services.pipeline_service import PipelineService
from api.routes_jobs import router as jobs_router, set_services

logger = logging.getLogger(__name__)

# Create app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Transform voice from songs into creative English lyrics"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI app."""
    
    # Initialize services
    job_service = JobService(settings.uploads_dir, settings.outputs_dir)
    pipeline_service = PipelineService()
    
    # Set services for routes
    set_services(job_service, pipeline_service)
    
    # Include routers
    app.include_router(jobs_router)
    
    logger.info(f"App initialized: {settings.app_name} v{settings.app_version}")
    logger.info(f"Models: {pipeline_service.get_available_models()}")
    
    return app


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "api": settings.api_prefix
    }


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "ok",
        "version": settings.app_version
    }


@app.get("/models")
async def get_models():
    """Get available models info."""
    pipeline = PipelineService()
    return pipeline.get_available_models()


# Initialize on import
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_config=None)
