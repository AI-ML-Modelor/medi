from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Gemini API key
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']

# Create the main app without a prefix
app = FastAPI(title="Medical Diagnosis AI", description="AI-powered medical diagnosis system")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class DiagnosisSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_responses: List[str] = []
    current_question: Optional[str] = None
    confidence_score: float = 0.0
    potential_conditions: List[str] = []
    final_diagnosis: Optional[str] = None
    recommendations: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class UserResponse(BaseModel):
    session_id: str
    answer: str  # "yes", "no", "maybe", "unsure"
    
class DiagnosisResult(BaseModel):
    session_id: str
    question: Optional[str] = None
    confidence_score: float
    potential_conditions: List[str]
    final_diagnosis: Optional[str] = None
    recommendations: Optional[dict] = None
    is_complete: bool = False

class MedicalCondition(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    symptoms: List[str]
    medicines: List[str]
    exercises: List[str]
    doctor_specialization: str
    description: str

# Medical conditions database
MEDICAL_CONDITIONS = [
    {
        "name": "Common Cold",
        "symptoms": ["runny nose", "cough", "sore throat", "sneezing", "fatigue"],
        "medicines": ["Acetaminophen", "Ibuprofen", "Decongestants", "Cough syrups"],
        "exercises": ["Rest", "Light walking", "Deep breathing exercises"],
        "doctor_specialization": "General Practitioner",
        "description": "Viral infection affecting upper respiratory tract"
    },
    {
        "name": "Migraine",
        "symptoms": ["severe headache", "nausea", "sensitivity to light", "visual disturbances"],
        "medicines": ["Sumatriptan", "Rizatriptan", "Acetaminophen", "Ibuprofen"],
        "exercises": ["Neck stretches", "Relaxation techniques", "Regular sleep schedule"],
        "doctor_specialization": "Neurologist",
        "description": "Recurring headaches with moderate to severe pain"
    },
    {
        "name": "Allergic Rhinitis",
        "symptoms": ["sneezing", "runny nose", "itchy eyes", "nasal congestion"],
        "medicines": ["Antihistamines", "Nasal corticosteroids", "Decongestants"],
        "exercises": ["Nasal irrigation", "Avoid allergens", "Indoor air purification"],
        "doctor_specialization": "Allergist",
        "description": "Allergic reaction causing inflammation in the nose"
    },
    {
        "name": "Anxiety Disorder",
        "symptoms": ["excessive worry", "restlessness", "rapid heartbeat", "sweating"],
        "medicines": ["SSRIs", "Benzodiazepines", "Beta-blockers"],
        "exercises": ["Deep breathing", "Yoga", "Regular cardio exercise", "Meditation"],
        "doctor_specialization": "Psychiatrist",
        "description": "Mental health condition characterized by excessive anxiety"
    },
    {
        "name": "Hypertension",
        "symptoms": ["high blood pressure", "headaches", "dizziness", "chest pain"],
        "medicines": ["ACE inhibitors", "Diuretics", "Beta-blockers", "Calcium channel blockers"],
        "exercises": ["Regular cardio", "Walking", "Swimming", "Weight training"],
        "doctor_specialization": "Cardiologist",
        "description": "High blood pressure condition"
    }
]

def get_medical_system_prompt():
    return """You are an expert medical AI assistant similar to Akinator, but for medical diagnosis. Your role is to:

1. Ask intelligent YES/NO questions to diagnose medical conditions
2. Start with general symptoms and narrow down to specific conditions
3. Consider common conditions first, then rare ones
4. Ask about symptom severity, duration, and triggers
5. Be thorough but efficient - aim for 5-10 questions max
6. Provide confidence scores and multiple possibilities

Available conditions you can diagnose:
- Common Cold
- Migraine  
- Allergic Rhinitis
- Anxiety Disorder
- Hypertension

Guidelines:
- Ask ONE question at a time
- Keep questions simple and clear
- Consider patient's previous answers
- Build towards a confident diagnosis
- If unsure, ask clarifying questions

Current conversation context: The user is experiencing health issues and you need to diagnose their condition through strategic questioning."""

async def get_gemini_response(session_id: str, user_input: str, conversation_history: List[str]) -> str:
    """Get response from Gemini for medical diagnosis"""
    try:
        # Create conversation context
        context = "\n".join(conversation_history) if conversation_history else "Starting new medical consultation."
        
        # Initialize Gemini chat
        chat = LlmChat(
            api_key=GEMINI_API_KEY,
            session_id=session_id,
            system_message=get_medical_system_prompt()
        ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(1000)
        
        # Create user message
        message = UserMessage(
            text=f"Patient response: {user_input}\n\nConversation so far:\n{context}\n\nPlease ask the next diagnostic question or provide diagnosis if confident."
        )
        
        # Get response
        response = await chat.send_message(message)
        return response
        
    except Exception as e:
        logging.error(f"Gemini API error: {str(e)}")
        return "I apologize, but I'm having trouble processing your request. Please try again."

@api_router.post("/start-diagnosis", response_model=DiagnosisResult)
async def start_diagnosis():
    """Start a new medical diagnosis session"""
    session_id = str(uuid.uuid4())
    
    # Get first question from Gemini
    first_question = await get_gemini_response(
        session_id, 
        "I want to start a medical diagnosis. Please ask me the first question to help diagnose my condition.",
        []
    )
    
    # Create session
    session = DiagnosisSession(
        session_id=session_id,
        current_question=first_question,
        user_responses=[],
        confidence_score=0.0,
        potential_conditions=[]
    )
    
    # Save to database
    await db.diagnosis_sessions.insert_one(session.dict())
    
    return DiagnosisResult(
        session_id=session_id,
        question=first_question,
        confidence_score=0.0,
        potential_conditions=[],
        is_complete=False
    )

@api_router.post("/answer-question", response_model=DiagnosisResult)
async def answer_question(response: UserResponse):
    """Process user's answer and get next question or diagnosis"""
    try:
        # Get session from database
        session_doc = await db.diagnosis_sessions.find_one({"session_id": response.session_id})
        if not session_doc:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = DiagnosisSession(**session_doc)
        
        # Add user response to history
        session.user_responses.append(f"Q: {session.current_question}\nA: {response.answer}")
        
        # Get next question or diagnosis from Gemini
        next_response = await get_gemini_response(
            response.session_id,
            response.answer,
            session.user_responses
        )
        
        # Analyze if this is a diagnosis or another question
        is_diagnosis = any(word in next_response.lower() for word in ["diagnosed", "condition", "likely", "probably", "appears to be"])
        
        if is_diagnosis or len(session.user_responses) >= 10:
            # This is likely a final diagnosis
            session.final_diagnosis = next_response
            session.confidence_score = 0.8  # High confidence for final diagnosis
            
            # Extract condition name and get recommendations
            condition_name = extract_condition_name(next_response)
            recommendations = get_recommendations(condition_name)
            session.recommendations = recommendations
            
            # Update database
            await db.diagnosis_sessions.update_one(
                {"session_id": response.session_id},
                {"$set": session.dict()}
            )
            
            return DiagnosisResult(
                session_id=response.session_id,
                question=None,
                confidence_score=session.confidence_score,
                potential_conditions=[condition_name] if condition_name else [],
                final_diagnosis=next_response,
                recommendations=recommendations,
                is_complete=True
            )
        else:
            # This is another question
            session.current_question = next_response
            session.confidence_score = min(0.1 * len(session.user_responses), 0.7)
            
            # Update database
            await db.diagnosis_sessions.update_one(
                {"session_id": response.session_id},
                {"$set": session.dict()}
            )
            
            return DiagnosisResult(
                session_id=response.session_id,
                question=next_response,
                confidence_score=session.confidence_score,
                potential_conditions=session.potential_conditions,
                is_complete=False
            )
            
    except Exception as e:
        logging.error(f"Error processing answer: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing your answer")

def extract_condition_name(diagnosis_text: str) -> str:
    """Extract condition name from diagnosis text"""
    for condition in MEDICAL_CONDITIONS:
        if condition["name"].lower() in diagnosis_text.lower():
            return condition["name"]
    return "Unknown Condition"

def get_recommendations(condition_name: str) -> dict:
    """Get recommendations for a specific condition"""
    for condition in MEDICAL_CONDITIONS:
        if condition["name"] == condition_name:
            return {
                "medicines": condition["medicines"],
                "exercises": condition["exercises"],
                "doctor_specialization": condition["doctor_specialization"],
                "description": condition["description"],
                "disclaimer": "⚠️ This is an AI-generated diagnosis. Please consult with a qualified healthcare professional for proper medical advice and treatment."
            }
    
    return {
        "medicines": ["Consult a doctor for proper medication"],
        "exercises": ["Light exercise as tolerated"],
        "doctor_specialization": "General Practitioner",
        "description": "Condition requires professional medical evaluation",
        "disclaimer": "⚠️ This is an AI-generated diagnosis. Please consult with a qualified healthcare professional for proper medical advice and treatment."
    }

@api_router.get("/session/{session_id}", response_model=DiagnosisSession)
async def get_session(session_id: str):
    """Get diagnosis session by ID"""
    session_doc = await db.diagnosis_sessions.find_one({"session_id": session_id})
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")
    return DiagnosisSession(**session_doc)

@api_router.get("/conditions", response_model=List[MedicalCondition])
async def get_medical_conditions():
    """Get all available medical conditions"""
    return [MedicalCondition(**condition) for condition in MEDICAL_CONDITIONS]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()