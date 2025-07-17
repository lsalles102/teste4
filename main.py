#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ObjectDetectionAssistant - Sistema de Detecção de Objetos em Tempo Real
Ponto de entrada principal da aplicação
"""

import sys
import os
import platform
import logging
from pathlib import Path

# Adicionar diretórios ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Verificar plataforma
IS_LINUX = platform.system() == 'Linux'
IS_WINDOWS = platform.system() == 'Windows'

if IS_LINUX:
    # No Linux (Replit), usar versão simplificada
    print("🎯 ObjectDetectionAssistant - Versão Demonstração (Replit)")
    print("Para funcionalidade completa, execute em ambiente Windows")
    print("Servindo interface web de demonstração...")
    
    # Servir página web de demonstração
    import http.server
    import socketserver
    import webbrowser
    import threading
    
    PORT = 5000
    
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory='.', **kwargs)
    
    def start_web_server():
        with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
            print(f"Servidor rodando em http://0.0.0.0:{PORT}")
            httpd.serve_forever()
    
    # Iniciar servidor em thread separada
    server_thread = threading.Thread(target=start_web_server, daemon=True)
    server_thread.start()
    
    # Manter o programa rodando
    try:
        server_thread.join()
    except KeyboardInterrupt:
        print("\nServidor finalizado.")
        sys.exit(0)
        
else:
    # Windows - funcionalidade completa
    from PyQt5.QtWidgets import QApplication
    from gui.app import ObjectDetectionGUI

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
