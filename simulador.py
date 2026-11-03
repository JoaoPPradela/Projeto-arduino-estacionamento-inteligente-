import time
import json
import urllib.request
import urllib.error

# URL da nossa API Flask
URL_API = "http://127.0.0.1:5000/api/leituras"

def enviar(distancia):
    """Envia a distancia para a API via POST."""
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
        with urllib.request.urlopen(req, timeout=2.0) as resposta:
            corpo = json.loads(resposta.read().decode('utf-8'))
            print(f"[OK] Enviado: {distancia} cm -> Nivel: {corpo.get('nivel_alerta')}")
            return True
    except Exception:
        print("[ERRO] Nao foi possivel conectar na API. Certifique-se de que 'python app.py' esta rodando!")
        return False

def simular_entrada():
    """Simula um carro se aproximando da parede."""
    print("\n--- SIMULANDO ENTRADA NA VAGA ---")
    passos = [160, 120, 95, 75, 68, 45, 25, 14]
    for d in passos:
        enviar(d)
        time.sleep(0.8)
    print("Concluido!\n")

def simular_saida():
    """Simula um carro saindo da vaga."""
    print("\n--- SIMULANDO SAIDA DA VAGA ---")
    passos = [14, 35, 60, 85, 110, 150, 180]
    for d in passos:
        enviar(d)
        time.sleep(0.8)
    print("Concluido!\n")

def main():
    print("=" * 45)
    print("   SIMULADOR DE VAGA IoT - SENAI")
    print("=" * 45)
    print("1 - Simular carro estacionando (Entrada)")
    print("2 - Simular carro saindo da vaga (Saida)")
    print("3 - Enviar uma distancia manual (ex: 68)")
    print("0 - Sair")

    opcao = input("\nEscolha uma opcao: ").strip()

    if opcao == '1':
        simular_entrada()
    elif opcao == '2':
        simular_saida()
    elif opcao == '3':
        valor = input("Digite a distancia em cm: ").strip()
        try:
            enviar(float(valor))
        except ValueError:
            print("Valor invalido!")
    else:
        print("Saindo.")

if __name__ == '__main__':
    main()
