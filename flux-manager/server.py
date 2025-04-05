from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import uuid
from datetime import datetime
import requests
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor
import psutil  # Para gerenciar processos usando PID

app = Flask(__name__)
CORS(app)  # Habilita CORS para todas as rotas

# Configurações de desempenho
MAX_CONNECTIONS = 10  # Número máximo de conexões simultâneas
executor = ThreadPoolExecutor(max_workers=MAX_CONNECTIONS)

# Dicionário para armazenar as informações das conexões ativas
active_connections = {}

def validate_stream_url(stream_url):
    """Verifica se a URL do stream é acessível."""
    try:
        response = requests.get(stream_url, timeout=5)
        if response.status_code == 200:
            return True
    except RequestException:
        return False
    return False

def start_recording(stream_url, output_file):
    """Inicia a gravação de um stream com segmentação de 30 minutos."""
    try:
        command = f"ffmpeg -i {stream_url} -c:v copy -c:a copy -f segment -segment_time 1800 -strftime 1 {output_file}"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.pid  # Retorna apenas o PID
    except Exception as e:
        print(f"Erro ao iniciar gravação: {e}")
        return None

def start_streaming(stream_url, hls_output):
    """Inicia o streaming HLS."""
    try:
        command = f"ffmpeg -i {stream_url} -c:v libx264 -preset ultrafast -c:a aac -strict -2 -f hls -hls_time 2 -hls_list_size 3 {hls_output}"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.pid  # Retorna apenas o PID
    except Exception as e:
        print(f"Erro ao iniciar streaming: {e}")
        return None

def is_process_running(pid):
    """Verifica se um processo está em execução com base no PID."""
    try:
        process = psutil.Process(pid)
        return process.is_running()
    except psutil.NoSuchProcess:
        return False

@app.route('/add', methods=['POST'])
def add_connection():
    if len(active_connections) >= MAX_CONNECTIONS:
        return jsonify({"error": "Número máximo de conexões atingido"}), 429

    data = request.json
    stream_url = data.get('stream_url')
    connection_type = data.get('type')  # 'record' or 'stream'
    camera_id = data.get('camera_id')  # Identificação da câmera
    connection_id = str(uuid.uuid4())

    # Valida a URL do stream
    #if not validate_stream_url(stream_url):
    #    return jsonify({"error": "Stream URL inválida ou inacessível"}), 400

    if connection_type == 'record':
        # Formato do nome do arquivo: camera_id_data_hora_inicio_%Y%m%d_%H%M%S.mp4
        start_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"videos/{camera_id}_{start_time}_%Y%m%d_%H%M%S.mp4"
        pid = start_recording(stream_url, output_file)
    elif connection_type == 'stream':
        # Formato do nome do arquivo: camera_id.m3u8
        hls_output = f"streams/{camera_id}.m3u8"
        pid = start_streaming(stream_url, hls_output)
    else:
        return jsonify({"error": "Tipo de conexão inválido"}), 400

    if not pid:
        return jsonify({"error": "Falha ao iniciar o processo"}), 500

    active_connections[connection_id] = {
        "pid": pid,  # Armazena apenas o PID
        "type": connection_type,
        "camera_id": camera_id,
        "url": stream_url,
        "output": output_file if connection_type == 'record' else hls_output
    }

    return jsonify({"connection_id": connection_id}), 201

@app.route('/connections', methods=['GET'])
def list_connections():
    # Retorna apenas informações serializáveis
    serialized_connections = {}
    for connection_id, details in active_connections.items():
        serialized_connections[connection_id] = {
            "pid": details["pid"],
            "type": details["type"],
            "camera_id": details["camera_id"],
            "url": details["url"],
            "output": details["output"],
            "status": "ativo" if is_process_running(details["pid"]) else "inativo"
        }
    return jsonify(serialized_connections)

@app.route('/stop/<connection_id>', methods=['DELETE'])
def stop_connection(connection_id):
    if connection_id in active_connections:
        pid = active_connections[connection_id]['pid']
        output = active_connections[connection_id]['output']

        # Finaliza o processo usando o PID
        try:
            process = psutil.Process(pid)
            process.terminate()
            process.wait()
        except psutil.NoSuchProcess:
            pass  # O processo já foi finalizado

        # Remove arquivos de gravação ou streaming
        if active_connections[connection_id]['type'] == 'record':
            # Remove todos os segmentos de gravação
            for file in os.listdir("videos"):
                if file.startswith(active_connections[connection_id]['camera_id']):
                    os.remove(f"videos/{file}")
        else:
            if os.path.exists(output):
                os.remove(output)

        del active_connections[connection_id]
        return jsonify({"message": "Conexão encerrada e recursos liberados"}), 200
    else:
        return jsonify({"error": "Conexão não encontrada"}), 404

@app.route('/status/<connection_id>', methods=['GET'])
def connection_status(connection_id):
    if connection_id in active_connections:
        pid = active_connections[connection_id]['pid']
        return jsonify({
            "status": "ativo" if is_process_running(pid) else "inativo",
            "type": active_connections[connection_id]['type'],
            "camera_id": active_connections[connection_id]['camera_id'],
            "url": active_connections[connection_id]['url'],
            "output": active_connections[connection_id]['output']
        }), 200
    else:
        return jsonify({"error": "Conexão não encontrada"}), 404

if __name__ == '__main__':
    if not os.path.exists('videos'):
        os.makedirs('videos')
    if not os.path.exists('streams'):
        os.makedirs('streams')
    #app.run(debug=True)
    port = 5005
    
    app.run(host='0.0.0.0', port=port, debug=True)
