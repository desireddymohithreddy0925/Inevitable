import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from inevitable.api.v1 import router
from inevitable.config import settings

# Structured logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("inevitable")

app = FastAPI(
    title="Inevitable API",
    description="Don't trust the patch. Prove it.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Predictable error responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error processing {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("inevitable.app:app", host=settings.backend_host, port=settings.backend_port, reload=True)
