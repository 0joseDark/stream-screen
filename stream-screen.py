import os
import tkinter as tk
from tkinter import filedialog, messagebox
import vlc
from flask import Flask, Response, render_template
import threading

# Indicar o caminho completo para a libvlc.dll
libvlc_path = r'C:\Program Files\VideoLAN\VLC\libvlc.dll'
os.environ["PYTHON_VLC_LIB_PATH"] = libvlc_path  # Definir o caminho da libvlc.dll

# Inicializar o player VLC
instance = vlc.Instance()
player = instance.media_player_new()

# Função para escolher o ficheiro de log
def escolher_log():
    log_file = filedialog.askopenfilename(title="Escolha o ficheiro de log")
    if log_file:
        log_path.set(log_file)
        print(f"Ficheiro de log selecionado: {log_file}")

# Função para ligar o stream
def ligar_stream():
    media = instance.media_new("caminho/para/video.mp4")
    player.set_media(media)
    player.play()
    print("Stream ligado")

# Função para desligar o stream
def desligar_stream():
    player.stop()
    print("Stream desligado")

# Função para ler o ficheiro de log
def ler_ficheiro_log():
    log_file = log_path.get()
    if os.path.exists(log_file):
        with open(log_file, "r") as file:
            conteudo = file.read()
        messagebox.showinfo("Conteúdo do Log", conteudo)
    else:
        messagebox.showerror("Erro", "Ficheiro de log não encontrado")

# Função para escolher ecrã e som do sistema
def escolher_ecran_e_som():
    # Simulação de escolha de ecrã e som
    print("Escolha do ecrã e som do sistema")

# Função para sair do programa
def sair_programa():
    root.destroy()

# Flask app para servir o stream
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream_video():
    # Função para enviar o vídeo como stream
    def generate():
        while True:
            frame = player.video_get_spu_text()  # Exemplo de obtenção de frames
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

def iniciar_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

# Criar janela Tkinter
root = tk.Tk()
root.title("Controlo de Stream")

# Variáveis para armazenar o caminho do log
log_path = tk.StringVar()

# Criar o menu
menu_bar = tk.Menu(root)
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Escolher ficheiro de log", command=escolher_log)
menu_bar.add_cascade(label="Ficheiro", menu=file_menu)

# Adicionar os botões
tk.Button(root, text="Ligar", command=ligar_stream).pack(pady=10)
tk.Button(root, text="Desligar", command=desligar_stream).pack(pady=10)
tk.Button(root, text="Ler ficheiro de log", command=ler_ficheiro_log).pack(pady=10)
tk.Button(root, text="Escolher Ecrã e Som", command=escolher_ecran_e_som).pack(pady=10)
tk.Button(root, text="Sair", command=sair_programa).pack(pady=10)

# Iniciar o Flask em thread separada
threading.Thread(target=iniciar_flask, daemon=True).start()

# Configurar o menu na janela
root.config(menu=menu_bar)

# Executar o loop principal da interface gráfica
root.mainloop()
