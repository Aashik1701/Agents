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
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  CircularProgress,
  Alert,
  IconButton,
  Stack,
} from '@mui/material';
import {
  Add as AddIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Assessment as ReportIcon,
  PictureAsPdf as PdfIcon,
  TableChart as CsvIcon,
  GridOn as ExcelIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { Report } from '../types';

const Reports: React.FC = () => {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [newReport, setNewReport] = useState({
    title: '',
    report_type: 'energy_summary' as const,
    format: 'pdf' as const,
    start_date: new Date(),
    end_date: new Date(),
    equipment_ids: [] as number[],
  });

  useEffect(() => {
    const fetchReports = async () => {
      try {
        setLoading(true);
        
        // Sample reports data
        const sampleReports: Report[] = [
          {
            id: 1,
            title: 'Monthly Energy Summary - December 2023',
            report_type: 'energy_summary',
            format: 'pdf',
            status: 'completed',
            created_by: 1,
            created_at: '2023-12-01T08:30:00Z',
            completed_at: '2023-12-01T08:32:15Z',
            file_path: '/reports/energy_summary_dec_2023.pdf',
          },
          {
            id: 2,
            title: 'Equipment Status Report',
            report_type: 'equipment_status',
            format: 'excel',
            status: 'completed',
            created_by: 1,
            created_at: '2023-12-01T10:15:00Z',
            completed_at: '2023-12-01T10:16:30Z',
            file_path: '/reports/equipment_status_2023.xlsx',
          },
          {
            id: 3,
            title: 'Anomaly Analysis Report',
            report_type: 'anomaly_report',
            format: 'pdf',
            status: 'generating',
            created_by: 1,
            created_at: '2023-12-01T14:20:00Z',
          },
          {
            id: 4,
            title: 'Maintenance Schedule Q4 2023',
            report_type: 'maintenance_schedule',
            format: 'csv',
            status: 'completed',
            created_by: 1,
            created_at: '2023-11-28T16:45:00Z',
            completed_at: '2023-11-28T16:46:12Z',
            file_path: '/reports/maintenance_schedule_q4.csv',
          },
        ];
        
        // Use sample data for now
        setReports(sampleReports);
        
        // Uncomment when backend is connected:
        // const response = await apiClient.getReports();
        // setReports(response);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load reports');
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, []);

  const handleGenerateReport = async () => {
    try {
      setGenerating(true);
      
      // Uncomment when backend is connected:
      // const reportData = {
      //   ...newReport,
      //   start_date: newReport.start_date.toISOString(),
      //   end_date: newReport.end_date.toISOString(),
      // };
      // const response = await apiClient.generateReport(reportData);
      // await fetchReports();
      
      // For now, simulate report generation
      const newReportItem: Report = {
        id: Date.now(),
        title: newReport.title,
        report_type: newReport.report_type,
        format: newReport.format,
        status: 'generating',
        created_by: 1,
        created_at: new Date().toISOString(),
      };
      
      setReports(prev => [newReportItem, ...prev]);
      
      // Simulate completion after 3 seconds
      setTimeout(() => {
        setReports(prev => prev.map(report => 
          report.id === newReportItem.id
            ? { ...report, status: 'completed' as const, completed_at: new Date().toISOString() }
            : report
        ));
      }, 3000);

      setDialogOpen(false);
      setNewReport({
        title: '',
        report_type: 'energy_summary',
        format: 'pdf',
        start_date: new Date(),
        end_date: new Date(),
        equipment_ids: [],
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadReport = async (report: Report) => {
    if (report.status === 'completed' && report.file_path) {
      // Uncomment when backend is connected:
      // window.open(`${apiClient.baseURL}${report.file_path}`, '_blank');
      
      // For now, show a message
      alert(`Downloading: ${report.title}`);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'generating': return 'warning';
      case 'pending': return 'info';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'pdf': return <PdfIcon color="error" />;
      case 'csv': return <CsvIcon color="success" />;
      case 'excel': return <ExcelIcon color="primary" />;
      default: return <ReportIcon />;
    }
  };

  const reportTypeOptions = [
    { value: 'energy_summary', label: 'Energy Summary' },
    { value: 'equipment_status', label: 'Equipment Status' },
    { value: 'anomaly_report', label: 'Anomaly Report' },
    { value: 'maintenance_schedule', label: 'Maintenance Schedule' },
    { value: 'custom', label: 'Custom Report' },
  ];

  const formatOptions = [
    { value: 'pdf', label: 'PDF' },
    { value: 'excel', label: 'Excel (XLSX)' },
    { value: 'csv', label: 'CSV' },
  ];

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
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4">
            Reports & Analytics
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setDialogOpen(true)}
          >
            Generate Report
          </Button>
        </Box>

        {/* Summary Cards */}
        <Box display="flex" gap={2} mb={3} flexWrap="wrap">
          <Card sx={{ flex: '1 1 200px', minWidth: 200 }}>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Reports
              </Typography>
              <Typography variant="h4">
                {reports.length}
              </Typography>
            </CardContent>
          </Card>
          <Card sx={{ flex: '1 1 200px', minWidth: 200 }}>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Completed
              </Typography>
              <Typography variant="h4" color="success.main">
                {reports.filter(r => r.status === 'completed').length}
              </Typography>
            </CardContent>
          </Card>
          <Card sx={{ flex: '1 1 200px', minWidth: 200 }}>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Generating
              </Typography>
              <Typography variant="h4" color="warning.main">
                {reports.filter(r => r.status === 'generating').length}
              </Typography>
            </CardContent>
          </Card>
          <Card sx={{ flex: '1 1 200px', minWidth: 200 }}>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                This Month
              </Typography>
              <Typography variant="h4" color="primary">
                {reports.filter(r => 
                  new Date(r.created_at).getMonth() === new Date().getMonth()
                ).length}
              </Typography>
            </CardContent>
          </Card>
        </Box>

        {/* Reports Table */}
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Report Title</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Format</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Completed</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {reports.map((report) => (
                <TableRow key={report.id}>
                  <TableCell>
                    <Box display="flex" alignItems="center">
                      {getFormatIcon(report.format)}
                      <Box ml={1}>
                        <Typography variant="body2" fontWeight="medium">
                          {report.title}
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    {reportTypeOptions.find(opt => opt.value === report.report_type)?.label}
                  </TableCell>
                  <TableCell>{report.format.toUpperCase()}</TableCell>
                  <TableCell>
                    <Chip
                      label={report.status}
                      color={getStatusColor(report.status) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {new Date(report.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    {report.completed_at 
                      ? new Date(report.completed_at).toLocaleDateString()
                      : '-'
                    }
                  </TableCell>
                  <TableCell align="center">
                    <Stack direction="row" spacing={1} justifyContent="center">
                      {report.status === 'completed' && (
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleDownloadReport(report)}
                          title="Download"
                        >
                          <DownloadIcon />
                        </IconButton>
                      )}
                      <IconButton
                        size="small"
                        color="info"
                        title="View Details"
                      >
                        <ViewIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        color="error"
                        title="Delete"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Generate Report Dialog */}
        <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
          <DialogTitle>Generate New Report</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <TextField
                fullWidth
                label="Report Title"
                value={newReport.title}
                onChange={(e) => setNewReport(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Enter report title"
              />
              <Box display="flex" gap={2}>
                <FormControl fullWidth>
                  <InputLabel>Report Type</InputLabel>
                  <Select
                    value={newReport.report_type}
                    label="Report Type"
                    onChange={(e) => setNewReport(prev => ({ 
                      ...prev, 
                      report_type: e.target.value as any 
                    }))}
                  >
                    {reportTypeOptions.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <FormControl fullWidth>
                  <InputLabel>Format</InputLabel>
                  <Select
                    value={newReport.format}
                    label="Format"
                    onChange={(e) => setNewReport(prev => ({ 
                      ...prev, 
                      format: e.target.value as any 
                    }))}
                  >
                    {formatOptions.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
              <Box display="flex" gap={2}>
                <DatePicker
                  label="Start Date"
                  value={newReport.start_date}
                  onChange={(date: Date | null) => date && setNewReport(prev => ({ 
                    ...prev, 
                    start_date: date 
                  }))}
                  slotProps={{ textField: { fullWidth: true } }}
                />
                <DatePicker
                  label="End Date"
                  value={newReport.end_date}
                  onChange={(date: Date | null) => date && setNewReport(prev => ({ 
                    ...prev, 
                    end_date: date 
                  }))}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Box>
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button 
              variant="contained" 
              onClick={handleGenerateReport}
              disabled={generating || !newReport.title}
            >
              {generating ? <CircularProgress size={24} /> : 'Generate Report'}
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </LocalizationProvider>
  );
};

export default Reports;
