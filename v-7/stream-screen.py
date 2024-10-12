import os
import subprocess
import threading
import cv2
import pyautogui
import numpy as np
import time
import socket
from flask import Flask, render_template, Response, request

# Inicializar o app Flask
app = Flask(__name__)

# Variáveis globais
streaming = False
SCREEN_SIZE = None
CAPTURE_FREQUENCY = 1  # Inicialmente 1 frame por segundo

class StreamingApp:
    def __init__(self):
        # Nenhuma interface gráfica no momento
        pass
    
    def start_streaming(self):
        global streaming, SCREEN_SIZE
        if not streaming:
            streaming = True
            SCREEN_SIZE = pyautogui.size()
            print("Streaming de vídeo e áudio iniciado")

    def stop_streaming(self):
        global streaming
        if streaming:
            streaming = False
            print("Streaming parado")
    
    def run_flask_app(self):
        ip_address = socket.gethostbyname(socket.gethostname())
        print(f"Servidor Flask rodando em http://{ip_address}:5000")
        app.run(host='0.0.0.0', port=5000, threaded=True)
        
    def quit_app(self):
        self.stop_streaming()
        os._exit(0)

def capture_screen():
    """Captura a tela e retorna um frame."""
    global SCREEN_SIZE
    img = pyautogui.screenshot()
    frame = np.array(img)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    frame = cv2.resize(frame, (SCREEN_SIZE.width // 2, SCREEN_SIZE.height // 2))
    return frame

def gen_frames():
    """Gera frames de vídeo continuamente."""
    global streaming, CAPTURE_FREQUENCY
    last_capture_time = 0
    while True:
        if streaming:
            current_time = time.time()
            if current_time - last_capture_time >= 1 / CAPTURE_FREQUENCY:
                frame = capture_screen()
                last_capture_time = current_time
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            time.sleep(0.1)

@app.route('/')
def index():
    """Renderiza a página HTML."""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Retorna o stream de vídeo."""
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/audio_feed')
def audio_feed():
    """Retorna o stream de áudio."""
    # Neste ponto, o áudio será servido de um arquivo, ou stream contínuo
    # O áudio precisa ser pré-gravado ou capturado usando uma fonte de áudio de microfone ou sistema
    audio_file = "path_to_audio_file.wav"
    def generate():
        with open(audio_file, 'rb') as f:
            data = f.read(1024)
            while data:
                yield data
                data = f.read(1024)
    return Response(generate(), mimetype="audio/wav")

@app.route('/update_frequency', methods=['POST'])
def update_frequency():
    """Atualiza a frequência dos frames."""
    global CAPTURE_FREQUENCY
    frequency = request.form.get('frequency', type=int)
    if 0 <= frequency <= 100:
        CAPTURE_FREQUENCY = max(1, frequency)  # Evita divisão por zero
        return 'OK', 200
    return 'Invalid frequency', 400

if __name__ == '__main__':
    streaming_app = StreamingApp()
    streaming_app.run_flask_app()
