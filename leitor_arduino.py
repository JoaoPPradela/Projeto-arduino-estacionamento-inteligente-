"""
Gateway de Comunicação Serial / MQTT para Raspberry Pi 3B
Projeto Integrador IoT - SENAI "Conde José Vicente de Azevedo"
Autores: João Pradela, João Palandi e Pedro Cesar
"""

import time, json, urllib.request

URL_API = "http://127.0.0.1:5000/api/leituras"
MQTT_BROKER = "localhost"
MQTT_TOPIC = "estacionamento/vaga01/distancia"

# Tenta carregar paho.mqtt se disponível na Raspberry Pi
mqtt_client = None
try:
    import paho.mqtt.client as mqtt
    mqtt_client = mqtt.Client()
    mqtt_client.connect(MQTT_BROKER, 1883, 60)
    print(f"[MQTT] Conectado ao Broker Mosquitto ({MQTT_BROKER}:1883)")
except Exception:
    print("[MQTT] Broker local não detectado ou paho-mqtt ausente. Operando via HTTP/Serial.")

def enviar_leitura(distancia):
    dados = {"vaga_codigo": "VAGA-01", "distancia_cm": float(distancia)}
    payload = json.dumps(dados)

    # 1. Publica no Broker MQTT (Requisito 4.3)
    if mqtt_client:
        try: mqtt_client.publish(MQTT_TOPIC, payload)
        except Exception: pass

    # 2. Envia para a API REST Flask (Requisito 4.4)
    try:
        req = urllib.request.Request(URL_API, data=payload.encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            corpo = json.loads(resp.read().decode('utf-8'))
            print(f"Objeto a {distancia:.1f} cm -> Alerta: {corpo.get('nivel_alerta', '')}")
    except Exception: pass

def main():
    print("=" * 60 + "\n   GATEWAY SERIAL / MQTT - RASPBERRY PI 3B\n" + "=" * 60)
    try:
        import serial, serial.tools.list_ports
    except ImportError:
        print("[ERRO] Instale pyserial: pip install pyserial")
        return

    portas = [p.device for p in serial.tools.list_ports.comports()]
    porta = next((x for x in ['/dev/ttyACM0', '/dev/ttyUSB0', 'COM3', 'COM4', 'COM5'] if x in portas), portas[0] if portas else None)

    if not porta:
        print("Nenhum Arduino detectado. Conecte o cabo USB e tente novamente.")
        return

    print(f"Conectando ao Arduino na porta: {porta} a 9600 bps...")
    try:
        ser = serial.Serial(porta, 9600, timeout=1.0)
        time.sleep(2)
        print("Conectado! Aproxime objetos do sensor HC-SR04...\n")
        while True:
            linha = ser.readline().decode('utf-8', errors='ignore').strip()
            if linha:
                try:
                    d = float(json.loads(linha).get('distancia_cm', linha))
                    if d >= 0: enviar_leitura(d)
                except (ValueError, json.JSONDecodeError): pass
            time.sleep(0.04)
    except KeyboardInterrupt:
        print("\nGateway finalizado.")

if __name__ == '__main__':
    main()
