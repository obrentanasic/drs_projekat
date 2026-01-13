-- Kreiranje baze podataka (već postoji iz environment variable)
-- \c quizplatform_db1; -- Nije potrebno, već smo u bazi

-- Kreiranje dodatnog korisnika sa privilegijama
CREATE USER IF NOT EXISTS quiz_app WITH PASSWORD 'quiz_app_password';
GRANT CONNECT ON DATABASE quizplatform_db1 TO quiz_app;

-- Tabela korisnika
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_blocked BOOLEAN DEFAULT FALSE,
    blocked_until TIMESTAMP,
    
    CONSTRAINT check_age CHECK (date_of_birth <= CURRENT_DATE - INTERVAL '13 years'),
    CONSTRAINT valid_role CHECK (role IN ('IGRAČ', 'MODERATOR', 'ADMINISTRATOR'))
);

-- Tabela login pokušaja
CREATE TABLE IF NOT EXISTS login_attempts (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) NOT NULL,
    attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    successful BOOLEAN DEFAULT FALSE,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Tabela za odobravanje kvizova
CREATE TABLE IF NOT EXISTS quiz_approvals (
    id SERIAL PRIMARY KEY,
    quiz_id VARCHAR(100) NOT NULL,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    approved_at TIMESTAMP,
    rejected_reason TEXT,
    admin_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'approved', 'rejected'))
);

-- Indeksi
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_login_attempts_email ON login_attempts(email);
CREATE INDEX IF NOT EXISTS idx_login_attempts_time ON login_attempts(attempt_time);
CREATE INDEX IF NOT EXISTS idx_quiz_approvals_status ON quiz_approvals(status);

-- Funkcija za updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE OR REPLACE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Default admin (lozinka: Admin123!)
INSERT INTO users (
    first_name, last_name, email, password_hash, 
    date_of_birth, role, country
) VALUES (
    'Admin',
    'User',
    'admin@quizplatform.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    '1990-01-01',
    'ADMINISTRATOR',
    'Serbia'
) ON CONFLICT (email) DO NOTHING;

-- Test moderator (lozinka: Moderator123!)
INSERT INTO users (
    first_name, last_name, email, password_hash, 
    date_of_birth, role, country
) VALUES (
    'Moderator',
    'Test',
    'moderator@quizplatform.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    '1995-05-15',
    'MODERATOR',
    'Serbia'
) ON CONFLICT (email) DO NOTHING;

-- Test player (lozinka: Player123!)
INSERT INTO users (
    first_name, last_name, email, password_hash, 
    date_of_birth, role, country
) VALUES (
    'Test',
    'Player',
    'player@quizplatform.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    '2000-10-20',
    'IGRAČ',
    'Serbia'
) ON CONFLICT (email) DO NOTHING;

-- Grant privilegije
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO quiz_user, quiz_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO quiz_user, quiz_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO quiz_user, quiz_app;

-- Informacije
SELECT '✅ Database setup complete!' as message;
SELECT COUNT(*) as total_users FROM users;
SELECT email, role FROM users ORDER BY role;