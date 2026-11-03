/*
  PROJETO INTEGRADOR IoT - SENAI "CONDE JOSÉ VICENTE DE AZEVEDO"
  Estacionamento Inteligente • Vaga 01
  Autores: João Pradela, João Palandi e Pedro Cesar

  Pinagem Arduino Uno R3:
  - HC-SR04 Trig   -> Pino 9
  - HC-SR04 Echo   -> Pino 10
  - Buzzer (+)     -> Pino 8
  - LED Verde (+)  -> Pino 5 (resistor 220 ohms)
  - LED Amarelo (+) -> Pino 6 (resistor 220 ohms)
  - LED Vermelho (+)-> Pino 7 (resistor 220 ohms)
  - Micro Servo    -> Pino 11 (Cancela Mecânica)
  - GND de todos   -> Pino GND
*/

#include <Servo.h>

const int pinoTrig = 9, pinoEcho = 10, pinoBuzzer = 8;
const int ledVerde = 5, ledAmarelo = 6, ledVermelho = 7, pinoServo = 11;

Servo servoCancela;
unsigned long tempoBipe = 0, tempoSerial = 0;
bool buzzerStatus = false;
bool cancelaAberta = false;

void setup() {
  Serial.begin(9600);
  pinMode(pinoTrig, OUTPUT);
  pinMode(pinoEcho, INPUT);
  pinMode(pinoBuzzer, OUTPUT);
  pinMode(ledVerde, OUTPUT);
  pinMode(ledAmarelo, OUTPUT);
  pinMode(ledVermelho, OUTPUT);

  // Conecta o servo motor da cancela (padrão fechada a 0 graus)
  servoCancela.attach(pinoServo);
  servoCancela.write(0);

  // Teste inicial rápido dos LEDs
  digitalWrite(ledVerde, HIGH); digitalWrite(ledAmarelo, HIGH); digitalWrite(ledVermelho, HIGH);
  delay(300);
  digitalWrite(ledVerde, LOW); digitalWrite(ledAmarelo, LOW); digitalWrite(ledVermelho, LOW);

  Serial.println(F("{\"status\":\"pronto\",\"sistema\":\"Estacionamento IoT SENAI\"}"));
}

float medirDistancia() {
  digitalWrite(pinoTrig, LOW);
  delayMicroseconds(2);
  digitalWrite(pinoTrig, HIGH);
  delayMicroseconds(10);
  digitalWrite(pinoTrig, LOW);

  long duracao = pulseIn(pinoEcho, HIGH, 30000);
  if (duracao == 0) return -1.0;
  return (duracao * 0.0343) / 2.0;
}

void controlarLeds(float dist) {
  digitalWrite(ledVerde, dist > 100 ? HIGH : LOW);
  digitalWrite(ledAmarelo, (dist >= 50 && dist <= 100) ? HIGH : LOW);
  digitalWrite(ledVermelho, (dist > 0 && dist < 50) ? HIGH : LOW);
}

void controlarBuzzer(float dist) {
  if (dist < 0 || dist > 200) { noTone(pinoBuzzer); return; }
  if (dist < 15) { tone(pinoBuzzer, 2400); return; } // Parada crítica contínua

  unsigned long intervalo = (dist < 50) ? 150 : ((dist <= 100) ? 400 : 800);
  int frequencia = (dist < 50) ? 2200 : ((dist <= 100) ? 1900 : 1600);

  unsigned long agora = millis();
  if (agora - tempoBipe >= intervalo) {
    tempoBipe = agora;
    buzzerStatus = !buzzerStatus;
    if (buzzerStatus) tone(pinoBuzzer, frequencia);
    else noTone(pinoBuzzer);
  }
}

// Processa comandos remotos recebidos da API / Web (Requisito 4.5)
void processarComandosRemotos() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.startsWith("C:ABRIR")) {
      servoCancela.write(90); // Abre cancela
      cancelaAberta = true;
    } else if (cmd.startsWith("C:FECHAR")) {
      servoCancela.write(0);  // Fecha cancela
      cancelaAberta = false;
    } else if (cmd.startsWith("B:TESTE")) {
      tone(pinoBuzzer, 2000, 400); // Beep de teste remoto
    }
  }
}

void loop() {
  float distancia = medirDistancia();
  controlarLeds(distancia);
  controlarBuzzer(distancia);
  processarComandosRemotos();

  // Envia a telemetria via serial a cada 250ms
  unsigned long agora = millis();
  if (agora - tempoSerial >= 250) {
    tempoSerial = agora;
    if (distancia >= 0) {
      Serial.print(F("{\"distancia_cm\":"));
      Serial.print(distancia, 1);
      Serial.println(F("}"));
    }
  }
  delay(20);
}
