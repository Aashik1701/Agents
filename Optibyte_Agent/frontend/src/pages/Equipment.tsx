import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import apiClient from '../services/apiClient';
import { EquipmentWithStats } from '../types';

const Equipment: React.FC = () => {
  const [equipment, setEquipment] = useState<EquipmentWithStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedEquipment, setSelectedEquipment] = useState<EquipmentWithStats | null>(null);

  useEffect(() => {
    fetchEquipment();
  }, []);

  const fetchEquipment = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getEquipmentWithStats();
      setEquipment(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load equipment');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'success';
      case 'offline': return 'error';
      case 'maintenance': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const handleEdit = (item: EquipmentWithStats) => {
    setSelectedEquipment(item);
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedEquipment(null);
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
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Equipment Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setDialogOpen(true)}
        >
          Add Equipment
        </Button>
      </Box>

      {/* Summary Cards */}
      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 3 }}>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(25% - 18px)' }, minWidth: '200px' }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Equipment
              </Typography>
              <Typography variant="h4">
                {equipment.length}
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(25% - 18px)' }, minWidth: '200px' }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Online
              </Typography>
              <Typography variant="h4" color="success.main">
                {equipment.filter(e => e.status === 'online').length}
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(25% - 18px)' }, minWidth: '200px' }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Offline
              </Typography>
              <Typography variant="h4" color="error.main">
                {equipment.filter(e => e.status === 'offline').length}
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(25% - 18px)' }, minWidth: '200px' }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Maintenance
              </Typography>
              <Typography variant="h4" color="warning.main">
                {equipment.filter(e => e.status === 'maintenance').length}
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Equipment Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Location</TableCell>
              <TableCell>Current Power (kW)</TableCell>
              <TableCell>Energy Today (kWh)</TableCell>
              <TableCell>Uptime %</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {equipment.map((item) => (
              <TableRow key={item.id}>
                <TableCell>
                  <Typography variant="body2" fontWeight="medium">
                    {item.name}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {item.serial_number}
                  </Typography>
                </TableCell>
                <TableCell>{item.equipment_type}</TableCell>
                <TableCell>
                  <Chip
                    label={item.status}
                    color={getStatusColor(item.status) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>{item.location || '-'}</TableCell>
                <TableCell>{item.current_power?.toFixed(2) || '0.00'}</TableCell>
                <TableCell>{item.energy_today?.toFixed(2) || '0.00'}</TableCell>
                <TableCell>{item.uptime_percentage?.toFixed(1) || '0'}%</TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => handleEdit(item)}
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    color="primary"
                  >
                    <SettingsIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Equipment Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedEquipment ? 'Edit Equipment' : 'Add Equipment'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 1 }}>
            <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 8px)' }, minWidth: 0 }}>
              <TextField
                fullWidth
                label="Equipment Name"
                defaultValue={selectedEquipment?.name || ''}
              />
            </Box>
            <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 8px)' }, minWidth: 0 }}>
              <TextField
                fullWidth
                select
                label="Equipment Type"
                defaultValue={selectedEquipment?.equipment_type || ''}
              >
                <MenuItem value="compressor">Compressor</MenuItem>
                <MenuItem value="motor">Motor</MenuItem>
                <MenuItem value="hvac">HVAC</MenuItem>
                <MenuItem value="pump">Pump</MenuItem>
                <MenuItem value="other">Other</MenuItem>
              </TextField>
            </Box>
            <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 8px)' }, minWidth: 0 }}>
              <TextField
                fullWidth
                label="Location"
                defaultValue={selectedEquipment?.location || ''}
              />
            </Box>
            <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 8px)' }, minWidth: 0 }}>
              <TextField
                fullWidth
                label="Manufacturer"
                defaultValue={selectedEquipment?.manufacturer || ''}
              />
            </Box>
            <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 8px)' }, minWidth: 0 }}>
              <TextField
                fullWidth
                label="Model"
                defaultValue={selectedEquipment?.model || ''}
              />
            </Box>
            <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 8px)' }, minWidth: 0 }}>
              <TextField
                fullWidth
                label="Serial Number"
                defaultValue={selectedEquipment?.serial_number || ''}
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button variant="contained" onClick={handleCloseDialog}>
            {selectedEquipment ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Equipment;
