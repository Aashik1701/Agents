import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Paper,
  TextField,
  Button,
  Avatar,
  IconButton,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Alert,
  InputAdornment,
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  Add as AddIcon,
  MoreVert as MoreIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { ChatSession, ChatMessage } from '../types';
import { useAuth } from '../contexts/AuthContext';

// Sample chat data
const sampleSessions: ChatSession[] = [
  {
    id: 1,
    title: 'Energy Optimization Discussion',
    user_id: 1,
    created_at: '2023-12-01T10:30:00Z',
    updated_at: '2023-12-01T11:45:00Z',
  },
  {
    id: 2,
    title: 'Equipment Maintenance Query',
    user_id: 1,
    created_at: '2023-12-01T14:20:00Z',
    updated_at: '2023-12-01T14:35:00Z',
  },
  {
    id: 3,
    title: 'Anomaly Analysis Help',
    user_id: 1,
    created_at: '2023-12-01T16:15:00Z',
    updated_at: '2023-12-01T16:30:00Z',
  },
];

const sampleMessages: { [sessionId: number]: ChatMessage[] } = {
  1: [
    {
      id: 1,
      session_id: 1,
      content: 'How can I optimize energy consumption for my HVAC systems?',
      role: 'user',
      timestamp: '2023-12-01T10:30:00Z',
    },
    {
      id: 2,
      session_id: 1,
      content: 'Based on your current HVAC data, I can suggest several optimization strategies:\n\n1. **Schedule Optimization**: Implement time-based scheduling to reduce energy usage during off-peak hours\n2. **Temperature Setpoints**: Adjust setpoints by 2-3°F during unoccupied periods\n3. **Variable Speed Controls**: Consider upgrading to variable frequency drives for better efficiency\n4. **Regular Maintenance**: Ensure filters are changed regularly and systems are properly calibrated\n\nWould you like me to analyze your specific HVAC equipment performance?',
      role: 'assistant',
      timestamp: '2023-12-01T10:31:15Z',
    },
    {
      id: 3,
      session_id: 1,
      content: 'Yes, please analyze HVAC-101 performance for the last week.',
      role: 'user',
      timestamp: '2023-12-01T10:35:00Z',
    },
    {
      id: 4,
      session_id: 1,
      content: 'I\'ve analyzed HVAC-101\'s performance for the past week:\n\n**Performance Summary:**\n- Average Energy Consumption: 45.2 kWh/day\n- Efficiency Rating: 87.3% (Good)\n- Peak Demand: 12.8 kW (Tuesday 2 PM)\n- Uptime: 94.5%\n\n**Recommendations:**\n1. The system shows higher consumption on Tuesday/Wednesday - consider adjusting schedules\n2. Efficiency dropped to 82% on Friday - maintenance check recommended\n3. Peak demand could be reduced by 15% with load shifting\n\nWould you like me to create an optimization schedule?',
      role: 'assistant',
      timestamp: '2023-12-01T10:36:30Z',
    },
  ],
  2: [
    {
      id: 5,
      session_id: 2,
      content: 'What maintenance is due for our equipment this month?',
      role: 'user',
      timestamp: '2023-12-01T14:20:00Z',
    },
    {
      id: 6,
      session_id: 2,
      content: 'Here\'s your maintenance schedule for December 2023:\n\n**Overdue:**\n- Motor-456: Filter replacement (Due: Nov 28)\n- Pump-789: Bearing inspection (Due: Nov 30)\n\n**This Week:**\n- Compressor-123: Routine inspection (Due: Dec 5)\n- HVAC-101: Coil cleaning (Due: Dec 7)\n\n**Next Week:**\n- Generator-555: Oil change (Due: Dec 12)\n- Fan-888: Belt replacement (Due: Dec 14)\n\nWould you like me to prioritize these by criticality or schedule maintenance reminders?',
      role: 'assistant',
      timestamp: '2023-12-01T14:21:10Z',
    },
  ],
  3: [
    {
      id: 7,
      session_id: 3,
      content: 'I see multiple anomalies detected today. Can you explain what\'s happening?',
      role: 'user',
      timestamp: '2023-12-01T16:15:00Z',
    },
    {
      id: 8,
      session_id: 3,
      content: 'I\'ve detected 3 anomalies today that require attention:\n\n**1. High Temperature - Compressor A (Critical)**\n- Detected: 2:30 PM\n- Temperature: 95°C (Normal: 65-75°C)\n- Likely cause: Cooling system malfunction\n- Action: Immediate inspection required\n\n**2. Power Spike - Motor B (Medium)**\n- Detected: 1:45 PM\n- Power increase: 23% above baseline\n- Likely cause: Increased load or bearing wear\n- Action: Schedule maintenance check\n\n**3. Efficiency Drop - HVAC C (Low)**\n- Detected: 11:20 AM\n- Efficiency decrease: 8% from normal\n- Likely cause: Filter clogging or sensor drift\n- Action: Routine maintenance recommended\n\nShall I create maintenance tickets for these issues?',
      role: 'assistant',
      timestamp: '2023-12-01T16:16:25Z',
    },
  ],
};

