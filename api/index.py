# api/index.py - Fixed Vercel handler
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import os
import requests
import PyPDF2
import io
import time
import openai
from openai import OpenAI

# Get OpenAI API key from environment
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Initialize OpenAI client
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = None

app = FastAPI(
    title="HackRx PDF QA API",
    description="PDF Question Answering API for HackRx 6.0",
    version="1.0.0"
)

# Authentication
BEARER_TOKEN = "hackrx_2024_bearer_token"

class PDFRequest(BaseModel):
    pdf_url: str
    questions: List[str]

class PDFResponse(BaseModel):
    answers: List[str]

def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    if token != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid bearer token")
    
    return token

def download_pdf(url: str) -> bytes:
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download PDF: {str(e)}")

def extract_text_from_pdf(pdf_content: bytes) -> str:
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract text from PDF: {str(e)}")

def find_relevant_content(text: str, question: str, max_chars: int = 3000) -> str:
    question_lower = question.lower()
    words = question_lower.split()
    
    sentences = text.split('.')
    relevant_sentences = []
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        score = sum(1 for word in words if word in sentence_lower)
        if score > 0:
            relevant_sentences.append((sentence.strip(), score))
    
    relevant_sentences.sort(key=lambda x: x[1], reverse=True)
    
    result = ""
    for sentence, _ in relevant_sentences:
        if len(result + sentence) < max_chars:
            result += sentence + ". "
        else:
            break
    
    return result.strip() or text[:max_chars]

def answer_question_with_openai(context: str, question: str) -> str:
    if not client or not OPENAI_API_KEY:
        return find_relevant_content(context, question, max_chars=500)
    
    try:
        prompt = f"""Based on the following insurance document content, please answer the question clearly and concisely.

Document Content:
{context}

Question: {question}

Answer based only on the information provided in the document. If the specific information is not available, say so."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions about insurance documents accurately and concisely."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    
    except openai.RateLimitError:
        return "Rate limit exceeded. Please try again in a few minutes."
    except Exception as e:
        return find_relevant_content(context, question, max_chars=500)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": int(time.time()),
        "openai_configured": bool(OPENAI_API_KEY)
    }

@app.post("/hackrx/run", response_model=PDFResponse)
async def process_pdf(request: PDFRequest, token: str = Depends(verify_token)):
    try:
        pdf_content = download_pdf(request.pdf_url)
        text = extract_text_from_pdf(pdf_content)
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text could be extracted from the PDF")
        
        answers = []
        for question in request.questions:
            relevant_content = find_relevant_content(text, question)
            answer = answer_question_with_openai(relevant_content, question)
            answers.append(answer)
            time.sleep(0.5)
        
        return PDFResponse(answers=answers)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "HackRx PDF QA API", 
        "docs": "/docs",
        "health": "/health"
    }

# Vercel handler function
def handler(request):
    return app

# Alternative exports for Vercel
application = app
