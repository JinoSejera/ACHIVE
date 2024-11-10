from alchive import Alchive, setup_logging, ChatHistory

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.models.bot import ChatRequest, ChatResponse

from semantic_kernel.exceptions import ServiceException

import logging

setup_logging()
# Set the logging level for  semantic_kernel.kernel to DEBUG.
logging.getLogger("kernel").setLevel(logging.DEBUG)

# Instantiate API router
router = APIRouter()

# Instantiate Alchive agent and services
agent = Alchive()
id = agent.initialize_kernel()
if id:
    print(id)
templates = Jinja2Templates(directory="app/templates")

# Define chat endpoints
@router.post("/chat", response_model=ChatResponse)
async def chat_alchive(request: ChatRequest):
    try:
        # Instatiate Chat history
        chat_history = ChatHistory()
        
        if request.history:
            chat_history = chat_history.from_rendered_prompt(request.history)
        # Generate Response from agent
        response = await agent.invoke_agent_alchive(request.message,chat_history)

        return ChatResponse(message=response.response,history=response.str_chat_history)
    except Exception as e:
        raise ServiceException(e)

@router.get("/chatbot", response_class=HTMLResponse)
async def chatbot_page(request: Request):
    return templates.TemplateResponse("chatbot.html", {"request":request})