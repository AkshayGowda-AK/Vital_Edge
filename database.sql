-- Create Database
CREATE DATABASE IF NOT EXISTS vitaledge;
USE vitaledge;

---

-- Users Table

---

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100),
    email VARCHAR(150),
    password VARCHAR(255),
    city VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

---

-- Products Table

---

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200),
    description TEXT,
    price DECIMAL(10,2),
    category VARCHAR(100),
    image_url TEXT,
    purchase_link TEXT,
    source VARCHAR(50),
    added_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

---

-- Cart Table

---

CREATE TABLE cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    product_id INT,
    quantity INT DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
