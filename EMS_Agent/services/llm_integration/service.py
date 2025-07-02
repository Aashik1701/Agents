#!/usr/bin/env python3
"""
Advanced AI and LLM Integration Service for EMS
Provides LangChain integration, advanced conversational AI, and intelligent analysis
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd

# LangChain imports
try:
    from langchain.llms import OpenAI
    from langchain.chat_models import ChatOpenAI
    from langchain.schema import HumanMessage, SystemMessage, AIMessage
    from langchain.chains import LLMChain, ConversationChain
    from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
    from langchain.prompts import PromptTemplate, ChatPromptTemplate
    from langchain.agents import AgentType, initialize_agent, Tool
    from langchain.tools import BaseTool
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.vectorstores import FAISS
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.document_loaders import TextLoader
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain not available. Install with: pip install langchain openai")

# Transformers for local LLM support
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers not available. Install with: pip install transformers torch")

from common.base_service import BaseService

logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """Context for maintaining conversation state"""
    session_id: str
    user_id: str
    conversation_history: List[Dict[str, str]]
    context_data: Dict[str, Any]
    last_updated: datetime
    system_prompt: str = ""


@dataclass
class AIResponse:
    """Structured AI response"""
    response_text: str
    confidence: float
    intent: str
    entities: Dict[str, Any]
    suggestions: List[str]
    data_analysis: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EMSKnowledgeBase:
    """Knowledge base for EMS domain expertise"""
    
    def __init__(self):
        self.documents = []
        self.embeddings_model = None
        self.vector_store = None
        self.ems_knowledge = {
            "power_concepts": {
                "active_power": "Real power that performs useful work, measured in Watts (W)",
                "reactive_power": "Power that flows back and forth, measured in VAR",
                "apparent_power": "Total power in AC circuit, measured in VA",
                "power_factor": "Ratio of active power to apparent power, indicates efficiency"
            },
            "voltage_standards": {
                "low_voltage": "Typically 230V-240V for residential",
                "medium_voltage": "1kV-35kV for distribution",
                "high_voltage": "Above 35kV for transmission"
            },
            "energy_efficiency": {
                "power_factor_correction": "Improving power factor reduces reactive power demand",
                "load_balancing": "Distributing loads evenly across phases",
                "demand_response": "Adjusting consumption based on grid conditions"
            },
            "anomaly_types": {
                "voltage_sag": "Temporary reduction in voltage magnitude",
                "voltage_swell": "Temporary increase in voltage magnitude", 
                "frequency_deviation": "Variation from nominal 50/60 Hz",
                "harmonic_distortion": "Non-sinusoidal waveform components"
            }
        }
    
    def initialize_embeddings(self):
        """Initialize embeddings model for semantic search"""
        if TRANSFORMERS_AVAILABLE:
            try:
                self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Initialized local embeddings model")
            except Exception as e:
                logger.error(f"Failed to initialize embeddings: {e}")
        elif LANGCHAIN_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            try:
                self.embeddings_model = OpenAIEmbeddings()
                logger.info("Initialized OpenAI embeddings")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI embeddings: {e}")
    
    def add_document(self, content: str, metadata: Dict[str, Any] = None):
        """Add document to knowledge base"""
        self.documents.append({
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now()
        })
    
    def search_knowledge(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant information"""
        # Simple keyword-based search for now
        results = []
        query_lower = query.lower()
        
        # Search EMS knowledge
        for category, items in self.ems_knowledge.items():
            for key, value in items.items():
                if any(word in value.lower() or word in key.lower() 
                      for word in query_lower.split()):
                    results.append({
                        "content": f"{key}: {value}",
                        "category": category,
                        "relevance": 0.8
                    })
        
        # Search documents
        for doc in self.documents:
            if any(word in doc["content"].lower() for word in query_lower.split()):
                results.append({
                    "content": doc["content"],
                    "metadata": doc["metadata"],
                    "relevance": 0.7
                })
        
        return sorted(results, key=lambda x: x["relevance"], reverse=True)[:top_k]


