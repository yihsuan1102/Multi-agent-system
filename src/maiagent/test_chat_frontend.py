#!/usr/bin/env python3
"""
Test script to simulate the frontend chat workflow and verify data flow
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_login_and_conversations():
    """Test the complete login -> conversations -> messages workflow"""
    
    print("🔐 Testing supervisor_sales login...")
    
    # Step 1: Login to get JWT token
    login_response = requests.post(f"{BASE_URL}/api/token/", 
        headers={"Content-Type": "application/json"},
        json={"username": "supervisor_sales", "password": "testpassword"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
        
    token_data = login_response.json()
    access_token = token_data["access"]
    print(f"✅ Login successful, got token: {access_token[:50]}...")
    
    # Step 2: Get conversations list
    print("\n📋 Testing conversations API...")
    conv_response = requests.get(f"{BASE_URL}/api/v1/conversations/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    )
    
    if conv_response.status_code != 200:
        print(f"❌ Conversations API failed: {conv_response.status_code}")
        return False
        
    conv_data = conv_response.json()
    conversations = conv_data["data"]["conversations"]
    print(f"✅ Got {len(conversations)} conversations")
    
    for i, conv in enumerate(conversations, 1):
        print(f"  {i}. {conv['title']} ({conv['scenario']['name']}) - {conv['status']}")
        
    if not conversations:
        print("❌ No conversations found!")
        return False
    
    # Step 3: Test specific session messages
    first_session = conversations[0]
    session_id = first_session["id"]
    print(f"\n💬 Testing session messages for: {first_session['title']}")
    
    session_response = requests.get(f"{BASE_URL}/api/v1/conversations/{session_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    )
    
    if session_response.status_code != 200:
        print(f"❌ Session API failed: {session_response.status_code}")
        print(f"Response: {session_response.text[:200]}")
        return False
        
    session_data = session_response.json()
    messages = session_data["data"]["session"]["messages"]
    print(f"✅ Got {len(messages)} messages in session")
    
    for i, msg in enumerate(messages, 1):
        role_emoji = "👤" if msg["message_type"] == "user" else "🤖"
        print(f"  {i}. {role_emoji} {msg['content'][:50]}...")
    
    # Step 4: Test LLM models API (if available)
    print(f"\n🤖 Testing LLM models API...")
    try:
        models_response = requests.get(f"{BASE_URL}/api/v1/llm-models/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        if models_response.status_code == 200:
            models_data = models_response.json()
            print(f"✅ Found LLM models endpoint")
        else:
            print(f"ℹ️ LLM models endpoint returned {models_response.status_code}")
    except Exception as e:
        print(f"ℹ️ LLM models endpoint not available: {e}")
    
    # Step 5: Simulate frontend data structure
    print(f"\n🖼️ Frontend data simulation...")
    print("JavaScript would receive this data structure:")
    print(json.dumps({
        "conversations": conversations,
        "selectedSession": {
            "id": session_id,
            "title": first_session["title"],
            "messages": messages
        }
    }, indent=2))
    
    print(f"\n✅ All tests passed! Frontend should display:")
    print(f"  - {len(conversations)} conversations in left sidebar")
    print(f"  - {len(messages)} messages when selecting '{first_session['title']}'")
    print(f"  - Message input should be enabled")
    print(f"  - Send button should work for new messages")
    
    return True

if __name__ == "__main__":
    print("🧪 Testing Chat Frontend Data Flow")
    print("=" * 50)
    
    success = test_login_and_conversations()
    
    if success:
        print(f"\n🎉 All tests completed successfully!")
        print(f"The frontend JavaScript should now display conversations correctly.")
        print(f"Next steps: Open browser at http://localhost:8000/chat/login/")
    else:
        print(f"\n💥 Tests failed. Check the errors above.")