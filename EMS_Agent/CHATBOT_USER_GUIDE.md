# EMS Agent Chatbot - User Guide

## 🚀 Quick Start

The EMS Agent Chatbot is now successfully deployed and running! It provides an intelligent, conversational interface to analyze your Energy Management System data.

### 🌐 Access the Chatbot

1. **Web Interface**: Open http://127.0.0.1:8091 in your browser
2. **API Health Check**: GET http://127.0.0.1:8091/health
3. **WebSocket Endpoint**: ws://127.0.0.1:8091/chat

### 💬 What You Can Ask

The chatbot can understand and respond to various types of energy-related questions:

#### 🔋 **Power & Energy Analysis**
- "What is the current power consumption?"
- "Show me today's energy usage"
- "What's our peak demand?"
- "How much energy have we consumed this month?"

#### 📊 **Trends & Patterns**
- "Show me energy usage trends"
- "What are the peak usage hours?"
- "How has our consumption changed over time?"
- "Show consumption patterns"

#### 🚨 **Anomalies & Issues**
- "Are there any anomalies in the system?"
- "Show me any power quality issues"
- "Check for voltage irregularities"
- "Detect system anomalies"

#### ⚡ **Electrical Quality**
- "How is the voltage performance?"
- "Show power factor analysis"
- "Check current levels"
- "Analyze power quality"

#### 💰 **Cost Analysis**
- "What is the total energy cost today?"
- "Show me cost breakdown"
- "Calculate monthly energy costs"
- "What are the demand charges?"

#### 📋 **Comprehensive Reports**
- "Give me a comprehensive system report"
- "Show me a complete analysis"
- "Generate a detailed summary"
- "Full system status report"

### 🎯 Key Features

✅ **Real-time Data Analysis** - Connects to MongoDB and analyzes live energy data
✅ **Natural Language Understanding** - Understands various ways of asking questions
✅ **Intent Recognition** - Automatically detects what type of analysis you need
✅ **Intelligent Responses** - Provides contextual, detailed answers with data insights
✅ **Modern Web Interface** - Clean, responsive chat interface with suggestion chips
✅ **WebSocket Communication** - Real-time, low-latency chat experience
✅ **Comprehensive Analytics** - Power, voltage, current, costs, trends, and anomalies

### 📊 Data Capabilities

The chatbot analyzes data from your MongoDB database including:

- **Power Consumption** - Active power, reactive power, apparent power
- **Electrical Parameters** - Voltage, current, power factor, frequency
- **Energy Metrics** - kWh consumption, demand patterns, load factors
- **Cost Analysis** - Energy costs, demand charges, rate calculations
- **Quality Metrics** - Voltage stability, power factor, harmonics
- **Anomaly Detection** - Statistical analysis and threshold-based detection
- **Trend Analysis** - Time-series patterns and consumption trends

### 🔧 Technical Details

- **Framework**: FastAPI with WebSocket support
- **Database**: MongoDB integration with real-time queries
- **ML Models**: Isolation Forest for anomaly detection
- **Frontend**: Modern HTML/CSS/JavaScript interface
- **API**: RESTful endpoints + WebSocket for real-time chat

### 🧪 Testing Results

✅ All core functions tested and working:
- WebSocket connection: ✅ Success
- MongoDB data retrieval: ✅ Success  
- Intent analysis: ✅ Success
- Power analysis: ✅ Success
- Trend analysis: ✅ Success
- Anomaly detection: ✅ Success
- Cost calculation: ✅ Success
- Voltage analysis: ✅ Success
- Comprehensive reporting: ✅ Success

### 🚀 Running the Chatbot

```bash
# Start the chatbot server
cd /Users/aashik/Documents/Sustainabyte/agent/EMS_Agent
python ems_chatbot.py

# The chatbot will be available at:
# http://127.0.0.1:8091
```

### 💡 Tips for Best Results

1. **Be specific** - "Show me today's power consumption" vs "power"
2. **Use natural language** - The chatbot understands conversational questions
3. **Try different phrasings** - Multiple ways to ask the same question work
4. **Ask follow-up questions** - Build on previous responses for deeper insights
5. **Use suggestion chips** - Click on suggested questions for quick access

### 🔗 Integration Options

The chatbot can be easily integrated with:
- Existing EMS dashboards
- Mobile applications
- Slack/Teams bots
- Voice assistants
- Custom applications via WebSocket API

---

🎉 **Your EMS Agent Chatbot is ready to use!** Start asking questions about your energy data and get intelligent, conversational insights.