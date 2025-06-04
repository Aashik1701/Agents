// Frontend types matching backend schemas

export interface User {
  id: number;
  email: string;
  full_name?: string;
  role: 'admin' | 'user' | 'viewer';
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface Equipment {
  id: number;
  name: string;
  equipment_type: 'compressor' | 'motor' | 'hvac' | 'pump' | 'other';
  status: 'online' | 'offline' | 'maintenance' | 'error';
  location?: string;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  rated_power?: number;
  rated_voltage?: number;
  rated_current?: number;
  rated_frequency?: number;
  installation_date?: string;
  description?: string;
  last_maintenance?: string;
  created_at: string;
  updated_at?: string;
}

export interface EquipmentWithStats extends Equipment {
  current_power?: number;
  energy_today?: number;
  uptime_percentage?: number;
  efficiency_score?: number;
  last_data_timestamp?: string;
}

export interface SensorData {
  id: number;
  equipment_id: number;
  timestamp: string;
  active_power?: number;
  reactive_power?: number;
  apparent_power?: number;
  power_factor?: number;
  voltage_a?: number;
  voltage_b?: number;
  voltage_c?: number;
  current_a?: number;
  current_b?: number;
  current_c?: number;
  frequency?: number;
  temperature?: number;
  humidity?: number;
  pressure?: number;
  energy_consumption?: number;
}

export interface Anomaly {
  id: number;
  equipment_id: number;
  anomaly_type: 'power_spike' | 'power_drop' | 'temperature_high' | 'temperature_low' | 'efficiency_drop' | 'zero_current' | 'other';
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'open' | 'investigating' | 'resolved' | 'false_positive';
  title: string;
  description: string;
  detected_at: string;
  resolved_at?: string;
  resolved_by?: number;
  resolution_notes?: string;
  metadata?: Record<string, any>;
}

export interface ChatSession {
  id: number;
  user_id: number;
  title: string;
  created_at: string;
  updated_at?: string;
}

export interface ChatMessage {
  id: number;
  session_id: number;
  role: 'user' | 'assistant';
  content: string;
  metadata?: Record<string, any>;
  timestamp: string;
}

export interface DashboardMetrics {
  total_equipment: number;
  online_equipment: number;
  offline_equipment: number;
  maintenance_equipment: number;
  error_equipment: number;
  total_energy_today: number;
  total_energy_month: number;
  active_anomalies: number;
  resolved_anomalies_today: number;
  average_efficiency: number;
  peak_demand_today: number;
  cost_savings_month: number;
  carbon_footprint_reduction: number;
}

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string;
    borderColor?: string;
    borderWidth?: number;
  }[];
}

export interface Report {
  id: number;
  title: string;
  report_type: 'energy_summary' | 'equipment_status' | 'anomaly_report' | 'maintenance_schedule' | 'custom';
  format: 'pdf' | 'csv' | 'excel';
  status: 'pending' | 'generating' | 'completed' | 'failed';
  created_by: number;
  created_at: string;
  completed_at?: string;
  file_path?: string;
  parameters?: Record<string, any>;
  error_message?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name?: string;
}

export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  error?: string;
}
