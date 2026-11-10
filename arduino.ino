/*
  PROJETO INTEGRADOR IoT - SENAI "CONDE JOSÉ VICENTE DE AZEVEDO"
  Estacionamento Inteligente • Vaga 01
  Autores: João Pradela, João Palandi e Pedro Cesar

  Pinagem no Arduino Uno R3:
  - Sensor Ultrassônico Gatilho (Trig) -> Pino Digital 9
  - Sensor Ultrassônico Retorno (Echo)  -> Pino Digital 10
  - Buzzer (Alarme Sonoro)              -> Pino Digital 8
  - LED Verde                           -> Pino Digital 5 (resistor 220 ohms)
  - LED Amarelo                         -> Pino Digital 6 (resistor 220 ohms)
  - LED Vermelho                        -> Pino Digital 7 (resistor 220 ohms)
  - Micro Servo (Cancela)               -> Pino Digital 11
  - GND comum                           -> Pino GND do Arduino
*/

#include <Servo.h>

// Definição dos pinos em português
const int pinoGatilho = 9;
const int pinoEco = 10;
const int pinoAlarmeSonoro = 8;
const int pinoLedVerde = 5;
const int pinoLedAmarelo = 6;
const int pinoLedVermelho = 7;
const int pinoServoCancela = 11;

// Objetos e variáveis globais
Servo motorCancela;
unsigned long tempoUltimoEnvioSerial = 0;
bool cancelaAberta = false;
float ultimaDistanciaValida = 68.0;

// Liga o buzzer com segurança (funciona tanto para buzzer ativo quanto passivo)
void ligarBuzzer(int frequenciaTom) {
  tone(pinoAlarmeSonoro, frequenciaTom);
  digitalWrite(pinoAlarmeSonoro, HIGH);
}

// Desliga o buzzer completamente
void desligarBuzzer() {
  noTone(pinoAlarmeSonoro);
  digitalWrite(pinoAlarmeSonoro, LOW);
}

// Move a cancela suavemente e desliga o sinal para evitar ruído e sobreaquecimento
void acionarCancela(int angulo) {
  motorCancela.attach(pinoServoCancela);
  motorCancela.write(angulo);
  delay(300);
  motorCancela.detach();
}

void setup() {
  Serial.begin(9600);

  pinMode(pinoGatilho, OUTPUT);
  pinMode(pinoEco, INPUT);
  pinMode(pinoAlarmeSonoro, OUTPUT);
  pinMode(pinoLedVerde, OUTPUT);
  pinMode(pinoLedAmarelo, OUTPUT);
  pinMode(pinoLedVermelho, OUTPUT);

  // Inicializa o buzzer desligado
  desligarBuzzer();

  // Posiciona a cancela fechada (0 graus)
  acionarCancela(0);

  // Pisca os 3 LEDs no início para confirmar inicialização
  digitalWrite(pinoLedVerde, HIGH);
  digitalWrite(pinoLedAmarelo, HIGH);
  digitalWrite(pinoLedVermelho, HIGH);
  delay(300);
  digitalWrite(pinoLedVerde, LOW);
  digitalWrite(pinoLedAmarelo, LOW);
  digitalWrite(pinoLedVermelho, LOW);

  Serial.println(F("{\"status\":\"pronto\",\"sistema\":\"Estacionamento IoT SENAI\"}"));
}

// Mede a distância em centímetros através do sensor ultrassônico HC-SR04
float medirDistancia() {
  digitalWrite(pinoGatilho, LOW);
  delayMicroseconds(2);
  digitalWrite(pinoGatilho, HIGH);
  delayMicroseconds(10);
  digitalWrite(pinoGatilho, LOW);

  // Timeout de 25000 microssegundos (~4 metros no máximo)
  long duracao = pulseIn(pinoEco, HIGH, 25000);
  if (duracao <= 0) return -1.0;

  float distanciaCalculada = (duracao * 0.0343) / 2.0;
  if (distanciaCalculada < 2.0 || distanciaCalculada > 350.0) return -1.0;

  return distanciaCalculada;
}

// Controla os 3 LEDs visuais de acordo com a distância
void controlarLeds(float distanciaCentimetros) {
  if (distanciaCentimetros <= 0) {
    digitalWrite(pinoLedVerde, LOW);
    digitalWrite(pinoLedAmarelo, LOW);
    digitalWrite(pinoLedVermelho, LOW);
    return;
  }
  digitalWrite(pinoLedVerde, distanciaCentimetros > 100 ? HIGH : LOW);
  digitalWrite(pinoLedAmarelo, (distanciaCentimetros >= 50 && distanciaCentimetros <= 100) ? HIGH : LOW);
  digitalWrite(pinoLedVermelho, (distanciaCentimetros > 0 && distanciaCentimetros < 50) ? HIGH : LOW);
}

// Controla os bipes do alarme sonoro com ritmo suave e sem explosões sonoras
void controlarBuzzer(float distancia) {
  // Fora da faixa de aproximação ou leitura inválida: silêncio absoluto
  if (distancia <= 0 || distancia > 150) {
    desligarBuzzer();
    return;
  }

  // Intervalos de bipe conforme a zona de aproximação
  unsigned long intervaloTotal;
  int frequenciaTom;

  if (distancia < 15) {
    intervaloTotal = 120; // Perigo iminente: bipes muito rápidos
    frequenciaTom = 2300;
  } else if (distancia < 50) {
    intervaloTotal = 250; // Muito perto: bipes rápidos
    frequenciaTom = 2100;
  } else if (distancia <= 100) {
    intervaloTotal = 500; // Atenção: bipes moderados
    frequenciaTom = 1850;
  } else {
    intervaloTotal = 900; // Longe: bipes lentos
    frequenciaTom = 1600;
  }

  // O bipe fica ligado apenas por 55 milissegundos dentro de cada ciclo
  unsigned long tempoNoCiclo = millis() % intervaloTotal;
  if (tempoNoCiclo < 55) {
    ligarBuzzer(frequenciaTom);
  } else {
    desligarBuzzer();
  }
}

// Processa comandos remotos recebidos via Serial da tela Web ou Raspberry Pi
void processarComandosRemotos() {
  if (Serial.available() > 0) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();

    if (comando.startsWith("C:ABRIR")) {
      acionarCancela(90);
      cancelaAberta = true;
    } else if (comando.startsWith("C:FECHAR")) {
      acionarCancela(0);
      cancelaAberta = false;
    } else if (comando.startsWith("B:TESTE")) {
      ligarBuzzer(2000);
      delay(200);
      desligarBuzzer();
    }
  }
}

void loop() {
  float distanciaLida = medirDistancia();

  // Se a leitura for válida, atualiza o valor estável
  if (distanciaLida > 0) {
    ultimaDistanciaValida = distanciaLida;
  }

  controlarLeds(distanciaLida > 0 ? distanciaLida : ultimaDistanciaValida);
  controlarBuzzer(distanciaLida);
  processarComandosRemotos();

  // Envia JSON pela porta serial a cada 250 milissegundos
  unsigned long agora = millis();
  if (agora - tempoUltimoEnvioSerial >= 250) {
    tempoUltimoEnvioSerial = agora;
    if (distanciaLida > 0) {
      Serial.print(F("{\"distancia_cm\":"));
      Serial.print(distanciaLida, 1);
      Serial.println(F("}"));
    }
  }

  delay(20);
}
