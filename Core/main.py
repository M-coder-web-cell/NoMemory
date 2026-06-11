from dotenv import load_dotenv
from llm import LLMClient
from fastapi import FastAPI
from pydantic import BaseModel
import os

load_dotenv()
CLAUDE_API_KEY = os.getenv('API_KEY_CLAUDE')

class Body(BaseModel):
    content : str

app = FastAPI()
client = LLMClient(api_key = CLAUDE_API_KEY, max_tokens = 4000)

def Fullprompt(rawHtml):
    return f"You have to Extract the full conversation from this upcoming raw html and Write a ready to paste prompt for another LLM about the full context, removing unncessary details Content : {rawHtml}"

app.post('/summarize')
async def Summarize(body : Body):
    raw_content = body.content
    response = await client.ask(Fullprompt(raw_content))
    return response 
