CREATE TABLE users (
	id SERIAL PRIMARY KEY,
	username VARCHAR(100) NOT NULL,
	email VARCHAR(100) NOT NULL,
	password TEXT NOT NULL,
	created_at DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE transactions (
	id SERIAL PRIMARY KEY,
	date DATE NOT NULL,
	description TEXT NOT NULL,
	category VARCHAR(30) NOT NULL,
	card VARCHAR(30) NOT NULL,
	amount DECIMAL(9, 2) NOT NULL,
	user_id INTEGER NOT NULL,
	FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE categories (
	id SERIAL PRIMARY KEY,
	category_name VARCHAR(30) NOT NULL
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    role VARCHAR(5) NOT NULL,
    message TEXT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id)
);

CREATE TABLE cards (
	id SERIAL PRIMARY KEY,
	name VARCHAR(30) NOT NULL,
	type VARCHAR(30) NOT NULL,
	last_numbers VARCHAR(4) NOT NULL,
	expired_date DATE NOT NULL,
	background_color VARCHAR(30) NOT NULL,
	color VARCHAR(30) NOT NULL,
	user_id INT NOT NULL,
	created_at DATE NOT NULL DEFAULT CURRENT_DATE,
	FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE user_settings (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    temperature NUMERIC(2, 1) NOT NULL DEFAULT 0.5 CHECK (temperature BETWEEN 0 AND 1),
    theme VARCHAR(10) NOT NULL DEFAULT 'dark' CHECK (theme IN ('dark', 'light'))
);