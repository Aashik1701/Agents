import React from 'react';
import { Box, Typography, Card, CardContent, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Chip } from '@mui/material';

const Anomalies: React.FC = () => {
  // Sample anomaly data
  const anomalies = [
    {
      id: 1,
      equipment: 'Compressor A',
      type: 'Temperature High',
      severity: 'High',
      status: 'Open',
      detected: '2023-12-01 14:30',
      description: 'Temperature exceeded normal operating range'
    },
    {
      id: 2,
      equipment: 'Motor B',
      type: 'Power Spike',
      severity: 'Medium',
      status: 'Investigating',
      detected: '2023-12-01 12:15',
      description: 'Unexpected power consumption increase detected'
    },
    {
      id: 3,
      equipment: 'HVAC C',
      type: 'Efficiency Drop',
      severity: 'Low',
      status: 'Resolved',
      detected: '2023-12-01 10:45',
      description: 'System efficiency below expected threshold'
    },
  ];

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      case 'critical': return 'error';
      default: return 'default';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'open': return 'error';
      case 'investigating': return 'warning';
      case 'resolved': return 'success';
      case 'false_positive': return 'default';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Anomaly Detection & Management
      </Typography>

      {/* Summary Cards */}
      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 3 }}>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(25% - 18px)' }, minWidth: '200px' }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Anomalies
              </Typography>
              <Typography variant="h4">
                {anomalies.length}
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(25% - 18px)' }, minWidth: '200px' }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Open Anomalies
              </Typography>
              <Typography variant="h4" color="error.main">
                {anomalies.filter(a => a.status === 'Open').length}
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(25% - 18px)' }, minWidth: '200px' }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Under Investigation
              </Typography>
              <Typography variant="h4" color="warning.main">
                {anomalies.filter(a => a.status === 'Investigating').length}
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(25% - 18px)' }, minWidth: '200px' }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Resolved Today
              </Typography>
              <Typography variant="h4" color="success.main">
                {anomalies.filter(a => a.status === 'Resolved').length}
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Anomalies Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Equipment</TableCell>
              <TableCell>Anomaly Type</TableCell>
              <TableCell>Severity</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Detected At</TableCell>
              <TableCell>Description</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {anomalies.map((anomaly) => (
              <TableRow key={anomaly.id}>
                <TableCell>{anomaly.equipment}</TableCell>
                <TableCell>{anomaly.type}</TableCell>
                <TableCell>
                  <Chip
                    label={anomaly.severity}
                    color={getSeverityColor(anomaly.severity) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={anomaly.status}
                    color={getStatusColor(anomaly.status) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>{anomaly.detected}</TableCell>
                <TableCell>{anomaly.description}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default Anomalies;
