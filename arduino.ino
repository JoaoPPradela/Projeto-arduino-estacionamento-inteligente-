/*
  PROJETO INTEGRADOR - INTERNET DAS COISAS (IoT)
  Estacionamento Inteligente • Vaga 01
  SENAI - Curso Técnico em Desenvolvimento de Sistemas
  Integrantes: João Pradela, João Palandi e Pedro Cesar

  Conexões no Arduino Uno R3:
  - HC-SR04 Trig   -> Pino Digital 9
  - HC-SR04 Echo   -> Pino Digital 10
  - Buzzer (+)     -> Pino Digital 8
  - LED Verde (+)  -> Pino Digital 5 (com resistor 220 ohms)
  - LED Amarelo (+) -> Pino Digital 6 (com resistor 220 ohms)
  - LED Vermelho (+)-> Pino Digital 7 (com resistor 220 ohms)
  - GND de todos   -> Pino GND do Arduino
  - Cabo USB       -> Conectado na USB da Raspberry Pi ou Computador
*/

const int pinoTrig = 9;
const int pinoEcho = 10;
const int pinoBuzzer = 8;
const int ledVerde = 5;
const int ledAmarelo = 6;
const int ledVermelho = 7;

unsigned long tempoBipe = 0;
unsigned long tempoSerial = 0;
bool buzzerStatus = false;

void setup() {
  // Inicia a comunicação serial para mandar os centímetros para a Raspberry Pi
  Serial.begin(9600);

  pinMode(pinoTrig, OUTPUT);
  pinMode(pinoEcho, INPUT);

  pinMode(pinoBuzzer, OUTPUT);
  pinMode(ledVerde, OUTPUT);
  pinMode(ledAmarelo, OUTPUT);
  pinMode(ledVermelho, OUTPUT);

  // Pisca os 3 LEDs no início para indicar que o circuito ligou
  digitalWrite(ledVerde, HIGH);
  digitalWrite(ledAmarelo, HIGH);
  digitalWrite(ledVermelho, HIGH);
  delay(300);
  digitalWrite(ledVerde, LOW);
  digitalWrite(ledAmarelo, LOW);
  digitalWrite(ledVermelho, LOW);

  Serial.println("Arduino pronto! Medindo distancia...");
}

// Mede a distância em centímetros através do sensor HC-SR04
float medirDistancia() {
  digitalWrite(pinoTrig, LOW);
  delayMicroseconds(2);
  digitalWrite(pinoTrig, HIGH);
  delayMicroseconds(10);
  digitalWrite(pinoTrig, LOW);

  long duracao = pulseIn(pinoEcho, HIGH, 30000);
  if (duracao == 0) {
    return -1.0; // Sem leitura ou fora do alcance
  }

  // Distância em centímetros = (tempo * 0.0343) / 2
  return (duracao * 0.0343) / 2.0;
}

// Acende os LEDs físicos conforme o objeto se aproxima
void controlarLeds(float dist) {
  if (dist < 0 || dist > 400) {
    digitalWrite(ledVerde, LOW);
    digitalWrite(ledAmarelo, LOW);
    digitalWrite(ledVermelho, LOW);
  } else if (dist > 100) {
    // Objeto longe (> 100 cm): LED Verde
    digitalWrite(ledVerde, HIGH);
    digitalWrite(ledAmarelo, LOW);
    digitalWrite(ledVermelho, LOW);
  } else if (dist >= 50) {
    // Objeto em distância de atenção (50 a 100 cm): LED Amarelo
    digitalWrite(ledVerde, LOW);
    digitalWrite(ledAmarelo, HIGH);
    digitalWrite(ledVermelho, LOW);
  } else {
    // Objeto muito perto (< 50 cm): LED Vermelho
    digitalWrite(ledVerde, LOW);
    digitalWrite(ledAmarelo, LOW);
    digitalWrite(ledVermelho, HIGH);
  }
}

// Controla o ritmo dos bipes do buzzer conforme o objeto se aproxima
void controlarBuzzer(float dist) {
  if (dist < 0 || dist > 200) {
    noTone(pinoBuzzer);
    return;
  }

  // Se o objeto estiver colado (< 15 cm): bipe contínuo de parada emergencial
  if (dist < 15) {
    tone(pinoBuzzer, 2400);
    return;
  }

  // Intervalos conforme os slides:
  // - Menos de 50 cm: bipes rápidos (150ms)
  // - De 50 a 100 cm: bipes moderados (400ms)
  // - Mais de 100 cm: bipes lentos (800ms)
  unsigned long intervalo = 800;
  int frequencia = 1600;

  if (dist < 50) {
    intervalo = 150;
    frequencia = 2200;
  } else if (dist <= 100) {
    intervalo = 400;
    frequencia = 1900;
  }

  unsigned long agora = millis();
  if (agora - tempoBipe >= intervalo) {
    tempoBipe = agora;
    buzzerStatus = !buzzerStatus;

    if (buzzerStatus) {
      tone(pinoBuzzer, frequencia);
    } else {
      noTone(pinoBuzzer);
    }
  }
}

void loop() {
  float distancia = medirDistancia();

  // 1. Atualiza LEDs e Buzzer instantaneamente no circuito
  controlarLeds(distancia);
  controlarBuzzer(distancia);

  // 2. Envia os centímetros medidos para a Raspberry Pi a cada 250ms (4 vezes por segundo)
  unsigned long agora = millis();
  if (agora - tempoSerial >= 250) {
    tempoSerial = agora;

    if (distancia >= 0) {
      // Envia em formato JSON simples para a Raspberry Pi ler
      Serial.print("{\"distancia_cm\":");
      Serial.print(distancia, 1);
      Serial.println("}");
    }
  }

  delay(20);
}
