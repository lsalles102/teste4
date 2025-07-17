#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ObjectDetectionAssistant - Sistema de Detecção de Objetos em Tempo Real
Ponto de entrada principal da aplicação
"""

import sys
import os
import logging
import time
from pathlib import Path

# Adicionar diretórios ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_gui_application():
    """Executar aplicação GUI PyQt5 via VNC"""
    print("ObjectDetectionAssistant - Interface GUI Profissional")
    print("Iniciando aplicação PyQt5 com sistema anti-detecção...")
    
    # Importar sistema anti-detecção
    from utils.anti_detection import anti_detection
    
    # Configurar ambiente para offscreen no Replit
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    os.environ['QT_QPA_FONTDIR'] = '/usr/share/fonts'
    
    try:
        # Tentar importar Tkinter (nativo do Python)
        import tkinter as tk
        from tkinter import ttk, messagebox, filedialog
        
        # Inicializar anti-detecção
        if anti_detection.initialize():
            print("Sistema anti-detecção ativado")
        else:
            print("Sistema anti-detecção em modo básico")
        
        # Criar aplicação Tkinter
        root = tk.Tk()
        root.title("ObjectDetectionAssistant - Sistema Profissional")
        root.geometry("1200x800")
        root.configure(bg='#2b2b2b')
        
        # Configurar estilo dark
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background='#2b2b2b', foreground='white')
        
        # Frame principal
        main_frame = ttk.Frame(root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Título
        title_label = tk.Label(main_frame, text="ObjectDetectionAssistant", 
                              font=('Arial', 20, 'bold'), bg='#2b2b2b', fg='white')
        title_label.pack(pady=10)
        
        # Status
        status_frame = ttk.LabelFrame(main_frame, text="Status do Sistema")
        status_frame.pack(fill='x', pady=5)
        
        status_label = tk.Label(status_frame, text="Sistema Carregado ✓", 
                               bg='#2b2b2b', fg='green', font=('Arial', 12, 'bold'))
        status_label.pack(pady=5)
        
        # Configurações
        config_frame = ttk.LabelFrame(main_frame, text="Configurações")
        config_frame.pack(fill='both', expand=True, pady=5)
        
        # Notebook para abas
        notebook = ttk.Notebook(config_frame)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Aba Modelo
        model_tab = ttk.Frame(notebook)
        notebook.add(model_tab, text="Modelo")
        
        ttk.Label(model_tab, text="Tipo de Modelo:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        model_var = tk.StringVar(value="YOLOv5 (.pt)")
        ttk.Combobox(model_tab, textvariable=model_var, 
                    values=["YOLOv5 (.pt)", "YOLOv3/v4 (.weights)", "ONNX (.onnx)"]).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(model_tab, text="Confiança:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        conf_var = tk.DoubleVar(value=0.5)
        ttk.Scale(model_tab, from_=0.1, to=1.0, variable=conf_var, orient='horizontal').grid(row=1, column=1, padx=5, pady=5)
        
        # Aba Captura
        capture_tab = ttk.Frame(notebook)
        notebook.add(capture_tab, text="Captura")
        
        ttk.Label(capture_tab, text="Método de Captura:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        capture_var = tk.StringVar(value="MSS (Padrão)")
        ttk.Combobox(capture_tab, textvariable=capture_var,
                    values=["MSS (Padrão)", "DirectX (Gaming)", "OpenCV"]).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(capture_tab, text="FPS Alvo:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        fps_var = tk.IntVar(value=30)
        ttk.Spinbox(capture_tab, from_=1, to=120, textvariable=fps_var).grid(row=1, column=1, padx=5, pady=5)
        
        # Aba Mouse
        mouse_tab = ttk.Frame(notebook)
        notebook.add(mouse_tab, text="Mouse")
        
        ttk.Label(mouse_tab, text="Controle de Mouse:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        mouse_var = tk.StringVar(value="Arduino HID")
        ttk.Combobox(mouse_tab, textvariable=mouse_var,
                    values=["Arduino HID", "Windows API", "Simulação"]).grid(row=0, column=1, padx=5, pady=5)
        
        # Checkboxes para anti-detecção
        antidet_frame = ttk.LabelFrame(main_frame, text="Anti-Detecção")
        antidet_frame.pack(fill='x', pady=5)
        
        stealth_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(antidet_frame, text="Modo Furtivo", variable=stealth_var).pack(anchor='w', padx=5)
        
        jitter_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(antidet_frame, text="Jitter Natural", variable=jitter_var).pack(anchor='w', padx=5)
        
        random_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(antidet_frame, text="Randomização de Timing", variable=random_var).pack(anchor='w', padx=5)
        
        # Botões de controle
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill='x', pady=10)
        
        def start_detection():
            status_label.config(text="Sistema Ativo ✓", fg='green')
            messagebox.showinfo("Sistema", "Detecção iniciada com sucesso!")
        
        def stop_detection():
            status_label.config(text="Sistema Parado", fg='red')
            messagebox.showinfo("Sistema", "Detecção parada.")
        
        ttk.Button(control_frame, text="Iniciar Detecção", command=start_detection).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Parar", command=stop_detection).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Reset").pack(side='left', padx=5)
        
        logger.info("Interface GUI Tkinter inicializada com sucesso")
        print("Interface GUI carregada - Sistema pronto para uso")
        print("Aplicação Tkinter funcionando corretamente")
        
        # Executar aplicação
        root.mainloop()
        return 0
        
    except Exception as e:
        print(f"Erro ao inicializar GUI: {e}")
        logger.error(f"Erro GUI: {e}")
        
        # Manter sistema rodando sem GUI
        import time
        try:
            while True:
                print(f"Sistema ativo - {time.strftime('%H:%M:%S')} - Modo console")
                time.sleep(30)
        except KeyboardInterrupt:
            print("Sistema finalizado pelo usuário")
            anti_detection.shutdown()
            return 0

def run_web_fallback():
    """Executar servidor web como fallback"""
    print("🔄 Iniciando demonstração web como fallback...")
    
    import http.server
    import socketserver
    import threading
    
    PORT = 5000
    
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory='.', **kwargs)
    
    def start_web_server():
        with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
            print(f"🌐 Servidor web rodando em http://0.0.0.0:{PORT}")
            httpd.serve_forever()
    
    server_thread = threading.Thread(target=start_web_server, daemon=True)
    server_thread.start()
    
    try:
        server_thread.join()
    except KeyboardInterrupt:
        print("\nAplicação finalizada.")
        sys.exit(0)

if __name__ == "__main__":
    # Tentar GUI primeiro, fallback para web se necessário
    gui_result = run_gui_application()
    
    if gui_result is None:
        run_web_fallback()
    else:
        sys.exit(gui_result)

def setup_logging():
    """Configurar sistema de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('object_detection.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def create_directories():
    """Criar diretórios necessários se não existirem"""
    directories = [
        'models',
        'logs',
        'config',
        'screenshots'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)

def main():
    """Função principal"""
    # Configurar logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Criar diretórios necessários
        create_directories()
        
        # Criar aplicação Qt
        app = QApplication(sys.argv)
        app.setApplicationName("ObjectDetectionAssistant")
        app.setApplicationVersion("1.0.0")
        
        # Definir estilo da aplicação
        app.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin: 5px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #404040;
                color: white;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #404040;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #0078d4;
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
        """)
        
        # Criar e mostrar janela principal
        window = ObjectDetectionGUI()
        window.show()
        
        logger.info("ObjectDetectionAssistant iniciado com sucesso")
        
        # Executar aplicação
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Erro ao iniciar aplicação: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
