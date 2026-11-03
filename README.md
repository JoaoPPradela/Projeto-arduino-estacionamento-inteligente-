# Estacionamento Inteligente • Vaga IoT

> **PROJETO INTEGRADOR • INTERNET DAS COISAS (IoT)**  
> **SENAI • Curso Técnico em Desenvolvimento de Sistemas**  
> **Integrantes da Equipe:** João Pradela, João Palandi e Pedro Cesar  

---

## 1. Como Funciona a Conexão Física (Arduino + Raspberry Pi)

A **Raspberry Pi 3B** e o **Arduino Uno R3** comunicam-se em tempo real através do **Cabo USB**:

```
+----------------+                +------------------+                +------------------+
| SENSOR HC-SR04 |  (4 Jumpers)   |  ARDUINO UNO R3  |   (Cabo USB)   | RASPBERRY PI 3B  |
| Mede a distância| -------------> | Processa bipes,  | -------------> | Servidor Flask,  |
| em centímetros |                | LEDs e Serial    |                | SQLite e Web     |
+----------------+                +------------------+                +------------------+
                                                                               |
                                                                               v
                                                                      +------------------+
                                                                      | TELA NO NAVEGADOR|
                                                                      | Mostra os cm     |
                                                                      | em tempo real!   |
                                                                      +------------------+
```

1. O **Sensor HC-SR04** fica apontado para onde o carro manobra.
2. O **Arduino** calcula a distância física em centímetros instantaneamente:
   - Se o objeto estiver **a mais de 100 cm:** Bipes lentos e **LED Verde**.
   - Se o objeto estiver **entre 50 e 100 cm:** Bipes moderados e **LED Amarelo** *(Slide 08: 68 cm)*.
   - Se o objeto estiver **a menos de 50 cm:** Bipes rápidos e **LED Vermelho**.
   - Se o objeto encostar **a menos de 15 cm:** Bipe contínuo (Emergência / PARE!).
3. Pelo **Cabo USB**, o Arduino envia os centímetros medidos para a Raspberry Pi a cada 250ms (4 vezes por segundo).
4. A **Raspberry Pi** recebe os centímetros, salva no banco SQLite e a **Tela Web** atualiza instantaneamente na frente do usuário!

---

## 2. Coordenadas de Conexão no Arduino (Pinagem)

| Componente | Pino do Componente | Conectar no Arduino | Observação |
| :--- | :--- | :--- | :--- |
| **HC-SR04 (Sensor)** | **VCC** | **5V** | Alimentação positiva (5 Volts) |
| **HC-SR04 (Sensor)** | **GND** | **GND** | Terra (Negativo comum) |
| **HC-SR04 (Sensor)** | **TRIG** | **Pino Digital 9** | Disparo do sinal ultrassônico |
| **HC-SR04 (Sensor)** | **ECHO** | **Pino Digital 10** | Retorno do eco (leitura da distância) |
| **Buzzer** | **Positivo (+)** | **Pino Digital 8** | Emissão dos bipes sonoros |
| **Buzzer** | **Negativo (-)** | **GND** | Conectado ao GND |
| **LED Verde** | **Ânodo (+)** | **Pino Digital 5** | Usar resistor de 220 $\Omega$ em série |
| **LED Verde** | **Cátodo (-)** | **GND** | Perna curta no negativo |
| **LED Amarelo** | **Ânodo (+)** | **Pino Digital 6** | Usar resistor de 220 $\Omega$ em série |
| **LED Amarelo** | **Cátodo (-)** | **GND** | Perna curta no negativo |
| **LED Vermelho** | **Ânodo (+)** | **Pino Digital 7** | Usar resistor de 220 $\Omega$ em série |
| **LED Vermelho** | **Cátodo (-)** | **GND** | Perna curta no negativo |
| **Cabo USB** | **USB Arduino** | **USB Raspberry Pi** | Comunicação Serial + Alimentação |

---

## 3. Estrutura do Projeto

```
Projeto ICOT/
├── app.py              # Servidor Flask com rotas, banco SQLite e leitura USB integrada
├── leitor_arduino.py   # Script de conexão serial Arduino <-> Raspberry Pi
├── simulador.py        # Simulador para testar pelo terminal sem o hardware
├── arduino.ino         # Código C++ para gravar na placa Arduino Uno
├── templates/
│   └── index.html      # Tela Web (layout fiel ao Slide 08 da Apresentação)
├── static/
│   ├── style.css       # Estilos da página
│   └── script.js       # JavaScript com atualização em tempo real e bipes
└── README.md           # Guia completo de instalação e montagem
```

---

## 4. Passo a Passo para Apresentar / Testar na Prática

### Passo 1: Gravar o código no Arduino
1. Abra o arquivo `arduino.ino` na **Arduino IDE**;
2. Conecte o Arduino na USB, selecione a placa *Arduino Uno* e a porta COM correspondente;
3. Clique em **Carregar (Upload)**.

### Passo 2: Conectar o Arduino na Raspberry Pi (ou no PC)
Plugue o cabo USB do Arduino em qualquer porta USB da Raspberry Pi ou do computador.

### Passo 3: Iniciar o Servidor
No terminal, execute:
```bash
python app.py
```
*O sistema abrirá a interface Web em `http://127.0.0.1:5000` e conectará automaticamente na porta USB do Arduino!*

### Passo 4: Ver o objeto se aproximando em tempo real!
* Aproxime a mão ou um obstáculo do sensor **HC-SR04**:
  - Conforme sua mão se aproxima, a distância na tela diminui em centímetros ao vivo;
  - O carrinho na tela avança em direção à parede;
  - O buzzer apita cada vez mais rápido;
  - Os LEDs físicos no circuito alternam entre **Verde**, **Amarelo** e **Vermelho**!
