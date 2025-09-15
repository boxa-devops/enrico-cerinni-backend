from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from app.config import settings

from app.api import (
    auth_router,
    products_router,
    clients_router,
    sales_router,
    dashboard_router,
    settings_router,
    brands_router,
    colors_router,
    seasons_router,
    finance_router,
    sizes_router,
    product_variants_router,
    marketing_router,
    reports_router,
)


app = FastAPI(
    title="Enrico Cerrini Backend API",
    description="Backend API for Enrico Cerrini clothing store management system",
    version="1.0.0",
)

# Add CORS middleware with cookie support for local and LAN development
allowed_origins = [origin.strip() for origin in settings.cors_origin.split(",") if origin.strip()] + ["https://enrico.uz"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    # Allow any LAN IP like http://192.168.x.x:3000 or http://10.x.x.x:3000 (and other ports)
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1|(10|172\.(1[6-9]|2[0-9]|3[0-1])|192\.168)(?:\.\d{1,3}){1,2})(?::\d+)?$",
    allow_credentials=True,  # Required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Set-Cookie"],  # Expose Set-Cookie header
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # TODO: Configure with specific domains in production
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "errors": [str(exc)],
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail, "errors": []},
    )


# Include routers
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(clients_router)
app.include_router(sales_router)
app.include_router(dashboard_router)
app.include_router(settings_router)
app.include_router(brands_router)
app.include_router(colors_router)
app.include_router(seasons_router)
app.include_router(finance_router)
app.include_router(sizes_router)
app.include_router(product_variants_router)
app.include_router(marketing_router)
app.include_router(reports_router)


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "success": True,
        "message": "API is running",
        "data": {"status": "healthy", "version": "1.0.0"},
    }


# Root endpoint
@app.get("/")
async def root():
    return {
        "success": True,
        "message": "Enrico Cerrini Backend API",
        "data": {
            "title": "Enrico Cerrini Backend API",
            "version": "1.0.0",
            "docs": "/docs",
        },
    }
