CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS advertisements (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_ads_user_id ON advertisements(user_id);
CREATE INDEX IF NOT EXISTS idx_ads_created_at ON advertisements(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ads_title ON advertisements(title);
CREATE INDEX IF NOT EXISTS idx_ads_description ON advertisements(description);
INSERT INTO users (username, email, password_hash)
VALUES
    ('testuser', 'test@example.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW')
ON CONFLICT (username) DO NOTHING;

INSERT INTO advertisements (title, description, user_id)
VALUES
    ('Продам велосипед', 'Отличный горный велосипед, почти новый. Использовался всего несколько раз.', 1),
    ('Ищу работу Python разработчиком', 'Опыт 2 года в разработке на Python. Ищу удаленную работу или в офисе Москвы.', 1),
    ('Сдам квартиру', 'Сдам 2-комнатную квартиру в центре. Ремонт, вся техника. Долгосрочно.', 1)
ON CONFLICT DO NOTHING;