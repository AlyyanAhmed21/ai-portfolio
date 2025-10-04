# Pydantic schemas for API I/O
from pydantic import BaseModel

class ChatRequest(BaseModel):
    """
    Defines the structure of a request to the /chat endpoint.
    """
    message: str
    # We can add more fields later, like session_id, etc.

class ChatResponse(BaseModel):
    """
    Defines the structure of a response from the /chat endpoint.
    """
    answer: str
    # We can add more fields later, like sources.