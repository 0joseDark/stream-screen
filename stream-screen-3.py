import os
import tkinter as tk
from tkinter import filedialog
import vlc
from flask import Flask, Response, render_template
import threading
import subprocess

# Definir o caminho para a libvlc.dll
libvlc_path = r'C:\Program Files\VideoLAN\VLC\libvlc.dll'
os.environ["PYTHON_VLC_LIB_PATH"] = libvlc_path  # Definir o caminho da libvlc.dll para o VLC

# Inicializar o VLC player para controlar media
instance = vlc.Instance()
player = instance.media_player_new()

# Função para escolher o ficheiro de log
def escolher_log():
    log_file = filedialog.askopenfilename(title="Escolha o ficheiro de log")
    if log_file:
        log_path.set(log_file)
        print(f"Ficheiro de log selecionado: {log_file}")

# Função para ligar o stream do ecrã e som via VLC (usando HLS)
def ligar_stream():
    stream_command = [
        r'C:\Program Files\VideoLAN\VLC\vlc.exe',  # Caminho completo para o vlc.exe
        'screen://',  # Serve a tela (ecrã)
        '--sout', '#transcode{vcodec=h264,acodec=mp3,ab=128,channels=2}:std{access=livehttp{seglen=10,delsegs=true,numsegs=5,index=/tmp/hls/index.m3u8,index-url=http://localhost:8080/hls/segment-%%05d.ts},mux=ts{use-key-frames},dst=/tmp/hls/segment-%%05d.ts}',
        '--no-sout-all', '--sout-keep',  # Manter o stream aberto
        '--screen-fps=30',  # FPS para a captura de ecrã
        '--screen-top=0', '--screen-left=0',  # Definir a posição da captura
        '--screen-width=1920', '--screen-height=1080',  # Resolução do ecrã (pode ajustar)
        '--audio-desync=-1'  # Ajustar a sincronização de som se necessário
    ]
    subprocess.Popen(stream_command)
    print(f"Stream de ecrã e som ligado.")

# Função para desligar o stream
def desligar_stream():
    player.stop()
    print("Stream desligado")

# Função para sair do programa
def sair_programa():
    root.destroy()

# Servidor Flask para servir o HTML
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hls/<segment>')
def hls(segment):
    # Servir os segmentos HLS gerados pelo VLC
    segment_path = f"/tmp/hls/{segment}"
    return Response(open(segment_path, 'rb').read(), mimetype='video/mp2t')

@app.route('/stream')
def stream_video():
    # Servir o arquivo de playlist HLS
    return Response(open('/tmp/hls/index.m3u8', 'rb').read(), mimetype='application/vnd.apple.mpegurl')

def iniciar_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

# Criar a janela principal com tkinter
root = tk.Tk()
root.title("Controlo de Stream")

log_path = tk.StringVar()

# Criar o menu
menu_bar = tk.Menu(root)
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Escolher ficheiro de log", command=escolher_log)
menu_bar.add_cascade(label="Ficheiro", menu=file_menu)

# Adicionar botões na janela
tk.Button(root, text="Ligar", command=ligar_stream).pack(pady=10)
tk.Button(root, text="Desligar", command=desligar_stream).pack(pady=10)
tk.Button(root, text="Sair", command=sair_programa).pack(pady=10)

# Iniciar o Flask numa thread separada
threading.Thread(target=iniciar_flask, daemon=True).start()

# Configurar o menu e iniciar a janela
root.config(menu=menu_bar)
root.mainloop()
