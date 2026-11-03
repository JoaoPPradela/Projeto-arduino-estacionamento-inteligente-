"""
Script de Leitura Serial do Arduino para Raspberry Pi / Computador
Projeto Integrador IoT - SENAI
Autores: João Pradela, João Palandi e Pedro Cesar

Função:
Lê em tempo real os centímetros medidos pelo Arduino via cabo USB
e envia diretamente para o app.py (Dashboard Web e Banco SQLite).
"""

import time
import json
import urllib.request
import urllib.error

# URL da nossa API Flask
URL_API = "http://127.0.0.1:5000/api/leituras"

def tentar_importar_serial():
    try:
        import serial
        import serial.tools.list_ports
        return serial
    except ImportError:
        print("\n" + "="*60)
        print(" [AVISO] A biblioteca 'pyserial' ainda não está instalada!")
        print(" Para conectar o Arduino físico na USB da Raspberry Pi ou PC:")
        print(" Digite no terminal: pip install pyserial")
        print("="*60 + "\n")
        return None

def encontrar_porta_arduino(serial_mod):
    """Procura automaticamente em qual porta USB o Arduino está conectado."""
    portas = list(serial_mod.tools.list_ports.comports())
    
    # 1. Procura por palavras-chave de Arduino
    for p in portas:
        nome = (p.description or "") + (p.manufacturer or "")
        if "Arduino" in nome or "CH340" in nome or "USB Serial" in nome:
            return p.device

    # 2. Portas padrão comuns na Raspberry Pi (Linux) e no Windows
    portas_comuns = ['/dev/ttyACM0', '/dev/ttyUSB0', '/dev/ttyACM1', 'COM3', 'COM4', 'COM5']
    for p_comum in portas_comuns:
        for p in portas:
            if p.device == p_comum:
                return p_comum

    # Se achar qualquer porta serial disponível, usa a primeira
    if len(portas) > 0:
        return portas[0].device

    return None

def enviar_para_api(distancia):
    """Envia os centímetros medidos para o app.py."""
    dados = {
        "vaga_codigo": "VAGA-01",
        "distancia_cm": float(distancia)
    }
    try:
        req = urllib.request.Request(
            URL_API,
            data=json.dumps(dados).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            corpo = json.loads(resp.read().decode('utf-8'))
            nivel = corpo.get('nivel_alerta', '')
            print(f"Objeto a {distancia:.1f} cm -> Nível: {nivel}")
    except Exception:
        # Se a API demorar ou não responder, não trava a leitura do Arduino
        pass

def main():
    print("=" * 60)
    print("   CONECTANDO ARDUINO NA RASPBERRY PI / COMPUTADOR")
    print("   Projeto IoT SENAI • Estacionamento Inteligente")
    print("=" * 60)

    serial_mod = tentar_importar_serial()
    if not serial_mod:
        return

    porta = encontrar_porta_arduino(serial_mod)
    if not porta:
        print("\n[ERRO] Nenhum Arduino foi encontrado nas portas USB!")
        print("1. Conecte o cabo USB do Arduino na Raspberry Pi ou no PC.")
        print("2. Verifique se o Arduino está com a luz ligada.")
        print("3. Execute este script novamente: python leitor_arduino.py\n")
        return

    print(f"\nArduino detectado na porta: {porta}")
    print("Conectando a 9600 bps...")

    try:
        conexao = serial_mod.Serial(porta, 9600, timeout=1.0)
        time.sleep(2) # Aguarda o Arduino reiniciar após conectar
        print("Conectado com sucesso! Aproxime a mão ou um objeto do sensor HC-SR04...\n")
    except Exception as e:
        print(f"[ERRO] Não foi possível abrir a porta {porta}: {e}")
        return

    try:
        while True:
            linha = conexao.readline().decode('utf-8', errors='ignore').strip()
            if linha:
                # O Arduino pode enviar: {"distancia_cm":68.5} ou apenas 68.5
                distancia = None

                try:
                    dados_json = json.loads(linha)
                    if 'distancia_cm' in dados_json:
                        distancia = float(dados_json['distancia_cm'])
                except json.JSONDecodeError:
                    try:
                        distancia = float(linha)
                    except ValueError:
                        pass

                if distancia is not None and distancia >= 0:
                    enviar_para_api(distancia)

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nLeitura serial encerrada pelo usuário.")
        conexao.close()

if __name__ == '__main__':
    main()

