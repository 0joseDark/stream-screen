import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from flask import Flask, render_template, Response
import cv2
import pyautogui
import numpy as np

# Variável global para controlar o streaming
streaming = False

app = Flask(__name__)

class StreamingApp:
    def __init__(self, master):
        self.master = master
        master.title("Aplicação de Streaming")
        
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
    
    def select_log_folder(self):
        self.log_folder = filedialog.askdirectory()
        if not self.log_folder:
            messagebox.showwarning("Aviso", "Nenhuma pasta selecionada")
        else:
            messagebox.showinfo("Info", f"Pasta de log selecionada: {self.log_folder}")
    
    def start_streaming(self):
        global streaming
        if not streaming:
            streaming = True
            if not self.flask_thread or not self.flask_thread.is_alive():
                self.flask_thread = threading.Thread(target=self.run_flask_app)
                self.flask_thread.start()
            messagebox.showinfo("Info", "Streaming iniciado")
            self.log_action("Streaming iniciado")
    
    def stop_streaming(self):
        global streaming
        if streaming:
            streaming = False
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
    
    def run_flask_app(self):
        app.run(host='0.0.0.0', port=5000, threaded=True)
    
    def quit_app(self):
        self.stop_streaming()
        self.master.quit()
        os._exit(0)  # Força o encerramento de todas as threads

def gen_frames():
    global streaming
    while True:
        if streaming:
            # Captura o ecrã
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Converte o frame para JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            # Se não estiver em streaming, aguarda um pouco antes de verificar novamente
            import time
            time.sleep(0.1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    root = tk.Tk()
    streaming_app = StreamingApp(root)
    root.mainloop()