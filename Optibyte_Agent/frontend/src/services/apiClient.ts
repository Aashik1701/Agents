import axios, { AxiosInstance } from 'axios';
import { AuthTokens, LoginCredentials, RegisterData } from '../types';

const BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private api: AxiosInstance;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    this.api = axios.create({
      baseURL: BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Load tokens from localStorage
    this.loadTokens();

    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      (config) => {
        if (this.accessToken) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle token refresh
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            await this.refreshAccessToken();
            originalRequest.headers.Authorization = `Bearer ${this.accessToken}`;
            return this.api(originalRequest);
          } catch (refreshError) {
            this.logout();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private loadTokens() {
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }

  private saveTokens(tokens: AuthTokens) {
    this.accessToken = tokens.access_token;
    this.refreshToken = tokens.refresh_token;
    localStorage.setItem('access_token', tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token);
  }

  private clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  // Authentication methods
  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    const response = await this.api.post('/auth/login', credentials);
    const tokens = response.data;
    this.saveTokens(tokens);
    return tokens;
  }

  async register(userData: RegisterData): Promise<AuthTokens> {
    const response = await this.api.post('/auth/register', userData);
    const tokens = response.data;
    this.saveTokens(tokens);
    return tokens;
  }

  async refreshAccessToken(): Promise<void> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await this.api.post('/auth/refresh', {
      refresh_token: this.refreshToken,
    });
    
    const tokens = response.data;
    this.saveTokens(tokens);
  }

  async logout(): Promise<void> {
    try {
      await this.api.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.clearTokens();
    }
  }

  // Equipment methods
  async getEquipment(params?: any) {
    const response = await this.api.get('/equipment', { params });
    return response.data;
  }

  async getEquipmentWithStats(params?: any) {
    const response = await this.api.get('/equipment/with-stats', { params });
    return response.data;
  }

  async getEquipmentById(id: number) {
    const response = await this.api.get(`/equipment/${id}`);
    return response.data;
  }

  async createEquipment(data: any) {
    const response = await this.api.post('/equipment', data);
    return response.data;
  }

  async updateEquipment(id: number, data: any) {
    const response = await this.api.put(`/equipment/${id}`, data);
    return response.data;
  }

  async deleteEquipment(id: number) {
    const response = await this.api.delete(`/equipment/${id}`);
    return response.data;
  }

  // Sensor data methods
  async getSensorData(params?: any) {
    const response = await this.api.get('/sensor-data', { params });
    return response.data;
  }

  async getLatestSensorData(equipmentIds?: number[]) {
    const params = equipmentIds ? { equipment_ids: equipmentIds } : {};
    const response = await this.api.get('/sensor-data/latest', { params });
    return response.data;
  }

  async getSensorDataStats(params?: any) {
    const response = await this.api.get('/sensor-data/stats', { params });
    return response.data;
  }

  async getAggregatedData(params?: any) {
    const response = await this.api.get('/sensor-data/aggregated', { params });
    return response.data;
  }

  // Dashboard methods
  async getDashboardMetrics() {
    const response = await this.api.get('/dashboard/metrics');
    return response.data;
  }

  async getEquipmentSummary() {
    const response = await this.api.get('/dashboard/equipment-summary');
    return response.data;
  }

  async generateChart(chartRequest: any) {
    const response = await this.api.post('/dashboard/chart', chartRequest);
    return response.data;
  }

  async getEnergyOverview(period: string = 'day') {
    const response = await this.api.get('/dashboard/energy-overview', {
      params: { period },
    });
    return response.data;
  }

  async getDashboardAlerts(limit: number = 10) {
    const response = await this.api.get('/dashboard/alerts', {
      params: { limit },
    });
    return response.data;
  }

  // Anomaly methods
  async getAnomalies(params?: any) {
    const response = await this.api.get('/anomalies', { params });
    return response.data;
  }

  async getAnomalyById(id: number) {
    const response = await this.api.get(`/anomalies/${id}`);
    return response.data;
  }

  async updateAnomaly(id: number, data: any) {
    const response = await this.api.put(`/anomalies/${id}`, data);
    return response.data;
  }

  async getAnomalyStats() {
    const response = await this.api.get('/anomalies/stats');
    return response.data;
  }

  async triggerAnomalyDetection() {
    const response = await this.api.post('/anomalies/detect');
    return response.data;
  }

  // Chat methods
  async getChatSessions() {
    const response = await this.api.get('/chat/sessions');
    return response.data;
  }

  async createChatSession(title: string) {
    const response = await this.api.post('/chat/sessions', { title });
    return response.data;
  }

  async getChatMessages(sessionId: number) {
    const response = await this.api.get(`/chat/sessions/${sessionId}/messages`);
    return response.data;
  }

  async sendChatMessage(sessionId: number, content: string) {
    const response = await this.api.post(`/chat/sessions/${sessionId}/messages`, {
      content,
    });
    return response.data;
  }

  async queryAI(query: string) {
    const response = await this.api.post('/chat/query', { query });
    return response.data;
  }

  // Report methods
  async getReports(params?: any) {
    const response = await this.api.get('/reports', { params });
    return response.data;
  }

  async generateReport(reportData: any) {
    const response = await this.api.post('/reports/generate', reportData);
    return response.data;
  }

  async getReportById(id: number) {
    const response = await this.api.get(`/reports/${id}`);
    return response.data;
  }

  async downloadReport(id: number) {
    const response = await this.api.get(`/reports/${id}/download`, {
      responseType: 'blob',
    });
    return response;
  }

  // Utility methods
  isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  getAccessToken(): string | null {
    return this.accessToken;
  }

  async getCurrentUser() {
    const response = await this.api.get('/auth/me');
    return response.data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;
