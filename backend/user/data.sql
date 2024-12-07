
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

USE Wonder_fur;

INSERT INTO users (username, email, password) VALUES
('alice', 'alice@example.com', MD5('wonderland')),
('bob', 'bob@example.com', MD5('buildit123')),
('charlie', 'charlie@example.com', MD5('funny456'));



