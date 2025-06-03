from typing import Dict, List, Any, Optional
import asyncio
import json
from datetime import datetime, timedelta
import structlog
from openai import AsyncOpenAI
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from app.core.config import settings
from app.services.data_service import data_service
from app.services.chart_generator import chart_generator
from app.services.report_generator import report_generator

logger = structlog.get_logger()


class AIAgent:
    """Main AI Agent for processing user queries and generating responses"""
    
    def __init__(self):
        self.openai_client: Optional[AsyncOpenAI] = None
        self.chroma_client = None
        self.collection = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.system_prompt = self._get_system_prompt()
        
    async def initialize(self):
        """Initialize AI services"""
        try:
            # Initialize OpenAI client
            if settings.OPENAI_API_KEY:
                self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized")
            else:
                logger.warning("OpenAI API key not provided")
            
            # Initialize ChromaDB
            self.chroma_client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT
            )
            
            # Get or create collection for knowledge base
            self.collection = self.chroma_client.get_or_create_collection(
                name="optibyte_knowledge",
                metadata={"description": "Optibyte energy management knowledge base"}
            )
            
            # Initialize knowledge base if empty
            await self._initialize_knowledge_base()
            
            logger.info("AI Agent initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize AI Agent", error=str(e))
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.openai_client:
            await self.openai_client.close()
        logger.info("AI Agent cleanup completed")
    
    async def process_message(self, message: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """Process user message and generate response"""
        start_time = datetime.now()
        
        try:
            # Detect intent
            intent = await self._detect_intent(message)
            
            # Get relevant context from knowledge base
            context = await self._get_relevant_context(message)
            
            # Process based on intent
            response_data = await self._process_intent(intent, message, context, user_id)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "type": "ai_response",
                "message": response_data.get("message", ""),
                "intent": intent,
                "data": response_data.get("data"),
                "charts": response_data.get("charts"),
                "recommendations": response_data.get("recommendations"),
                "processing_time": f"{processing_time:.0f}ms",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Error processing message", error=str(e), user_id=user_id)
            return {
                "type": "error",
                "message": "I apologize, but I encountered an error processing your request. Please try again.",
                "error": str(e) if settings.DEBUG else None,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _detect_intent(self, message: str) -> str:
        """Detect user intent from message"""
        if not self.openai_client:
            return "general_query"
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": """Classify the user's intent for an energy management system. 
                        Return only one of these intents:
                        - data_query: Asking for specific data, trends, or measurements
                        - anomaly_inquiry: Asking about problems, alerts, or abnormal readings
                        - equipment_status: Asking about specific equipment status or performance
                        - optimization: Asking for recommendations or improvements
                        - report_request: Asking to generate or view reports
                        - comparison: Comparing different equipment or time periods
                        - general_query: General questions or greetings"""
                    },
                    {"role": "user", "content": message}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            intent = response.choices[0].message.content.strip().lower()
            return intent if intent in [
                "data_query", "anomaly_inquiry", "equipment_status", 
                "optimization", "report_request", "comparison", "general_query"
            ] else "general_query"
            
        except Exception as e:
            logger.error("Error detecting intent", error=str(e))
            return "general_query"
    
    async def _get_relevant_context(self, query: str) -> List[str]:
        """Get relevant context from knowledge base"""
        if not self.collection:
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=5
            )
            
            return results.get("documents", [[]])[0]
            
        except Exception as e:
            logger.error("Error retrieving context", error=str(e))
            return []
    
    async def _process_intent(self, intent: str, message: str, context: List[str], user_id: str) -> Dict[str, Any]:
        """Process message based on detected intent"""
        
        if intent == "data_query":
            return await self._handle_data_query(message, context)
        elif intent == "anomaly_inquiry":
            return await self._handle_anomaly_inquiry(message)
        elif intent == "equipment_status":
            return await self._handle_equipment_status(message)
        elif intent == "optimization":
            return await self._handle_optimization_request(message)
        elif intent == "report_request":
            return await self._handle_report_request(message, user_id)
        elif intent == "comparison":
            return await self._handle_comparison_request(message)
        else:
            return await self._handle_general_query(message, context)
    
    async def _handle_data_query(self, message: str, context: List[str]) -> Dict[str, Any]:
        """Handle data-related queries"""
        # Extract equipment IDs and time ranges from message
        equipment_ids = self._extract_equipment_ids(message)
        time_range = self._extract_time_range(message)
        
        # Get data from database
        data = await data_service.get_sensor_data(equipment_ids, time_range)
        
        # Generate charts if data is available
        charts = []
        if data:
            charts = await chart_generator.generate_charts_for_data(data, message)
        
        # Generate AI response
        response_message = await self._generate_ai_response(message, context, {"data": data})
        
        return {
            "message": response_message,
            "data": data,
            "charts": charts
        }
    
    async def _handle_anomaly_inquiry(self, message: str) -> Dict[str, Any]:
        """Handle anomaly-related queries"""
        # Get recent anomalies
        anomalies = await data_service.get_recent_anomalies()
        
        response_message = await self._generate_ai_response(
            message, [], {"anomalies": anomalies}
        )
        
        return {
            "message": response_message,
            "data": {"anomalies": anomalies}
        }
    
    async def _handle_equipment_status(self, message: str) -> Dict[str, Any]:
        """Handle equipment status queries"""
        equipment_ids = self._extract_equipment_ids(message)
        
        # Get equipment status
        status_data = await data_service.get_equipment_status(equipment_ids)
        
        response_message = await self._generate_ai_response(
            message, [], {"equipment_status": status_data}
        )
        
        return {
            "message": response_message,
            "data": status_data
        }
    
    async def _handle_optimization_request(self, message: str) -> Dict[str, Any]:
        """Handle optimization and recommendation requests"""
        # Get optimization recommendations
        recommendations = await self._generate_recommendations()
        
        response_message = await self._generate_ai_response(
            message, [], {"recommendations": recommendations}
        )
        
        return {
            "message": response_message,
            "recommendations": recommendations
        }
    
    async def _handle_report_request(self, message: str, user_id: str) -> Dict[str, Any]:
        """Handle report generation requests"""
        report_type = self._extract_report_type(message)
        time_range = self._extract_time_range(message)
        
        # Generate report
        report = await report_generator.generate_report(report_type, time_range, user_id)
        
        response_message = f"I've generated a {report_type} report for {time_range}. You can download it using the link below."
        
        return {
            "message": response_message,
            "data": {"report": report}
        }
    
    async def _handle_comparison_request(self, message: str) -> Dict[str, Any]:
        """Handle comparison queries"""
        equipment_ids = self._extract_equipment_ids(message)
        time_range = self._extract_time_range(message)
        
        if len(equipment_ids) < 2:
            return {
                "message": "Please specify at least two equipment IDs for comparison.",
                "data": None
            }
        
        # Get comparison data
        comparison_data = await data_service.get_comparison_data(equipment_ids, time_range)
        
        # Generate comparison charts
        charts = await chart_generator.generate_comparison_charts(comparison_data)
        
        response_message = await self._generate_ai_response(
            message, [], {"comparison": comparison_data}
        )
        
        return {
            "message": response_message,
            "data": comparison_data,
            "charts": charts
        }
    
    async def _handle_general_query(self, message: str, context: List[str]) -> Dict[str, Any]:
        """Handle general queries and conversations"""
        response_message = await self._generate_ai_response(message, context, {})
        
        return {
            "message": response_message,
            "data": None
        }
    
    async def _generate_ai_response(self, message: str, context: List[str], data: Dict[str, Any]) -> str:
        """Generate AI response using OpenAI"""
        if not self.openai_client:
            return "I'm currently unable to process your request. Please check the AI service configuration."
        
        try:
            # Prepare context
            context_text = "\n".join(context) if context else ""
            data_text = json.dumps(data, default=str) if data else ""
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"""
                User Query: {message}
                
                Context: {context_text}
                
                Data: {data_text}
                
                Please provide a helpful, conversational response based on the query and available data.
                """}
            ]
            
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error("Error generating AI response", error=str(e))
            return "I apologize, but I'm having trouble generating a response right now. Please try again later."
    
    def _extract_equipment_ids(self, message: str) -> List[str]:
        """Extract equipment IDs from message"""
        import re
        # Look for patterns like IKC0073, IKC0076, etc.
        pattern = r'\b[A-Z]{2,3}\d{4,5}\b'
        return re.findall(pattern, message.upper())
    
    def _extract_time_range(self, message: str) -> Dict[str, Any]:
        """Extract time range from message"""
        # Simple time range extraction
        # In production, use more sophisticated NLP
        
        now = datetime.now()
        
        if "today" in message.lower():
            return {
                "start": now.replace(hour=0, minute=0, second=0, microsecond=0),
                "end": now
            }
        elif "yesterday" in message.lower():
            yesterday = now - timedelta(days=1)
            return {
                "start": yesterday.replace(hour=0, minute=0, second=0, microsecond=0),
                "end": yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
            }
        elif "week" in message.lower():
            return {
                "start": now - timedelta(days=7),
                "end": now
            }
        elif "month" in message.lower():
            return {
                "start": now - timedelta(days=30),
                "end": now
            }
        else:
            # Default to last 24 hours
            return {
                "start": now - timedelta(hours=24),
                "end": now
            }
    
    def _extract_report_type(self, message: str) -> str:
        """Extract report type from message"""
        message_lower = message.lower()
        
        if "daily" in message_lower:
            return "daily"
        elif "weekly" in message_lower:
            return "weekly"
        elif "monthly" in message_lower:
            return "monthly"
        elif "anomaly" in message_lower:
            return "anomaly"
        else:
            return "custom"
    
    async def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate optimization recommendations"""
        # This would analyze current data and generate recommendations
        # For now, return sample recommendations
        return [
            {
                "type": "energy_optimization",
                "title": "Optimize Load Scheduling",
                "description": "Consider rescheduling non-critical loads to off-peak hours to reduce energy costs by up to 15%.",
                "priority": "medium",
                "estimated_savings": "15%"
            },
            {
                "type": "maintenance",
                "title": "Power Factor Correction",
                "description": "Equipment IKC0076 shows declining power factor. Schedule maintenance to improve efficiency.",
                "priority": "high",
                "estimated_savings": "8%"
            }
        ]
    
    async def _initialize_knowledge_base(self):
        """Initialize knowledge base with Optibyte-specific information"""
        if not self.collection:
            return
        
        try:
            # Check if collection already has documents
            count = self.collection.count()
            if count > 0:
                logger.info(f"Knowledge base already initialized with {count} documents")
                return
            
            # Sample knowledge base entries
            knowledge_entries = [
                {
                    "id": "power_factor_info",
                    "content": "Power factor is a measure of electrical efficiency, ranging from 0 to 1. A higher power factor indicates more efficient use of electrical power. In the Optibyte system, power factor is measured for each equipment and should ideally be above 0.9 for optimal efficiency.",
                    "metadata": {"category": "electrical_measurements", "type": "definition"}
                },
                {
                    "id": "cfm_explanation",
                    "content": "CFM stands for Cubic Feet per Minute, a measure of air flow rate. In compressor systems, CFM indicates the volume of air being moved. Higher CFM values generally indicate better performance, but should be considered alongside power consumption for efficiency calculations.",
                    "metadata": {"category": "air_flow", "type": "definition"}
                },
                {
                    "id": "anomaly_types",
                    "content": "Common anomalies in energy management systems include: 1) Zero current detection - equipment showing no power draw despite being active, 2) Voltage spikes - sudden increases in voltage that may damage equipment, 3) High temperature - indicating potential overheating, 4) Low power factor - indicating inefficient power usage.",
                    "metadata": {"category": "anomalies", "type": "reference"}
                },
                {
                    "id": "equipment_types",
                    "content": "Optibyte monitors various equipment types: Compressors (IKC series) - Used for air compression and refrigeration, Motors - Drive various mechanical systems, Pumps - Move fluids through systems, HVAC units - Heating, ventilation, and air conditioning systems.",
                    "metadata": {"category": "equipment", "type": "reference"}
                }
            ]
            
            # Add documents to collection
            for entry in knowledge_entries:
                self.collection.add(
                    ids=[entry["id"]],
                    documents=[entry["content"]],
                    metadatas=[entry["metadata"]]
                )
            
            logger.info(f"Initialized knowledge base with {len(knowledge_entries)} entries")
            
        except Exception as e:
            logger.error("Error initializing knowledge base", error=str(e))
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI agent"""
        return """You are an AI assistant for the Optibyte energy management system. You help users understand their energy data, detect anomalies, and optimize energy usage.

Key capabilities:
- Analyze energy consumption data from various equipment
- Detect and explain anomalies in electrical measurements
- Provide optimization recommendations
- Generate reports and visualizations
- Answer questions about power factor, CFM, voltage, current, and other electrical parameters

Be conversational, helpful, and technical when appropriate. Always provide specific insights based on the data when available. If you don't have enough data to answer a question, suggest how the user might get the information they need.

For equipment references, use the full equipment ID (like IKC0073) when discussing specific equipment.

When discussing measurements:
- Power factor should ideally be > 0.9
- Zero current for active equipment indicates a problem
- Voltage spikes can damage equipment
- High temperatures may indicate overheating
- CFM measures air flow rate

Always prioritize safety and efficiency in your recommendations."""


# Global instance
ai_agent = AIAgent()
