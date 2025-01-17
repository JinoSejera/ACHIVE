from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from msal import ConfidentialClientApplication
from app.models.bot import ChatRequest, ChatResponse
from semantic_kernel.exceptions import ServiceException
import logging
import os
import markdown
import httpx
from dotenv import load_dotenv
from alchive import Alchive, setup_logging, ChatHistory
import json
from datetime import datetime
from pathlib import Path


load_dotenv()

setup_logging()
logging.getLogger("kernel").setLevel(logging.DEBUG)

router = APIRouter()

agent = Alchive()
id = agent.initialize_kernel()
if id:
    print(id)
templates = Jinja2Templates(directory="app/templates")

# MSAL Config
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
REDIRECT_URI = "http://localhost:8000/api/v1/auth/callback"
SCOPE = ["User.Read"]

msal_app = ConfidentialClientApplication(
    AZURE_CLIENT_ID,
    authority=AUTHORITY,
    client_credential=AZURE_CLIENT_SECRET
)

@router.get("/login")
async def login(request: Request):
    auth_url = msal_app.get_authorization_request_url(
        SCOPE,
        redirect_uri=REDIRECT_URI,
        state=request.url_for("chatbot_page")
    )
    return RedirectResponse(auth_url)

@router.get("/auth/callback")
async def auth_callback(request: Request):
    logging.info(f"Callback URL: {request.url}")
    logging.info(f"Query params: {request.query_params}")

    code = request.query_params.get("code")
    error = request.query_params.get("error")
    state = request.query_params.get("state")

    if error:
        logging.error(f"Authentication error: {error}")
        raise HTTPException(status_code=400, detail=f"Authentication error: {error}")
    if not code:
        logging.error("Authorization code is missing")
        raise HTTPException(status_code=400, detail="Authorization code is missing")

    try:
        result = msal_app.acquire_token_by_authorization_code(
            code,
            scopes=SCOPE,
            redirect_uri=REDIRECT_URI
        )
        if "error" in result:
            logging.error(f"Token acquisition error: {result.get('error_description')}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=result.get("error_description"))

        access_token = result.get('access_token')
        if not access_token:
            logging.error("Access token is missing from the MSAL response")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to acquire access token")

        response = RedirectResponse(url=state or "/api/v1/chatbot")
        response.set_cookie(
            key="access_token", 
            value=access_token,
            httponly=True,
            max_age=3600,
            expires=3600,
            secure=True,
            samesite="lax"
        )
        return response
    except Exception as e:
        logging.error(f"Error in auth_callback: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during authentication")

async def get_user_info(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return response.json()

async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        return await get_user_info(token)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

@router.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/api/v1/chatbot")
    response.delete_cookie("access_token")
    return response

@router.post("/chat", response_model=ChatResponse)
async def chat_alchive(chat_request: ChatRequest, user: dict = Depends(get_current_user)):
    try:
        print(user)
        chat_history = ChatHistory()
        if chat_request.history:
            chat_history = chat_history.from_rendered_prompt(chat_request.history)
        response = await agent.invoke_agent_alchive(chat_request.message, chat_history)
        return ChatResponse(message=markdown.markdown(response.response), history=response.str_chat_history, user_name=user['name'], user_id=user['email'])
    except Exception as e:
        raise ServiceException(e)

@router.post("/ingest")
async def upload_files_to_acs():
    try:
        await agent.upload_file()
    except Exception as e:
        raise ServiceException(e)
    
@router.get("/chatbot", response_class=HTMLResponse)
async def chatbot_page(request: Request):
    return templates.TemplateResponse("chatbot.html", {
        "request": request,
        "client_id": AZURE_CLIENT_ID,
        "tenant_id": AZURE_TENANT_ID,
        "redirect_uri": REDIRECT_URI
    })

# Saving History ------------------------------
@router.post("/save_chat_history")
async def save_chat_history(request: Request):
    user = await get_current_user(request)
    data = await request.json()
    
    history_dir = Path("history")
    history_dir.mkdir(exist_ok=True)
    
    file_path = history_dir / f"{user['id']}.json"
    
    try:
        if file_path.exists():
            with open(file_path, "r") as f:
                existing_data = json.load(f)
        else:
            existing_data = []
        
        new_entry = {
            "timestamp": datetime.now().isoformat(),
            "message": data["message"],
            "sender": data["sender"]
        }
        existing_data.append(new_entry)
        
        with open(file_path, "w") as f:
            json.dump(existing_data, f, indent=2)
        
        return {"status": "success"}
    except Exception as e:
        logging.error(f"Error saving chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error saving chat history")

@router.post("/save_chat_history_v2")
async def save_chat_history_v2(request: Request):
    user = await get_current_user(request)
    data = await request.json()
    
    file_name = f"{user['id']}.json"
    
    try:     
        new_entry = {
            "timestamp": datetime.now().isoformat(),
            "message": data["message"],
            "sender": data["sender"]
        }
        agent.save_history_to_storage(file_name,new_entry)
        logging.info("Message successfully added in the history.")
        return {"status": "success"}
    except Exception as e:
        logging.error(f"Error saving chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error saving chat history")
    
@router.get("/load_chat_history")
async def load_chat_history(request: Request):
    user = await get_current_user(request)
    
    history_dir = Path("history")
    file_path = history_dir / f"{user['id']}.json"
    
    try:
        if file_path.exists():
            with open(file_path, "r") as f:
                chat_history = json.load(f)
            return {"chat_history": chat_history}
        else:
            return {"chat_history": []}
    except Exception as e:
        logging.error(f"Error loading chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error loading chat history")
    
@router.get("/load_chat_history_v2")
async def load_chat_history_v2(request: Request):
    user = await get_current_user(request)
    file_name = f"{user['id']}.json"
    
    try:
        chat_history = agent.download_history_from_storage(file_name)
        return {"chat_history": chat_history}
    except Exception as e:
        logging.error(f"Error loading chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error loading chat history")

# Update the get_user_info function to include the user's ID
async def get_user_info(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        user_data = response.json()
        return {
            "id": user_data.get("id"),
            "name": user_data.get("displayName"),
            "email": user_data.get("userPrincipalName")
        }

# -------------------------------------------
