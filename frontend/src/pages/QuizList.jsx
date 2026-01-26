import React, { useEffect, useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Chip,
  Alert,
} from '@mui/material'
import { quizAPI } from '../services/api'
import websocketService from '../services/websocket'

const QuizList = () => {
  const [quizzes, setQuizzes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadQuizzes = async () => {
    try {
      setLoading(true)
      const response = await quizAPI.getQuizzes()
      setQuizzes(response.data.quizzes || [])
    } catch (err) {
      console.error('Failed to load quizzes', err)
      setError(err.response?.data?.error || 'Failed to load quizzes')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadQuizzes()
  }, [])

  useEffect(() => {
    websocketService.connect()
    const handleApproved = () => {
      loadQuizzes()
    }
    websocketService.on('quiz_approved', handleApproved)
    return () => {
      websocketService.off('quiz_approved', handleApproved)
    }
  }, [])

  return (
    <Box sx={{ py: 4 }}>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        Available Quizzes
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Approved quizzes are available for players to join.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading && <Typography>Loading quizzes...</Typography>}

      {!loading && quizzes.length === 0 && (
        <Alert severity="info">No approved quizzes available yet.</Alert>
      )}

      <Grid container spacing={3} sx={{ mt: 1 }}>
        {quizzes.map((quiz) => (
          <Grid item xs={12} md={6} key={quiz.id}>
            <Card variant="outlined">
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="h6">{quiz.title}</Typography>
                  <Chip label={`${quiz.duration_seconds}s`} color="primary" size="small" />
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Author: {quiz.author_name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Questions: {quiz.question_count}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}

export default QuizList