class ConversationalAI:
    """Advanced conversational AI with EMS domain expertise"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm = None
        self.local_llm = None
        self.conversations = {}
        self.knowledge_base = EMSKnowledgeBase()
        self.conversation_memory = ConversationBufferMemory()
        
        # Intent classification patterns
        self.intent_patterns = {
            "power_analysis": ["power", "consumption", "usage", "energy", "demand"],
            "voltage_analysis": ["voltage", "volt", "electrical", "supply"],
            "anomaly_detection": ["anomaly", "issue", "problem", "fault", "error"],
            "efficiency_optimization": ["efficiency", "optimize", "improve", "reduce"],
            "cost_analysis": ["cost", "price", "bill", "expense", "savings"],
            "trend_analysis": ["trend", "pattern", "history", "over time"],
            "system_status": ["status", "health", "condition", "state"],
            "recommendations": ["recommend", "suggest", "advice", "should"]
        }
    
    async def initialize(self):
        """Initialize conversational AI components"""
        # Initialize knowledge base
        self.knowledge_base.initialize_embeddings()
        
        # Initialize LLM
        if LANGCHAIN_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            try:
                self.llm = ChatOpenAI(
                    temperature=0.7,
                    model_name="gpt-3.5-turbo",
                    max_tokens=1000
                )
                logger.info("Initialized OpenAI LLM")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI LLM: {e}")
        
        # Initialize local LLM as fallback
        if TRANSFORMERS_AVAILABLE and not self.llm:
            try:
                self.local_llm = pipeline(
                    "text-generation",
                    model="microsoft/DialoGPT-small",
                    tokenizer="microsoft/DialoGPT-small"
                )
                logger.info("Initialized local LLM")
            except Exception as e:
                logger.error(f"Failed to initialize local LLM: {e}")
    
    def classify_intent(self, message: str) -> str:
        """Classify user intent from message"""
        message_lower = message.lower()
        scores = {}
        
        for intent, keywords in self.intent_patterns.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                scores[intent] = score
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return "general_inquiry"
    
    def extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities from user message"""
        entities = {}
        message_lower = message.lower()
        
        # Extract time periods
        time_patterns = {
            "today": ["today", "current", "now"],
            "yesterday": ["yesterday"],
            "week": ["week", "weekly"],
            "month": ["month", "monthly"],
            "year": ["year", "yearly", "annual"]
        }
        
        for period, keywords in time_patterns.items():
            if any(keyword in message_lower for keyword in keywords):
                entities["time_period"] = period
                break
        
        # Extract device/meter references
        if any(word in message_lower for word in ["meter", "device", "sensor"]):
            entities["target"] = "device"
        
        # Extract metric types
        metric_patterns = {
            "power": ["power", "consumption", "usage"],
            "voltage": ["voltage", "volt"],
            "current": ["current", "amp"],
            "temperature": ["temperature", "temp"],
            "cost": ["cost", "price", "bill"]
        }
        
        for metric, keywords in metric_patterns.items():
            if any(keyword in message_lower for keyword in keywords):
                entities["metric"] = metric
                break
        
        return entities
    
    async def generate_response(self, 
                              message: str, 
                              context: ConversationContext,
                              ems_data: Dict[str, Any] = None) -> AIResponse:
        """Generate intelligent response using LLM and EMS knowledge"""
        
        # Classify intent and extract entities
        intent = self.classify_intent(message)
        entities = self.extract_entities(message)
        
        # Search knowledge base
        relevant_knowledge = self.knowledge_base.search_knowledge(message)
        
        # Prepare context for LLM
        system_prompt = self._build_system_prompt(intent, entities, relevant_knowledge, ems_data)
        
        # Generate response using LLM
        if self.llm:
            response_text = await self._generate_llm_response(system_prompt, message, context)
        elif self.local_llm:
            response_text = self._generate_local_response(message, context)
        else:
            response_text = self._generate_template_response(intent, entities, ems_data)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(intent, entities)
        
        # Perform data analysis if relevant
        data_analysis = None
        if ems_data and intent in ["power_analysis", "voltage_analysis", "trend_analysis"]:
            data_analysis = self._analyze_ems_data(ems_data, intent, entities)
        
        return AIResponse(
            response_text=response_text,
            confidence=0.85 if self.llm else 0.7,
            intent=intent,
            entities=entities,
            suggestions=suggestions,
            data_analysis=data_analysis
        )
    
    def _build_system_prompt(self, 
                           intent: str, 
                           entities: Dict[str, Any],
                           knowledge: List[Dict[str, Any]],
                           ems_data: Dict[str, Any] = None) -> str:
        """Build system prompt for LLM"""
        
        base_prompt = """You are an expert Energy Management System (EMS) AI assistant. 
        You help users understand their energy consumption, analyze electrical data, 
        detect anomalies, and optimize energy efficiency.
        
        Key capabilities:
        - Analyze power consumption, voltage, current, and other electrical parameters
        - Detect anomalies and power quality issues
        - Provide energy efficiency recommendations
        - Explain electrical concepts in simple terms
        - Calculate costs and savings
        
        Always provide accurate, helpful, and actionable information.
        """
        
        # Add relevant knowledge
        if knowledge:
            knowledge_text = "\n".join([f"- {item['content']}" for item in knowledge])
            base_prompt += f"\n\nRelevant knowledge:\n{knowledge_text}"
        
        # Add current data context
        if ems_data:
            data_summary = self._summarize_ems_data(ems_data)
            base_prompt += f"\n\nCurrent system data:\n{data_summary}"
        
        return base_prompt
    
    async def _generate_llm_response(self, 
                                   system_prompt: str, 
                                   message: str,
                                   context: ConversationContext) -> str:
        """Generate response using LangChain LLM"""
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=message)
            ]
            
            # Add conversation history
            for msg in context.conversation_history[-5:]:  # Last 5 messages
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))
            
            response = await self.llm.agenerate([messages])
            return response.generations[0][0].text.strip()
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return "I apologize, but I'm having trouble processing your request right now."
    
    def _generate_local_response(self, message: str, context: ConversationContext) -> str:
        """Generate response using local LLM"""
        try:
            # Simple local generation
            response = self.local_llm(message, max_length=150, do_sample=True)
            return response[0]['generated_text'][len(message):].strip()
        except Exception as e:
            logger.error(f"Local LLM generation failed: {e}")
            return self._generate_template_response("general_inquiry", {}, None)
    
    def _generate_template_response(self, 
                                  intent: str, 
                                  entities: Dict[str, Any],
                                  ems_data: Dict[str, Any] = None) -> str:
        """Generate template-based response as fallback"""
        
        templates = {
            "power_analysis": "Based on your energy data, I can help analyze power consumption patterns and identify optimization opportunities.",
            "voltage_analysis": "I can analyze voltage levels and power quality to ensure your electrical system is operating efficiently.",
            "anomaly_detection": "Let me check for any anomalies or unusual patterns in your energy system data.",
            "efficiency_optimization": "I can provide recommendations to improve your energy efficiency and reduce consumption.",
            "cost_analysis": "I'll help you understand your energy costs and identify potential savings opportunities.",
            "trend_analysis": "I can analyze historical trends in your energy usage to identify patterns and predict future consumption.",
            "system_status": "Let me check the current status and health of your energy management system.",
            "recommendations": "Based on your data, I can provide specific recommendations to optimize your energy usage."
        }
        
        base_response = templates.get(intent, "I'm here to help you with your energy management questions.")
        
        # Add data-specific information if available
        if ems_data:
            if "voltage" in ems_data:
                base_response += f" Current voltage reading: {ems_data['voltage']:.1f}V."
            if "power" in ems_data:
                base_response += f" Current power consumption: {ems_data['power']:.1f}W."
        
        return base_response
    
    def _generate_suggestions(self, intent: str, entities: Dict[str, Any]) -> List[str]:
        """Generate contextual suggestions"""
        
        suggestion_map = {
            "power_analysis": [
                "Show me peak demand hours",
                "What's my average daily consumption?",
                "Compare this month to last month"
            ],
            "voltage_analysis": [
                "Check for voltage irregularities", 
                "Show voltage trends over time",
                "Analyze power factor performance"
            ],
            "anomaly_detection": [
                "Run full system diagnostic",
                "Check for power quality issues",
                "Show recent alerts"
            ],
            "efficiency_optimization": [
                "Suggest energy saving measures",
                "Optimize power factor",
                "Identify inefficient equipment"
            ]
        }
        
        return suggestion_map.get(intent, [
            "Check system status",
            "Show energy summary", 
            "Analyze recent trends"
        ])
    
    def _analyze_ems_data(self, 
                         ems_data: Dict[str, Any], 
                         intent: str,
                         entities: Dict[str, Any]) -> Dict[str, Any]:
        """Perform data analysis based on intent"""
        
        analysis = {}
        
        if "voltage" in ems_data:
            voltage = ems_data["voltage"]
            analysis["voltage_status"] = (
                "normal" if 220 <= voltage <= 240 else
                "high" if voltage > 240 else "low"
            )
        
        if "power" in ems_data:
            power = ems_data["power"]
            analysis["power_level"] = (
                "high" if power > 1500 else
                "medium" if power > 500 else "low"
            )
        
        if "power_factor" in ems_data:
            pf = ems_data["power_factor"]
            analysis["power_factor_status"] = (
                "excellent" if pf > 0.95 else
                "good" if pf > 0.85 else
                "needs_improvement" if pf > 0.7 else "poor"
            )
        
        return analysis
    
    def _summarize_ems_data(self, ems_data: Dict[str, Any]) -> str:
        """Create summary of EMS data for context"""
        summary_parts = []
        
        if "voltage" in ems_data:
            summary_parts.append(f"Voltage: {ems_data['voltage']:.1f}V")
        if "current" in ems_data:
            summary_parts.append(f"Current: {ems_data['current']:.1f}A")
        if "power" in ems_data:
            summary_parts.append(f"Power: {ems_data['power']:.1f}W")
        if "power_factor" in ems_data:
            summary_parts.append(f"Power Factor: {ems_data['power_factor']:.2f}")
        
        return ", ".join(summary_parts) if summary_parts else "No current data available"
    
    def update_conversation(self, 
                          session_id: str,
                          user_message: str, 
                          ai_response: str,
                          user_id: str = "default") -> ConversationContext:
        """Update conversation context"""
        
        if session_id not in self.conversations:
            self.conversations[session_id] = ConversationContext(
                session_id=session_id,
                user_id=user_id,
                conversation_history=[],
                context_data={},
                last_updated=datetime.now()
            )
        
        context = self.conversations[session_id]
        context.conversation_history.extend([
            {"role": "user", "content": user_message, "timestamp": datetime.now().isoformat()},
            {"role": "assistant", "content": ai_response, "timestamp": datetime.now().isoformat()}
        ])
        
        # Keep only last 20 messages
        context.conversation_history = context.conversation_history[-20:]
        context.last_updated = datetime.now()
        
        return context


