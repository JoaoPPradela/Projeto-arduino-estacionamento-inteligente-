from flask import Flask, render_template, jsonify, request
import sqlite3, os, webbrowser, threading, time, json

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'estacionamento.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT, vaga_codigo TEXT NOT NULL,
            distancia_cm REAL NOT NULL, nivel_alerta TEXT NOT NULL,
            descricao_alerta TEXT NOT NULL, sensor_status TEXT NOT NULL,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        if conn.execute('SELECT COUNT(*) FROM leituras').fetchone()[0] == 0:
            conn.execute("INSERT INTO leituras (vaga_codigo, distancia_cm, nivel_alerta, descricao_alerta, sensor_status) VALUES ('VAGA-01', 68.0, 'Atenção', 'Bipes moderados', 'Ativo')")

def classificar(d):
    if d is None or d < 0 or d > 400:
        return {'nivel': 'Falha', 'descricao': 'Leitura Inválida', 'sensor': 'Falha', 'led': 'Nenhum', 'cor': '#ef4444'}
    if d > 100:
        return {'nivel': 'Longe', 'descricao': 'Bipes lentos', 'sensor': 'Ativo', 'led': 'Verde', 'cor': '#22c55e'}
    if d >= 50:
        return {'nivel': 'Atenção', 'descricao': 'Bipes moderados', 'sensor': 'Ativo', 'led': 'Amarelo', 'cor': '#eab308'}
    return {'nivel': 'Muito Perto', 'descricao': 'Bipe contínuo' if d <= 15 else 'Bipes rápidos', 'sensor': 'Ativo', 'led': 'Vermelho', 'cor': '#ef4444'}

def salvar(vaga, d):
    info = classificar(d)
    with get_db() as conn:
        conn.execute("INSERT INTO leituras (vaga_codigo, distancia_cm, nivel_alerta, descricao_alerta, sensor_status) VALUES (?, ?, ?, ?, ?)",
                     (vaga, d, info['nivel'], info['descricao'], info['sensor']))
    return info

def loop_serial():
    try:
        import serial, serial.tools.list_ports
    except ImportError:
        return
    while True:
        try:
            portas = [p.device for p in serial.tools.list_ports.comports()]
            porta = next((p for p in ['/dev/ttyACM0', '/dev/ttyUSB0', 'COM3', 'COM4', 'COM5'] if p in portas), portas[0] if portas else None)
            if porta:
                ser = serial.Serial(porta, 9600, timeout=1.0)
                time.sleep(2)
                while True:
                    linha = ser.readline().decode('utf-8', errors='ignore').strip()
                    if linha:
                        try:
                            d = float(json.loads(linha).get('distancia_cm', linha))
                            if d >= 0: salvar('VAGA-01', d)
                        except (ValueError, json.JSONDecodeError): pass
                    time.sleep(0.04)
        except Exception:
            time.sleep(3)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/vaga/status')
def status():
    with get_db() as conn:
        row = conn.execute("SELECT * FROM leituras ORDER BY id DESC LIMIT 1").fetchone()
    if not row:
        return jsonify({'vaga_codigo': 'VAGA-01', 'distancia_cm': 68.0, 'nivel_alerta': 'Atenção', 'descricao_alerta': 'Bipes moderados', 'sensor_status': 'Ativo', 'led': 'Amarelo', 'cor': '#eab308'})
    info = classificar(row['distancia_cm'])
    return jsonify({'id': row['id'], 'vaga_codigo': row['vaga_codigo'], 'distancia_cm': round(row['distancia_cm'], 1),
                    'nivel_alerta': row['nivel_alerta'], 'descricao_alerta': row['descricao_alerta'],
                    'sensor_status': row['sensor_status'], 'led': info['led'], 'cor': info['cor'], 'data_hora': row['data_hora']})

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
    return jsonify({'historico': [{'id': r['id'], 'vaga_codigo': r['vaga_codigo'], 'distancia_cm': round(r['distancia_cm'], 1),
                                  'nivel_alerta': r['nivel_alerta'], 'descricao_alerta': r['descricao_alerta'],
                                  'sensor_status': r['sensor_status'], 'data_hora': r['data_hora']} for r in rows]})

if __name__ == '__main__':
    init_db()
    print("=" * 60 + "\n   ESTACIONAMENTO IoT - SENAI\n   http://127.0.0.1:5000\n" + "=" * 60)
    threading.Thread(target=loop_serial, daemon=True).start()
    threading.Thread(target=lambda: (time.sleep(1.2), webbrowser.open('http://127.0.0.1:5000')), daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False)
