# HackRx 6.0 - Lightweight Solution (Windows-Safe)
# No heavy ML dependencies - uses keyword matching + OpenAI GPT

import os
import requests
import json
import re
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import PyPDF2
from io import BytesIO
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="HackRx 6.0 - LLM Query System", version="1.0.0")

# Security
security = HTTPBearer()

# Expected bearer token
EXPECTED_TOKEN = "52f647633dca7c9f44b5810213fcecccdfc1cd7b036219642a36a69c0a3b7ff6"

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get("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", "")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# Models
class QueryRequest(BaseModel):
    documents: str  # URL to PDF document
    questions: List[str]

class Answer(BaseModel):
    question: str
    answer: str

class QueryResponse(BaseModel):
    answers: List[Answer]

# Authentication
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != EXPECTED_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return credentials.credentials

# PDF Processing
def download_pdf(url: str) -> bytes:
    """Download PDF from URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        logger.error(f"Error downloading PDF: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to download PDF: {str(e)}")

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF content"""
    try:
        pdf_file = BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to extract text from PDF: {str(e)}")

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        
        if i + chunk_size >= len(words):
            break
    
    return chunks

def find_relevant_chunks(question: str, chunks: List[str], max_chunks: int = 3) -> List[str]:
    """Find relevant chunks using keyword matching"""
    question_words = set(re.findall(r'\w+', question.lower()))
    
    scored_chunks = []
    for chunk in chunks:
        chunk_words = set(re.findall(r'\w+', chunk.lower()))
        
        # Calculate overlap score
        overlap = len(question_words.intersection(chunk_words))
        score = overlap / len(question_words) if question_words else 0
        
        scored_chunks.append((chunk, score))
    
    # Sort by score and return top chunks
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    return [chunk for chunk, score in scored_chunks[:max_chunks] if score > 0]

def generate_answer_with_openai(question: str, context: str) -> str:
    """Generate answer using OpenAI GPT with retry logic"""
    import time
    import random
    
    max_retries = 3
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""Based on the following document content, answer the question accurately and concisely.

Document Content:
{context}

Question: {question}

Instructions:
- Answer based only on the information provided in the document
- Be specific and accurate  
- If the information is not in the document, say "Information not found in document"
- Keep the answer concise but complete

Answer:"""

            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that answers questions based on document content."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 200,
                "temperature": 0.3
            }
            
            response = requests.post(OPENAI_API_URL, headers=headers, json=data, timeout=30)
            
            if response.status_code == 429:  # Rate limit hit
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Rate limit hit, waiting {delay:.2f} seconds before retry {attempt + 1}")
                    time.sleep(delay)
                    continue
                else:
                    return "Rate limit exceeded. Please try again in a few minutes."
            
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"Request failed, retrying in {delay:.2f} seconds...")
                time.sleep(delay)
                continue
            else:
                logger.error(f"Error generating answer with OpenAI after {max_retries} attempts: {str(e)}")
                return f"Error generating answer after retries: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error generating answer with OpenAI: {str(e)}")
            return f"Error generating answer: {str(e)}"

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/hackrx/run", response_model=QueryResponse)
async def process_query(request: QueryRequest, token: str = Depends(verify_token)):
    """Main endpoint for processing document queries"""
    try:
        logger.info(f"Processing request with {len(request.questions)} questions")
        
        # Download and process PDF
        pdf_content = download_pdf(request.documents)
        text = extract_text_from_pdf(pdf_content)
        chunks = chunk_text(text)
        
        logger.info(f"Extracted {len(text)} characters, created {len(chunks)} chunks")
        
        answers = []
        
        for question in request.questions:
            try:
                # Find relevant chunks
                relevant_chunks = find_relevant_chunks(question, chunks)
                context = "\n\n".join(relevant_chunks)
                
                # Generate answer with delay between requests
                if context:
                    answer = generate_answer_with_openai(question, context)
                else:
                    answer = "No relevant information found in the document."
                
                answers.append(Answer(question=question, answer=answer))
                logger.info(f"Processed question: {question[:50]}...")
                
                # Add small delay between OpenAI requests to avoid rate limiting
                import time
                time.sleep(0.5)  # 500ms delay between requests
                
            except Exception as e:
                logger.error(f"Error processing question '{question}': {str(e)}")
                answers.append(Answer(
                    question=question, 
                    answer=f"Error processing question: {str(e)}"
                ))
        
        return QueryResponse(answers=answers)
        
    except Exception as e:
        logger.error(f"Error in process_query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
