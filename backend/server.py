from fastapi import FastAPI, APIRouter, HTTPException, File, UploadFile
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
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io
import cv2
import numpy as np

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Gemini API key
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']

# Create the main app without a prefix
app = FastAPI(title="Enhanced Medical AI Assistant", description="Comprehensive AI-powered medical diagnosis, medicine suggestions, and exercise recommendations")

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

class MedicineRequest(BaseModel):
    disease_name: str

class ExerciseRequest(BaseModel):
    condition: str

class DocumentAnalysis(BaseModel):
    filename: str
    extracted_text: str
    analysis: dict
    recommendations: Optional[dict] = None

# Enhanced Medical Knowledge Base
MEDICAL_CONDITIONS = [
    {
        "name": "Common Cold",
        "symptoms": ["runny nose", "cough", "sore throat", "sneezing", "fatigue", "congestion"],
        "medicines": ["Acetaminophen 500mg (2-3 times daily)", "Ibuprofen 400mg (3 times daily)", "Decongestants", "Cough syrups", "Vitamin C supplements"],
        "exercises": ["Rest and sleep 8+ hours", "Light walking 10-15 mins", "Deep breathing exercises", "Steam inhalation", "Gargling with warm salt water"],
        "diet": ["Warm liquids (tea, soup)", "Citrus fruits (vitamin C)", "Ginger tea", "Honey", "Avoid dairy products"],
        "doctor_specialization": "General Practitioner",
        "description": "Viral infection affecting upper respiratory tract"
    },
    {
        "name": "Migraine",
        "symptoms": ["severe headache", "nausea", "sensitivity to light", "visual disturbances", "throbbing pain"],
        "medicines": ["Sumatriptan 50mg (as needed)", "Rizatriptan 10mg", "Acetaminophen 1000mg", "Ibuprofen 600mg", "Ergotamine"],
        "exercises": ["Neck stretches", "Progressive muscle relaxation", "Regular sleep schedule", "Yoga", "Avoid trigger foods"],
        "diet": ["Regular meals", "Magnesium-rich foods", "Avoid chocolate, cheese", "Stay hydrated", "Limit caffeine"],
        "doctor_specialization": "Neurologist",
        "description": "Recurring headaches with moderate to severe pain"
    },
    {
        "name": "Allergic Rhinitis",
        "symptoms": ["sneezing", "runny nose", "itchy eyes", "nasal congestion", "watery eyes"],
        "medicines": ["Cetirizine 10mg (once daily)", "Loratadine 10mg", "Nasal corticosteroids", "Decongestants", "Eye drops"],
        "exercises": ["Nasal irrigation with saline", "Breathing exercises", "Avoid allergens", "Indoor air purification"],
        "diet": ["Anti-inflammatory foods", "Quercetin-rich foods", "Local honey", "Avoid processed foods"],
        "doctor_specialization": "Allergist",
        "description": "Allergic reaction causing inflammation in the nose"
    },
    {
        "name": "Hypertension",
        "symptoms": ["high blood pressure", "headaches", "dizziness", "chest pain", "fatigue"],
        "medicines": ["ACE inhibitors", "Amlodipine 5mg", "Metoprolol 25mg", "Hydrochlorothiazide", "Lifestyle changes"],
        "exercises": ["Cardio 30 mins daily", "Walking", "Swimming", "Cycling", "Weight training (light)"],
        "diet": ["Low sodium diet", "DASH diet", "Potassium-rich foods", "Limit alcohol", "Reduce caffeine"],
        "doctor_specialization": "Cardiologist",
        "description": "High blood pressure condition requiring lifestyle changes"
    },
    {
        "name": "Diabetes Type 2",
        "symptoms": ["increased thirst", "frequent urination", "fatigue", "blurred vision", "slow healing"],
        "medicines": ["Metformin 500mg (twice daily)", "Glipizide", "Insulin (if needed)", "Blood glucose monitoring"],
        "exercises": ["Regular walking 45 mins", "Resistance training", "Swimming", "Cycling", "Monitor blood sugar"],
        "diet": ["Low glycemic index foods", "Whole grains", "Vegetables", "Lean proteins", "Limit sugary foods"],
        "doctor_specialization": "Endocrinologist",
        "description": "Metabolic disorder affecting blood sugar regulation"
    },
    {
        "name": "Asthma",
        "symptoms": ["wheezing", "shortness of breath", "chest tightness", "coughing", "difficulty breathing"],
        "medicines": ["Albuterol inhaler (as needed)", "Budesonide inhaler", "Prednisone (for attacks)", "Montelukast"],
        "exercises": ["Swimming", "Walking", "Yoga", "Breathing exercises", "Avoid cold air exercise"],
        "diet": ["Anti-inflammatory foods", "Omega-3 rich foods", "Avoid food allergens", "Stay hydrated"],
        "doctor_specialization": "Pulmonologist",
        "description": "Chronic respiratory condition causing airway inflammation"
    },
    {
        "name": "Acid Reflux (GERD)",
        "symptoms": ["heartburn", "chest pain", "difficulty swallowing", "regurgitation", "sour taste"],
        "medicines": ["Omeprazole 20mg (once daily)", "Ranitidine 150mg", "Antacids", "Domperidone"],
        "exercises": ["Walk after meals", "Elevate head while sleeping", "Avoid lying down after eating"],
        "diet": ["Avoid spicy foods", "Small frequent meals", "Avoid citrus", "Limit caffeine", "Alkaline foods"],
        "doctor_specialization": "Gastroenterologist",
        "description": "Stomach acid flows back into esophagus causing irritation"
    },
    {
        "name": "Anxiety Disorder",
        "symptoms": ["excessive worry", "restlessness", "rapid heartbeat", "sweating", "panic attacks"],
        "medicines": ["Sertraline 50mg", "Alprazolam 0.25mg (short-term)", "Propranolol", "Buspirone"],
        "exercises": ["Deep breathing", "Yoga", "Regular cardio", "Meditation", "Progressive muscle relaxation"],
        "diet": ["Omega-3 foods", "Magnesium-rich foods", "Limit caffeine", "Avoid alcohol", "Complex carbohydrates"],
        "doctor_specialization": "Psychiatrist",
        "description": "Mental health condition characterized by excessive anxiety"
    },
    {
        "name": "Depression",
        "symptoms": ["persistent sadness", "loss of interest", "fatigue", "sleep disturbances", "appetite changes"],
        "medicines": ["Fluoxetine 20mg", "Sertraline 50mg", "Citalopram", "Venlafaxine"],
        "exercises": ["Regular cardio 30 mins", "Yoga", "Walking outdoors", "Group activities", "Strength training"],
        "diet": ["Omega-3 rich foods", "Folate-rich foods", "Protein-rich meals", "Avoid alcohol", "Regular meals"],
        "doctor_specialization": "Psychiatrist",
        "description": "Mental health disorder affecting mood and daily functioning"
    },
    {
        "name": "Arthritis",
        "symptoms": ["joint pain", "stiffness", "swelling", "reduced range of motion", "morning stiffness"],
        "medicines": ["Ibuprofen 600mg", "Naproxen", "Methotrexate", "Glucosamine", "Topical analgesics"],
        "exercises": ["Gentle stretching", "Swimming", "Tai Chi", "Range of motion exercises", "Low-impact activities"],
        "diet": ["Anti-inflammatory foods", "Omega-3 rich foods", "Turmeric", "Avoid processed foods", "Maintain healthy weight"],
        "doctor_specialization": "Rheumatologist",
        "description": "Joint inflammation causing pain and stiffness"
    }
]