const Chat: React.FC = () => {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Sample chat data
  const fetchSessions = useCallback(async () => {
    try {
      setSessionLoading(true);
      // Use sample data for now
      setSessions(sampleSessions);
      if (sampleSessions.length > 0) {
        setActiveSession(sampleSessions[0]);
      }
      
      // Uncomment when backend is connected:
      // const response = await apiClient.getChatSessions();
      // setSessions(response);
      // if (response.length > 0) {
      //   setActiveSession(response[0]);
      // }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load chat sessions');
    } finally {
      setSessionLoading(false);
    }
  }, []);

  const fetchMessages = useCallback(async (sessionId: number) => {
    try {
      // Use sample data for now
      setMessages(sampleMessages[sessionId] || []);
      
      // Uncomment when backend is connected:
      // const response = await apiClient.getChatMessages(sessionId);
      // setMessages(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load messages');
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  useEffect(() => {
    if (activeSession) {
      fetchMessages(activeSession.id);
    }
  }, [activeSession, fetchMessages]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !activeSession) return;

    const userMessage: ChatMessage = {
      id: Date.now(),
      session_id: activeSession.id,
      content: inputValue,
      role: 'user',
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    try {
      // Uncomment when backend is connected:
      // const response = await apiClient.sendChatMessage(activeSession.id, inputValue);
      // setMessages(prev => [...prev, response]);

      // Simulate AI response for now
      setTimeout(() => {
        const aiMessage: ChatMessage = {
          id: Date.now() + 1,
          session_id: activeSession.id,
          content: `I understand your query: "${inputValue}". Let me help you with that.\n\nBased on the current system data, I can provide insights and recommendations. Would you like me to analyze specific equipment or provide general optimization suggestions?`,
          role: 'assistant',
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, aiMessage]);
        setLoading(false);
      }, 1500);

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send message');
      setLoading(false);
    }
  };

  const handleNewSession = async () => {
    const newSession: ChatSession = {
      id: Date.now(),
      title: 'New Chat Session',
      user_id: user?.id || 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setSessions(prev => [newSession, ...prev]);
    setActiveSession(newSession);
    setMessages([]);

    // Uncomment when backend is connected:
    // try {
    //   const response = await apiClient.createChatSession({ title: 'New Chat Session' });
    //   setSessions(prev => [response, ...prev]);
    //   setActiveSession(response);
    //   setMessages([]);
    // } catch (err: any) {
    //   setError(err.response?.data?.detail || 'Failed to create new session');
    // }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  if (sessionLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box height="calc(100vh - 180px)">
      <Typography variant="h4" gutterBottom>
        AI Assistant Chat
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Box sx={{ display: 'flex', gap: 2, height: 'calc(100% - 60px)' }}>
        {/* Chat Sessions Sidebar */}
        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 25%' }, minWidth: 0 }}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ pb: 1 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Chat Sessions</Typography>
                <Button
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={handleNewSession}
                >
                  New
                </Button>
              </Box>
              <TextField
                fullWidth
                size="small"
                placeholder="Search sessions..."
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </CardContent>
            <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
              <List dense>
                {sessions.map((session) => (
                  <ListItem
                    key={session.id}
                    component="div"
                    sx={{
                      borderRadius: 1,
                      mx: 1,
                      mb: 0.5,
                      cursor: 'pointer',
                      backgroundColor: activeSession?.id === session.id ? 'primary.main' : 'transparent',
                      color: activeSession?.id === session.id ? 'primary.contrastText' : 'inherit',
                      '&:hover': {
                        backgroundColor: activeSession?.id === session.id ? 'primary.dark' : 'action.hover',
                      },
                    }}
                    onClick={() => setActiveSession(session)}
                  >
                    <ListItemText
                      primary={session.title}
                      secondary={session.updated_at ? new Date(session.updated_at).toLocaleDateString() : ''}
                      sx={{
                        '& .MuiListItemText-secondary': {
                          color: activeSession?.id === session.id ? 'inherit' : 'text.secondary',
                          opacity: activeSession?.id === session.id ? 0.7 : 1,
                        },
                      }}
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          </Card>
        </Box>

        {/* Chat Messages Area */}
        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 70%' }, minWidth: 0 }}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Chat Header */}
            <CardContent sx={{ pb: 1, borderBottom: 1, borderColor: 'divider' }}>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="h6">
                  {activeSession?.title || 'Select a chat session'}
                </Typography>
                <IconButton size="small">
                  <MoreIcon />
                </IconButton>
              </Box>
            </CardContent>

            {/* Messages Area */}
            <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
              {activeSession ? (
                <>
                  {messages.map((message) => (
                    <Box key={message.id} mb={2}>
                      <Box
                        display="flex"
                        justifyContent={message.role === 'user' ? 'flex-end' : 'flex-start'}
                        alignItems="flex-start"
                        gap={1}
                      >
                        {message.role === 'assistant' && (
                          <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
                            <BotIcon fontSize="small" />
                          </Avatar>
                        )}
                        <Paper
                          sx={{
                            p: 2,
                            maxWidth: '70%',
                            bgcolor: message.role === 'user' ? 'primary.main' : 'grey.100',
                            color: message.role === 'user' ? 'primary.contrastText' : 'text.primary',
                          }}
                        >
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                            {message.content}
                          </Typography>
                          <Typography
                            variant="caption"
                            sx={{
                              display: 'block',
                              mt: 0.5,
                              opacity: 0.7,
                            }}
                          >
                            {formatTimestamp(message.timestamp)}
                          </Typography>
                        </Paper>
                        {message.role === 'user' && (
                          <Avatar sx={{ bgcolor: 'secondary.main', width: 32, height: 32 }}>
                            <PersonIcon fontSize="small" />
                          </Avatar>
                        )}
                      </Box>
                    </Box>
                  ))}
                  {loading && (
                    <Box display="flex" justifyContent="flex-start" alignItems="center" gap={1} mb={2}>
                      <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
                        <BotIcon fontSize="small" />
                      </Avatar>
                      <Paper sx={{ p: 2, bgcolor: 'grey.100' }}>
                        <Box display="flex" alignItems="center" gap={1}>
                          <CircularProgress size={16} />
                          <Typography variant="body2">AI is thinking...</Typography>
                        </Box>
                      </Paper>
                    </Box>
                  )}
                  <div ref={messagesEndRef} />
                </>
              ) : (
                <Box
                  display="flex"
                  justifyContent="center"
                  alignItems="center"
                  height="100%"
                  textAlign="center"
                >
                  <Box>
                    <BotIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="textSecondary" gutterBottom>
                      Welcome to Optibyte AI Assistant
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Select a chat session or create a new one to start chatting
                    </Typography>
                  </Box>
                </Box>
              )}
            </Box>

            {/* Message Input */}
            {activeSession && (
              <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
                <Box display="flex" gap={1}>
                  <TextField
                    fullWidth
                    multiline
                    maxRows={4}
                    placeholder="Ask about energy optimization, equipment status, anomalies, or maintenance..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage();
                      }
                    }}
                    disabled={loading}
                  />
                  <Button
                    variant="contained"
                    onClick={handleSendMessage}
                    disabled={!inputValue.trim() || loading}
                    sx={{ minWidth: 'auto', px: 2 }}
                  >
                    <SendIcon />
                  </Button>
                </Box>
              </Box>
            )}
          </Card>
        </Box>
      </Box>
    </Box>
  );
};

export default Chat;
