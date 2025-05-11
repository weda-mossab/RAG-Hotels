from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_groq import ChatGroq
import uuid
from datetime import datetime
import os
# ... (keep all the existing imports and setup code)

app=FastAPI()

# ===== MODÈLES PYDANTIC =====
class QuestionRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    

class Message(BaseModel):
    id: str
    content: str
    sender: str  # "user" or "bot"
    timestamp: str

class Conversation(BaseModel):
    id: str
    messages: List[Message]

# In-memory storage for conversations (replace with a database in production)
conversations = {}

@app.post("/ask")
async def ask_question(request: QuestionRequest, conversation_id: Optional[str] = None):
    try:
        # Create new conversation if no ID provided
        if not conversation_id or conversation_id not in conversations:
            conversation_id = str(uuid.uuid4())
            conversations[conversation_id] = {
                "id": conversation_id,
                "messages": []
            }
        
        # Add user message to conversation
        user_message = Message(
            id=str(uuid.uuid4()),
            content=request.question,
            sender="user",
            timestamp=datetime.now().isoformat()
        )
        conversations[conversation_id]["messages"].append(user_message)
        
        # Get bot response
        result = qa_chain.run(request.question)
        
        # Add bot message to conversation
        bot_message = Message(
            id=str(uuid.uuid4()),
            content=result,
            sender="bot",
            timestamp=datetime.now().isoformat()
        )
        conversations[conversation_id]["messages"].append(bot_message)
        
        return {
            "conversation_id": conversation_id,
            "messages": [user_message, bot_message]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Initialisation du modèle de prompt
prompt_template = PromptTemplate(
    template=(
        "Vous êtes un assistant expert en tourisme et hôtels en Tunisie. "
        "Répondez en français avec des informations précises.\n\n"
        "Contexte: {context}\n"
        "Question: {question}\n\n"
        "Réponse:"
    ),
    input_variables=["context", "question"]
)

@app.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversations[conversation_id]

# Update the conversation storage
conversations: Dict[str, Dict] = {}  # Stores all conversations
user_conversations: Dict[str, List[str]] = {}  # Maps user IDs to conversation IDs

class NewConversationRequest(BaseModel):
    user_id: str  # In production, use proper authentication

@app.post("/new-conversation")
async def new_conversation(request: NewConversationRequest):
    conversation_id = str(uuid.uuid4())
    conversations[conversation_id] = {
        "id": conversation_id,
        "user_id": request.user_id,
        "created_at": datetime.now().isoformat(),
        "messages": []
    }
    
    if request.user_id not in user_conversations:
        user_conversations[request.user_id] = []
    user_conversations[request.user_id].append(conversation_id)
    
    return {"conversation_id": conversation_id}

@app.get("/conversations/{user_id}")
async def get_user_conversations(user_id: str):
    if user_id not in user_conversations:
        return {"conversations": []}
    
    conv_list = []
    for conv_id in user_conversations[user_id]:
        if conv_id in conversations:
            conv_list.append({
                "id": conv_id,
                "created_at": conversations[conv_id]["created_at"],
                "preview": conversations[conv_id]["messages"][0]["content"] if conversations[conv_id]["messages"] else "Nouvelle conversation"
            })
    
    return {"conversations": conv_list}

