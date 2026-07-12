from fastapi import FastAPI
from src.agent import SECAgent
from langchain.messages import HumanMessage
from pydantic import BaseModel
import asyncio 

app = FastAPI()

agent = SECAgent().build()

class ChatRequest(BaseModel):
    question: str

@app.get("/ping")
def test():
    return {"Hello" : "World"}

@app.post("/agent")
async def ask_agent(request: ChatRequest):
    question = request.question
    result = await asyncio.to_thread(agent.invoke, {"messages": [HumanMessage(content=question)]})
    messages = result["messages"]
    return {"result" : messages[-1].content}