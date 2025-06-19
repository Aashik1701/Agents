#!/usr/bin/env python3
"""
Test script for integrated EMS system with services
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import initialize_ems, service_integrator
from ems_search import EMSQueryEngine
import json

def test_basic_functionality():
    """Test basic EMS functionality"""
    print("🧪 Testing Basic EMS Functionality")
    print("=" * 60)
    
    # Initialize EMS
    if not initialize_ems():
        print("❌ Failed to initialize EMS")
        return False
    
    # Create query engine
    engine = EMSQueryEngine()
    
    # Test basic queries
    test_queries = [
        "What is the system status?",
        "Show me the latest readings",
        "What's the average voltage?",
        "Are there any anomalies?", 
        "Give me today's summary",
        "What's the maximum power consumption?",
        "Show me energy trends",
        "Tell me about power factor"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        try:
            result = engine.search(query)
            answer = result.get('answer', 'No answer')
            confidence = result.get('confidence', 0)
            method = result.get('method', 'unknown')
            
            print(f"   ✅ Answer: {answer[:100]}{'...' if len(answer) > 100 else ''}")
            print(f"   📊 Confidence: {confidence:.0%}")
            print(f"   🔧 Method: {method}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    engine.close()
    return True

def test_service_integration():
    """Test microservices integration"""
    print("\n\n🔗 Testing Service Integration")
    print("=" * 60)
    
    # Check service availability
    available_services = service_integrator.available_services
    print("Available Services:")
    for service, status in available_services.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {service}: {'Online' if status else 'Offline'}")
    
    if not any(available_services.values()):
        print("\n⚠️ No microservices available. System running in legacy mode.")
        print("To test with services, start them using:")
        print("   docker-compose up -d")
        return False
    
    # Test analytics service
    if available_services.get('analytics'):
        print(f"\n📊 Testing Analytics Service...")
        try:
            result = service_integrator.get_analytics('trend_analysis', {'test': True})
            print(f"   Analytics Result: {result}")
        except Exception as e:
            print(f"   Error: {e}")
    
    # Test ML service
    if available_services.get('advanced_ml'):
        print(f"\n🤖 Testing ML Service...")
        try:
            result = service_integrator.get_ml_prediction({'test': True})
            print(f"   ML Result: {result}")
        except Exception as e:
            print(f"   Error: {e}")
    
    return True

def test_enhanced_queries():
    """Test enhanced query processing with services"""
    print("\n\n🚀 Testing Enhanced Query Processing")
    print("=" * 60)
    
    # Enhanced test queries that should trigger service integration
    enhanced_queries = [
        {
            'query': 'Detect any voltage anomalies in the system',
            'expected_services': ['advanced_ml'],
            'description': 'Should trigger ML anomaly detection'
        },
        {
            'query': 'Predict energy consumption for next week',
            'expected_services': ['analytics', 'advanced_ml'], 
            'description': 'Should trigger forecasting services'
        },
        {
            'query': 'Optimize power factor efficiency',
            'expected_services': ['advanced_ml'],
            'description': 'Should trigger optimization recommendations'
        },
        {
            'query': 'Show current system trends and patterns',
            'expected_services': ['analytics'],
            'description': 'Should trigger trend analysis'
        }
    ]
    
    for i, test_case in enumerate(enhanced_queries, 1):
        query = test_case['query']
        print(f"\n{i}. Enhanced Query: '{query}'")
        print(f"   Expected to trigger: {', '.join(test_case['expected_services'])}")
        print(f"   Description: {test_case['description']}")
        
        # Simulate the enhanced query processing from app.py
        # This would normally be called through the Flask API
        try:
            engine = EMSQueryEngine()
            base_response = engine.process_query(query)
            
            # Check service integration
            services_used = []
            enhanced_features = {}
            
            query_lower = query.lower()
            
            # Check for anomaly-related queries
            if any(word in query_lower for word in ['anomaly', 'anomalies', 'abnormal', 'spike', 'unusual']):
                ml_anomalies = service_integrator.get_anomalies()
                if ml_anomalies:
                    enhanced_features['ml_anomalies'] = ml_anomalies
                    services_used.append('advanced_ml')
            
            # Check for prediction/forecast queries
            if any(word in query_lower for word in ['predict', 'forecast', 'future', 'trend']):
                analytics_data = service_integrator.get_analytics('trend_analysis', {'query': query})
                if analytics_data:
                    enhanced_features['trend_analysis'] = analytics_data
                    services_used.append('analytics')
            
            # Check for performance/optimization queries  
            if any(word in query_lower for word in ['optimize', 'efficiency', 'performance', 'improve']):
                ml_recommendations = service_integrator.get_ml_prediction({'type': 'optimization', 'context': query})
                if ml_recommendations:
                    enhanced_features['ml_recommendations'] = ml_recommendations
                    services_used.append('advanced_ml')
            
            print(f"   ✅ Base Response: {base_response[:80]}{'...' if len(base_response) > 80 else ''}")
            print(f"   🔧 Services Used: {services_used if services_used else 'None (legacy mode)'}")
            print(f"   ⚡ Enhanced Features: {len(enhanced_features)} feature(s)")
            
            engine.close()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    """Main test function"""
    print("🔋 EMS (Energy Management System) Integration Test")
    print("=" * 80)
    
    # Run tests
    basic_success = test_basic_functionality()
    service_success = test_service_integration() 
    test_enhanced_queries()
    
    print("\n\n📋 Test Summary")
    print("=" * 60)
    print(f"✅ Basic Functionality: {'PASS' if basic_success else 'FAIL'}")
    print(f"🔗 Service Integration: {'PASS' if service_success else 'LEGACY MODE'}")
    
    print("\n🎯 Recommended Test Questions for EMS Chat:")
    print("=" * 60)
    
    # Generate test questions
    test_questions = [
        # Basic system queries
        "What is the current system status?",
        "Show me the latest energy readings",
        "What's the total energy consumption today?",
        
        # Statistical queries
        "What's the average voltage across all meters?",
        "Show me the maximum power consumption this week",
        "What's the minimum current reading?",
        
        # Anomaly detection (uses ML services if available)
        "Are there any voltage anomalies in the system?",
        "Detect unusual power consumption patterns",
        "Show me any abnormal current spikes",
        
        # Trend analysis (uses analytics services if available)
        "What are the energy consumption trends?",
        "Show me power factor patterns over time",
        "Analyze voltage stability trends",
        
        # Predictive queries (uses ML services if available)
        "Predict energy consumption for tomorrow",
        "Forecast voltage requirements for next week", 
        "What will be the peak power demand?",
        
        # Optimization queries (uses ML services if available)
        "How can I optimize power factor efficiency?",
        "Suggest ways to reduce energy consumption",
        "Recommend voltage regulation improvements",
        
        # Complex analytical queries
        "Give me a comprehensive energy report",
        "Compare today's consumption with yesterday",
        "What's the energy efficiency score?",
        
        # Real-time monitoring
        "Show real-time power consumption",
        "What are the current voltage levels?",
        "Monitor live energy metrics"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"{i:2d}. {question}")
    
    print(f"\n💡 Total Test Questions: {len(test_questions)}")
    print("\n🚀 To start the EMS system:")
    print("   python app.py")
    print("\n🔗 To test with microservices:")
    print("   export MICROSERVICES_MODE=true")
    print("   docker-compose up -d")

if __name__ == "__main__":
    main()
