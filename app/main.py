# main.py
import importlib
import logging
import pkgutil
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.session import check_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
#  Auto Router Discovery  —  scans app/api/v1/ and registers all routers
# =============================================================================
def register_routers(app: FastAPI) -> None:
    """
    Automatically finds and registers every router in app/api/v1/.

    Each endpoint file must expose:
        router = APIRouter()
    """
    api_path   = Path(__file__).parent / "api" / "v1"
    package    = "app.api.v1"

    for module_info in pkgutil.iter_modules([str(api_path)]):
        module_name = module_info.name

        # skip private / utility files like __init__, _helpers, etc.
        if module_name.startswith("_"):
            continue

        try:
            module = importlib.import_module(f"{package}.{module_name}")

            if hasattr(module, "router"):
                app.include_router(
                    module.router,
                    prefix=f"{settings.API_PREFIX}/{module_name}",  # e.g. /api/v1/users
                )
                logger.info(f"✅ Router registered: /api/v1/{module_name}")
            else:
                logger.warning(f"⚠️  Skipped {module_name}.py — no 'router' found")

        except Exception as e:
            logger.error(f"❌ Failed to load router '{module_name}': {e}", exc_info=True)


# =============================================================================
#  Lifespan
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info(f"Starting  : {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug      : {settings.DEBUG}")

    if check_db_connection():
        logger.info("✅ Database connected successfully")
    else:
        logger.critical("❌ Database connection FAILED — check DATABASE_URL")

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info(f"Shutting down {settings.APP_NAME}...")


# =============================================================================
#  App
# =============================================================================
IS_PROD = settings.ENVIRONMENT == "production"

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url=None        if IS_PROD else "/docs",
    redoc_url=None       if IS_PROD else "/redoc",
    openapi_url=None     if IS_PROD else "/openapi.json",
    lifespan=lifespan,
)


# =============================================================================
#  Middleware
# =============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
#  Register all routers dynamically
# =============================================================================
register_routers(app)


# =============================================================================
#  Core Routes
# =============================================================================
@app.get("/", tags=["Root"])
def home():
    return {
        "app":         settings.APP_NAME,
        "version":     settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs":        "/docs" if not IS_PROD else "disabled",
    }


@app.get("/health", tags=["Health"])
def health_check():
    db_ok = check_db_connection()
    return {
        "status":      "healthy"   if db_ok else "unhealthy",
        "app":         settings.APP_NAME,
        "version":     settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database":    "connected" if db_ok else "unreachable",
    }