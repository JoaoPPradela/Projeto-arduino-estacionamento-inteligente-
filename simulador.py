import time
import json
import urllib.request
import urllib.error

# Endereço da API REST local
ENDERECO_API = "http://127.0.0.1:5000/api/leituras"

def enviar_distancia(distancia_centimetros):
    """Envia uma leitura de distância para a API via requisição POST."""
    dados_envio = {
        "vaga_codigo": "VAGA-01",
        "distancia_cm": float(distancia_centimetros)
    }

    try:
        requisicao_http = urllib.request.Request(
            ENDERECO_API,
            data=json.dumps(dados_envio).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(requisicao_http, timeout=2.0) as resposta_servidor:
            corpo = json.loads(resposta_servidor.read().decode('utf-8'))
            print(f"[OK] Enviado: {distancia_centimetros:>5.1f} cm | Nível: {corpo.get('nivel_alerta', '')} | LED: {corpo.get('led', '')}")
            return True
    except urllib.error.HTTPError as erro:
        print(f"[ERRO HTTP {erro.code}] Detalhes: {erro.reason}")
        return False
    except urllib.error.URLError:
        print("\n[AVISO] Não foi possível conectar ao servidor em http://127.0.0.1:5000.")
        print("       -> Certifique-se de iniciar o servidor primeiro com: python app.py\n")
        return False
    except Exception as erro:
        print(f"[ERRO] {erro}")
        return False

def simular_entrada_vaga():
    """Simula um veículo se aproximando da parede da vaga."""
    print("\n--- SIMULANDO ENTRADA NA VAGA (VEÍCULO APROXIMANDO) ---")
    passos_aproximacao = [160, 130, 95, 75, 68, 45, 25, 14]
    for distancia in passos_aproximacao:
        if not enviar_distancia(distancia):
            break
        time.sleep(0.8)
    print("Simulação de entrada concluída!\n")

def simular_saida_vaga():
    """Simula o veículo saindo da vaga."""
    print("\n--- SIMULANDO SAÍDA DA VAGA (VEÍCULO AFASTANDO) ---")
    passos_afastamento = [14, 30, 55, 80, 110, 145, 180]
    for distancia in passos_afastamento:
        if not enviar_distancia(distancia):
            break
        time.sleep(0.8)
    print("Simulação de saída concluída!\n")

def menu_simulador():
    """Menu interativo para teste de bancada via terminal."""
    while True:
        print("=" * 48)
        print("   SIMULADOR DE VAGA IoT - SENAI")
        print("   API Alvo: http://127.0.0.1:5000/api/leituras")
        print("=" * 48)
        print("1 - Simular carro estacionando (Entrada)")
        print("2 - Simular carro saindo da vaga (Saída)")
        print("3 - Enviar uma distância manual (ex: 68)")
        print("0 - Sair")

        opcao = input("\nEscolha uma opção: ").strip()

        if opcao == '1':
            simular_entrada_vaga()
        elif opcao == '2':
            simular_saida_vaga()
        elif opcao == '3':
            valor = input("Digite a distância em cm (ex: 68): ").strip()
            try:
                enviar_distancia(float(valor))
            except ValueError:
                print("Valor inválido! Digite apenas números.")
        elif opcao == '0':
            print("Saindo do simulador.")
            break
        else:
            print("Opção inválida, tente novamente.")

if __name__ == '__main__':
    menu_simulador()