class LLMIntegrationService(BaseService):
    """Advanced LLM Integration Service for EMS"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("llm_integration", config)
        self.app = self._create_fastapi_app()
        self.conversational_ai = ConversationalAI(config)
        
    async def initialize(self):
        """Initialize LLM integration service"""
        await super().initialize()
        await self.conversational_ai.initialize()
        logger.info("LLM integration service initialized")
    
    def _create_fastapi_app(self) -> FastAPI:
        """Create FastAPI application"""
        app = FastAPI(
            title="EMS LLM Integration Service",
            description="Advanced AI and LLM integration for EMS",
            version="1.0.0"
        )
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._add_routes(app)
        return app
    
    def _add_routes(self, app: FastAPI):
        """Add FastAPI routes"""
        
        @app.get("/health")
        async def health_check():
            return await self.health_check()
        
        @app.post("/chat")
        async def chat_endpoint(request: Dict[str, Any]):
            """Main chat endpoint for conversational AI"""
            try:
                message = request.get("message", "")
                session_id = request.get("session_id", "default")
                user_id = request.get("user_id", "default")
                ems_data = request.get("ems_data", {})
                
                # Get or create conversation context
                context = self.conversational_ai.conversations.get(
                    session_id,
                    ConversationContext(
                        session_id=session_id,
                        user_id=user_id,
                        conversation_history=[],
                        context_data={},
                        last_updated=datetime.now()
                    )
                )
                
                # Generate AI response
                ai_response = await self.conversational_ai.generate_response(
                    message, context, ems_data
                )
                
                # Update conversation
                updated_context = self.conversational_ai.update_conversation(
                    session_id, message, ai_response.response_text, user_id
                )
                
                return {
                    "response": asdict(ai_response),
                    "session_id": session_id,
                    "context_updated": True
                }
                
            except Exception as e:
                logger.error(f"Chat endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/analyze")
        async def analyze_endpoint(request: Dict[str, Any]):
            """Advanced data analysis with AI insights"""
            try:
                data = request.get("data", {})
                analysis_type = request.get("analysis_type", "general")
                
                # Perform AI-powered analysis
                insights = await self._perform_ai_analysis(data, analysis_type)
                
                return {"insights": insights, "analysis_type": analysis_type}
                
            except Exception as e:
                logger.error(f"Analysis endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/knowledge")
        async def knowledge_search(query: str, limit: int = 5):
            """Search EMS knowledge base"""
            try:
                results = self.conversational_ai.knowledge_base.search_knowledge(query, limit)
                return {"query": query, "results": results}
                
            except Exception as e:
                logger.error(f"Knowledge search error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _perform_ai_analysis(self, data: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """Perform AI-powered data analysis"""
        
        insights = {
            "summary": "AI analysis completed",
            "patterns": [],
            "recommendations": [],
            "confidence": 0.8
        }
        
        # Analyze based on type
        if analysis_type == "power_efficiency":
            if "power_factor" in data:
                pf = data["power_factor"]
                if pf < 0.85:
                    insights["recommendations"].append(
                        "Consider power factor correction to improve efficiency"
                    )
            
            if "power" in data and "voltage" in data:
                current = data["power"] / data["voltage"]
                if current > 15:
                    insights["recommendations"].append(
                        "High current detected - check for overloaded circuits"
                    )
        
        elif analysis_type == "anomaly_detection":
            # Simple statistical anomaly detection
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    if abs(value) > 1000:  # Simple threshold
                        insights["patterns"].append(f"Unusual {key} value: {value}")
        
        return insights
    
    async def health_check(self):
        """Service-specific health check"""
        try:
            status = {
                "status": "healthy",
                "service": self.service_name,
                "llm_available": self.conversational_ai.llm is not None,
                "local_llm_available": self.conversational_ai.local_llm is not None,
                "active_conversations": len(self.conversational_ai.conversations)
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise Exception(f"LLM integration service unhealthy: {e}")
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process service-specific requests"""
        request_type = request_data.get('type')
        
        if request_type == 'chat':
            return await self.chat_endpoint(request_data)
        elif request_type == 'analyze':
            return await self.analyze_endpoint(request_data)
        else:
            raise ValueError(f"Unknown request type: {request_type}")


def create_llm_integration_service(config: Dict[str, Any] = None) -> LLMIntegrationService:
    """Create and configure LLM integration service"""
    if config is None:
        config = {
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "model_name": "gpt-3.5-turbo",
            "max_tokens": 1000,
            "temperature": 0.7
        }
    
    return LLMIntegrationService(config)


# Example usage and testing
if __name__ == "__main__":
    import uvicorn
    
    # Create service
    config = {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "model_name": "gpt-3.5-turbo"
    }
    
    service = create_llm_integration_service(config)
    
    # Run FastAPI app
    uvicorn.run(service.app, host="0.0.0.0", port=8010)
