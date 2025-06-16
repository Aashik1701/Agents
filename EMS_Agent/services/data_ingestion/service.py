#!/usr/bin/env python3
"""
Data Ingestion Service for EMS
Handles data loading, validation, and real-time data streaming
"""

import asyncio
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from common.base_service import BaseService
from common.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class DataValidationError(Exception):
    """Custom exception for data validation errors"""
    pass


class DataIngestionService(BaseService):
    """Data ingestion service for EMS data"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("data_ingestion", config)
        self.collections = {}
        self.validation_rules = self._get_validation_rules()
        self.batch_size = config.get('batch_size', 1000)
        self.app = self._create_fastapi_app()
    
    async def initialize(self):
        """Initialize data ingestion service"""
        await super().initialize()
        
        # Initialize database collections
        if self.db_client:
            db = self.db_client[self.config['mongodb']['database']]
            self.collections = {
                'raw_data': db.ems_raw_data,
                'processed_data': db.ems_processed_data,
                'validation_errors': db.ems_validation_errors,
                'ingestion_logs': db.ems_ingestion_logs
            }
        
        # Create indexes for performance
        await self._create_indexes()
    
    def _create_fastapi_app(self) -> FastAPI:
        """Create FastAPI application"""
        app = FastAPI(
            title="EMS Data Ingestion Service",
            description="Data ingestion and validation service for EMS",
            version="1.0.0"
        )
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add routes
        self._add_routes(app)
        
        return app
    
    def _add_routes(self, app: FastAPI):
        """Add FastAPI routes"""
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return self.get_health_status()
        
        @app.post("/ingest/excel")
        async def ingest_excel_data(
            file_path: str,
            background_tasks: BackgroundTasks
        ):
            """Ingest data from Excel file"""
            background_tasks.add_task(self.process_excel_file, file_path)
            return {"message": "Excel file processing started", "file_path": file_path}
        
        @app.post("/ingest/realtime")
        async def ingest_realtime_data(data: Dict[str, Any]):
            """Ingest real-time data"""
            try:
                result = await self.process_realtime_data(data)
                return {"success": True, "result": result}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @app.get("/stats")
        async def get_ingestion_stats():
            """Get ingestion statistics"""
            return await self.get_ingestion_statistics()
        
        @app.post("/validate")
        async def validate_data(data: List[Dict[str, Any]]):
            """Validate data without ingesting"""
            try:
                validation_results = await self.validate_data_batch(data)
                return {"validation_results": validation_results}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
    
    def _get_validation_rules(self) -> Dict[str, Any]:
        """Define data validation rules"""
        return {
            'required_fields': [
                'timestamp', 'equipment_id', 'voltage', 'current', 'power_factor'
            ],
            'field_types': {
                'timestamp': 'datetime',
                'equipment_id': 'string',
                'voltage': 'float',
                'current': 'float',
                'power_factor': 'float',
                'temperature': 'float',
                'cfm': 'float'
            },
            'field_ranges': {
                'voltage': (0, 1000),
                'current': (0, 1000),
                'power_factor': (0, 1),
                'temperature': (-50, 200),
                'cfm': (0, 10000)
            },
            'equipment_id_pattern': r'^[A-Z]{2,3}\d{4,5}$'
        }
    
    async def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            # Create indexes on commonly queried fields
            await asyncio.to_thread(
                self.collections['raw_data'].create_index,
                [("timestamp", 1), ("equipment_id", 1)]
            )
            await asyncio.to_thread(
                self.collections['raw_data'].create_index,
                [("equipment_id", 1)]
            )
            await asyncio.to_thread(
                self.collections['processed_data'].create_index,
                [("timestamp", 1), ("equipment_id", 1)]
            )
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    async def process_excel_file(self, file_path: str) -> Dict[str, Any]:
        """Process Excel file with batch processing"""
        try:
            logger.info(f"Starting Excel file processing: {file_path}")
            
            # Load Excel file
            df = await asyncio.to_thread(pd.read_excel, file_path)
            
            # Log ingestion start
            ingestion_log = {
                'type': 'excel_ingestion',
                'file_path': file_path,
                'total_rows': len(df),
                'start_time': datetime.now(),
                'status': 'processing'
            }
            
            await asyncio.to_thread(
                self.collections['ingestion_logs'].insert_one,
                ingestion_log
            )
            
            # Process data in batches
            processed_count = 0
            error_count = 0
            
            for i in range(0, len(df), self.batch_size):
                batch = df.iloc[i:i + self.batch_size]
                batch_result = await self.process_data_batch(batch.to_dict('records'))
                
                processed_count += batch_result['processed']
                error_count += batch_result['errors']
                
                # Update progress in cache
                if self.redis_client:
                    progress = {
                        'processed': processed_count,
                        'total': len(df),
                        'errors': error_count,
                        'percentage': (processed_count / len(df)) * 100
                    }
                    await self.redis_client.setex(
                        f"ingestion_progress:{file_path}",
                        3600,  # 1 hour TTL
                        json.dumps(progress)
                    )
            
            # Update ingestion log
            await asyncio.to_thread(
                self.collections['ingestion_logs'].update_one,
                {'file_path': file_path, 'start_time': ingestion_log['start_time']},
                {
                    '$set': {
                        'end_time': datetime.now(),
                        'status': 'completed',
                        'processed_count': processed_count,
                        'error_count': error_count
                    }
                }
            )
            
            # Trigger analytics service to process new data
            await self.call_service(
                'analytics',
                '/analyze/new_data',
                {'source': 'excel', 'count': processed_count}
            )
            
            logger.info(f"Excel processing completed: {processed_count} processed, {error_count} errors")
            
            return {
                'success': True,
                'processed': processed_count,
                'errors': error_count,
                'file_path': file_path
            }
            
        except Exception as e:
            logger.error(f"Error processing Excel file: {e}")
            
            # Update ingestion log with error
            await asyncio.to_thread(
                self.collections['ingestion_logs'].update_one,
                {'file_path': file_path},
                {
                    '$set': {
                        'end_time': datetime.now(),
                        'status': 'failed',
                        'error_message': str(e)
                    }
                }
            )
            
            raise
    
    async def process_data_batch(self, data_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a batch of data records"""
        processed_records = []
        error_records = []
        
        for record in data_batch:
            try:
                # Validate record
                validated_record = await self.validate_record(record)
                
                # Enrich record with metadata
                enriched_record = await self.enrich_record(validated_record)
                
                processed_records.append(enriched_record)
                
            except DataValidationError as e:
                error_record = {
                    'original_record': record,
                    'error_message': str(e),
                    'error_type': 'validation_error',
                    'timestamp': datetime.now()
                }
                error_records.append(error_record)
                
            except Exception as e:
                error_record = {
                    'original_record': record,
                    'error_message': str(e),
                    'error_type': 'processing_error',
                    'timestamp': datetime.now()
                }
                error_records.append(error_record)
        
        # Insert processed records
        if processed_records:
            await asyncio.to_thread(
                self.collections['raw_data'].insert_many,
                processed_records
            )
        
        # Insert error records
        if error_records:
            await asyncio.to_thread(
                self.collections['validation_errors'].insert_many,
                error_records
            )
        
        return {
            'processed': len(processed_records),
            'errors': len(error_records)
        }
    
    async def validate_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single data record"""
        # Check required fields
        for field in self.validation_rules['required_fields']:
            if field not in record or record[field] is None:
                raise DataValidationError(f"Missing required field: {field}")
        
        # Validate field types and ranges
        for field, expected_type in self.validation_rules['field_types'].items():
            if field in record and record[field] is not None:
                value = record[field]
                
                # Type validation
                if expected_type == 'datetime':
                    if not isinstance(value, datetime):
                        try:
                            record[field] = pd.to_datetime(value)
                        except:
                            raise DataValidationError(f"Invalid datetime format for {field}: {value}")
                
                elif expected_type == 'float':
                    try:
                        record[field] = float(value)
                    except:
                        raise DataValidationError(f"Invalid float value for {field}: {value}")
                
                elif expected_type == 'string':
                    record[field] = str(value)
                
                # Range validation
                if field in self.validation_rules['field_ranges']:
                    min_val, max_val = self.validation_rules['field_ranges'][field]
                    if not (min_val <= record[field] <= max_val):
                        raise DataValidationError(
                            f"Value out of range for {field}: {record[field]} (expected {min_val}-{max_val})"
                        )
        
        # Equipment ID pattern validation
        if 'equipment_id' in record:
            import re
            pattern = self.validation_rules['equipment_id_pattern']
            if not re.match(pattern, record['equipment_id']):
                raise DataValidationError(f"Invalid equipment ID format: {record['equipment_id']}")
        
        return record
    
    async def enrich_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich record with additional metadata"""
        # Add ingestion timestamp
        record['ingestion_timestamp'] = datetime.now()
        
        # Add data quality score
        record['quality_score'] = await self.calculate_quality_score(record)
        
        # Add equipment metadata if available
        equipment_metadata = await self.get_equipment_metadata(record.get('equipment_id'))
        if equipment_metadata:
            record['equipment_metadata'] = equipment_metadata
        
        return record
    
    async def calculate_quality_score(self, record: Dict[str, Any]) -> float:
        """Calculate data quality score (0-1)"""
        score = 1.0
        
        # Penalize for missing optional fields
        optional_fields = ['temperature', 'cfm']
        for field in optional_fields:
            if field not in record or record[field] is None:
                score -= 0.1
        
        # Check for suspicious values
        if 'power_factor' in record and record['power_factor'] > 1:
            score -= 0.2
        
        if 'current' in record and record['current'] == 0 and 'voltage' in record and record['voltage'] > 0:
            score -= 0.3  # Equipment should draw current if voltage is present
        
        return max(0.0, score)
    
    async def get_equipment_metadata(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """Get equipment metadata from cache or database"""
        if not equipment_id or not self.redis_client:
            return None
        
        # Check cache first
        cached_metadata = await self.redis_client.get(f"equipment_metadata:{equipment_id}")
        if cached_metadata:
            return json.loads(cached_metadata)
        
        # If not in cache, this would typically query an equipment database
        # For now, return basic metadata based on equipment ID pattern
        metadata = {
            'type': 'compressor' if equipment_id.startswith('IKC') else 'unknown',
            'category': 'hvac',
            'last_maintenance': None
        }
        
        # Cache for future use
        await self.redis_client.setex(
            f"equipment_metadata:{equipment_id}",
            3600,  # 1 hour TTL
            json.dumps(metadata)
        )
        
        return metadata
    
    async def process_realtime_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process real-time data"""
        try:
            # Validate and enrich
            validated_data = await self.validate_record(data)
            enriched_data = await self.enrich_record(validated_data)
            
            # Insert into database
            await asyncio.to_thread(
                self.collections['raw_data'].insert_one,
                enriched_data
            )
            
            # Publish to real-time analytics
            if self.redis_client:
                await self.redis_client.publish(
                    'realtime_data',
                    json.dumps(enriched_data, default=str)
                )
            
            return {'success': True, 'record_id': str(enriched_data['_id'])}
            
        except Exception as e:
            logger.error(f"Error processing real-time data: {e}")
            raise
    
    async def get_ingestion_statistics(self) -> Dict[str, Any]:
        """Get ingestion statistics"""
        try:
            # Get counts from collections
            raw_count = await asyncio.to_thread(self.collections['raw_data'].count_documents, {})
            error_count = await asyncio.to_thread(self.collections['validation_errors'].count_documents, {})
            
            # Get recent ingestion logs
            recent_logs = await asyncio.to_thread(
                self.collections['ingestion_logs'].find,
                {},
                {'_id': 0, 'type': 1, 'status': 1, 'processed_count': 1, 'error_count': 1, 'start_time': 1}
            )
            recent_logs = list(recent_logs)
            
            return {
                'total_records': raw_count,
                'total_errors': error_count,
                'recent_ingestions': recent_logs,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting ingestion statistics: {e}")
            return {'error': str(e)}
    
    async def validate_data_batch(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate a batch of data without ingesting"""
        results = []
        
        for i, record in enumerate(data):
            try:
                await self.validate_record(record)
                results.append({
                    'index': i,
                    'status': 'valid',
                    'record': record
                })
            except DataValidationError as e:
                results.append({
                    'index': i,
                    'status': 'invalid',
                    'error': str(e),
                    'record': record
                })
        
        return results
    
    async def health_check(self):
        """Service-specific health check"""
        # Check if we can write to database
        test_record = {
            'test': True,
            'timestamp': datetime.now(),
            'service': self.service_name
        }
        
        await asyncio.to_thread(
            self.collections['raw_data'].insert_one,
            test_record
        )
        
        # Clean up test record
        await asyncio.to_thread(
            self.collections['raw_data'].delete_one,
            {'_id': test_record['_id']}
        )
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process service-specific requests"""
        request_type = request_data.get('type')
        
        if request_type == 'ingest_excel':
            return await self.process_excel_file(request_data['file_path'])
        elif request_type == 'ingest_realtime':
            return await self.process_realtime_data(request_data['data'])
        elif request_type == 'validate':
            return await self.validate_data_batch(request_data['data'])
        else:
            raise ValueError(f"Unknown request type: {request_type}")


def create_data_ingestion_service():
    """Factory function to create data ingestion service"""
    config_manager = ConfigManager("data_ingestion")
    config = config_manager.get_all_config()
    
    return DataIngestionService(config)


async def run_service():
    """Run the data ingestion service"""
    service = create_data_ingestion_service()
    await service.initialize()
    
    # Run FastAPI app
    config = uvicorn.Config(
        service.app,
        host="0.0.0.0",
        port=service.config.get('port', 8001),
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    finally:
        await service.shutdown()


if __name__ == "__main__":
    asyncio.run(run_service())
