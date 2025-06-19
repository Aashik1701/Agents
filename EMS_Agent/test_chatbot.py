#!/usr/bin/env python3
"""
Test script for EMS Chatbot functionality
"""
import asyncio
import websockets
import json

async def test_chatbot_websocket():
    """Test the chatbot WebSocket functionality"""
    uri = "ws://127.0.0.1:8091/chat"
    
    test_questions = [
        "What is the current power consumption?",
        "Show me energy usage trends",
        "Are there any anomalies in the system?",
        "What is the total energy cost today?",
        "How is the voltage performance?",
        "Give me a comprehensive system report",
        "What are the peak usage hours?",
        "Show power factor analysis"
    ]
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to EMS Chatbot WebSocket")
            print("=" * 60)
            
            for i, question in enumerate(test_questions, 1):
                print(f"\n📝 Test {i}: {question}")
                print("-" * 40)
                
                # Send the question
                await websocket.send(json.dumps({"message": question}))
                
                # Receive the response
                response = await websocket.recv()
                response_data = json.loads(response)
                
                print(f"🤖 Response: {response_data.get('message', 'No message')}")
                
                if response_data.get('data'):
                    print(f"📊 Data Keys: {list(response_data['data'].keys())}")
                
                if response_data.get('suggestions'):
                    print(f"💡 Suggestions: {', '.join(response_data['suggestions'])}")
                
                # Wait a bit between requests
                await asyncio.sleep(1)
                
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    print("🧪 Starting EMS Chatbot Tests")
    asyncio.run(test_chatbot_websocket())
