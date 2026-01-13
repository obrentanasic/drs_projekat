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
    gender: Optional[str]
    country: Optional[str]
    street: Optional[str]
    number: Optional[str]
    role: str
    profile_image: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
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

# ==================== AUTH DTOs ====================

class TokenResponseDTO(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int
    user: UserResponseDTO
    
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