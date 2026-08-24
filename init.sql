CREATE DATABASE IF NOT EXISTS almox;

USE almox;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    tipo ENUM('admin','usuario') NOT NULL
);

CREATE TABLE itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    quantidade INT NOT NULL DEFAULT 0,
    horario TIME,
    responsavel VARCHAR(100)
);

CREATE TABLE movimentacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    tipo ENUM('ADICIONAR','RETIRAR') NOT NULL,
    quantidade INT NOT NULL,
    responsavel VARCHAR(100),
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES itens(id)
);

INSERT INTO usuarios (email, senha, tipo)
VALUES (
    'admin@gmail.com',
    '$2b$12$c2s6DR2K9bL6XaHha/GOKOhX2U321ADCXQWWSrpNzLJv5LssxByZ6',
    'admin'
);

SELECT * FROM   usuarios;
SELECT * FROM   itens;
SELECT * FROM   movimentacoes