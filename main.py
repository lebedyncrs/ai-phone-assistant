from __future__ import annotations

from fastapi import FastAPI
import uvicorn

from middlewares.middlewares import log_requests
from config.logging_config import configure_logging
from api.routes import twilio, google, orders

logger = configure_logging()
app = FastAPI(
    title="Personal Voice Assistant API",
    description="A FastAPI application for a personal voice assistant",
    version="0.1.0"
)
app.middleware("http")(log_requests)

# Include routers
app.include_router(twilio.router)
app.include_router(google.router)
app.include_router(orders.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
