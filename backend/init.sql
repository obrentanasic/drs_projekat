-- OVO JE ISPRAVLJENI init.sql
-- Ne kreiraj bazu - ona već postoji iz POSTGRES_DB environment variable

-- Konektuj se na već kreiranu bazu
\c quizplatform_db1;

-- Kreiraj tabelu users ako ne postoji
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10),
    country VARCHAR(50),
    street VARCHAR(100),
    number VARCHAR(20),
    role VARCHAR(20) NOT NULL DEFAULT 'IGRAČ',
    profile_image VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_blocked BOOLEAN DEFAULT FALSE,
    blocked_until TIMESTAMP
);

-- Kreiraj tabelu login_attempts ako ne postoji
CREATE TABLE IF NOT EXISTS login_attempts (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) NOT NULL,
    attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    successful BOOLEAN DEFAULT FALSE,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Dodaj test korisnike (ignoriši ako već postoje)
INSERT INTO users (first_name, last_name, email, password_hash, date_of_birth, role, country) VALUES
('Admin', 'User', 'admin@quizplatform.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', '1990-01-01', 'ADMINISTRATOR', 'Serbia'),
('Moderator', 'Test', 'moderator@quizplatform.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', '1995-05-15', 'MODERATOR', 'Serbia'),
('Test', 'Player', 'player@quizplatform.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', '2000-10-20', 'IGRAČ', 'Serbia')
ON CONFLICT (email) DO NOTHING;

SELECT '✅ Database initialized successfully!' as message;
SELECT COUNT(*) as total_users FROM users;