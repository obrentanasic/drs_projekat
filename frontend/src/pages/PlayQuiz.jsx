import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../App.css';

const PlayQuiz = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [timeLeft, setTimeLeft] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  
  const startTime = useRef(Date.now());
  const timerRef = useRef(null);

  useEffect(() => {
    fetchQuiz();
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [id]);

  const fetchQuiz = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `http://localhost:5000/quizzes/${id}/play`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      console.log('Quiz data:', response.data);
      setQuiz(response.data);
      setTimeLeft(response.data.duration_seconds);
      startTimer(response.data.duration_seconds);
      
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load quiz');
    } finally {
      setLoading(false);
    }
  };

  const startTimer = (duration) => {
    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current);
          handleSubmit(true); // Auto-submit when time's up
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const handleAnswerChange = (questionId, answerId) => {
    setAnswers((prev) => {
      const current = prev[questionId] || [];
      
      // Check if this question allows multiple answers
      const question = quiz.questions.find(q => q.id === questionId);
      const correctCount = question?.answers?.filter(a => a.is_correct).length || 1;
      
      if (correctCount > 1) {
        // Multiple choice - toggle answer
        if (current.includes(answerId)) {
          return { ...prev, [questionId]: current.filter(id => id !== answerId) };
        } else {
          return { ...prev, [questionId]: [...current, answerId] };
        }
      } else {
        // Single choice - replace answer
        return { ...prev, [questionId]: [answerId] };
      }
    });
  };

  const handleSubmit = async (autoSubmit = false) => {
    if (!autoSubmit && submitting) return;
    
    setSubmitting(true);
    clearInterval(timerRef.current);

    const timeSpent = Math.floor((Date.now() - startTime.current) / 1000);

    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `http://localhost:5000/quizzes/${id}/submit`,
        {
          answers: answers,
          time_spent: timeSpent
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      alert('Quiz submitted! Results will be emailed to you.');
      navigate('/dashboard');
      
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to submit quiz');
      setSubmitting(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) return <div className="container"><p>Loading quiz...</p></div>;
  if (error) return <div className="container"><p className="error">{error}</p></div>;
  if (!quiz) return <div className="container"><p>Quiz not found</p></div>;

  return (
    <div className="container">
      <div className="quiz-header">
        <h1>{quiz.title}</h1>
        <div className={`timer ${timeLeft < 60 ? 'timer-warning' : ''}`}>
          Time Remaining: {formatTime(timeLeft)}
        </div>
      </div>

      <div className="quiz-questions">
        {quiz.questions?.map((question, qIdx) => (
          <div key={question.id} className="question-card">
            <h3>
              Question {qIdx + 1} ({question.points} points)
            </h3>
            <p>{question.text}</p>
            
            <div className="answers">
              {question.answers?.map((answer, aIdx) => {
                const isSelected = answers[question.id]?.includes(aIdx);
                
                return (
                  <div
                    key={aIdx}
                    className={`answer-option ${isSelected ? 'selected' : ''}`}
                    onClick={() => handleAnswerChange(question.id, aIdx)}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => {}}
                    />
                    <label>{answer.text}</label>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="quiz-actions">
        <button
          onClick={() => handleSubmit(false)}
          disabled={submitting}
          className="submit-btn"
        >
          {submitting ? 'Submitting...' : 'Submit Quiz'}
        </button>
      </div>

      <style jsx>{`
        .quiz-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 2rem;
          padding-bottom: 1rem;
          border-bottom: 2px solid #eee;
        }

        .timer {
          font-size: 1.5rem;
          font-weight: bold;
          color: #4CAF50;
          padding: 0.5rem 1rem;
          background: #f0f0f0;
          border-radius: 8px;
        }

        .timer-warning {
          color: #f44336;
          animation: pulse 1s infinite;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        .quiz-questions {
          margin-bottom: 2rem;
        }

        .question-card {
          background: white;
          padding: 1.5rem;
          margin-bottom: 1.5rem;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .question-card h3 {
          margin-bottom: 0.5rem;
          color: #333;
        }

        .answers {
          margin-top: 1rem;
        }

        .answer-option {
          padding: 1rem;
          margin: 0.5rem 0;
          border: 2px solid #ddd;
          border-radius: 8px;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 0.5rem;
          transition: all 0.2s;
        }

        .answer-option:hover {
          border-color: #4CAF50;
          background: #f0f8f0;
        }

        .answer-option.selected {
          border-color: #4CAF50;
          background: #e8f5e8;
        }

        .answer-option input {
          cursor: pointer;
        }

        .answer-option label {
          cursor: pointer;
          flex: 1;
        }

        .quiz-actions {
          text-align: center;
          padding: 2rem 0;
        }

        .submit-btn {
          padding: 1rem 3rem;
          font-size: 1.1rem;
          background: #4CAF50;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .submit-btn:hover:not(:disabled) {
          background: #45a049;
          transform: translateY(-2px);
        }

        .submit-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
};

export default PlayQuiz;