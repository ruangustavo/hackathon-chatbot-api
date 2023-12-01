from pydantic import BaseModel, Field


class MessageInput(BaseModel):
    content: str = Field(..., max_length=100)
