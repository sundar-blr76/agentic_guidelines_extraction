#!/usr/bin/env python3
"""
Test script to demonstrate session-aware chat functionality.
"""

import os
import sys
import requests
import json
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000"

def test_session_functionality():
    """Test the session management features."""
    print("🧪 Testing Session Management Functionality\n")
    
    # 1. Create a new session
    print("1. Creating a new session...")
    response = requests.post(f"{BASE_URL}/agent/session/create", 
                           json={"context": {"test": "demo_session"}})
    if response.status_code == 200:
        session_data = response.json()
        session_id = session_data["session_id"]
        print(f"✅ Session created: {session_id}\n")
    else:
        print(f"❌ Failed to create session: {response.text}")
        return
    
    # 2. Test first message
    print("2. Sending first message...")
    message1 = "What are investment guidelines?"
    response = requests.post(f"{BASE_URL}/agent/chat", 
                           json={"input": message1, "session_id": session_id})
    if response.status_code == 200:
        chat_data = response.json()
        print(f"✅ Message sent: {message1}")
        print(f"📝 Response: {chat_data['output'][:100]}...\n")
    else:
        print(f"❌ Failed to send message: {response.text}")
        return
    
    # 3. Test follow-up message (should have context)
    print("3. Sending follow-up message...")
    message2 = "Can you elaborate on what you just mentioned?"
    response = requests.post(f"{BASE_URL}/agent/chat", 
                           json={"input": message2, "session_id": session_id})
    if response.status_code == 200:
        chat_data = response.json()
        print(f"✅ Follow-up sent: {message2}")
        print(f"📝 Response: {chat_data['output'][:100]}...\n")
    else:
        print(f"❌ Failed to send follow-up: {response.text}")
        return
    
    # 4. Get session history
    print("4. Retrieving session history...")
    response = requests.get(f"{BASE_URL}/agent/session/{session_id}/history")
    if response.status_code == 200:
        history_data = response.json()
        print(f"✅ Session history retrieved:")
        print(f"📜 History length: {len(history_data.get('conversation_history', ''))}")
        print(f"🔧 Context: {history_data.get('context', {})}\n")
    else:
        print(f"❌ Failed to get history: {response.text}")
    
    # 5. Update session context
    print("5. Updating session context...")
    context_update = {"portfolio_focus": "retirement_funds", "user_level": "beginner"}
    response = requests.put(f"{BASE_URL}/agent/session/{session_id}/context", 
                          json=context_update)
    if response.status_code == 200:
        print(f"✅ Context updated: {context_update}\n")
    else:
        print(f"❌ Failed to update context: {response.text}")
    
    # 6. Test context-aware message
    print("6. Testing context-aware response...")
    message3 = "What should I focus on as a beginner?"
    response = requests.post(f"{BASE_URL}/agent/chat", 
                           json={"input": message3, "session_id": session_id})
    if response.status_code == 200:
        chat_data = response.json()
        print(f"✅ Context-aware message sent: {message3}")
        print(f"📝 Response: {chat_data['output'][:100]}...\n")
    else:
        print(f"❌ Failed to send context-aware message: {response.text}")
    
    # 7. Get session stats
    print("7. Getting session statistics...")
    response = requests.get(f"{BASE_URL}/agent/sessions/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Session stats: {stats}\n")
    else:
        print(f"❌ Failed to get stats: {response.text}")
    
    # 8. Test new session without previous context
    print("8. Testing new session (should have no context)...")
    message4 = "What were we just discussing?"
    response = requests.post(f"{BASE_URL}/agent/chat", 
                           json={"input": message4})  # No session_id = new session
    if response.status_code == 200:
        chat_data = response.json()
        new_session_id = chat_data["session_id"]
        print(f"✅ New session created: {new_session_id}")
        print(f"📝 Response (should indicate no context): {chat_data['output'][:100]}...\n")
    else:
        print(f"❌ Failed to test new session: {response.text}")
    
    print("🎉 Session functionality test completed!")

def test_server_connection():
    """Test if server is running."""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("🚀 Session Management Test Suite\n")
    
    if not test_server_connection():
        print("❌ Server not running. Please start the server first:")
        print("   source venv/bin/activate")
        print("   python -m uvicorn guidelines_agent.mcp_server.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    try:
        test_session_functionality()
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()