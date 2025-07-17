#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface Gráfica Principal do ObjectDetectionAssistant
"""

import sys
import os
import json
import logging
import threading
import time
from pathlib import Path

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QPushButton, QLabel, QSlider, QComboBox, QSpinBox,
    QCheckBox, QLineEdit, QTextEdit, QProgressBar, QFileDialog,
    QMessageBox, QTabWidget, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPixmap, QIcon

# Importar módulos do sistema
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detector.detector_loader import DetectorLoader
from capture.capture_mss import ScreenCaptureMSS
from capture.capture_dx import ScreenCaptureDX
from mouse_control.arduino import ArduinoController
from mouse_control.dll_mouse import DLLMouseController
from mouse_control.software import SoftwareMouseController
from utils.smoothing import MovementSmoother

class DetectionThread(QThread):
    """Thread para execução da detecção em tempo real"""
    detection_result = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, detector, capture, mouse_controller, settings):
        super().__init__()
        self.detector = detector
        self.capture = capture
        self.mouse_controller = mouse_controller
        self.settings = settings
        self.running = False
        self.smoother = MovementSmoother()
        
    def run(self):
        """Executar loop de detecção"""
        self.running = True
        logger = logging.getLogger(__name__)
        
        while self.running:
            try:
                # Capturar tela
                frame = self.capture.capture()
                if frame is None:
                    continue
                
                # Realizar detecção
                detections = self.detector.detect(frame, 
                    confidence_threshold=self.settings['confidence_threshold'])
                
                if detections:
                    # Processar detecções
                    for detection in detections:
                        if detection['confidence'] >= self.settings['confidence_threshold']:
                            # Calcular posição do objeto
                            x, y = detection['center']
                            
                            # Aplicar suavização
                            smooth_x, smooth_y = self.smoother.smooth(x, y, 
                                self.settings['smoothing_factor'])
                            
                            # Mover mouse
                            if self.mouse_controller:
                                self.mouse_controller.move_to(smooth_x, smooth_y)
                            
                            # Emitir resultado
                            self.detection_result.emit({
                                'detections': detections,
                                'position': (smooth_x, smooth_y)
                            })
                            break
                
                # Controlar FPS
                time.sleep(1.0 / self.settings.get('max_fps', 30))
                
            except Exception as e:
                logger.error(f"Erro na thread de detecção: {e}")
                self.error_occurred.emit(str(e))
                break
    
    def stop(self):
        """Parar thread"""
        self.running = False

class ObjectDetectionGUI(QMainWindow):
    """Interface gráfica principal"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Variáveis de estado
        self.detector = None
        self.capture = None
        self.mouse_controller = None
        self.detection_thread = None
        self.is_running = False
        
        # Configurações padrão
        self.settings = self.load_settings()
        
        # Configurar interface
        self.init_ui()
        self.setup_connections()
        
        # Timer para atualização da interface
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_interface)
        self.update_timer.start(100)  # 10 FPS para UI
        
    def init_ui(self):
        """Inicializar interface do usuário"""
        self.setWindowTitle("ObjectDetectionAssistant v1.0")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        
        # Painel de controles
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel, 1)
        
        # Painel de status e logs
        status_panel = self.create_status_panel()
        main_layout.addWidget(status_panel, 2)
        
    def create_control_panel(self):
        """Criar painel de controles"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Controles de modelo
        model_group = self.create_model_group()
        layout.addWidget(model_group)
        
        # Controles de captura
        capture_group = self.create_capture_group()
        layout.addWidget(capture_group)
        
        # Controles de movimento
        movement_group = self.create_movement_group()
        layout.addWidget(movement_group)
        
        # Controles de detecção
        detection_group = self.create_detection_group()
        layout.addWidget(detection_group)
        
        # Controles principais
        main_controls = self.create_main_controls()
        layout.addWidget(main_controls)
        
        layout.addStretch()
        return panel
        
    def create_model_group(self):
        """Criar grupo de controles do modelo"""
        group = QGroupBox("Configuração do Modelo")
        layout = QGridLayout(group)
        
        # Seleção de arquivo de modelo
        layout.addWidget(QLabel("Arquivo do Modelo:"), 0, 0)
        self.model_path_edit = QLineEdit(self.settings.get('model_path', ''))
        layout.addWidget(self.model_path_edit, 0, 1)
        
        self.browse_model_btn = QPushButton("Navegar")
        self.browse_model_btn.clicked.connect(self.browse_model_file)
        layout.addWidget(self.browse_model_btn, 0, 2)
        
        # Arquivo de nomes
        layout.addWidget(QLabel("Arquivo de Classes:"), 1, 0)
        self.names_path_edit = QLineEdit(self.settings.get('names_path', 'models/coco.names'))
        layout.addWidget(self.names_path_edit, 1, 1)
        
        self.browse_names_btn = QPushButton("Navegar")
        self.browse_names_btn.clicked.connect(self.browse_names_file)
        layout.addWidget(self.browse_names_btn, 1, 2)
        
        # Backend
        layout.addWidget(QLabel("Backend:"), 2, 0)
        self.backend_combo = QComboBox()
        self.backend_combo.addItems(["CPU", "CUDA", "DirectML"])
        self.backend_combo.setCurrentText(self.settings.get('backend', 'CPU'))
        layout.addWidget(self.backend_combo, 2, 1)
        
        return group
        
    def create_capture_group(self):
        """Criar grupo de controles de captura"""
        group = QGroupBox("Captura de Tela")
        layout = QGridLayout(group)
        
        # Método de captura
        layout.addWidget(QLabel("Método:"), 0, 0)
        self.capture_method_combo = QComboBox()
        self.capture_method_combo.addItems(["MSS", "DirectX"])
        self.capture_method_combo.setCurrentText(self.settings.get('capture_method', 'MSS'))
        layout.addWidget(self.capture_method_combo, 0, 1)
        
        # Região de captura
        layout.addWidget(QLabel("Região:"), 1, 0)
        self.capture_region_combo = QComboBox()
        self.capture_region_combo.addItems(["Tela Inteira", "Janela Ativa", "Personalizada"])
        layout.addWidget(self.capture_region_combo, 1, 1)
        
        # FPS máximo
        layout.addWidget(QLabel("FPS Máximo:"), 2, 0)
        self.max_fps_spin = QSpinBox()
        self.max_fps_spin.setRange(1, 120)
        self.max_fps_spin.setValue(self.settings.get('max_fps', 30))
        layout.addWidget(self.max_fps_spin, 2, 1)
        
        return group
        
    def create_movement_group(self):
        """Criar grupo de controles de movimento"""
        group = QGroupBox("Controle de Movimento")
        layout = QGridLayout(group)
        
        # Método de movimento
        layout.addWidget(QLabel("Método:"), 0, 0)
        self.movement_method_combo = QComboBox()
        self.movement_method_combo.addItems(["Arduino (HID)", "DLL Nativa", "Software"])
        self.movement_method_combo.setCurrentText(self.settings.get('movement_method', 'Software'))
        layout.addWidget(self.movement_method_combo, 0, 1)
        
        # Porta COM (para Arduino)
        layout.addWidget(QLabel("Porta COM:"), 1, 0)
        self.com_port_edit = QLineEdit(self.settings.get('com_port', 'COM3'))
        layout.addWidget(self.com_port_edit, 1, 1)
        
        # Suavização
        layout.addWidget(QLabel("Suavização:"), 2, 0)
        self.smoothing_slider = QSlider(Qt.Horizontal)
        self.smoothing_slider.setRange(0, 100)
        self.smoothing_slider.setValue(int(self.settings.get('smoothing_factor', 50)))
        layout.addWidget(self.smoothing_slider, 2, 1)
        
        self.smoothing_label = QLabel(f"{self.smoothing_slider.value()}%")
        layout.addWidget(self.smoothing_label, 2, 2)
        
        return group
        
    def create_detection_group(self):
        """Criar grupo de controles de detecção"""
        group = QGroupBox("Parâmetros de Detecção")
        layout = QGridLayout(group)
        
        # Confiança mínima
        layout.addWidget(QLabel("Confiança Mínima:"), 0, 0)
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setRange(1, 100)
        self.confidence_slider.setValue(int(self.settings.get('confidence_threshold', 50) * 100))
        layout.addWidget(self.confidence_slider, 0, 1)
        
        self.confidence_label = QLabel(f"{self.confidence_slider.value()}%")
        layout.addWidget(self.confidence_label, 0, 2)
        
        # FOV
        layout.addWidget(QLabel("Campo de Visão:"), 1, 0)
        self.fov_slider = QSlider(Qt.Horizontal)
        self.fov_slider.setRange(10, 100)
        self.fov_slider.setValue(int(self.settings.get('fov_percentage', 80)))
        layout.addWidget(self.fov_slider, 1, 1)
        
        self.fov_label = QLabel(f"{self.fov_slider.value()}%")
        layout.addWidget(self.fov_label, 1, 2)
        
        # Classe alvo
        layout.addWidget(QLabel("Classe Alvo:"), 2, 0)
        self.target_class_combo = QComboBox()
        self.target_class_combo.addItems(["person", "car", "bicycle", "motorbike", "all"])
        self.target_class_combo.setCurrentText(self.settings.get('target_class', 'person'))
        layout.addWidget(self.target_class_combo, 2, 1)
        
        return group
        
    def create_main_controls(self):
        """Criar controles principais"""
        group = QGroupBox("Controles Principais")
        layout = QVBoxLayout(group)
        
        # Botão principal
        self.start_stop_btn = QPushButton("Iniciar Detecção")
        self.start_stop_btn.setMinimumHeight(40)
        self.start_stop_btn.clicked.connect(self.toggle_detection)
        layout.addWidget(self.start_stop_btn)
        
        # Botões secundários
        button_layout = QHBoxLayout()
        
        self.test_capture_btn = QPushButton("Testar Captura")
        self.test_capture_btn.clicked.connect(self.test_capture)
        button_layout.addWidget(self.test_capture_btn)
        
        self.test_movement_btn = QPushButton("Testar Movimento")
        self.test_movement_btn.clicked.connect(self.test_movement)
        button_layout.addWidget(self.test_movement_btn)
        
        layout.addLayout(button_layout)
        
        # Salvar/Carregar configurações
        config_layout = QHBoxLayout()
        
        self.save_config_btn = QPushButton("Salvar Config")
        self.save_config_btn.clicked.connect(self.save_settings)
        config_layout.addWidget(self.save_config_btn)
        
        self.load_config_btn = QPushButton("Carregar Config")
        self.load_config_btn.clicked.connect(self.load_settings_from_file)
        config_layout.addWidget(self.load_config_btn)
        
        layout.addLayout(config_layout)
        
        return group
        
    def create_status_panel(self):
        """Criar painel de status"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Abas
        tabs = QTabWidget()
        
        # Aba de status
        status_tab = self.create_status_tab()
        tabs.addTab(status_tab, "Status")
        
        # Aba de logs
        logs_tab = self.create_logs_tab()
        tabs.addTab(logs_tab, "Logs")
        
        # Aba de visualização
        preview_tab = self.create_preview_tab()
        tabs.addTab(preview_tab, "Visualização")
        
        layout.addWidget(tabs)
        
        return panel
        
    def create_status_tab(self):
        """Criar aba de status"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Status geral
        status_group = QGroupBox("Status do Sistema")
        status_layout = QGridLayout(status_group)
        
        # Indicadores de status
        status_layout.addWidget(QLabel("Detector:"), 0, 0)
        self.detector_status = QLabel("Não Carregado")
        status_layout.addWidget(self.detector_status, 0, 1)
        
        status_layout.addWidget(QLabel("Captura:"), 1, 0)
        self.capture_status = QLabel("Inativo")
        status_layout.addWidget(self.capture_status, 1, 1)
        
        status_layout.addWidget(QLabel("Movimento:"), 2, 0)
        self.movement_status = QLabel("Não Conectado")
        status_layout.addWidget(self.movement_status, 2, 1)
        
        layout.addWidget(status_group)
        
        # Estatísticas
        stats_group = QGroupBox("Estatísticas em Tempo Real")
        stats_layout = QGridLayout(stats_group)
        
        stats_layout.addWidget(QLabel("FPS:"), 0, 0)
        self.fps_label = QLabel("0")
        stats_layout.addWidget(self.fps_label, 0, 1)
        
        stats_layout.addWidget(QLabel("Detecções:"), 1, 0)
        self.detections_label = QLabel("0")
        stats_layout.addWidget(self.detections_label, 1, 1)
        
        stats_layout.addWidget(QLabel("Posição Mouse:"), 2, 0)
        self.mouse_pos_label = QLabel("(0, 0)")
        stats_layout.addWidget(self.mouse_pos_label, 2, 1)
        
        layout.addWidget(stats_group)
        
        layout.addStretch()
        return widget
        
    def create_logs_tab(self):
        """Criar aba de logs"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Área de logs
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(1000)  # Limitar linhas
        layout.addWidget(self.log_text)
        
        # Controles de log
        log_controls = QHBoxLayout()
        
        clear_logs_btn = QPushButton("Limpar Logs")
        clear_logs_btn.clicked.connect(self.log_text.clear)
        log_controls.addWidget(clear_logs_btn)
        
        save_logs_btn = QPushButton("Salvar Logs")
        save_logs_btn.clicked.connect(self.save_logs)
        log_controls.addWidget(save_logs_btn)
        
        log_controls.addStretch()
        layout.addLayout(log_controls)
        
        return widget
        
    def create_preview_tab(self):
        """Criar aba de visualização"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Label para preview
        self.preview_label = QLabel("Preview não disponível")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(640, 480)
        self.preview_label.setStyleSheet("border: 1px solid #555555; background-color: #404040;")
        layout.addWidget(self.preview_label)
        
        return widget
        
    def setup_connections(self):
        """Configurar conexões de sinais"""
        # Sliders
        self.smoothing_slider.valueChanged.connect(
            lambda v: self.smoothing_label.setText(f"{v}%"))
        self.confidence_slider.valueChanged.connect(
            lambda v: self.confidence_label.setText(f"{v}%"))
        self.fov_slider.valueChanged.connect(
            lambda v: self.fov_label.setText(f"{v}%"))
        
        # Combos
        self.movement_method_combo.currentTextChanged.connect(self.on_movement_method_changed)
        
    def browse_model_file(self):
        """Navegar por arquivo de modelo"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Selecionar Modelo", "", 
            "Modelos (*.weights *.pt *.onnx);;Todos os arquivos (*)")
        
        if file_path:
            self.model_path_edit.setText(file_path)
            
    def browse_names_file(self):
        """Navegar por arquivo de nomes"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Selecionar Arquivo de Classes", "", 
            "Arquivos de texto (*.names *.txt);;Todos os arquivos (*)")
        
        if file_path:
            self.names_path_edit.setText(file_path)
            
    def on_movement_method_changed(self, method):
        """Callback para mudança do método de movimento"""
        # Habilitar/desabilitar controles baseado no método
        is_arduino = "Arduino" in method
        self.com_port_edit.setEnabled(is_arduino)
        
    def toggle_detection(self):
        """Alternar detecção"""
        if not self.is_running:
            self.start_detection()
        else:
            self.stop_detection()
            
    def start_detection(self):
        """Iniciar detecção"""
        try:
            # Atualizar configurações
            self.update_settings_from_ui()
            
            # Carregar detector
            self.load_detector()
            
            # Configurar captura
            self.setup_capture()
            
            # Configurar controle de movimento
            self.setup_movement_control()
            
            # Iniciar thread de detecção
            self.detection_thread = DetectionThread(
                self.detector, self.capture, self.mouse_controller, self.settings)
            self.detection_thread.detection_result.connect(self.on_detection_result)
            self.detection_thread.error_occurred.connect(self.on_detection_error)
            self.detection_thread.start()
            
            # Atualizar UI
            self.is_running = True
            self.start_stop_btn.setText("Parar Detecção")
            self.start_stop_btn.setStyleSheet("background-color: #d73527;")
            
            self.log_message("Detecção iniciada com sucesso")
            
        except Exception as e:
            self.show_error(f"Erro ao iniciar detecção: {e}")
            
    def stop_detection(self):
        """Parar detecção"""
        try:
            if self.detection_thread:
                self.detection_thread.stop()
                self.detection_thread.wait()
                
            self.is_running = False
            self.start_stop_btn.setText("Iniciar Detecção")
            self.start_stop_btn.setStyleSheet("")
            
            self.log_message("Detecção parada")
            
        except Exception as e:
            self.show_error(f"Erro ao parar detecção: {e}")
            
    def load_detector(self):
        """Carregar detector"""
        model_path = self.model_path_edit.text()
        names_path = self.names_path_edit.text()
        backend = self.backend_combo.currentText()
        
        if not model_path or not os.path.exists(model_path):
            raise ValueError("Arquivo de modelo não encontrado")
            
        self.detector = DetectorLoader.load_detector(
            model_path, names_path, backend)
        self.detector_status.setText("Carregado")
        
    def setup_capture(self):
        """Configurar captura de tela"""
        method = self.capture_method_combo.currentText()
        
        if method == "MSS":
            self.capture = ScreenCaptureMSS()
        else:
            self.capture = ScreenCaptureDX()
            
        self.capture_status.setText("Ativo")
        
    def setup_movement_control(self):
        """Configurar controle de movimento"""
        method = self.movement_method_combo.currentText()
        
        if "Arduino" in method:
            com_port = self.com_port_edit.text()
            self.mouse_controller = ArduinoController(com_port)
        elif "DLL" in method:
            self.mouse_controller = DLLMouseController()
        else:
            self.mouse_controller = SoftwareMouseController()
            
        self.movement_status.setText("Conectado")
        
    def test_capture(self):
        """Testar captura de tela"""
        try:
            self.setup_capture()
            frame = self.capture.capture()
            if frame is not None:
                self.show_info("Captura de tela funcionando corretamente")
            else:
                self.show_error("Falha na captura de tela")
        except Exception as e:
            self.show_error(f"Erro no teste de captura: {e}")
            
    def test_movement(self):
        """Testar movimento do mouse"""
        try:
            self.setup_movement_control()
            # Mover mouse para centro da tela
            self.mouse_controller.move_to(960, 540)
            self.show_info("Teste de movimento executado")
        except Exception as e:
            self.show_error(f"Erro no teste de movimento: {e}")
            
    def on_detection_result(self, result):
        """Callback para resultado de detecção"""
        detections = result.get('detections', [])
        position = result.get('position', (0, 0))
        
        # Atualizar estatísticas
        self.detections_label.setText(str(len(detections)))
        self.mouse_pos_label.setText(f"({position[0]}, {position[1]})")
        
    def on_detection_error(self, error):
        """Callback para erro de detecção"""
        self.show_error(f"Erro na detecção: {error}")
        self.stop_detection()
        
    def update_interface(self):
        """Atualizar interface periodicamente"""
        # Atualizar FPS se necessário
        pass
        
    def update_settings_from_ui(self):
        """Atualizar configurações a partir da UI"""
        self.settings.update({
            'model_path': self.model_path_edit.text(),
            'names_path': self.names_path_edit.text(),
            'backend': self.backend_combo.currentText(),
            'capture_method': self.capture_method_combo.currentText(),
            'movement_method': self.movement_method_combo.currentText(),
            'com_port': self.com_port_edit.text(),
            'smoothing_factor': self.smoothing_slider.value() / 100.0,
            'confidence_threshold': self.confidence_slider.value() / 100.0,
            'fov_percentage': self.fov_slider.value(),
            'target_class': self.target_class_combo.currentText(),
            'max_fps': self.max_fps_spin.value()
        })
        
    def load_settings(self):
        """Carregar configurações"""
        try:
            with open('config/settings.json', 'r') as f:
                return json.load(f)
        except:
            return {
                'model_path': '',
                'names_path': 'models/coco.names',
                'backend': 'CPU',
                'capture_method': 'MSS',
                'movement_method': 'Software',
                'com_port': 'COM3',
                'smoothing_factor': 0.5,
                'confidence_threshold': 0.5,
                'fov_percentage': 80,
                'target_class': 'person',
                'max_fps': 30
            }
            
    def save_settings(self):
        """Salvar configurações"""
        try:
            self.update_settings_from_ui()
            with open('config/settings.json', 'w') as f:
                json.dump(self.settings, f, indent=4)
            self.show_info("Configurações salvas com sucesso")
        except Exception as e:
            self.show_error(f"Erro ao salvar configurações: {e}")
            
    def load_settings_from_file(self):
        """Carregar configurações de arquivo"""
        try:
            self.settings = self.load_settings()
            # Atualizar UI com configurações carregadas
            self.model_path_edit.setText(self.settings.get('model_path', ''))
            self.names_path_edit.setText(self.settings.get('names_path', 'models/coco.names'))
            # ... outros controles
            self.show_info("Configurações carregadas com sucesso")
        except Exception as e:
            self.show_error(f"Erro ao carregar configurações: {e}")
            
    def save_logs(self):
        """Salvar logs"""
        try:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getSaveFileName(
                self, "Salvar Logs", "logs.txt", "Arquivos de texto (*.txt)")
            
            if file_path:
                with open(file_path, 'w') as f:
                    f.write(self.log_text.toPlainText())
                self.show_info("Logs salvos com sucesso")
        except Exception as e:
            self.show_error(f"Erro ao salvar logs: {e}")
            
    def log_message(self, message):
        """Adicionar mensagem ao log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def show_info(self, message):
        """Mostrar mensagem de informação"""
        QMessageBox.information(self, "Informação", message)
        self.log_message(f"INFO: {message}")
        
    def show_error(self, message):
        """Mostrar mensagem de erro"""
        QMessageBox.critical(self, "Erro", message)
        self.log_message(f"ERRO: {message}")
        
    def closeEvent(self, event):
        """Evento de fechamento da janela"""
        if self.is_running:
            self.stop_detection()
        self.save_settings()
        event.accept()
