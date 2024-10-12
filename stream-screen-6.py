import os
import tkinter as tk
from tkinter import filedialog
import subprocess
from flask import Flask, Response, render_template
import threading

# Definir o caminho para a libvlc.dll (ajustar conforme necessário)
libvlc_path = r'C:\Program Files\VideoLAN\VLC\libvlc.dll'
os.environ["PYTHON_VLC_LIB_PATH"] = libvlc_path  # Definir a variável de ambiente

# Função para escolher o ficheiro de log
def escolher_log():
    log_file = filedialog.askopenfilename(title="Escolha o ficheiro de log")
    if log_file:
        log_path.set(log_file)
        print(f"Ficheiro de log selecionado: {log_file}")

# Função para ligar o stream do ecrã e som via VLC
def ligar_stream():
    stream_command = [
        r'C:\Program Files\VideoLAN\VLC\vlc.exe',  # Caminho completo para o vlc.exe
        'screen://',  # Serve a tela (ecrã)
        '--sout', '#transcode{vcodec=VP80,vb=800,scale=1,acodec=vorb,ab=128,channels=2}:std{access=http,mux=webm,dst=:8080/}',  # Serve via HTTP com mux WebM
        '--no-sout-all', '--sout-keep',  # Manter o stream aberto
        '--screen-fps=30',  # FPS para a captura de ecrã
        '--screen-top=0', '--screen-left=0',  # Definir a posição da captura
        '--screen-width=1920', '--screen-height=1080',  # Resolução do ecrã (pode ajustar)
        '--audio-desync=-1'  # Ajustar a sincronização de som se necessário
    ]
    subprocess.Popen(stream_command)
    print("Stream de ecrã e som ligado em formato WebM.")

# Função para desligar o stream
def desligar_stream():
    print("Stream desligado")
    subprocess.Popen(['taskkill', '/F', '/IM', 'vlc.exe'])  # Mata o processo VLC

# Função para sair do programa
def sair_programa():
    root.destroy()

# Servidor Flask para servir o HTML e o vídeo
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')  # Página principal com o elemento de vídeo

@app.route('/stream')
def stream_video():
    # Redireciona para o stream VLC
    return Response("http://localhost:8080", mimetype='video/webm')

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
