# DOSSIÊ TÉCNICO • PROJETO INTEGRADOR IoT (ITCOI)

**ESCOLA E FACULDADE SENAI "CONDE JOSÉ VICENTE DE AZEVEDO"**  
**Curso Técnico em Desenvolvimento de Sistemas | Novo Ensino Médio (SESI-SENAI)**  
**Unidade Curricular:** Internet das Coisas (ITCOI - 75H) • Módulo Específico I  
**Tema:** "Desafio IoT 360°: Soluções Conectadas para a Indústria e a Sociedade"  
**Equipe:** João Pradela, João Palandi e Pedro Cesar  
**Projeto:** Estacionamento Inteligente com Auxílio Acústico, Visual, Telemetria MQTT e Controle Remoto de Atuadores  

---

## 1. ETAPA 1 • Matriz de Requisitos e Escopo (RF / RNF)

### 1.1. Contexto e Problema
Estacionar em garagens apertadas e docas de carga traz alto risco de colisões por ponto cego traseiro. A solução desenvolvida automatiza a vaga com sensor de eco ultrassônico, alertas sonoros e luminosos progressivos, telemetria em tempo real transmitida via rede local (MQTT/HTTP) e painel web responsivo com controle de atuadores.

### 1.2. Requisitos Funcionais (RF)
* **RF01 – Medição Ultrassônica:** O sensor HC-SR04 deve capturar a distância em centímetros (alcance operacional de 2 cm a 400 cm).
* **RF02 – Sinalização Sonora Progressiva:** O buzzer deve aumentar a cadência dos bipes conforme o objeto se aproxima (lento >100cm, moderado 50-100cm, rápido <50cm e contínuo <15cm).
* **RF03 – Sinalização Visual Local:** Três LEDs devem refletir a zona de risco: Verde (Seguro), Amarelo (Atenção) e Vermelho (Crítico).
* **RF04 – Comunicação Serial & MQTT:** O microcontrolador deve enviar dados via Serial USB e publicar no Broker MQTT no tópico `estacionamento/vaga01/distancia`.
* **RF05 – Painel Web em Tempo Real:** Exibir a distância em tempo real em centímetros, estado do sensor, alertas sonoros e histórico.
* **RF06 – Comando Remoto aos Atuadores (Item 4.5):** A interface web deve permitir abrir/fechar a cancela física (Micro Servo) e disparar bipes de teste no buzzer.

### 1.3. Requisitos Não Funcionais (RNF)
* **RNF01 – Baixa Latência:** Resposta física no microcontrolador em menos de 50ms (lógica assíncrona com `millis()`, sem `delay()` bloqueante).
* **RNF02 – Operação em Rede Local Autônoma:** Operar via Hotspot Wi-Fi da Raspberry Pi 3B sem dependência de internet.
* **RNF03 – Persistência Relacional Normalizada:** Gravação histórica estruturada em SQLite através do script DDL/DML [`schema.sql`](schema.sql).
* **RNF04 – Interface Web Responsiva:** Atualização assíncrona rápida (Fetch API) sem recarregamento de página.

---

## 2. ETAPA 2 • Simulação Virtual e Hardware (TinkerCad Circuits)

### 2.1. Mapa de Pinagem do Arduino Uno R3

| Componente | Terminal | Pino no Arduino | Função / Observação Técnica |
| :--- | :--- | :--- | :--- |
| **Sensor HC-SR04** | VCC | **5V** | Alimentação positiva de 5V |
| **Sensor HC-SR04** | GND | **GND** | Terra de referência comum |
| **Sensor HC-SR04** | TRIG | **Digital 9** | Disparo do pulso sonoro (Trigger 10µs) |
| **Sensor HC-SR04** | ECHO | **Digital 10** | Leitura da largura do pulso de retorno |
| **Buzzer Piezo** | (+) / (-) | **Digital 8 / GND** | PWM de áudio (frequências de 1600 Hz a 2400 Hz) |
| **LED Verde** | Ânodo (+) | **Digital 5** | Resistor 220 $\Omega$ / Zona Segura (> 100 cm) |
| **LED Amarelo**| Ânodo (+) | **Digital 6** | Resistor 220 $\Omega$ / Atenção (50 a 100 cm) |
| **LED Vermelho**| Ânodo (+) | **Digital 7** | Resistor 220 $\Omega$ / Zona Crítica (< 50 cm) |
| **Micro Servo**| Sinal | **Digital 11** | Controle angular da cancela (0° fechada, 90° aberta) |

### 2.2. Lógica Matemática do Sensor:
$$\text{distância (cm)} = \frac{\text{tempo de eco (µs)} \times 0.0343}{2}$$

---

## 3. ETAPA 3 • Arquitetura de Redes & Broker MQTT (Raspberry Pi 3B)

```
[ Arduino Uno R3 ] --(USB Serial / 9600 bps)--> [ Raspberry Pi 3B (Gateway) ]
                                                        ├── Hotspot Wi-Fi Local (192.168.4.1)
                                                        ├── Broker MQTT Mosquitto (:1883)
                                                        │     ├── Tópico Sub: estacionamento/vaga01/distancia
                                                        │     └── Tópico Pub: estacionamento/vaga01/atuadores
                                                        └── API Python FastAPI & SQLite (:5000) • Swagger (/docs)
```

### Configuração no Raspberry Pi OS:
```bash
sudo apt update && sudo apt install -y mosquitto mosquitto-clients
pip install paho-mqtt pyserial fastapi uvicorn
```

---

## 4. ETAPA 4 • Modelagem de Dados (MER / DER e SQL)

### 4.1. Diagrama Entidade-Relacionamento (DER)
```
+--------------------+           +-------------------------+
|       VAGAS        | 1       N |        LEITURAS         |
+--------------------+-----------+-------------------------+
| PK id (INT)        |           | PK id (INT)             |
| UK codigo (TEXT)   |           | FK vaga_codigo (TEXT)   |
|    nome (TEXT)     |           |    distancia_cm (REAL)  |
|    status (TEXT)   |           |    nivel_alerta (TEXT)  |
+--------------------+           |    descricao_alerta(TEXT|
                                 |    sensor_status (TEXT) |
+--------------------+           |    data_hora (TIMESTAMP)|
|   LOGS_ATUADORES   |           +-------------------------+
+--------------------+
| PK id (INT)        |
|    atuador (TEXT)  |
|    acao (TEXT)     |
|    origem (TEXT)   |
|    data_hora (TIME)|
+--------------------+
```

* Os scripts completos **DDL** (`CREATE TABLE`) e **DML** (`INSERT`) estão organizados em [`schema.sql`](schema.sql).

---

## 5. ETAPA 5 • Especificação das Rotas REST (API Flask)

| Método | Endpoint | Entrada (JSON) | Resposta | Finalidade |
| :---: | :--- | :--- | :--- | :--- |
| `GET` | `/api/vaga/status` | - | `200 OK` (JSON) | Telemetria ao vivo e status da cancela |
| `POST`| `/api/leituras` | `{"distancia_cm": 68.0}` | `201 Created` | Registra medição do sensor |
| `GET` | `/api/leituras/historico` | - | `200 OK` (Array) | Histórico recente para a tabela |
| `POST`| `/api/atuadores/comando` | `{"atuador":"cancela","acao":"ABRIR"}` | `200 OK` | Comando remoto para o Micro Servo/Buzzer |
