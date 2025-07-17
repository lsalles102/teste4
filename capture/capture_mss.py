#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Captura de tela usando MSS (Multi Screen Shots)
"""

import mss
import numpy as np
import cv2
import logging
from typing import Optional, Dict, Tuple
import time

class ScreenCaptureMSS:
    """Captura de tela usando biblioteca MSS"""
    
    def __init__(self, monitor_index: int = 0, region: Optional[Dict] = None):
        """
        Inicializar capturador MSS
        
        Args:
            monitor_index: Índice do monitor (0 para todos os monitores)
            region: Região específica para captura {top, left, width, height}
        """
        self.logger = logging.getLogger(__name__)
        self.monitor_index = monitor_index
        self.region = region
        
        # Inicializar MSS
        self.sct = mss.mss()
        self.monitor = None
        
        # Estatísticas
        self.frame_count = 0
        self.last_time = time.time()
        self.fps = 0
        
        self._setup_monitor()
        
    def _setup_monitor(self):
        """Configurar monitor para captura"""
        try:
            # Obter informações dos monitores
            monitors = self.sct.monitors
            self.logger.info(f"Monitores disponíveis: {len(monitors) - 1}")
            
            # Selecionar monitor
            if self.monitor_index < len(monitors):
                self.monitor = monitors[self.monitor_index]
            else:
                self.monitor = monitors[0]  # Monitor principal
                
            # Aplicar região personalizada se especificada
            if self.region:
                self.monitor = {
                    'top': self.region.get('top', self.monitor['top']),
                    'left': self.region.get('left', self.monitor['left']),
                    'width': self.region.get('width', self.monitor['width']),
                    'height': self.region.get('height', self.monitor['height'])
                }
                
            self.logger.info(f"Monitor configurado: {self.monitor}")
            
        except Exception as e:
            self.logger.error(f"Erro ao configurar monitor: {e}")
            raise
            
    def capture(self) -> Optional[np.ndarray]:
        """
        Capturar frame da tela
        
        Returns:
            Array numpy com a imagem capturada ou None em caso de erro
        """
        try:
            # Capturar tela
            screenshot = self.sct.grab(self.monitor)
            
            # Converter para numpy array
            frame = np.array(screenshot)
            
            # Converter de BGRA para BGR (remover canal alpha)
            if frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            elif frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
            # Atualizar estatísticas
            self._update_stats()
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Erro na captura MSS: {e}")
            return None
            
    def capture_region(self, x: int, y: int, width: int, height: int) -> Optional[np.ndarray]:
        """
        Capturar região específica da tela
        
        Args:
            x, y: Coordenadas do canto superior esquerdo
            width, height: Dimensões da região
            
        Returns:
            Array numpy com a região capturada
        """
        try:
            # Definir região
            region = {
                'top': y,
                'left': x,
                'width': width,
                'height': height
            }
            
            # Capturar região
            screenshot = self.sct.grab(region)
            frame = np.array(screenshot)
            
            # Converter formato
            if frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            elif frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
            return frame
            
        except Exception as e:
            self.logger.error(f"Erro na captura de região: {e}")
            return None
            
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Obter dimensões da tela
        
        Returns:
            Tupla (largura, altura)
        """
        if self.monitor:
            return self.monitor['width'], self.monitor['height']
        return 0, 0
        
    def set_region(self, x: int, y: int, width: int, height: int):
        """
        Definir região de captura
        
        Args:
            x, y: Coordenadas do canto superior esquerdo
            width, height: Dimensões da região
        """
        self.region = {
            'top': y,
            'left': x,
            'width': width,
            'height': height
        }
        self._setup_monitor()
        
    def reset_region(self):
        """Resetar para captura de tela completa"""
        self.region = None
        self._setup_monitor()
        
    def get_monitors_info(self) -> list:
        """
        Obter informações de todos os monitores
        
        Returns:
            Lista com informações dos monitores
        """
        monitors_info = []
        
        try:
            for i, monitor in enumerate(self.sct.monitors):
                if i == 0:  # Pular monitor "All in One"
                    continue
                    
                info = {
                    'index': i,
                    'top': monitor['top'],
                    'left': monitor['left'],
                    'width': monitor['width'],
                    'height': monitor['height']
                }
                monitors_info.append(info)
                
        except Exception as e:
            self.logger.error(f"Erro ao obter informações dos monitores: {e}")
            
        return monitors_info
        
    def _update_stats(self):
        """Atualizar estatísticas de performance"""
        self.frame_count += 1
        current_time = time.time()
        
        # Calcular FPS a cada segundo
        if current_time - self.last_time >= 1.0:
            self.fps = self.frame_count / (current_time - self.last_time)
            self.frame_count = 0
            self.last_time = current_time
            
    def get_fps(self) -> float:
        """Obter FPS atual"""
        return self.fps
        
    def benchmark(self, duration: int = 10) -> Dict:
        """
        Executar benchmark de performance
        
        Args:
            duration: Duração do teste em segundos
            
        Returns:
            Dicionário com estatísticas de performance
        """
        self.logger.info(f"Iniciando benchmark por {duration} segundos...")
        
        start_time = time.time()
        frame_count = 0
        frame_times = []
        
        while time.time() - start_time < duration:
            frame_start = time.time()
            
            frame = self.capture()
            if frame is not None:
                frame_count += 1
                
            frame_end = time.time()
            frame_times.append(frame_end - frame_start)
            
        total_time = time.time() - start_time
        avg_fps = frame_count / total_time
        avg_frame_time = np.mean(frame_times) * 1000  # em ms
        min_frame_time = np.min(frame_times) * 1000
        max_frame_time = np.max(frame_times) * 1000
        
        stats = {
            'total_frames': frame_count,
            'total_time': total_time,
            'average_fps': avg_fps,
            'average_frame_time_ms': avg_frame_time,
            'min_frame_time_ms': min_frame_time,
            'max_frame_time_ms': max_frame_time,
            'capture_method': 'MSS'
        }
        
        self.logger.info(f"Benchmark concluído: {avg_fps:.2f} FPS, "
                        f"{avg_frame_time:.2f}ms por frame")
        
        return stats
        
    def close(self):
        """Fechar capturador"""
        try:
            self.sct.close()
            self.logger.info("Capturador MSS fechado")
        except Exception as e:
            self.logger.error(f"Erro ao fechar capturador: {e}")
