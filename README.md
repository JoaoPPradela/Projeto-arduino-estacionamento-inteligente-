# Estacionamento Inteligente • Vaga IoT (ITCOI)

> **PROJETO INTEGRADOR IoT • SENAI "CONDE JOSÉ VICENTE DE AZEVEDO"**  
> **Curso Técnico em Desenvolvimento de Sistemas | Módulo Específico I**  
> **Equipe:** João Pradela, João Palandi e Pedro Cesar  

---

## 1. Escopo e Matriz de Requisitos (Etapa 1)
O projeto resolve a dificuldade de visibilidade ao manobrar em vagas apertadas através de medição física contínua de distância com avisos progressivos (bipes e LEDs) e telemetria transmitida em rede local via MQTT/HTTP para um painel web com controle de atuadores.

* **Requisitos Funcionais (RF):**
  - **RF01:** Medir distância em centímetros (2 a 400 cm) via sensor ultrassônico HC-SR04.
  - **RF02:** Emitir bipes no buzzer com frequência proporcional à proximidade.
  - **RF03:** Sinalizar status com 3 LEDs (Verde >100cm, Amarelo 50-100cm, Vermelho <50cm).
  - **RF04:** Enviar telemetria via Serial e MQTT (`estacionamento/vaga01/distancia`).
  - **RF05:** Dashboard Web em tempo real exibindo centímetros, nível e histórico.
  - **RF06:** Emitir comandos remotos aos atuadores (abrir/fechar cancela e testar buzzer).
* **Requisitos Não Funcionais (RNF):**
  - **RNF01:** Tempo de resposta físico inferior a 50ms (sem delays bloqueantes).
  - **RNF02:** Operar de forma autônoma via Hotspot Wi-Fi da Raspberry Pi 3B.
  - **RNF03:** Armazenar leituras e logs de atuadores no banco SQLite (`schema.sql`).
  - **RNF04:** Interface responsiva atualizada via Fetch API assíncrona.

---

## 2. Pinagem e Simulação Virtual (Etapa 2 • TinkerCad)

| Componente | Terminal | Pino Arduino | Observação / Função |
| :--- | :--- | :--- | :--- |
| **HC-SR04** | VCC / GND | **5V / GND** | Alimentação positiva e terra comum |
| **HC-SR04** | TRIG | **Digital 9** | Disparo do pulso ultrassônico |
| **HC-SR04** | ECHO | **Digital 10** | Retorno do eco (leitura dos cm) |
| **Buzzer** | (+) / (-) | **Digital 8 / GND** | Alertas sonoros progressivos |
| **LED Verde** | Ânodo (+) | **Digital 5** | Resistor 220 $\Omega$ / Longe (> 100 cm) |
| **LED Amarelo**| Ânodo (+) | **Digital 6** | Resistor 220 $\Omega$ / Atenção (50 a 100 cm) |
| **LED Vermelho**| Ânodo (+) | **Digital 7** | Resistor 220 $\Omega$ / Muito Perto (< 50 cm) |
| **Micro Servo**| Sinal | **Digital 11** | Cancela do estacionamento (0° a 90°) |

---

## 3. Arquitetura de Rede e Broker MQTT (Etapa 3 • Raspberry Pi 3B)

```
[ Arduino Uno R3 ] --(USB Serial / 9600 bps)--> [ Raspberry Pi 3B (Gateway) ]
                                                        ├── Hotspot Wi-Fi Local (192.168.4.1)
                                                        ├── Broker MQTT Mosquitto (:1883)
                                                        │     ├── Sub: estacionamento/vaga01/distancia
                                                        │     └── Pub: estacionamento/vaga01/atuadores
                                                        └── API Python Flask & SQLite (:5000)
```

### Instalação na Raspberry Pi:
```bash
sudo apt update && sudo apt install -y mosquitto mosquitto-clients python3-pip
pip install paho-mqtt pyserial flask
```

---

## 4. Banco de Dados e Modelagem DER (Etapa 4)
O arquivo [`schema.sql`](schema.sql) implementa os scripts normalizados:
* **Tabela `vagas`:** Cadastro e estado da vaga (`codigo`, `nome`, `status`).
* **Tabela `leituras`:** Histórico temporal (`vaga_codigo`, `distancia_cm`, `nivel_alerta`, `sensor_status`, `data_hora`).
* **Tabela `logs_atuadores`:** Registro de comandos remotos (`atuador`, `acao`, `origem`, `data_hora`).

---

## 5. Rotas da API REST (Etapa 5)

* `GET /api/vaga/status`: Retorna a distância atual, níveis, LEDs e estado da cancela.
* `POST /api/leituras`: Recebe payload `{"distancia_cm": 68.0}` e persiste no banco.
* `GET /api/leituras/historico`: Retorna as últimas 8 medições.
* `POST /api/atuadores/comando`: Recebe `{"atuador": "cancela", "acao": "ABRIR"}` e aciona o servo.

---

## 6. Como Rodar e Demonstrar

1. **Gravar no Arduino:** Abra `arduino.ino` na Arduino IDE e carregue na placa.
2. **Conectar na Raspberry Pi:** Plugue o cabo USB do Arduino em qualquer porta USB da Raspberry Pi (ou PC).
3. **Iniciar a Aplicação:**
   ```bash
   python app.py
   ```
   *(Acesse no navegador: `http://127.0.0.1:5000`)*.
4. **Teste Prático:** Aproxime a mão do sensor HC-SR04: os centímetros cairão ao vivo na tela, o buzzer apitará mais rápido, os LEDs alternarão e você poderá clicar em *"Abrir Cancela"* e *"Testar Buzzer"*.

