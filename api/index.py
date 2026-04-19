"""Vercel serverless entry point — wraps the FastAPI app with Mangum."""

from mangum import Mangum
from src.app import app

handler = Mangum(app, lifespan="off")
