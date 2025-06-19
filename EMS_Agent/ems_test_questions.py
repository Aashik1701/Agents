#!/usr/bin/env python3
"""
EMS Chat Test Questions - Comprehensive Collection
Organized by functionality and complexity levels
"""

def get_test_questions():
    """
    Returns comprehensive test questions for EMS chat system
    Organized by categories and complexity levels
    """
    
    questions = {
        "basic_system": {
            "title": "🔧 Basic System Queries",
            "description": "Test basic system functionality and status",
            "questions": [
                "What is the current system status?",
                "Is the EMS system working properly?", 
                "Check system health",
                "Show system connection status",
                "How many records are in the database?",
                "What collections are available?",
                "Test the database connection"
            ]
        },
        
        "current_data": {
            "title": "📊 Current Data & Readings",
            "description": "Get latest and real-time energy data",
            "questions": [
                "Show me the latest energy readings",
                "What are the current voltage levels?",
                "Display real-time power consumption",
                "What's the current power factor?",
                "Show current consumption rates",
                "Get the most recent meter readings",
                "What's happening right now in the system?"
            ]
        },
        
        "statistical_analysis": {
            "title": "📈 Statistical Analysis",
            "description": "Mathematical analysis of energy data",
            "questions": [
                "What's the average voltage across all meters?",
                "Calculate the mean power consumption",
                "Show me the maximum current reading",
                "What's the minimum voltage recorded?",
                "Calculate average power factor",
                "What's the peak power demand?",
                "Show statistical summary of all parameters"
            ]
        },
        
        "anomaly_detection": {
            "title": "⚠️ Anomaly Detection (Uses ML if available)",
            "description": "Detect unusual patterns and anomalies",
            "questions": [
                "Are there any voltage anomalies in the system?",
                "Detect unusual power consumption patterns",
                "Show me any abnormal current spikes",
                "Find voltage fluctuations",
                "Identify power factor anomalies",
                "Check for energy consumption spikes",
                "Detect system irregularities",
                "Are there any outliers in the data?"
            ]
        },
        
        "trend_analysis": {
            "title": "📊 Trend Analysis (Uses Analytics if available)",
            "description": "Analyze patterns and trends over time",
            "questions": [
                "What are the energy consumption trends?",
                "Show me power factor patterns over time",
                "Analyze voltage stability trends",
                "How has power consumption changed?",
                "Display current trending patterns",
                "What trends do you see in the data?",
                "Show energy usage patterns",
                "Analyze system performance trends"
            ]
        },
        
        "predictive_analysis": {
            "title": "🔮 Predictive Analysis (Uses ML if available)",
            "description": "Forecast and predict future energy patterns",
            "questions": [
                "Predict energy consumption for tomorrow",
                "Forecast voltage requirements for next week",
                "What will be the peak power demand?",
                "Predict future power factor trends",
                "Estimate next week's energy usage",
                "Forecast system load requirements",
                "Predict when anomalies might occur",
                "What's the expected energy pattern?"
            ]
        },
        
        "optimization": {
            "title": "⚡ Optimization (Uses ML if available)", 
            "description": "Get recommendations for system optimization",
            "questions": [
                "How can I optimize power factor efficiency?",
                "Suggest ways to reduce energy consumption",
                "Recommend voltage regulation improvements",
                "How to improve system efficiency?",
                "Optimize energy usage patterns",
                "Suggest cost reduction strategies",
                "Recommend performance improvements",
                "How to minimize energy waste?"
            ]
        },
        
        "time_based": {
            "title": "🕐 Time-Based Queries",
            "description": "Query data for specific time periods",
            "questions": [
                "Show today's energy consumption summary",
                "What happened yesterday?",
                "Display this week's energy report",
                "Compare today with yesterday",
                "Show hourly consumption patterns",
                "What's this month's energy usage?",
                "Display daily energy summary",
                "Show recent energy history"
            ]
        },
        
        "comprehensive_reports": {
            "title": "📋 Comprehensive Reports",
            "description": "Generate detailed system reports",
            "questions": [
                "Give me a comprehensive energy report",
                "Generate a complete system analysis",
                "Show full energy management summary",
                "Create detailed performance report",
                "Display complete system overview",
                "Generate energy audit report",
                "Show comprehensive data analysis",
                "Create system health report"
            ]
        },
        
        "specific_parameters": {
            "title": "🔍 Specific Parameter Queries",
            "description": "Focus on specific energy parameters",
            "questions": [
                "Tell me about voltage levels",
                "Analyze current consumption patterns",
                "Focus on power factor performance",
                "Show energy consumption details",
                "Analyze power quality parameters",
                "Display voltage regulation data",
                "Show current flow patterns",
                "Analyze power efficiency metrics"
            ]
        },
        
        "troubleshooting": {
            "title": "🔧 Troubleshooting & Diagnostics",
            "description": "Identify and diagnose system issues",
            "questions": [
                "What issues do you see in the system?",
                "Diagnose energy efficiency problems",
                "Check for power quality issues",
                "Identify voltage regulation problems",
                "Find current imbalance issues",
                "Detect power factor correction needs",
                "Check system stability",
                "Identify maintenance requirements"
            ]
        },
        
        "advanced_queries": {
            "title": "🚀 Advanced Queries (Full Service Integration)",
            "description": "Complex queries that use multiple services",
            "questions": [
                "Perform advanced anomaly detection with ML predictions",
                "Analyze trends and predict future anomalies",
                "Optimize system performance based on historical data",
                "Generate predictive maintenance recommendations",
                "Perform comprehensive energy efficiency analysis",
                "Create advanced forecasting models",
                "Analyze multi-parameter correlations",
                "Generate AI-powered optimization strategies"
            ]
        }
    }
    
    return questions

def print_questions_by_category():
    """Print all questions organized by category"""
    questions = get_test_questions()
    
    print("🔋 EMS CHAT - COMPREHENSIVE TEST QUESTIONS")
    print("=" * 80)
    print("📝 Use these questions to test all functionality levels")
    print("🔗 Enhanced features activate when microservices are available")
    print("=" * 80)
    
    total_questions = 0
    
    for category_id, category in questions.items():
        print(f"\n{category['title']}")
        print(f"📖 {category['description']}")
        print("-" * 60)
        
        for i, question in enumerate(category['questions'], 1):
            print(f"{i:2d}. {question}")
            total_questions += 1
        
        print(f"\n📊 Subtotal: {len(category['questions'])} questions")
    
    print(f"\n🎯 TOTAL TEST QUESTIONS: {total_questions}")
    print(f"\n💡 USAGE:")
    print(f"   • Copy any question above")
    print(f"   • Paste into EMS chat interface")
    print(f"   • Test system responses")
    print(f"   • Compare legacy vs enhanced mode")

def get_quick_test_set():
    """Get a quick set of essential test questions"""
    return [
        "What is the current system status?",
        "Show me the latest energy readings", 
        "Are there any anomalies in the system?",
        "What's the average voltage?",
        "Predict tomorrow's energy consumption",
        "How can I optimize system efficiency?",
        "Give me a comprehensive energy report",
        "Show energy consumption trends"
    ]

if __name__ == "__main__":
    print_questions_by_category()
    
    print(f"\n" + "="*80)
    print("🚀 QUICK TEST SET (Essential Questions)")
    print("="*80)
    
    quick_tests = get_quick_test_set()
    for i, question in enumerate(quick_tests, 1):
        print(f"{i}. {question}")
    
    print(f"\n🎮 Ready to test! Start with: python app.py")
