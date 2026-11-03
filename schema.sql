-- ========================================================
-- PROJETO INTEGRADOR IoT • SENAI "CONDE JOSÉ VICENTE DE AZEVEDO"
-- SCRIPT DE BANCO DE DADOS: DDL (Definição) e DML (Dados Iniciais)
-- Integrantes: João Pradela, João Palandi e Pedro Cesar
-- ========================================================

-- 1. DDL: Criação das Tabelas Normalizadas
CREATE TABLE IF NOT EXISTS vagas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE NOT NULL,
    nome TEXT NOT NULL,
    status TEXT DEFAULT 'LIVRE',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS leituras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vaga_codigo TEXT NOT NULL,
    distancia_cm REAL NOT NULL,
    nivel_alerta TEXT NOT NULL,
    descricao_alerta TEXT NOT NULL,
    sensor_status TEXT NOT NULL,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vaga_codigo) REFERENCES vagas(codigo)
);

CREATE TABLE IF NOT EXISTS logs_atuadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    atuador TEXT NOT NULL,       -- 'cancela', 'buzzer', 'leds'
    acao TEXT NOT NULL,          -- 'ABERTO', 'FECHADO', 'TESTE', 'BIPE'
    origem TEXT NOT NULL,        -- 'MANUAL_WEB', 'AUTOMATICO_SENSOR'
    detalhes TEXT,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. DML: Inserção de Registros Iniciais
INSERT OR IGNORE INTO vagas (codigo, nome, status) 
VALUES ('VAGA-01', 'Vaga 01 - Traseira', 'LIVRE');

INSERT OR IGNORE INTO leituras (vaga_codigo, distancia_cm, nivel_alerta, descricao_alerta, sensor_status)
VALUES ('VAGA-01', 68.0, 'Atenção', 'Bipes moderados', 'Ativo');

INSERT OR IGNORE INTO logs_atuadores (atuador, acao, origem, detalhes)
VALUES ('cancela', 'FECHADO', 'SISTEMA', 'Inicialização padrão da cancela');

