from pydantic import BaseModel

# Request model
class ChatRequest(BaseModel):
    message:str
    history:str

# Response model
class ChatResponse(BaseModel):
    message:str
    history:str
    user_name:str
    user_id:str