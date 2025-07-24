# test_openai.py - Test your OpenAI API key directly
import requests
import json

# PUT YOUR ACTUAL API KEY HERE
OPENAI_API_KEY = "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"  # Replace this!

def test_openai_key():
    """Test if OpenAI API key works"""
    
    print(f"🔑 Testing API Key: {OPENAI_API_KEY[:10]}...{OPENAI_API_KEY[-4:]}")
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 10
    }
    
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", 
                               headers=headers, json=data, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! Your OpenAI API key is working!")
            print(f"🤖 Response: {result['choices'][0]['message']['content']}")
            return True
            
        elif response.status_code == 401:
            print("❌ UNAUTHORIZED (401)")
            print("🔧 Possible issues:")
            print("   - Invalid API key")
            print("   - API key not copied correctly") 
            print("   - Missing 'sk-proj-' or 'sk-' prefix")
            print(f"📝 Your key starts with: {OPENAI_API_KEY[:10]}...")
            
        elif response.status_code == 429:
            print("⚠️ RATE LIMITED (429)")
            print("✅ Your API key is valid, just too many requests!")
            return True
            
        elif response.status_code == 402:
            print("💳 PAYMENT REQUIRED (402)")
            print("🔧 You need to add a payment method to OpenAI")
            print("💡 Even for free $5 credits, billing info is required")
            
        else:
            print(f"❓ UNKNOWN ERROR ({response.status_code})")
            
        print(f"📄 Full response: {response.text}")
        return False
        
    except Exception as e:
        print(f"💥 EXCEPTION: {str(e)}")
        return False

def check_key_format():
    """Check if API key has correct format"""
    print("\n🔍 CHECKING API KEY FORMAT...")
    
    if OPENAI_API_KEY == "sk-your-actual-key-here":
        print("❌ You haven't replaced the placeholder!")
        print("🔧 Go to main.py and replace 'sk-your-actual-key-here' with your real key")
        return False
        
    if not (OPENAI_API_KEY.startswith("sk-proj-") or OPENAI_API_KEY.startswith("sk-")):
        print("❌ API key should start with 'sk-proj-' or 'sk-'")
        print(f"📝 Your key starts with: {OPENAI_API_KEY[:10]}")
        return False
        
    if len(OPENAI_API_KEY) < 20:
        print("❌ API key seems too short")
        print(f"📏 Length: {len(OPENAI_API_KEY)} (should be 50+ characters)")
        return False
        
    print("✅ API key format looks correct!")
    return True

if __name__ == "__main__":
    print("🧪 OPENAI API KEY TESTER")
    print("=" * 50)
    
    if check_key_format():
        test_openai_key()
    
    print("\n📋 NEXT STEPS:")
    print("1. If key is invalid → Get new key from OpenAI")
    print("2. If payment required → Add billing info to OpenAI")
    print("3. If working → Update your main.py with the same key")