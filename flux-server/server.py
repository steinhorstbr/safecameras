import subprocess
import threading
import time
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Dicionário para armazenar os processos de gravação e visualização
streams = {}

output_dir = os.getenv("OUTPUT_DIR", "/var/www/recordings")

# Rota para a URL raiz
@app.route('/')
def index():
    return "Servidor de gravação e visualização de streams está rodando!"

def start_recording(stream_key, input_url):
    """Inicia a gravação de um stream."""
    output_file = f"{output_dir}/{stream_key}_%Y%m%d_%H%M%S.mp4"

    # Comando FFmpeg para gravação
    command = [
        "ffmpeg",
        "-i", input_url,  # URL de entrada (RTSP ou RTMP)
        "-c:v", "copy",    # Copiar o vídeo sem re-encode
        "-c:a", "aac",     # Codificar áudio em AAC
        "-f", "segment",   # Segmentar a gravação
        "-segment_time", "3600",  # Duração de cada segmento (1 hora)
        "-strftime", "1",  # Usar timestamps no nome do arquivo
        "-reset_timestamps", "1",
        output_file
    ]

    # Inicia o processo FFmpeg para gravação
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    start_time = time.time()

    # Armazena informações do processo de gravação
    streams[stream_key] = {
        "recording_process": process,
        "start_time": start_time,
        "input_url": input_url,
        "output_dir": output_dir,
        "viewing_process": None  # Processo de visualização (inicialmente None)
    }

def start_viewing(stream_key):
    """Inicia a retransmissão de um stream para visualização."""
    hls_output = f"{output_dir}/{stream_key}/playlist.m3u8"

    # Cria o diretório de saída se não existir
    os.makedirs(f"{output_dir}/{stream_key}", exist_ok=True)

    # Comando FFmpeg para retransmissão (HLS)
    command = [
        "ffmpeg",
        "-i", streams[stream_key]["input_url"],  # URL de entrada (RTSP ou RTMP)
        "-c:v", "copy",    # Copiar o vídeo sem re-encode
        "-c:a", "aac",     # Codificar áudio em AAC
        "-f", "hls",       # Retransmitir via HLS
        "-hls_time", "2",  # Duração de cada segmento HLS (2 segundos)
        "-hls_list_size", "3",  # Número de segmentos na playlist
        "-hls_flags", "delete_segments",  # Apagar segmentos antigos
        hls_output
    ]

    # Inicia o processo FFmpeg para visualização
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    streams[stream_key]["viewing_process"] = process

@app.route('/add_stream', methods=['POST'])
def add_stream():
    """Adiciona um novo stream (somente gravação)."""
    data = request.json
    stream_key = data.get('stream_key')
    input_url = data.get('input_url')
    output_dir = data.get('output_dir', '/var/www/recordings')

    if not stream_key or not input_url:
        return jsonify({"error": "Missing stream_key or input_url"}), 400

    if stream_key in streams:
        return jsonify({"error": "Stream already exists"}), 400

    # Inicia a gravação em uma thread separada
    thread = threading.Thread(target=start_recording, args=(stream_key, input_url))
    thread.start()

    return jsonify({"message": "Stream recording started", "stream_key": stream_key}), 200

@app.route('/start_viewing', methods=['POST'])
def start_viewing_endpoint():
    """Inicia a visualização de um stream."""
    data = request.json
    stream_key = data.get('stream_key')

    if not stream_key:
        return jsonify({"error": "Missing stream_key"}), 400

    if stream_key not in streams:
        return jsonify({"error": "Stream not found"}), 404

    if streams[stream_key]["viewing_process"] is not None:
        return jsonify({"error": "Viewing already started"}), 400

    # Inicia a visualização em uma thread separada
    thread = threading.Thread(target=start_viewing, args=(stream_key, streams[stream_key]["output_dir"]))
    thread.start()

    return jsonify({"message": "Viewing started", "stream_key": stream_key}), 200

@app.route('/stop_viewing', methods=['POST'])
def stop_viewing():
    """Para a visualização de um stream."""
    data = request.json
    stream_key = data.get('stream_key')

    if not stream_key:
        return jsonify({"error": "Missing stream_key"}), 400

    if stream_key not in streams:
        return jsonify({"error": "Stream not found"}), 404

    if streams[stream_key]["viewing_process"] is None:
        return jsonify({"error": "Viewing not started"}), 400

    # Encerra o processo de visualização
    streams[stream_key]["viewing_process"].terminate()
    streams[stream_key]["viewing_process"] = None

    return jsonify({"message": "Viewing stopped", "stream_key": stream_key}), 200

@app.route('/remove_stream', methods=['POST'])
def remove_stream():
    """Remove um stream (gravação e visualização)."""
    data = request.json
    stream_key = data.get('stream_key')

    if not stream_key:
        return jsonify({"error": "Missing stream_key"}), 400

    if stream_key not in streams:
        return jsonify({"error": "Stream not found"}), 404

    # Encerra o processo de gravação
    streams[stream_key]["recording_process"].terminate()

    # Encerra o processo de visualização (se estiver ativo)
    if streams[stream_key]["viewing_process"] is not None:
        streams[stream_key]["viewing_process"].terminate()

    # Remove o stream do dicionário
    del streams[stream_key]

    return jsonify({"message": "Stream removed", "stream_key": stream_key}), 200

@app.route('/list_streams', methods=['GET'])
def list_streams():
    """Lista todos os streams em execução."""
    stream_list = []
    for stream_key, stream_info in streams.items():
        recording_process = stream_info["recording_process"]
        viewing_process = stream_info["viewing_process"]
        start_time = stream_info["start_time"]

        # Verifica o status da gravação
        if recording_process.poll() is None:
            recording_status = "running"
            uptime = time.time() - start_time
        else:
            recording_status = "stopped"
            uptime = 0

        # Verifica o status da visualização
        if viewing_process is not None and viewing_process.poll() is None:
            viewing_status = "running"
        else:
            viewing_status = "stopped"

        stream_list.append({
            "stream_key": stream_key,
            "input_url": stream_info["input_url"],
            "output_dir": stream_info["output_dir"],
            "recording_status": recording_status,
            "viewing_status": viewing_status,
            "uptime": uptime
        })

    return jsonify({"streams": stream_list}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
