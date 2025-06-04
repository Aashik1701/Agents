import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

const Analytics: React.FC = () => {
  // Sample data for charts
  const energyData = [
    { time: '00:00', energy: 120 },
    { time: '04:00', energy: 98 },
    { time: '08:00', energy: 185 },
    { time: '12:00', energy: 220 },
    { time: '16:00', energy: 195 },
    { time: '20:00', energy: 165 },
  ];

  const equipmentData = [
    { name: 'Compressor A', power: 45 },
    { name: 'Motor B', power: 32 },
    { name: 'HVAC C', power: 28 },
    { name: 'Pump D', power: 15 },
  ];

  const statusData = [
    { name: 'Online', value: 12, color: '#4caf50' },
    { name: 'Offline', value: 3, color: '#f44336' },
    { name: 'Maintenance', value: 2, color: '#ff9800' },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Analytics & Insights
      </Typography>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* First Row */}
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
          {/* Energy Consumption Trend */}
          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 65%' }, minWidth: 0 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Energy Consumption Trend (24h)
                </Typography>
                <Box height={300}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={energyData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="energy" stroke="#1976d2" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Box>

          {/* Equipment Status Distribution */}
          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 30%' }, minWidth: 0 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Equipment Status
                </Typography>
                <Box height={300}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={statusData}
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        dataKey="value"
                        label={({ name, value }) => `${name}: ${value}`}
                      >
                        {statusData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Box>
        </Box>

        {/* Second Row */}
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
          {/* Power Consumption by Equipment */}
          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 48%' }, minWidth: 0 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Power Consumption by Equipment
                </Typography>
                <Box height={300}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={equipmentData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="power" fill="#1976d2" />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Box>

          {/* Efficiency Metrics */}
          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 48%' }, minWidth: 0 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Key Performance Indicators
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                  <Box sx={{ flex: '1 1 45%', textAlign: 'center', minWidth: '120px' }}>
                    <Typography variant="h4" color="primary">
                      87.5%
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Overall Efficiency
                    </Typography>
                  </Box>
                  <Box sx={{ flex: '1 1 45%', textAlign: 'center', minWidth: '120px' }}>
                    <Typography variant="h4" color="success.main">
                      94.2%
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      System Uptime
                    </Typography>
                  </Box>
                  <Box sx={{ flex: '1 1 45%', textAlign: 'center', minWidth: '120px' }}>
                    <Typography variant="h4" color="warning.main">
                      12.3%
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Energy Savings
                    </Typography>
                  </Box>
                  <Box sx={{ flex: '1 1 45%', textAlign: 'center', minWidth: '120px' }}>
                    <Typography variant="h4" color="secondary">
                      $2,540
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Monthly Savings
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

export default Analytics;
