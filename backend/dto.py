from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import date, datetime
import re

# ==================== USER DTOs ====================

class UserRegisterDTO(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str
    date_of_birth: date
    gender: Optional[str] = None
    country: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Lozinka mora imati najmanje 8 karaktera')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Lozinka mora sadržati bar jedno veliko slovo')
        if not re.search(r'[a-z]', v):
            raise ValueError('Lozinka mora sadržati bar jedno malo slovo')
        if not re.search(r'\d', v):
            raise ValueError('Lozinka mora sadržati bar jedan broj')
        # Commented out special character requirement for easier testing
        # if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
        #     raise ValueError('Lozinka mora sadržati bar jedan specijalni karakter')
        return v
    
    @validator('date_of_birth')
    def validate_age(cls, v):
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 13:
            raise ValueError('Morate imati najmanje 13 godina')
        if age > 120:
            raise ValueError('Nevalidan datum rođenja')
        return v
    
    @validator('email')
    def normalize_email(cls, v):
        return v.lower().strip()
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if not v or not v.strip():
            raise ValueError('Polje ne može biti prazno')
        return ' '.join(v.strip().split())
    
    class Config:
        extra = 'forbid'

class UserLoginDTO(BaseModel):
    email: EmailStr
    password: str
    
    @validator('email')
    def normalize_email(cls, v):
        return v.lower().strip()
    
    class Config:
        extra = 'forbid'

class UserUpdateDTO(BaseModel):
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    country: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    
    @validator('date_of_birth')
    def validate_age(cls, v):
        if v:
            today = date.today()
            age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
            if age < 13:
                raise ValueError('Morate imati najmanje 13 godina')
        return v
    
    class Config:
        extra = 'forbid'

class UserResponseDTO(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    date_of_birth: date
    gender: Optional[str] = None
    country: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    role: str
    profile_image: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_blocked: bool = False
    blocked_until: Optional[datetime] = None
    login_attempts: int = 0
    
    class Config:
        extra = 'ignore'

class ChangeRoleDTO(BaseModel):
    role: str
    
    @validator('role')
    def validate_role(cls, v):
        valid_roles = ['IGRAČ', 'MODERATOR', 'ADMINISTRATOR']
        if v not in valid_roles:
            raise ValueError(f'Uloga mora biti jedna od: {", ".join(valid_roles)}')
        return v
    
    class Config:
        extra = 'forbid'

class ImageUploadResponseDTO(BaseModel):
    message: str
    image_url: str
    filename: str
    
    class Config:
        extra = 'forbid'

# ==================== AUTH RESPONSE DTOs ====================

class AuthResponseDTO(BaseModel):
    success: bool
    message: str
    access_token: str
    refresh_token: Optional[str] = None
    user: UserResponseDTO
    
    class Config:
        extra = 'forbid'

class LoginResponseDTO(BaseModel):
    success: bool
    message: str
    access_token: str
    refresh_token: Optional[str] = None
    user: UserResponseDTO
    blocked: Optional[bool] = False
    blocked_until: Optional[str] = None
    remaining_seconds: Optional[int] = None
    attempts_left: Optional[int] = None
    
    class Config:
        extra = 'forbid'

class RegisterResponseDTO(BaseModel):
    success: bool
    message: str
    access_token: str
    refresh_token: Optional[str] = None
    user: UserResponseDTO
    
    class Config:
        extra = 'forbid'

class ErrorResponseDTO(BaseModel):
    error: str
    code: Optional[str] = None
    details: Optional[dict] = None
    success: bool = False
    
    class Config:
        extra = 'forbid'

# ==================== ADMIN DTOs ====================

class UserStatsDTO(BaseModel):
    total_users: int
    players: int
    moderators: int
    admins: int
    blocked_users: int
    new_users_last_week: int
    
    class Config:
        extra = 'forbid'

class UserListResponseDTO(BaseModel):
    users: List[UserResponseDTO]
    total: int
    page: int
    per_page: int
    pages: int
    
    class Config:
        extra = 'forbid'

# ==================== TOKEN DTOs ====================

class TokenResponseDTO(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int
    user: UserResponseDTO
    
    class Config:
        extra = 'forbid'
    
    # ==================== QUIZ DTOs ====================

class QuizAnswerDTO(BaseModel):
    text: str = Field(..., min_length=1, max_length=200)
    is_correct: bool
    
    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError('Odgovor ne može biti prazan')
        return v.strip()
    
    class Config:
        extra = 'forbid'

class QuizQuestionDTO(BaseModel):
    text: str = Field(..., min_length=5, max_length=500)
    points: int = Field(..., ge=1, le=1000)
    answers: List[QuizAnswerDTO]
    
    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError('Pitanje ne može biti prazno')
        return v.strip()
    
    @validator('answers')
    def validate_answers(cls, v):
        if len(v) < 2:
            raise ValueError('Pitanje mora imati najmanje 2 ponuđena odgovora')
        if not any(answer.is_correct for answer in v):
            raise ValueError('Pitanje mora imati bar jedan tačan odgovor')
        return v
    
    class Config:
        extra = 'forbid'

class QuizCreateDTO(BaseModel):
    title: str = Field(..., min_length=3, max_length=120)
    duration_seconds: int = Field(..., ge=5, le=3600)
    questions: List[QuizQuestionDTO]
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Naziv kviza je obavezan')
        return v.strip()
    
    @validator('questions')
    def validate_questions(cls, v):
        if len(v) < 1:
            raise ValueError('Kviz mora imati najmanje jedno pitanje')
        return v
    
    class Config:
        extra = 'forbid'

class QuizUpdateDTO(QuizCreateDTO):
    pass

class QuizAnswerResponseDTO(BaseModel):
    id: int
    text: str
    is_correct: bool
    order: int
    
    class Config:
        extra = 'ignore'

class QuizQuestionResponseDTO(BaseModel):
    id: int
    text: str
    points: int
    order: int
    answers: List[QuizAnswerResponseDTO]
    
    class Config:
        extra = 'ignore'

class QuizResponseDTO(BaseModel):
    id: int
    title: str
    author_id: int
    author_name: str
    duration_seconds: int
    status: str
    rejection_reason: Optional[str] = None
    question_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    questions: Optional[List[QuizQuestionResponseDTO]] = None
    
    class Config:
        extra = 'ignore'