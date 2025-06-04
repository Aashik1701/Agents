import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Chip,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Power,
  Warning,
  CheckCircle,
  Error,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import apiClient from '../services/apiClient';
import { DashboardMetrics, EquipmentWithStats } from '../types';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  change?: number;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon, color, change }) => (
  <Card>
    <CardContent>
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography color="textSecondary" gutterBottom>
            {title}
          </Typography>
          <Typography variant="h4" component="div">
            {value}
          </Typography>
          {change !== undefined && (
            <Box display="flex" alignItems="center" mt={1}>
              {change >= 0 ? (
                <TrendingUp color="success" fontSize="small" />
              ) : (
                <TrendingDown color="error" fontSize="small" />
              )}
              <Typography
                variant="body2"
                color={change >= 0 ? 'success.main' : 'error.main'}
                ml={0.5}
              >
                {Math.abs(change)}%
              </Typography>
            </Box>
          )}
        </Box>
        <Box color={`${color}.main`}>
          {icon}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [equipment, setEquipment] = useState<EquipmentWithStats[]>([]);
  const [energyData, setEnergyData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        
        // Fetch dashboard metrics
        const metricsResponse = await apiClient.getDashboardMetrics();
        setMetrics(metricsResponse);

        // Fetch equipment with stats
        const equipmentResponse = await apiClient.getEquipmentWithStats({ limit: 10 });
        setEquipment(equipmentResponse);

        // Fetch energy overview data
        const energyResponse = await apiClient.getEnergyOverview('day');
        setEnergyData(energyResponse.data || []);

      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'success';
      case 'offline': return 'error';
      case 'maintenance': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      {/* Metrics Cards */}
      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 3 }}>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(25% - 18px)' }, minWidth: '200px' }}>
          <MetricCard
            title="Total Equipment"
            value={metrics?.total_equipment || 0}
            icon={<Power fontSize="large" />}
            color="primary"
          />
        </Box>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(25% - 18px)' }, minWidth: '200px' }}>
          <MetricCard
            title="Online Equipment"
            value={metrics?.online_equipment || 0}
            icon={<CheckCircle fontSize="large" />}
            color="success"
          />
        </Box>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(25% - 18px)' }, minWidth: '200px' }}>
          <MetricCard
            title="Energy Today (kWh)"
            value={metrics?.total_energy_today?.toFixed(2) || '0'}
            icon={<TrendingUp fontSize="large" />}
            color="primary"
          />
        </Box>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(25% - 18px)' }, minWidth: '200px' }}>
          <MetricCard
            title="Active Anomalies"
            value={metrics?.active_anomalies || 0}
            icon={<Warning fontSize="large" />}
            color="warning"
          />
        </Box>
      </Box>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* First Row */}
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
          {/* Energy Consumption Chart */}
          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 65%' }, minWidth: 0 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Energy Consumption Today
                </Typography>
                <Box height={300}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={energyData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <Tooltip />
                      <Line 
                        type="monotone" 
                        dataKey="energy" 
                        stroke="#1976d2" 
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Box>

          {/* Equipment Status */}
          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 30%' }, minWidth: 0 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Equipment Status
                </Typography>
                <Box>
                  {equipment.slice(0, 5).map((item) => (
                    <Box
                      key={item.id}
                      display="flex"
                      justifyContent="space-between"
                      alignItems="center"
                      py={1}
                      borderBottom="1px solid #eee"
                    >
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          {item.name}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {item.current_power?.toFixed(1) || '0'} kW
                        </Typography>
                      </Box>
                      <Chip
                        label={item.status}
                        color={getStatusColor(item.status) as any}
                        size="small"
                      />
                    </Box>
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Box>
        </Box>

        {/* Second Row */}
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
          {/* Additional Metrics */}
          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 48%' }, minWidth: 0 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Performance Metrics
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                  <Box sx={{ flex: '1 1 45%', textAlign: 'center', minWidth: '120px' }}>
                    <Typography variant="h5" color="primary">
                      {metrics?.average_efficiency?.toFixed(1) || '0'}%
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Average Efficiency
                    </Typography>
                  </Box>
                  <Box sx={{ flex: '1 1 45%', textAlign: 'center', minWidth: '120px' }}>
                    <Typography variant="h5" color="secondary">
                      {metrics?.peak_demand_today?.toFixed(1) || '0'} kW
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Peak Demand Today
                    </Typography>
                  </Box>
                  <Box sx={{ flex: '1 1 45%', textAlign: 'center', minWidth: '120px' }}>
                    <Typography variant="h5" color="success.main">
                      ${metrics?.cost_savings_month?.toFixed(0) || '0'}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Cost Savings (Month)
                    </Typography>
                  </Box>
                  <Box sx={{ flex: '1 1 45%', textAlign: 'center', minWidth: '120px' }}>
                    <Typography variant="h5" color="success.main">
                      {metrics?.carbon_footprint_reduction?.toFixed(1) || '0'}%
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Carbon Reduction
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>

          {/* Recent Activity */}
          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 48%' }, minWidth: 0 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent Activity
                </Typography>
                <Box>
                  <Box display="flex" alignItems="center" py={1}>
                    <CheckCircle color="success" fontSize="small" sx={{ mr: 1 }} />
                    <Typography variant="body2">
                      Equipment ABC-123 came online
                    </Typography>
                  </Box>
                  <Box display="flex" alignItems="center" py={1}>
                    <Warning color="warning" fontSize="small" sx={{ mr: 1 }} />
                    <Typography variant="body2">
                      High temperature detected on Motor-456
                    </Typography>
                  </Box>
                  <Box display="flex" alignItems="center" py={1}>
                    <Error color="error" fontSize="small" sx={{ mr: 1 }} />
                    <Typography variant="body2">
                      Compressor-789 went offline
                    </Typography>
                  </Box>
                  <Box display="flex" alignItems="center" py={1}>
                    <CheckCircle color="success" fontSize="small" sx={{ mr: 1 }} />
                    <Typography variant="body2">
                      Maintenance completed on HVAC-101
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default Dashboard;
