import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Alert,
  Box,
  Typography,
  Chip,
  IconButton
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import TimerIcon from '@mui/icons-material/Timer';
import { quizAPI } from '../services/api';

const QuizLeaderboard = ({ open, onClose, quizId, quizTitle }) => {
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (open && quizId) {
      fetchLeaderboard();
    }
  }, [open, quizId]);

  const fetchLeaderboard = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await quizAPI.getLeaderboard(quizId);
      setLeaderboard(response.data || []);
    } catch (err) {
      console.error('Failed to load leaderboard:', err);
      setError(err.response?.data?.error || 'Nije moguće učitati rang listu');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const getMedalIcon = (position) => {
    if (position === 0) return '🥇';
    if (position === 1) return '🥈';
    if (position === 2) return '🥉';
    return position + 1;
  };

  const getMedalColor = (position) => {
    if (position === 0) return '#FFD700';
    if (position === 1) return '#C0C0C0';
    if (position === 2) return '#CD7F32';
    return 'transparent';
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="md" 
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          minHeight: '400px'
        }
      }}
    >
      <DialogTitle sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        pb: 1
      }}>
        <Box display="flex" alignItems="center" gap={1}>
          <EmojiEventsIcon color="primary" fontSize="large" />
          <Box>
            <Typography variant="h5" fontWeight="bold">
              Rang lista
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {quizTitle}
            </Typography>
          </Box>
        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent>
        {loading && (
          <Box display="flex" justifyContent="center" alignItems="center" py={4}>
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {!loading && !error && leaderboard.length === 0 && (
          <Alert severity="info">
            Nema rezultata za ovaj kviz. Budite prvi koji će ga uraditi!
          </Alert>
        )}

        {!loading && !error && leaderboard.length > 0 && (
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow sx={{ bgcolor: 'primary.light' }}>
                  <TableCell sx={{ fontWeight: 'bold', width: '80px' }}>
                    Pozicija
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    Korisnik
                  </TableCell>
                  <TableCell align="center" sx={{ fontWeight: 'bold' }}>
                    <Box display="flex" alignItems="center" justifyContent="center" gap={0.5}>
                      <EmojiEventsIcon fontSize="small" />
                      Bodovi
                    </Box>
                  </TableCell>
                  <TableCell align="center" sx={{ fontWeight: 'bold' }}>
                    <Box display="flex" alignItems="center" justifyContent="center" gap={0.5}>
                      <TimerIcon fontSize="small" />
                      Vreme
                    </Box>
                  </TableCell>
                  <TableCell align="center" sx={{ fontWeight: 'bold' }}>
                    Procenat
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {leaderboard.map((result, index) => {
                  const percentage = result.max_score > 0 
                    ? ((result.score / result.max_score) * 100).toFixed(1)
                    : 0;

                  return (
                    <TableRow
                      key={result._id}
                      sx={{
                        bgcolor: getMedalColor(index),
                        '&:hover': {
                          bgcolor: index < 3 
                            ? getMedalColor(index) 
                            : 'action.hover'
                        },
                        transition: 'background-color 0.2s'
                      }}
                    >
                      <TableCell>
                        <Box 
                          display="flex" 
                          alignItems="center" 
                          justifyContent="center"
                          sx={{
                            fontSize: index < 3 ? '1.5rem' : '1rem',
                            fontWeight: index < 3 ? 'bold' : 'normal'
                          }}
                        >
                          {getMedalIcon(index)}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body1" fontWeight={index < 3 ? 'bold' : 'normal'}>
                          {result.user_name || 'Anonimni korisnik'}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Chip 
                          label={`${result.score} / ${result.max_score}`}
                          color={index < 3 ? 'primary' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="body2" color="text.secondary">
                          {formatTime(result.time_spent)}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Chip 
                          label={`${percentage}%`}
                          color={
                            percentage >= 80 ? 'success' : 
                            percentage >= 60 ? 'warning' : 
                            'error'
                          }
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        {!loading && !error && leaderboard.length > 0 && (
          <Box mt={2} p={2} bgcolor="grey.50" borderRadius={1}>
            <Typography variant="body2" color="text.secondary" textAlign="center">
              <strong>Ukupno učesnika:</strong> {leaderboard.length}
            </Typography>
          </Box>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default QuizLeaderboard;
