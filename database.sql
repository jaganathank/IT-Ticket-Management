PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    fullname TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('employee','it'))
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    priority TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Open',
    employee_id INTEGER NOT NULL,
    assigned_to INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    resolution_notes TEXT,
    FOREIGN KEY(employee_id) REFERENCES users(id),
    FOREIGN KEY(assigned_to) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    comment TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(ticket_id) REFERENCES tickets(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    created_by INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(ticket_id) REFERENCES tickets(id),
    FOREIGN KEY(created_by) REFERENCES users(id)
);

INSERT OR IGNORE INTO users (username, password, fullname, role) VALUES
('employee1', 'password1', 'Ravi Sharma', 'employee'),
('employee2', 'password2', 'Anita Patel', 'employee'),
('it1', 'passwordit', 'Nikhil Rao', 'it'),
('it2', 'passwordit2', 'Sanya Mehta', 'it');
