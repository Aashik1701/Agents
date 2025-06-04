# Optibyte AI Agent

An intelligent AI agent for the Optibyte energy management system that provides conversational interfaces, anomaly detection, predictive maintenance, and intelligent insights.

## 🚀 Features

### 1. **Intelligent Dashboard Assistant**
- Natural language querying of energy data
- KPI monitoring and alerting
- Trend analysis and summaries

### 2. **Anomaly & Fault Detection**
- Real-time detection of abnormal readings
- Predictive maintenance alerts
- Zero current detection for equipment

### 3. **Natural Language Interface**
- Conversational chat interface
- Voice-to-text support
- Auto-generated visualizations

### 4. **Recommendation Engine**
- Energy optimization suggestions
- Load scheduling recommendations
- Goal alignment strategies

### 5. **Report Automation**
- Custom report generation
- Scheduled email reports
- Export capabilities (PDF, CSV)

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   AI Services   │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (OpenAI/LLM)  │
│                 │    │                 │    │                 │
│ • Chat Widget   │    │ • API Gateway   │    │ • Intent Recog  │
│ • Dashboards    │    │ • Auth Service  │    │ • Anomaly Det   │
│ • Reports       │    │ • Data Pipeline │    │ • Recommender   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                    ┌─────────────────┐
                    │   Database      │
                    │   (PostgreSQL   │
                    │   + TimescaleDB)│
                    └─────────────────┘
```

## 🛠️ Tech Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS, ShadCN UI, Recharts
- **Backend**: FastAPI, Python 3.11+, Pydantic, SQLAlchemy
- **AI/ML**: OpenAI GPT-4, LangChain, ChromaDB, Sentence Transformers
- **Database**: PostgreSQL + TimescaleDB extension
- **Real-time**: WebSockets, Redis
- **Infrastructure**: Docker, Docker Compose

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+
- Python 3.11+
- OpenAI API Key

### Installation

1. **Clone and Setup**
   ```bash
   cd Optibyte_Agent
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Start Services**
   ```bash
   docker-compose up -d
   ```

3. **Install Dependencies**
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   
   # Frontend
   cd ../frontend
   npm install
   ```

4. **Run Development Servers**
   ```bash
   # Backend (Terminal 1)
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Frontend (Terminal 2)
   cd frontend
   npm run dev
   ```

5. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 📊 Usage Examples

### Natural Language Queries
```
User: "What was the power factor for IKC0073 in the past 6 hours?"
AI: Analyzing power factor data for IKC0073... [Shows trend chart]

User: "Which compressor had the highest current today?"
AI: IKC0078 had the highest current at 164.11 A today.

User: "Generate yesterday's energy consumption report"
AI: [Generates comprehensive report with charts and insights]
```

### Anomaly Detection
- Automatic alerts for abnormal frequency, current, or voltage
- Predictive maintenance based on sensor patterns
- Zero current detection for active equipment

### Recommendations
- Load scheduling optimization
- Equipment efficiency improvements
- Carbon footprint reduction strategies

## 🔐 Security

- JWT-based authentication
- Role-based access control (Admin, Viewer, Support)
- API rate limiting
- Data encryption at rest and in transit

## 📈 Monitoring

- Application metrics with Prometheus
- Real-time dashboards with Grafana
- Error tracking with Sentry
- Performance monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.