# Document Processing Class
class DocumentProcessor:
    @staticmethod
    def extract_text_from_image(image_bytes: bytes) -> str:
        """Extract text from image using OCR"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Use pytesseract to extract text
            text = pytesseract.image_to_string(image, lang='eng')
            return text.strip()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
    
    @staticmethod
    def extract_text_from_pdf(pdf_bytes: bytes) -> str:
        """Extract text from PDF using OCR"""
        try:
            images = convert_from_bytes(pdf_bytes)
            extracted_text = ""
            for i, image in enumerate(images):
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                
                page_text = DocumentProcessor.extract_text_from_image(img_byte_arr)
                extracted_text += f"--- Page {i+1} ---\n{page_text}\n\n"
            
            return extracted_text.strip()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

def get_medical_system_prompt():
    return """You are an expert medical AI assistant similar to Akinator, but for medical diagnosis. Your role is to:

1. Ask intelligent YES/NO questions to diagnose medical conditions
2. Start with general symptoms and narrow down to specific conditions
3. Consider common conditions first, then rare ones
4. Ask about symptom severity, duration, and triggers
5. Be thorough but efficient - aim for 5-10 questions max
6. Provide confidence scores and multiple possibilities

Available conditions you can diagnose:
- Common Cold, Migraine, Allergic Rhinitis, Hypertension, Diabetes Type 2
- Asthma, Acid Reflux (GERD), Anxiety Disorder, Depression, Arthritis

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
        context = "\n".join(conversation_history) if conversation_history else "Starting new medical consultation."
        
        chat = LlmChat(
            api_key=GEMINI_API_KEY,
            session_id=session_id,
            system_message=get_medical_system_prompt()
        ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(1000)
        
        message = UserMessage(
            text=f"Patient response: {user_input}\n\nConversation so far:\n{context}\n\nPlease ask the next diagnostic question or provide diagnosis if confident."
        )
        
        response = await chat.send_message(message)
        return response
        
    except Exception as e:
        logging.error(f"Gemini API error: {str(e)}")
        return "I apologize, but I'm having trouble processing your request. Please try again."

async def analyze_medical_document(text: str) -> dict:
    """Analyze medical document text using Gemini"""
    try:
        chat = LlmChat(
            api_key=GEMINI_API_KEY,
            session_id=str(uuid.uuid4()),
            system_message="You are a medical document analysis expert. Analyze medical reports and extract key information."
        ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(1500)
        
        message = UserMessage(
            text=f"Analyze this medical document and extract: 1) Diagnosed conditions 2) Mentioned symptoms 3) Prescribed medicines 4) Recommended tests 5) Key medical values. Document text: {text}"
        )
        
        response = await chat.send_message(message)
        return {"analysis": response}
        
    except Exception as e:
        return {"analysis": f"Error analyzing document: {str(e)}"}

# API Endpoints

@api_router.post("/start-diagnosis", response_model=DiagnosisResult)
async def start_diagnosis():
    """Start a new medical diagnosis session"""
    session_id = str(uuid.uuid4())
    
    first_question = await get_gemini_response(
        session_id, 
        "I want to start a medical diagnosis. Please ask me the first question to help diagnose my condition.",
        []
    )
    
    session = DiagnosisSession(
        session_id=session_id,
        current_question=first_question,
        user_responses=[],
        confidence_score=0.0,
        potential_conditions=[]
    )
    
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
        session_doc = await db.diagnosis_sessions.find_one({"session_id": response.session_id})
        if not session_doc:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = DiagnosisSession(**session_doc)
        session.user_responses.append(f"Q: {session.current_question}\nA: {response.answer}")
        
        next_response = await get_gemini_response(
            response.session_id,
            response.answer,
            session.user_responses
        )
        
        is_diagnosis = any(word in next_response.lower() for word in ["diagnosed", "condition", "likely", "probably", "appears to be"])
        
        if is_diagnosis or len(session.user_responses) >= 10:
            session.final_diagnosis = next_response
            session.confidence_score = 0.8
            
            condition_name = extract_condition_name(next_response)
            recommendations = get_recommendations(condition_name)
            session.recommendations = recommendations
            
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
            session.current_question = next_response
            session.confidence_score = min(0.1 * len(session.user_responses), 0.7)
            
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

@api_router.post("/upload-medical-document")
async def upload_medical_document(file: UploadFile = File(...)):
    """Upload and analyze medical documents (PDF or images)"""
    allowed_types = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file.content_type} not supported. Allowed: PDF, PNG, JPG, JPEG"
        )
    
    try:
        file_content = await file.read()
        
        if file.content_type == 'application/pdf':
            extracted_text = DocumentProcessor.extract_text_from_pdf(file_content)
        else:
            extracted_text = DocumentProcessor.extract_text_from_image(file_content)
        
        # Analyze with Gemini
        analysis = await analyze_medical_document(extracted_text)
        
        # Get recommendations based on analysis
        recommendations = await get_document_recommendations(extracted_text)
        
        # Save to database
        document = {
            "document_id": str(uuid.uuid4()),
            "filename": file.filename,
            "file_type": file.content_type,
            "extracted_text": extracted_text,
            "analysis": analysis,
            "recommendations": recommendations,
            "uploaded_at": datetime.utcnow()
        }
        await db.medical_documents.insert_one(document)
        
        return DocumentAnalysis(
            filename=file.filename,
            extracted_text=extracted_text,
            analysis=analysis,
            recommendations=recommendations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@api_router.post("/get-medicine-suggestions")
async def get_medicine_suggestions(request: MedicineRequest):
    """Get medicine suggestions for a specific disease"""
    condition = find_condition_by_name(request.disease_name)
    if condition:
        return {
            "disease": condition["name"],
            "medicines": condition["medicines"],
            "description": condition["description"],
            "doctor_specialization": condition["doctor_specialization"],
            "disclaimer": "⚠️ This is for informational purposes only. Consult a healthcare professional before taking any medication."
        }
    else:
        # Use Gemini for unknown conditions
        try:
            chat = LlmChat(
                api_key=GEMINI_API_KEY,
                session_id=str(uuid.uuid4()),
                system_message="You are a medical expert providing medicine suggestions."
            ).with_model("gemini", "gemini-2.0-flash")
            
            message = UserMessage(
                text=f"Provide common over-the-counter medicine suggestions for {request.disease_name}. Include dosages and precautions."
            )
            
            response = await chat.send_message(message)
            
            return {
                "disease": request.disease_name,
                "ai_suggestions": response,
                "disclaimer": "⚠️ AI-generated suggestions. Always consult a healthcare professional."
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail="Error getting medicine suggestions")

@api_router.post("/get-exercise-suggestions")
async def get_exercise_suggestions(request: ExerciseRequest):
    """Get exercise and diet suggestions for a specific condition"""
    condition = find_condition_by_name(request.condition)
    if condition:
        return {
            "condition": condition["name"],
            "exercises": condition["exercises"],
            "diet": condition.get("diet", []),
            "description": condition["description"],
            "disclaimer": "⚠️ Consult your doctor before starting any exercise program."
        }
    else:
        # Use Gemini for unknown conditions
        try:
            chat = LlmChat(
                api_key=GEMINI_API_KEY,
                session_id=str(uuid.uuid4()),
                system_message="You are a fitness and nutrition expert providing exercise and diet advice for medical conditions."
            ).with_model("gemini", "gemini-2.0-flash")
            
            message = UserMessage(
                text=f"Provide safe exercise recommendations and dietary guidelines for someone with {request.condition}."
            )
            
            response = await chat.send_message(message)
            
            return {
                "condition": request.condition,
                "ai_suggestions": response,
                "disclaimer": "⚠️ AI-generated suggestions. Consult healthcare professionals before making changes."
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail="Error getting exercise suggestions")

@api_router.get("/conditions")
async def get_medical_conditions():
    """Get all available medical conditions"""
    return MEDICAL_CONDITIONS

@api_router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get diagnosis session by ID"""
    session_doc = await db.diagnosis_sessions.find_one({"session_id": session_id})
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")
    return DiagnosisSession(**session_doc)

# Helper Functions
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
                "diet": condition.get("diet", []),
                "doctor_specialization": condition["doctor_specialization"],
                "description": condition["description"],
                "disclaimer": "⚠️ This is an AI-generated diagnosis. Please consult with a qualified healthcare professional for proper medical advice and treatment."
            }
    
    return {
        "medicines": ["Consult a doctor for proper medication"],
        "exercises": ["Light exercise as tolerated"],
        "diet": ["Maintain balanced diet"],
        "doctor_specialization": "General Practitioner",
        "description": "Condition requires professional medical evaluation",
        "disclaimer": "⚠️ This is an AI-generated diagnosis. Please consult with a qualified healthcare professional for proper medical advice and treatment."
    }

def find_condition_by_name(name: str) -> dict:
    """Find condition by name (case insensitive)"""
    name_lower = name.lower()
    for condition in MEDICAL_CONDITIONS:
        if name_lower in condition["name"].lower() or condition["name"].lower() in name_lower:
            return condition
        # Check symptoms too
        for symptom in condition["symptoms"]:
            if name_lower in symptom.lower():
                return condition
    return None

async def get_document_recommendations(text: str) -> dict:
    """Get AI-powered recommendations based on document analysis"""
    try:
        chat = LlmChat(
            api_key=GEMINI_API_KEY,
            session_id=str(uuid.uuid4()),
            system_message="You are a medical advisor providing recommendations based on medical reports."
        ).with_model("gemini", "gemini-2.0-flash")
        
        message = UserMessage(
            text=f"Based on this medical report, provide recommendations for: 1) Lifestyle changes 2) Diet modifications 3) Exercise suggestions 4) Follow-up care. Report: {text}"
        )
        
        response = await chat.send_message(message)
        
        return {
            "ai_recommendations": response,
            "disclaimer": "⚠️ These are AI-generated recommendations based on document analysis. Always follow your doctor's advice."
        }
    except Exception as e:
        return {
            "error": "Could not generate recommendations",
            "disclaimer": "⚠️ Please consult your healthcare provider for personalized recommendations."
        }

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