from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.schema import Document
import pandas as pd
import os
import re
import json
import numpy as np
from typing import List, Optional
import uuid
from datetime import datetime

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# In-memory storage for conversations
conversations = {}

# Data cleaning functions
def clean_text(text):
    if isinstance(text, str):
        text = text.lower()
        text = re.sub(r'[éèêë]', 'e', text)
        text = re.sub(r'[àâä]', 'a', text)
        text = re.sub(r'[îï]', 'i', text)
        text = re.sub(r'[ôö]', 'o', text)
        text = re.sub(r'[ùûü]', 'u', text)
        text = re.sub(r'[^a-zA-Z0-9\s,]', '', text)
    return text

def generate_hotel_text(hotel):
    name = hotel.get('name', 'nom inconnu')
    location = hotel.get('location', 'localisation inconnue')
    price = hotel.get('price', 'prix non renseigné')
    rating = hotel.get('rating', 'note non disponible')
    features = hotel.get('features', 'non renseigné')
    beaches = hotel.get('nearby_beaches', 'non renseigné')
    
    return (
        f"Nom de l'hôtel : {name}.\n"
        f"Localisation : {location}.\n"
        f"Prix : {price} TND par nuit.\n"
        f"Note : {rating}.\n"
        f"Caractéristiques : {features}.\n"
        f"Plages à proximité : {beaches}.\n"
    )

def initialize_components():
    # Load and clean data
    file_path = "hotels.xlsx"
    #file_path = os.path.join(os.path.dirname(__file__), "..", "hotels.xlsx")
    #file_path = os.path.abspath(file_path)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Error: File '{file_path}' not found.")
    
    xls = pd.ExcelFile(file_path)
    df_hotels = xls.parse('Hotels')
    df_comments = xls.parse('Commentaires')
    df_questions = xls.parse('QuestionReponse')

    # Clean data
    df_hotels = df_hotels.rename(columns=lambda x: clean_text(x))
    df_hotels['nom hotel'] = df_hotels['nom hotel'].apply(clean_text)
    df_hotels['etoile'] = pd.to_numeric(df_hotels['etoile'], errors='coerce')
    df_hotels['prix'] = pd.to_numeric(df_hotels['prix'], errors='coerce')

    df_comments = df_comments.rename(columns=lambda x: clean_text(x))
    df_comments['nom hotel'] = df_comments['nom hotel'].apply(clean_text)
    df_comments['note'] = df_comments['note'].astype(str).str.replace(',', '.').astype(float)

    df_questions = df_questions.rename(columns=lambda x: clean_text(x))
    df_questions['nom hotel'] = df_questions['nom hotel'].apply(clean_text)

    # Convert to JSON structure
    df_hotels['hotel_id'] = np.arange(1, len(df_hotels) + 1)
    hotels_json = []
    
    for _, hotel in df_hotels.iterrows():
        hotel_id = hotel['hotel_id']
        hotel_name = hotel['nom hotel']

        comments = df_comments[df_comments['nom hotel'] == hotel_name][['titre', 'commentaire', 'note', 'date commentaire']].to_dict(orient='records')
        questions = df_questions[df_questions['nom hotel'] == hotel_name][['question', 'answertext']].to_dict(orient='records')

        hotel_data = {
            "hotel_id": int(hotel_id),
            "name": hotel['nom hotel'],
            "location": hotel['lieu'],
            "address": hotel['adresse'],
            "stars": hotel['etoile'],
            "price": hotel['prix'],
            "rating": hotel['rate nominal'],
            "features": hotel['points fort'],
            "nearby_places": hotel['lieux a proximite'],
            "nearby_beaches": hotel['plages a proximite'],
            "transport": hotel['transports en commun'],
            "airports": hotel['aeroports les plus proches'],
            "policies": {
                "checkin": hotel['arrive'],
                "checkout": hotel['depart'],
                "age_restriction": hotel['restriction dage'],
                "pets": hotel['animaux domestiques'],
                "children_beds": hotel['enfants et lits']
            },
            "additional_info": hotel['a savoir'],
            "comments": comments,
            "faq": questions
        }
        hotels_json.append(hotel_data)

    # Generate text for each hotel
    documents = []
    for hotel in hotels_json:
        text = generate_hotel_text(hotel)
        documents.append(Document(
            page_content=text,
            metadata={
                "hotel_id": hotel["hotel_id"],
                "name": hotel["name"],
                "location": hotel["location"]
            }
        ))

    # Initialize embedding model
    embedding_function = HuggingFaceEmbeddings(model_name="intfloat/e5-large-v2")

    # Initialize ChromaDB
    persist_directory = "chroma_db"
    if os.path.exists(persist_directory):
        vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=embedding_function
        )
    else:
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embedding_function,
            persist_directory=persist_directory
        )
        vectorstore.persist()

    # Initialize LLM
    llm = ChatGroq(
        model="llama-3.3-70b-versatile", 
        api_key="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",
        temperature=0.1
    )

    # Create prompt template
    prompt_template = PromptTemplate(
        template=(
            "Tu es un assistant touristique tunisien expert en hôtels.\n"
            "Utilise uniquement les informations fournies dans le contexte ci-dessous.\n"
            "**N'invente jamais.** Si une information est absente, indique : 'Non renseigné'.\n\n"
            "Contexte : {context}\n"
            "Question du client : {question}\n\n"
            "Réponse détaillée en français:"
        ),
        input_variables=["context", "question"]
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt_template}
    )

    return qa_chain

# Initialize components at startup
qa_chain = initialize_components()

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    try:
        # Create new conversation if no ID provided
        if not request.conversation_id or request.conversation_id not in conversations:
            conversation_id = str(uuid.uuid4())
            conversations[conversation_id] = {
                "id": conversation_id,
                "messages": []
            }
        else:
            conversation_id = request.conversation_id
        
        # Add user message to conversation
        user_message = Message(
            id=str(uuid.uuid4()),
            content=request.question,
            sender="user",
            timestamp=datetime.now().isoformat()
        )
        conversations[conversation_id]["messages"].append(user_message)
        
        # Get bot response
        result = qa_chain({"query": request.question})
        response = result["result"]
        
        # Add bot message to conversation
        bot_message = Message(
            id=str(uuid.uuid4()),
            content=response,
            sender="bot",
            timestamp=datetime.now().isoformat()
        )
        conversations[conversation_id]["messages"].append(bot_message)
        
        return {
            "conversation_id": conversation_id,
            "messages": [bot_message]  # Return only the bot's response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversations[conversation_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)