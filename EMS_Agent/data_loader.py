#!/usr/bin/env python3
"""
EMS Data Loader and MongoDB Uploader
Loads energy meter data from Excel and uploads to MongoDB Atlas
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import json
from config import MONGODB_URI, MONGODB_DATABASE

class EMSDataLoader:
    def __init__(self):
        """Initialize EMS Data Loader"""
        self.client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
        self.db = self.client[MONGODB_DATABASE]
        
        # Collections for different types of data
        self.collections = {
            'raw_data': self.db.ems_raw_data,
            'hourly_aggregates': self.db.ems_hourly_aggregates,
            'daily_aggregates': self.db.ems_daily_aggregates,
            'anomalies': self.db.ems_anomalies,
            'predictions': self.db.ems_predictions
        }
    
    def load_excel_data(self, file_path):
        """Load data from Excel file"""
        try:
            print(f"📊 Loading EMS data from {file_path}...")
            
            # Read Excel file
            df = pd.read_excel(file_path)
            
            print(f"✅ Loaded {len(df)} rows of data")
            print(f"📋 Columns: {list(df.columns)}")
            
            # Display sample data
            print(f"\n📝 Sample data:")
            print(df.head())
            
            return df
            
        except Exception as e:
            print(f"❌ Error loading Excel data: {e}")
            return None
    
    def clean_and_process_data(self, df):
        """Clean and process the energy data"""
        try:
            print("\n🧹 Cleaning and processing data...")
            
            # Standardize column names
            df.columns = df.columns.str.lower().str.replace(' ', '_')
            
            # If there's no timestamp column, create one
            if 'timestamp' not in df.columns and 'time' not in df.columns:
                # Create timestamps starting from now, going back in time
                end_time = datetime.now()
                start_time = end_time - timedelta(minutes=len(df))
                timestamps = pd.date_range(start=start_time, end=end_time, periods=len(df))
                df['timestamp'] = timestamps
            
            # Ensure we have the required energy columns
            expected_columns = ['voltage', 'current', 'power_factor', 'active_power', 'reactive_power']
            
            # Map common column variations
            column_mappings = {
                'v': 'voltage',
                'volt': 'voltage',
                'voltage(v)': 'voltage',
                'i': 'current',
                'amp': 'current',
                'current(a)': 'current',
                'pf': 'power_factor',
                'power_factor(pf)': 'power_factor',
                'p': 'active_power',
                'active_power(w)': 'active_power',
                'q': 'reactive_power',
                'reactive_power(var)': 'reactive_power'
            }
            
            # Apply mappings
            for old_name, new_name in column_mappings.items():
                if old_name in df.columns:
                    df.rename(columns={old_name: new_name}, inplace=True)
            
            # Fill missing energy columns with synthetic data if needed
            if 'voltage' not in df.columns:
                df['voltage'] = np.random.normal(230, 5, len(df))  # 230V ±5V
            
            if 'current' not in df.columns:
                df['current'] = np.random.normal(10, 2, len(df))  # 10A ±2A
            
            if 'power_factor' not in df.columns:
                df['power_factor'] = np.random.normal(0.95, 0.05, len(df))  # 0.95 ±0.05
            
            if 'active_power' not in df.columns:
                df['active_power'] = df['voltage'] * df['current'] * df['power_factor']
            
            if 'reactive_power' not in df.columns:
                df['reactive_power'] = df['active_power'] * np.tan(np.arccos(df['power_factor']))
            
            # Calculate additional metrics
            df['apparent_power'] = df['voltage'] * df['current']
            df['energy_consumed'] = df['active_power'] / 60  # Wh per minute
            df['load_factor'] = df['active_power'] / df['apparent_power']
            
            # Add quality indicators
            df['voltage_quality'] = np.where(
                (df['voltage'] >= 220) & (df['voltage'] <= 240), 'Good',
                np.where((df['voltage'] >= 200) & (df['voltage'] <= 250), 'Acceptable', 'Poor')
            )
            
            df['pf_quality'] = np.where(
                df['power_factor'] >= 0.9, 'Excellent',
                np.where(df['power_factor'] >= 0.8, 'Good', 'Poor')
            )
            
            print(f"✅ Data processed successfully")
            print(f"📊 Final columns: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error processing data: {e}")
            return None
    
    def detect_anomalies(self, df):
        """Detect anomalies in the energy data"""
        anomalies = []
        
        try:
            print("\n🚨 Detecting anomalies...")
            
            # Voltage anomalies (outside ±10% of nominal 230V)
            voltage_anomalies = df[
                (df['voltage'] < 207) | (df['voltage'] > 253)
            ]
            
            for _, row in voltage_anomalies.iterrows():
                anomalies.append({
                    'timestamp': row['timestamp'],
                    'type': 'voltage_anomaly',
                    'severity': 'high' if abs(row['voltage'] - 230) > 30 else 'medium',
                    'value': row['voltage'],
                    'threshold': '207-253V',
                    'description': f"Voltage {row['voltage']:.2f}V outside normal range"
                })
            
            # Current spikes (above 15A)
            current_spikes = df[df['current'] > 15]
            for _, row in current_spikes.iterrows():
                anomalies.append({
                    'timestamp': row['timestamp'],
                    'type': 'current_spike',
                    'severity': 'high' if row['current'] > 20 else 'medium',
                    'value': row['current'],
                    'threshold': '15A',
                    'description': f"Current spike {row['current']:.2f}A"
                })
            
            # Poor power factor (below 0.8)
            pf_anomalies = df[df['power_factor'] < 0.8]
            for _, row in pf_anomalies.iterrows():
                anomalies.append({
                    'timestamp': row['timestamp'],
                    'type': 'poor_power_factor',
                    'severity': 'medium' if row['power_factor'] < 0.7 else 'low',
                    'value': row['power_factor'],
                    'threshold': '0.8',
                    'description': f"Low power factor {row['power_factor']:.3f}"
                })
            
            print(f"🚨 Found {len(anomalies)} anomalies")
            return anomalies
            
        except Exception as e:
            print(f"❌ Error detecting anomalies: {e}")
            return []
    
    def create_aggregates(self, df):
        """Create hourly and daily aggregates"""
        try:
            print("\n📈 Creating aggregates...")
            
            # Ensure timestamp is datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Hourly aggregates
            hourly = df.resample('H').agg({
                'voltage': ['mean', 'min', 'max', 'std'],
                'current': ['mean', 'min', 'max', 'std'],
                'power_factor': ['mean', 'min', 'max'],
                'active_power': ['mean', 'sum'],
                'reactive_power': ['mean', 'sum'],
                'energy_consumed': 'sum'
            }).reset_index()
            
            # Flatten column names
            hourly.columns = ['_'.join(col).strip() if col[1] else col[0] for col in hourly.columns]
            hourly.rename(columns={'timestamp_': 'timestamp'}, inplace=True)
            
            # Daily aggregates
            daily = df.resample('D').agg({
                'voltage': ['mean', 'min', 'max', 'std'],
                'current': ['mean', 'min', 'max', 'std'],
                'power_factor': ['mean', 'min', 'max'],
                'active_power': ['mean', 'sum'],
                'reactive_power': ['mean', 'sum'],
                'energy_consumed': 'sum'
            }).reset_index()
            
            # Flatten column names
            daily.columns = ['_'.join(col).strip() if col[1] else col[0] for col in daily.columns]
            daily.rename(columns={'timestamp_': 'timestamp'}, inplace=True)
            
            print(f"✅ Created {len(hourly)} hourly and {len(daily)} daily aggregates")
            
            return hourly, daily
            
        except Exception as e:
            print(f"❌ Error creating aggregates: {e}")
            return None, None
    
    def upload_to_mongodb(self, df, anomalies, hourly_df, daily_df):
        """Upload all data to MongoDB"""
        try:
            print("\n📤 Uploading data to MongoDB...")
            
            # Clear existing data
            for collection in self.collections.values():
                collection.delete_many({})
            
            # Upload raw data
            raw_data = df.reset_index().to_dict('records')
            # Convert numpy types to Python types for JSON serialization
            for record in raw_data:
                for key, value in record.items():
                    if isinstance(value, (np.integer, np.floating)):
                        record[key] = float(value)
                    elif pd.isna(value):
                        record[key] = None
                    elif isinstance(value, pd.Timestamp):
                        record[key] = value.isoformat()
            
            self.collections['raw_data'].insert_many(raw_data)
            print(f"✅ Uploaded {len(raw_data)} raw data records")
            
            # Upload anomalies
            if anomalies:
                # Convert timestamps to ISO format
                for anomaly in anomalies:
                    if isinstance(anomaly['timestamp'], pd.Timestamp):
                        anomaly['timestamp'] = anomaly['timestamp'].isoformat()
                
                self.collections['anomalies'].insert_many(anomalies)
                print(f"✅ Uploaded {len(anomalies)} anomaly records")
            
            # Upload aggregates
            if hourly_df is not None:
                hourly_data = hourly_df.to_dict('records')
                for record in hourly_data:
                    for key, value in record.items():
                        if isinstance(value, (np.integer, np.floating)):
                            record[key] = float(value)
                        elif pd.isna(value):
                            record[key] = None
                        elif isinstance(value, pd.Timestamp):
                            record[key] = value.isoformat()
                
                self.collections['hourly_aggregates'].insert_many(hourly_data)
                print(f"✅ Uploaded {len(hourly_data)} hourly aggregate records")
            
            if daily_df is not None:
                daily_data = daily_df.to_dict('records')
                for record in daily_data:
                    for key, value in record.items():
                        if isinstance(value, (np.integer, np.floating)):
                            record[key] = float(value)
                        elif pd.isna(value):
                            record[key] = None
                        elif isinstance(value, pd.Timestamp):
                            record[key] = value.isoformat()
                
                self.collections['daily_aggregates'].insert_many(daily_data)
                print(f"✅ Uploaded {len(daily_data)} daily aggregate records")
            
            print("🎉 All data uploaded successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error uploading to MongoDB: {e}")
            return False
    
    def get_database_stats(self):
        """Get statistics about the uploaded data"""
        try:
            stats = {}
            
            for name, collection in self.collections.items():
                count = collection.count_documents({})
                stats[name] = count
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting database stats: {e}")
            return {}
    
    def process_and_upload(self, excel_file_path):
        """Main method to process Excel data and upload to MongoDB"""
        print("🚀 Starting EMS Data Processing and Upload")
        print("=" * 60)
        
        # Test connection first
        try:
            self.client.admin.command('ping')
            print("✅ Connected to MongoDB Atlas")
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            return False
        
        # Load data
        df = self.load_excel_data(excel_file_path)
        if df is None:
            return False
        
        # Process data
        df = self.clean_and_process_data(df)
        if df is None:
            return False
        
        # Detect anomalies
        anomalies = self.detect_anomalies(df)
        
        # Create aggregates
        hourly_df, daily_df = self.create_aggregates(df.copy())
        
        # Upload to MongoDB
        self.upload_to_mongodb(df, anomalies, hourly_df, daily_df)
        
        # Show stats
        stats = self.get_database_stats()
        print(f"\n📊 Database Statistics:")
        for collection_name, count in stats.items():
            print(f"   • {collection_name}: {count} documents")
        
        return True
    
    def load_and_process_all(self, excel_file_path):
        """
        Complete data loading pipeline for Flask app
        Returns a result dictionary with success status and stats
        """
        try:
            print(f"🚀 Starting complete data processing for {excel_file_path}")
            
            # Test MongoDB connection
            try:
                self.client.admin.command('ping')
                print("✅ Connected to MongoDB Atlas")
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Failed to connect to MongoDB: {str(e)}"
                }
            
            # Load data
            df = self.load_excel_data(excel_file_path)
            if df is None:
                return {
                    'success': False,
                    'error': "Failed to load Excel data"
                }
            
            # Process data
            df = self.clean_and_process_data(df)
            if df is None:
                return {
                    'success': False,
                    'error': "Failed to process data"
                }
            
            # Detect anomalies
            anomalies = self.detect_anomalies(df)
            
            # Create aggregates
            hourly_df, daily_df = self.create_aggregates(df.copy())
            
            # Upload to MongoDB
            upload_success = self.upload_to_mongodb(df, anomalies, hourly_df, daily_df)
            if not upload_success:
                return {
                    'success': False,
                    'error': "Failed to upload data to MongoDB"
                }
            
            # Get final stats
            stats = self.get_database_stats()
            
            return {
                'success': True,
                'stats': stats,
                'collections': list(self.collections.keys()),
                'message': 'Data processing completed successfully'
            }
            
        except Exception as e:
            print(f"❌ Error in load_and_process_all: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()

if __name__ == "__main__":
    loader = EMSDataLoader()
    
    # Process the Excel file
    excel_file = "EMS_Energy_Meter_Data.xlsx"
    success = loader.process_and_upload(excel_file)
    
    if success:
        print("\n🎉 EMS data processing completed successfully!")
        print("🚀 Ready to start the EMS Agent application!")
    else:
        print("\n❌ EMS data processing failed!")
    
    loader.close()
