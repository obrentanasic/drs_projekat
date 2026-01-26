import React, { useEffect, useMemo, useState } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  Divider,
  Grid,
  IconButton,
  Paper,
  TextField,
  Typography,
  Chip,
  Alert,
} from '@mui/material'
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Save as SaveIcon,
} from '@mui/icons-material'
import { useAuth } from '../context/AuthContext'
import { quizAPI } from '../services/api'
import websocketService from '../services/websocket'
import { toast } from 'react-hot-toast'

const emptyAnswer = () => ({ text: '', is_correct: false })
const emptyQuestion = () => ({
  text: '',
  points: 1,
  answers: [emptyAnswer(), emptyAnswer()],
})

const CreateQuiz = () => {
  const { user } = useAuth()
  const [quizData, setQuizData] = useState({
    title: '',
    duration_seconds: 60,
    questions: [emptyQuestion()],
  })
  const [myQuizzes, setMyQuizzes] = useState([])
  const [editingQuizId, setEditingQuizId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const isEditing = useMemo(() => Boolean(editingQuizId), [editingQuizId])

  const loadMyQuizzes = async () => {
    try {
      setLoading(true)
      const response = await quizAPI.getMyQuizzes()
      setMyQuizzes(response.data.quizzes || [])
    } catch (err) {
      console.error('Failed to load quizzes', err)
      setError(err.response?.data?.error || 'Failed to load quizzes')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadMyQuizzes()
  }, [])

  useEffect(() => {
    websocketService.connect()
    const handleApproved = (payload) => {
      if (payload?.author_id === user?.id) {
        toast.success(`Quiz "${payload.title}" approved!`)
        loadMyQuizzes()
      }
    }
    const handleRejected = (payload) => {
      if (payload?.author_id === user?.id) {
        toast.error(`Quiz "${payload.title}" rejected: ${payload.rejection_reason}`)
        loadMyQuizzes()
      }
    }
    websocketService.on('quiz_approved', handleApproved)
    websocketService.on('quiz_rejected', handleRejected)
    return () => {
      websocketService.off('quiz_approved', handleApproved)
      websocketService.off('quiz_rejected', handleRejected)
    }
  }, [user])

  const updateQuizField = (field, value) => {
    setQuizData((prev) => ({ ...prev, [field]: value }))
  }

  const updateQuestionField = (index, field, value) => {
    setQuizData((prev) => {
      const questions = [...prev.questions]
      questions[index] = { ...questions[index], [field]: value }
      return { ...prev, questions }
    })
  }

  const updateAnswerField = (questionIndex, answerIndex, field, value) => {
    setQuizData((prev) => {
      const questions = [...prev.questions]
      const answers = [...questions[questionIndex].answers]
      answers[answerIndex] = { ...answers[answerIndex], [field]: value }
      questions[questionIndex] = { ...questions[questionIndex], answers }
      return { ...prev, questions }
    })
  }

  const addQuestion = () => {
    setQuizData((prev) => ({
      ...prev,
      questions: [...prev.questions, emptyQuestion()],
    }))
  }

  const removeQuestion = (index) => {
    setQuizData((prev) => ({
      ...prev,
      questions: prev.questions.filter((_, idx) => idx !== index),
    }))
  }

  const addAnswer = (questionIndex) => {
    setQuizData((prev) => {
      const questions = [...prev.questions]
      const answers = [...questions[questionIndex].answers, emptyAnswer()]
      questions[questionIndex] = { ...questions[questionIndex], answers }
      return { ...prev, questions }
    })
  }

  const removeAnswer = (questionIndex, answerIndex) => {
    setQuizData((prev) => {
      const questions = [...prev.questions]
      const answers = questions[questionIndex].answers.filter((_, idx) => idx !== answerIndex)
      questions[questionIndex] = { ...questions[questionIndex], answers }
      return { ...prev, questions }
    })
  }

  const validateQuiz = () => {
    if (!quizData.title.trim()) {
      return 'Quiz title is required.'
    }
    if (quizData.duration_seconds < 5) {
      return 'Quiz duration must be at least 5 seconds.'
    }
    if (quizData.questions.length < 1) {
      return 'Quiz must have at least one question.'
    }
    for (const [qIndex, question] of quizData.questions.entries()) {
      if (!question.text.trim()) {
        return `Question ${qIndex + 1} text is required.`
      }
      if (question.answers.length < 2) {
        return `Question ${qIndex + 1} must have at least two answers.`
      }
      const hasCorrect = question.answers.some((answer) => answer.is_correct)
      if (!hasCorrect) {
        return `Question ${qIndex + 1} must have at least one correct answer.`
      }
      for (const [aIndex, answer] of question.answers.entries()) {
        if (!answer.text.trim()) {
          return `Answer ${aIndex + 1} in question ${qIndex + 1} cannot be empty.`
        }
      }
    }
    return ''
  }

  const resetForm = () => {
    setQuizData({
      title: '',
      duration_seconds: 60,
      questions: [emptyQuestion()],
    })
    setEditingQuizId(null)
  }

  const handleSubmit = async () => {
    const validationError = validateQuiz()
    if (validationError) {
      setError(validationError)
      return
    }
    setError('')
    setSaving(true)
    
    try {
      if (isEditing) {
        await quizAPI.updateQuiz(editingQuizId, quizData)
        toast.success('Quiz updated and sent for approval.')
      } else {
        await quizAPI.createQuiz(quizData)
        toast.success('Quiz submitted for approval.')
      }
      resetForm()
      loadMyQuizzes()
    } catch (err) {
      console.error('Quiz submit error', err)
      setError(err.response?.data?.error || 'Failed to submit quiz')
    } finally {
      setSaving(false)
    }
  }

  const handleEdit = (quiz) => {
    setEditingQuizId(quiz.id)
    setQuizData({
      title: quiz.title,
      duration_seconds: quiz.duration_seconds,
      questions: quiz.questions.map((question) => ({
        text: question.text,
        points: question.points,
        answers: question.answers.map((answer) => ({
          text: answer.text,
          is_correct: answer.is_correct,
        })),
      })),
    })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <Box sx={{ py: 4 }}>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        {isEditing ? 'Edit Rejected Quiz' : 'Create Quiz'}
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Provide quiz details, questions, answers, and mark correct answers before submitting for approval.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <TextField
              fullWidth
              label="Quiz title"
              value={quizData.title}
              onChange={(e) => updateQuizField('title', e.target.value)}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              type="number"
              label="Duration (seconds)"
              value={quizData.duration_seconds}
              onChange={(e) => updateQuizField('duration_seconds', Number(e.target.value))}
              inputProps={{ min: 5 }}
            />
          </Grid>
        </Grid>
      </Paper>

      {quizData.questions.map((question, qIndex) => (
        <Card key={qIndex} sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Typography variant="h6">Question {qIndex + 1}</Typography>
              {quizData.questions.length > 1 && (
                <IconButton color="error" onClick={() => removeQuestion(qIndex)}>
                  <DeleteIcon />
                </IconButton>
              )}
            </Box>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} md={8}>
                <TextField
                  fullWidth
                  label="Question text"
                  value={question.text}
                  onChange={(e) => updateQuestionField(qIndex, 'text', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  type="number"
                  label="Points"
                  value={question.points}
                  onChange={(e) => updateQuestionField(qIndex, 'points', Number(e.target.value))}
                  inputProps={{ min: 1 }}
                />
              </Grid>
            </Grid>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle1" gutterBottom>
              Answers
            </Typography>
            {question.answers.map((answer, aIndex) => (
              <Grid container spacing={2} alignItems="center" key={aIndex} sx={{ mb: 1 }}>
                <Grid item xs={12} md={7}>
                  <TextField
                    fullWidth
                    label={`Answer ${aIndex + 1}`}
                    value={answer.text}
                    onChange={(e) => updateAnswerField(qIndex, aIndex, 'text', e.target.value)}
                  />
                </Grid>
                <Grid item xs={8} md={3}>
                  <Box display="flex" alignItems="center">
                    <Checkbox
                      checked={answer.is_correct}
                      onChange={(e) => updateAnswerField(qIndex, aIndex, 'is_correct', e.target.checked)}
                    />
                    <Typography variant="body2">Correct</Typography>
                  </Box>
                </Grid>
                <Grid item xs={4} md={2}>
                  {question.answers.length > 2 && (
                    <IconButton color="error" onClick={() => removeAnswer(qIndex, aIndex)}>
                      <DeleteIcon />
                    </IconButton>
                  )}
                </Grid>
              </Grid>
            ))}
            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={() => addAnswer(qIndex)}
            >
              Add answer
            </Button>
          </CardContent>
        </Card>
      ))}

      <Box display="flex" gap={2} flexWrap="wrap">
        <Button variant="contained" startIcon={<AddIcon />} onClick={addQuestion}>
          Add question
        </Button>
        <Button
          variant="contained"
          color="secondary"
          startIcon={isEditing ? <SaveIcon /> : <EditIcon />}
          onClick={handleSubmit}
          disabled={saving}
        >
          {isEditing ? 'Resubmit quiz' : 'Submit quiz'}
        </Button>
        {isEditing && (
          <Button variant="text" onClick={resetForm}>
            Cancel edit
          </Button>
        )}
      </Box>

      <Divider sx={{ my: 4 }} />

      <Typography variant="h5" fontWeight="bold" gutterBottom>
        My quizzes
      </Typography>
      {loading && <Typography>Loading quizzes...</Typography>}
      {!loading && myQuizzes.length === 0 && (
        <Alert severity="info">You have not created any quizzes yet.</Alert>
      )}
      <Grid container spacing={3} sx={{ mt: 1 }}>
        {myQuizzes.map((quiz) => (
          <Grid item xs={12} md={6} key={quiz.id}>
            <Card variant="outlined">
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="h6">{quiz.title}</Typography>
                  <Chip
                    label={quiz.status}
                    color={
                      quiz.status === 'APPROVED'
                        ? 'success'
                        : quiz.status === 'REJECTED'
                        ? 'error'
                        : 'warning'
                    }
                  />
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Questions: {quiz.question_count} • Duration: {quiz.duration_seconds}s
                </Typography>
                {quiz.rejection_reason && (
                  <Alert severity="warning" sx={{ mt: 2 }}>
                    {quiz.rejection_reason}
                  </Alert>
                )}
                {quiz.status === 'REJECTED' && (
                  <Button
                    variant="outlined"
                    startIcon={<EditIcon />}
                    sx={{ mt: 2 }}
                    onClick={() => handleEdit(quiz)}
                  >
                    Edit and resubmit
                  </Button>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}

export default CreateQuiz