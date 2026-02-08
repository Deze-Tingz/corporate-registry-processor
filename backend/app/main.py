import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import admin, audit, auth, classifications, documents, health, mfa, queue, reviews

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("CRDP starting up")
    yield
    logger.info("CRDP shutting down")


app = FastAPI(
    title="Corporate Registry Document Processor",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(mfa.router)
app.include_router(documents.router)
app.include_router(classifications.router)
app.include_router(reviews.router)
app.include_router(queue.router)
app.include_router(audit.router)
app.include_router(admin.router)
