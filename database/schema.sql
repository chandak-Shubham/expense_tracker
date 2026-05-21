--table-1 users(sign up/login)

CREATE TABLE users(
    user_id SERIAL PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL,
    user_email VARCHAR(150) UNIQUE NOT NULL,
    user_password VARCHAR(255) NOT NULL
);

-- table 2 FRIENDS

CREATE TABLE friends(
    friendship_id SERIAL PRIMARY KEY,
    user1_id INTEGER NOT NULL,
    user2_id INTEGER NOT NULL,
    FOREIGN KEY (user1_id) REFERENCES users(user_id),
    FOREIGN KEY (user2_id) REFERENCES users(user_id),
    CHECK (user1_id <> user2_id), --(1,5) AND (5,1) both can come in database and becoz of this if 1 adds 5 friend...it will work only unidirectionly not bidrectional
    UNIQUE (user1_id, user2_id)
);

-- table 3 expenses

CREATE TABLE expenses(
    expense_id SERIAL PRIMARY KEY,
    description VARCHAR(255) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL CHECK(total_amount>0),
    created_by INTEGER NOT NULL,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- table 4 expense details

CREATE TABLE expense_details(
    detail_id SERIAL PRIMARY KEY,
    expense_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    paid_amount DECIMAL(10,2) DEFAULT 0 CHECK(paid_amount >= 0),
    owed_amount DECIMAL(10,2) NOT NULL CHECK(owed_amount >= 0),
    FOREIGN KEY (expense_id) REFERENCES expenses(expense_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(expense_id,user_id)
);