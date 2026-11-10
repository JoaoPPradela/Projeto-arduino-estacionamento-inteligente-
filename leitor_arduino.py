"""
Gateway de Comunicação Serial / MQTT para Raspberry Pi 3B
Projeto Integrador IoT - SENAI "Conde José Vicente de Azevedo"
Autores: João Pradela, João Palandi e Pedro Cesar
"""

import time, json, urllib.request

ENDERECO_API = "http://127.0.0.1:5000/api/leituras"
SERVIDOR_BROKER_MQTT = "localhost"
TOPICO_DISTANCIA_MQTT = "estacionamento/vaga01/distancia"

# Tenta carregar o cliente MQTT se o paho-mqtt estiver instalado
cliente_mqtt = None
try:
    import paho.mqtt.client as mqtt  # type: ignore
    cliente_mqtt = mqtt.Client()
    cliente_mqtt.connect(SERVIDOR_BROKER_MQTT, 1883, 60)
    print(f"[MQTT] Conectado ao Broker Mosquitto em ({SERVIDOR_BROKER_MQTT}:1883)")
except Exception:
    print("[MQTT] Broker Mosquitto não detectado ou paho-mqtt ausente. Operando via HTTP e Serial.")

def enviar_leitura_sensor(distancia_centimetros):
    """Envia a leitura tanto para o Broker MQTT quanto para a API REST."""
    dados_envio = {
        "vaga_codigo": "VAGA-01",
        "distancia_cm": float(distancia_centimetros)
    }
    mensagem_json = json.dumps(dados_envio)

    # 1. Publica no Broker MQTT
    if cliente_mqtt:
        try:
            cliente_mqtt.publish(TOPICO_DISTANCIA_MQTT, mensagem_json)
        except Exception:
            pass

    # 2. Envia para a API REST
    try:
        requisicao_http = urllib.request.Request(
            ENDERECO_API,
            data=mensagem_json.encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(requisicao_http, timeout=1.0) as resposta_servidor:
            corpo_resposta = json.loads(resposta_servidor.read().decode('utf-8'))
            print(f"Objeto a {distancia_centimetros:>5.1f} cm -> Alerta: {corpo_resposta.get('nivel_alerta', '')}")
    except Exception:
        pass

def iniciar_gateway_serial_mqtt():
    """Inicia a leitura serial da porta USB do Arduino com proteção contra falhas."""
    print("=" * 60 + "\n   GATEWAY SERIAL / MQTT - RASPBERRY PI 3B\n" + "=" * 60)
    try:
        import serial, serial.tools.list_ports  # type: ignore
    except ImportError:
        print("[ERRO] Instale a biblioteca serial com: pip install pyserial")
        return

    portas_conectadas = [item.device for item in serial.tools.list_ports.comports()]
    porta_alvo = next((p for p in ['/dev/ttyACM0', '/dev/ttyUSB0', 'COM3', 'COM4', 'COM5'] if p in portas_conectadas), portas_conectadas[0] if portas_conectadas else None)

    if not porta_alvo:
        print("[AVISO] Nenhum Arduino detectado. Conecte o cabo USB e tente novamente.")
        return

    print(f"Conectando ao Arduino na porta: {porta_alvo} a 9600 bps...")
    try:
        conexao_serial = serial.Serial(porta_alvo, 9600, timeout=1.0)
    except Exception as erro_abertura:
        print(f"\n[ERRO NA PORTA {porta_alvo}] Não foi possível abrir a porta:")
        print("  -> Certifique-se de fechar o Monitor Serial da IDE do Arduino.")
        print("  -> Se 'app.py' já estiver lendo a serial, ele já faz isso automaticamente!\n")
        return

    try:
        time.sleep(2)
        print("Conectado com sucesso! Aproxime objetos do sensor HC-SR04...\n")

        while True:
            linha_lida = conexao_serial.readline().decode('utf-8', errors='ignore').strip()
            if linha_lida:
                try:
                    dados = json.loads(linha_lida)
                    if isinstance(dados, dict) and 'distancia_cm' in dados:
                        valor = float(dados['distancia_cm'])
                        if valor > 0:
                            enviar_leitura_sensor(valor)
                except Exception:
                    pass
            time.sleep(0.04)
    except KeyboardInterrupt:
        print("\nGateway finalizado pelo usuário.")
    finally:
        conexao_serial.close()

if __name__ == '__main__':
    iniciar_gateway_serial_mqtt()
