from flask import Flask, render_template, jsonify, request
import sqlite3, os, webbrowser, threading, time, json

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'estacionamento.db')
porta_serial_ativa = None

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS vagas (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT UNIQUE, nome TEXT, status TEXT DEFAULT 'LIVRE');
            CREATE TABLE IF NOT EXISTS leituras (id INTEGER PRIMARY KEY AUTOINCREMENT, vaga_codigo TEXT, distancia_cm REAL, nivel_alerta TEXT, descricao_alerta TEXT, sensor_status TEXT, data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS logs_atuadores (id INTEGER PRIMARY KEY AUTOINCREMENT, atuador TEXT, acao TEXT, origem TEXT, data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        ''')
        if conn.execute('SELECT COUNT(*) FROM leituras').fetchone()[0] == 0:
            conn.execute("INSERT INTO leituras (vaga_codigo, distancia_cm, nivel_alerta, descricao_alerta, sensor_status) VALUES ('VAGA-01', 68.0, 'Atenção', 'Bipes moderados', 'Ativo')")
        if conn.execute('SELECT COUNT(*) FROM logs_atuadores').fetchone()[0] == 0:
            conn.execute("INSERT INTO logs_atuadores (atuador, acao, origem) VALUES ('cancela', 'FECHADA', 'SISTEMA')")

def classificar(d):
    if d is None or d < 0 or d > 400: return {'nivel': 'Falha', 'descricao': 'Leitura Inválida', 'sensor': 'Falha', 'led': 'Nenhum', 'cor': '#ef4444'}
    if d > 100: return {'nivel': 'Longe', 'descricao': 'Bipes lentos', 'sensor': 'Ativo', 'led': 'Verde', 'cor': '#22c55e'}
    if d >= 50: return {'nivel': 'Atenção', 'descricao': 'Bipes moderados', 'sensor': 'Ativo', 'led': 'Amarelo', 'cor': '#eab308'}
    return {'nivel': 'Muito Perto', 'descricao': 'Bipe contínuo' if d <= 15 else 'Bipes rápidos', 'sensor': 'Ativo', 'led': 'Vermelho', 'cor': '#ef4444'}

def salvar(vaga, d):
    info = classificar(d)
    with get_db() as conn:
        conn.execute("INSERT INTO leituras (vaga_codigo, distancia_cm, nivel_alerta, descricao_alerta, sensor_status) VALUES (?, ?, ?, ?, ?)",
                     (vaga, d, info['nivel'], info['descricao'], info['sensor']))
    return info

def registrar_atuador(atuador, acao, origem='WEB'):
    global porta_serial_ativa
    with get_db() as conn:
        conn.execute("INSERT INTO logs_atuadores (atuador, acao, origem) VALUES (?, ?, ?)", (atuador, acao, origem))
    # Envia comando de caractere para o Arduino se estiver conectado
    if porta_serial_ativa:
        try:
            cmd = f"{atuador[0].upper()}:{acao}\n"
            porta_serial_ativa.write(cmd.encode('utf-8'))
        except Exception: pass

# Thread Serial (Arduino USB) + Suporte MQTT
def loop_hardware():
    global porta_serial_ativa
    try:
        import serial, serial.tools.list_ports
        while True:
            try:
                portas = [p.device for p in serial.tools.list_ports.comports()]
                p = next((x for x in ['/dev/ttyACM0', '/dev/ttyUSB0', 'COM3', 'COM4', 'COM5'] if x in portas), portas[0] if portas else None)
                if p:
                    ser = serial.Serial(p, 9600, timeout=1.0)
                    porta_serial_ativa = ser
                    time.sleep(2)
                    while True:
                        l = ser.readline().decode('utf-8', errors='ignore').strip()
                        if l:
                            try:
                                d = float(json.loads(l).get('distancia_cm', l))
                                if d >= 0: salvar('VAGA-01', d)
                            except (ValueError, json.JSONDecodeError): pass
                        time.sleep(0.04)
            except Exception:
                porta_serial_ativa = None
                time.sleep(3)
    except ImportError: pass

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/vaga/status')
def status():
    with get_db() as conn:
        row = conn.execute("SELECT * FROM leituras ORDER BY id DESC LIMIT 1").fetchone()
        cancela = conn.execute("SELECT acao FROM logs_atuadores WHERE atuador='cancela' ORDER BY id DESC LIMIT 1").fetchone()
    info = classificar(row['distancia_cm'] if row else 68.0)
    return jsonify({
        'vaga_codigo': 'VAGA-01', 'distancia_cm': round(row['distancia_cm'], 1) if row else 68.0,
        'nivel_alerta': info['nivel'], 'descricao_alerta': info['descricao'],
        'sensor_status': info['sensor'], 'led': info['led'], 'cor': info['cor'],
        'cancela_status': cancela['acao'] if cancela else 'FECHADA',
        'data_hora': row['data_hora'] if row else '--:--'
    })

@app.route('/api/leituras', methods=['POST'])
def nova_leitura():
    dados = request.get_json(silent=True) or {}
    d = dados.get('distancia_cm', dados.get('distancia'))
    if d is None: return jsonify({'erro': 'distancia_cm obrigatorio'}), 400
    try: d = float(d)
    except ValueError: return jsonify({'erro': 'invalido'}), 400
    info = salvar(dados.get('vaga_codigo', 'VAGA-01'), d)
    return jsonify({'sucesso': True, 'distancia_cm': d, **info}), 201

@app.route('/api/leituras/historico')
def historico():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM leituras ORDER BY id DESC LIMIT 8").fetchall()
    return jsonify({'historico': [dict(r) for r in rows]})

# Requisito 4.5: Emissão de Comandos Remotos aos Atuadores
@app.route('/api/atuadores/comando', methods=['POST'])
def comando_atuador():
    dados = request.get_json(silent=True) or {}
    atuador = dados.get('atuador', 'cancela') # 'cancela' ou 'buzzer'
    acao = dados.get('acao', 'ABRIR')         # 'ABRIR', 'FECHAR', 'TESTE'
    registrar_atuador(atuador, acao, 'WEB')
    return jsonify({'sucesso': True, 'atuador': atuador, 'acao': acao})

if __name__ == '__main__':
    init_db()
    print("=" * 60 + "\n   ESTACIONAMENTO IoT - SENAI\n   http://127.0.0.1:5000\n" + "=" * 60)
    threading.Thread(target=loop_hardware, daemon=True).start()
    threading.Thread(target=lambda: (time.sleep(1.2), webbrowser.open('http://127.0.0.1:5000')), daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False)
