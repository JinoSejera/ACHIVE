from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import uvicorn
from app.api.v1.endpoints import router as api_roputer

from alchive import load_dotenv

load_dotenv
app = FastAPI()

# Allow all CORS origins
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include the API router
app.include_router(api_roputer, prefix="/api/v1")

# Mount static files directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def root():
    return RedirectResponse("/api/v1/chatbot")