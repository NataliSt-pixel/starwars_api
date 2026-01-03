CREATE TABLE IF NOT EXISTS characters (
    id SERIAL PRIMARY KEY,
    uid INTEGER UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    birth_year VARCHAR(20),
    eye_color VARCHAR(50),
    gender VARCHAR(50),
    hair_color VARCHAR(50),
    homeworld VARCHAR(255),
    mass VARCHAR(20),
    skin_color VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_characters_name ON characters(name);
CREATE INDEX IF NOT EXISTS idx_characters_gender ON characters(gender);
CREATE INDEX IF NOT EXISTS idx_characters_homeworld ON characters(homeworld);
CREATE INDEX IF NOT EXISTS idx_characters_uid ON characters(uid);

INSERT INTO characters (uid, name, birth_year, eye_color, gender, hair_color, homeworld, mass, skin_color)
VALUES
    (1, 'Luke Skywalker', '19BBY', 'blue', 'male', 'blond', 'https://www.swapi.tech/api/planets/1', '77', 'fair'),
    (2, 'C-3PO', '112BBY', 'yellow', 'n/a', 'n/a', 'https://www.swapi.tech/api/planets/1', '75', 'gold'),
    (3, 'R2-D2', '33BBY', 'red', 'n/a', 'n/a', 'https://www.swapi.tech/api/planets/8', '32', 'white, blue'),
    (4, 'Darth Vader', '41.9BBY', 'yellow', 'male', 'none', 'https://www.swapi.tech/api/planets/1', '136', 'white'),
    (5, 'Leia Organa', '19BBY', 'brown', 'female', 'brown', 'https://www.swapi.tech/api/planets/2', '49', 'light')
ON CONFLICT (uid) DO NOTHING;