from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# URL do serviço de gravação
RECORDING_SERVICE_URL = "http://stream_server:5000"

# Rota para a interface gráfica
@app.route('/')
def index():
    return render_template('index.html')

# Rota para adicionar um stream
@app.route('/add_stream', methods=['POST'])
def add_stream():
    data = request.json
    response = requests.post(f"{RECORDING_SERVICE_URL}/add_stream", json=data)
    return jsonify(response.json()), response.status_code

# Rota para iniciar a visualização de um stream
@app.route('/start_viewing', methods=['POST'])
def start_viewing():
    data = request.json
    response = requests.post(f"{RECORDING_SERVICE_URL}/start_viewing", json=data)
    return jsonify(response.json()), response.status_code

# Rota para parar a visualização de um stream
@app.route('/stop_viewing', methods=['POST'])
def stop_viewing():
    data = request.json
    response = requests.post(f"{RECORDING_SERVICE_URL}/stop_viewing", json=data)
    return jsonify(response.json()), response.status_code

# Rota para remover um stream
@app.route('/remove_stream', methods=['POST'])
def remove_stream():
    data = request.json
    response = requests.post(f"{RECORDING_SERVICE_URL}/remove_stream", json=data)
    return jsonify(response.json()), response.status_code

# Rota para listar os streams em execução
@app.route('/list_streams', methods=['GET'])
def list_streams():
    response = requests.get(f"{RECORDING_SERVICE_URL}/list_streams")
    return jsonify(response.json()), response.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
