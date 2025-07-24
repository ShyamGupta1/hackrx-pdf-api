# quick_test.py - Save this file and run it to test your API
import requests
import json

# Test configuration
API_URL = "http://localhost:8000/hackrx/run"
BEARER_TOKEN = "52f647633dca7c9f44b5810213fcecccdfc1cd7b036219642a36a69c0a3b7ff6"

# Your 5 PDFs converted to direct download URLs
PDF_URLS = [
    "https://drive.google.com/uc?export=download&id=16_iM8R9uhCJvF7q5E3G5j2gd3Ce5mzXT",
    "https://drive.google.com/uc?export=download&id=1jhVn2OKp6034dF98pKW0d0rR0vxzDRF9", 
    "https://drive.google.com/uc?export=download&id=1VY_6cwO1l9La7o4t7cG4xXmkm-LUJoog",
    "https://drive.google.com/uc?export=download&id=1963u3JrBJLFCsdFSqqT8Xkvagjl8-sWn",
    "https://drive.google.com/uc?export=download&id=1BCKR6_1ZV2UR97HNRYysSS2Y6zQnA8sL"
]

# Use first PDF for testing
PDF_URL = PDF_URLS[0]

# Test questions for insurance documents
TEST_QUESTIONS = [
    "What is the maximum distance covered for air ambulance services?",
    "What expenses are covered under Well Mother Cover?",
    "What are the exclusions for air ambulance cover?"
]

def test_api():
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "documents": PDF_URL,
        "questions": TEST_QUESTIONS
    }
    
    try:
        print("🚀 Testing HackRx API...")
        print(f"PDF URL: {PDF_URL[:50]}...")
        print(f"Questions: {len(TEST_QUESTIONS)}")
        
        response = requests.post(API_URL, headers=headers, json=data, timeout=120)  # Increased to 120 seconds
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCESS! Your API is working!")
            
            for i, answer in enumerate(result["answers"], 1):
                print(f"\n--- Answer {i} ---")
                print(f"Q: {answer['question']}")
                print(f"A: {answer['answer']}")
            
            print(f"\n🎉 API Response Time: {response.elapsed.total_seconds():.2f} seconds")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

def test_all_pdfs():
    """Test all 5 PDFs with different questions"""
    insurance_questions = [
        "What is the maximum distance covered for air ambulance services?",
        "What expenses are covered under Well Mother Cover?", 
        "What routine care is provided for newborn babies?",
        "What are the exclusions for air ambulance cover?",
        "What is the waiting period for this policy?",
        "What is the sum insured amount?",
        "Which medical conditions are excluded?",
        "What documentation is required for claims?"
    ]
    
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    for i, pdf_url in enumerate(PDF_URLS, 1):
        print(f"\n{'='*60}")
        print(f"🧪 TESTING PDF {i}/5")
        print(f"{'='*60}")
        
        # Use first 3 questions for each PDF
        test_questions = insurance_questions[:3]
        
        data = {
            "documents": pdf_url,
            "questions": test_questions
        }
        
        try:
            print(f"📄 Processing PDF {i}...")
            response = requests.post(API_URL, headers=headers, json=data, timeout=120)  # Increased timeout
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ PDF {i} - SUCCESS!")
                
                for j, answer in enumerate(result["answers"], 1):
                    print(f"\n--- Question {j} ---")  
                    print(f"Q: {answer['question']}")
                    print(f"A: {answer['answer'][:200]}{'...' if len(answer['answer']) > 200 else ''}")
                
                print(f"⏱️ Response Time: {response.elapsed.total_seconds():.2f}s")
                
            else:
                print(f"❌ PDF {i} - Error: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ PDF {i} - Exception: {str(e)}")
        
        # Small delay between tests
        import time
        time.sleep(2)

if __name__ == "__main__":
    # First check if API is running
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ API is running!")
            
            choice = input("\nChoose test option:\n1. Quick test (1 PDF)\n2. Full test (all 5 PDFs)\nEnter 1 or 2: ")
            
            if choice == "2":
                test_all_pdfs()
            else:
                test_api()
        else:
            print("❌ API health check failed")
    except:
        print("❌ API is not running!")
        print("Start it with: python main.py")