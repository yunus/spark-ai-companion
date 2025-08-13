from pathlib import Path

from app.core.logging import setup_logging, get_logger

# Setup logging before importing other modules
setup_logging()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from app.infrastructure.external.firebase_client import FirebaseClient
from app.core.config import settings
from app.infrastructure.web.lifespan import LifespanManager
from app.infrastructure.web.middleware import MiddlewareManager
from app.infrastructure.web.exception_handlers import ExceptionHandlerManager
from app.api import router as api_routes

# Global instances
firebase_client: FirebaseClient = None

logger = get_logger(__name__)

lifespan_manager = LifespanManager(logger, settings)
middleware_manager = MiddlewareManager(logger)
exception_handler_manager = ExceptionHandlerManager(logger, settings)

# Static files configuration
STATIC_DIR = Path("static")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    global firebase_client

    # Startup
    logger.info(
        "Starting application lifespan", phase="startup", app_name="AI Travel Agent API"
    )

    firebase_client = await lifespan_manager.startup()

    # Store instances in app state
    _app.state.firebase_client = firebase_client

    logger.info(
        "Application lifespan startup completed",
        phase="startup_completed",
        services=["firebase"],
    )

    try:
        yield
    finally:
        # Shutdown
        logger.info("Starting application lifespan shutdown", phase="shutdown")

        await lifespan_manager.shutdown(firebase_client)

        logger.info(
            "Application lifespan shutdown completed", phase="shutdown_completed"
        )


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    logger.info("Creating FastAPI application", app_creation_phase="started")

    # Create FastAPI app with lifespan
    _app = FastAPI(
        title=settings.app_title,
        description=f"""
    {settings.app_description}
        """,
        version=settings.app_api_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    logger.info(
        "FastAPI application instance created",
        title=settings.app_title,
        version=settings.app_api_version,
        debug_mode=settings.debug,
        docs_enabled=settings.debug,
    )

    # Setup application components
    logger.info(
        "Setting up application components", app_creation_phase="components_setup"
    )

    middleware_manager.setup_middleware(_app)
    exception_handler_manager.setup_exception_handlers(_app)
    setup_static_files(_app)
    setup_routes(_app)

    logger.info(
        "FastAPI application creation completed",
        app_creation_phase="completed",
        components_configured=[
            "middleware",
            "exception_handlers",
            "static_files",
            "routes",
        ],
    )

    return _app


def setup_static_files(_app: FastAPI):
    """Configure static file serving."""
    logger.info("Setting up static files", static_setup_phase="started")

    # Only mount static files if the directory exists
    if STATIC_DIR.exists():
        _app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
        logger.info(
            "Static files mounted",
            static_setup_phase="completed",
            directory=str(STATIC_DIR),
            mount_path="/static",
        )
    else:
        logger.warning(
            "Static directory does not exist, skipping static files setup",
            directory=str(STATIC_DIR),
        )


def setup_routes(_app: FastAPI):
    """Configure application routes."""
    logger.info("Setting up application routes", route_setup_phase="started")

    # Include API routes
    _app.include_router(api_routes, prefix="/api")

    # Add root route for serving index.html
    @_app.get("/")
    async def root():
        """Serves the index.html"""
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        else:
            logger.warning("index.html not found in static directory")
            return {"message": "Welcome to AI Travel Agent API"}

    logger.info(
        "Application routes configured",
        route_setup_phase="completed",
        routes_configured=["api_routes", "root_route"],
    )


# Create the app instance
logger.info(f"Initializing {settings.app_title}", initialization_phase="app_creation")

app = create_application()

logger.info(
    f"{settings.app_title} initialization completed", initialization_phase="completed"
)
