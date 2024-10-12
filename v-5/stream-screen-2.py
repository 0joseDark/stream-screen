import os
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from flask import Flask, render_template, Response, request
import cv2
import pyautogui
import numpy as np
import time
from werkzeug.serving import make_server
import vlc  # Biblioteca VLC para manipulação de áudio
import socket

# Indicar o caminho completo para a libvlc.dll
libvlc_path = r'C:\Program Files\VideoLAN\VLC\libvlc.dll'
vlc_instance = vlc.Instance("--input-repeat=-1", "--fullscreen", "--no-video")  # Instância VLC para áudio

# Variáveis globais
streaming = False
SCREEN_SIZE = None
CAPTURE_FREQUENCY = 1  # Valor inicial: 1 frame por segundo

app = Flask(__name__)

class StreamingApp:
    def __init__(self, master):
        self.master = master
        master.title("Aplicação de Streaming com Som")
        
        # Configuração do menu
        menubar = tk.Menu(master)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Selecionar pasta de log", command=self.select_log_folder)
        menubar.add_cascade(label="Ficheiro", menu=filemenu)
        master.config(menu=menubar)
        
        # Botões
        self.start_button = tk.Button(master, text="Ligar", command=self.start_streaming)
        self.start_button.pack()
        
        self.stop_button = tk.Button(master, text="Desligar", command=self.stop_streaming)
        self.stop_button.pack()
        
        self.read_log_button = tk.Button(master, text="Ler ficheiro log", command=self.read_log)
        self.read_log_button.pack()
        
        self.exit_button = tk.Button(master, text="Sair", command=self.quit_app)
        self.exit_button.pack()
        
        # Variáveis de controle
        self.log_folder = ""
        self.flask_thread = None
        self.server = None
        self.audio_player = None  # Para controle do áudio
    
    def select_log_folder(self):
        self.log_folder = filedialog.askdirectory()
        if not self.log_folder:
            messagebox.showwarning("Aviso", "Nenhuma pasta selecionada")
        else:
            messagebox.showinfo("Info", f"Pasta de log selecionada: {self.log_folder}")
    
    def start_streaming(self):
        global streaming, SCREEN_SIZE
        if not streaming:
            streaming = True
            SCREEN_SIZE = pyautogui.size()
            if not self.flask_thread or not self.flask_thread.is_alive():
                self.flask_thread = threading.Thread(target=self.run_flask_app)
                self.flask_thread.start()
            messagebox.showinfo("Info", "Streaming iniciado")
            self.log_action("Streaming iniciado")
            self.open_firewall_port()  # Abrir a porta da firewall automaticamente
            self.start_audio_stream()  # Iniciar o áudio
    
    def stop_streaming(self):
        global streaming
        if streaming:
            streaming = False
            if self.server:
                self.server.shutdown()
            if self.audio_player:
                self.audio_player.stop()  # Parar o áudio
            messagebox.showinfo("Info", "Streaming parado")
            self.log_action("Streaming parado")
    
    def read_log(self):
        if not self.log_folder:
            messagebox.showwarning("Aviso", "Selecione uma pasta de log primeiro")
            return
        
        log_file = os.path.join(self.log_folder, "streaming_log.txt")
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                content = f.read()
            messagebox.showinfo("Conteúdo do Log", content)
        else:
            messagebox.showinfo("Info", "Ficheiro de log não encontrado")
    
    def log_action(self, action):
        if not self.log_folder:
            return
        
        log_file = os.path.join(self.log_folder, "streaming_log.txt")
        with open(log_file, "a") as f:
            f.write(f"{action}\n")
    
    def open_firewall_port(self):
        try:
            # Abrir a porta 5000 no firewall do Windows para tráfego TCP
            command = 'netsh advfirewall firewall add rule name="Flask Server" dir=in action=allow protocol=TCP localport=5000'
            subprocess.run(command, shell=True, check=True)
            messagebox.showinfo("Info", "Porta 5000 aberta no firewall com sucesso!")
        except subprocess.CalledProcessError:
            messagebox.showerror("Erro", "Falha ao abrir a porta 5000 no firewall.")
    
    def run_flask_app(self):
        # Pega o endereço IP da máquina
        ip_address = socket.gethostbyname(socket.gethostname())
        self.server = make_server('0.0.0.0', 5000, app)  # Permitir acesso externo em qualquer IP
        print(f"Servidor Flask rodando em http://{ip_address}:5000")
        self.server.serve_forever()
    
    def start_audio_stream(self):
        """Iniciar o stream de áudio usando VLC"""
        # Captura o som do sistema (ou especificar outro stream de áudio)
        media = vlc_instance.media_new("dshow://")  # Pode alterar para stream online ou dispositivo de áudio
        self.audio_player = vlc_instance.media_player_new()
        self.audio_player.set_media(media)
        self.audio_player.play()  # Iniciar o áudio
    
    def quit_app(self):
        self.stop_streaming()
        self.master.quit()
        os._exit(0)  # Força o encerramento de todas as threads

def capture_screen():
    global SCREEN_SIZE
    img = pyautogui.screenshot()
    frame = np.array(img)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    frame = cv2.resize(frame, (SCREEN_SIZE.width // 2, SCREEN_SIZE.height // 2))
    return frame

def gen_frames():
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
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/update_frequency', methods=['POST'])
def update_frequency():
    global CAPTURE_FREQUENCY
    frequency = request.form.get('frequency', type=int)
    if 0 <= frequency <= 100:
        CAPTURE_FREQUENCY = max(1, frequency)  # Evita divisão por zero
        return 'OK', 200
    return 'Invalid frequency', 400

if __name__ == '__main__':
    root = tk.Tk()
    streaming_app = StreamingApp(root)
    root.mainloop()
