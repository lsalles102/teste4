#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Captura de tela usando DirectX Screen Duplication API
"""

import numpy as np
import cv2
import logging
from typing import Optional, Dict, Tuple
import time
import platform

# Windows específico
if platform.system() == 'Windows':
    import ctypes
    import ctypes.wintypes
else:
    # Mock para sistemas não-Windows
    ctypes = None

# Constantes do Windows
DXGI_ERROR_WAIT_TIMEOUT = 0x887A0027
DXGI_ERROR_ACCESS_LOST = 0x887A0026
DXGI_ERROR_INVALID_CALL = 0x887A0001

class ScreenCaptureDX:
    """Captura de tela usando DirectX Screen Duplication API"""
    
    def __init__(self, adapter_index: int = 0, output_index: int = 0):
        """
        Inicializar capturador DirectX
        
        Args:
            adapter_index: Índice do adaptador gráfico
            output_index: Índice da saída (monitor)
        """
        self.logger = logging.getLogger(__name__)
        self.adapter_index = adapter_index
        self.output_index = output_index
        
        # Handles DirectX
        self.d3d_device = None
        self.dxgi_output = None
        self.duplication = None
        
        # Estatísticas
        self.frame_count = 0
        self.last_time = time.time()
        self.fps = 0
        
        # Verificar se ctypes está disponível (Windows)
        if ctypes is None:
            self.logger.warning("DirectX não disponível - sistema não Windows")
            self.initialized = False
            return
        
        # Tentar inicializar DirectX
        self.initialized = False
        self._initialize_dx()
        
    def _initialize_dx(self):
        """Inicializar componentes DirectX"""
        try:
            self.logger.info("Inicializando DirectX Screen Duplication...")
            
            # Esta é uma implementação simplificada
            # Para uma implementação completa, seria necessário usar bibliotecas como
            # comtypes ou win32gui para acessar as APIs DirectX
            
            # Por enquanto, usar fallback para captura básica do Windows
            self._use_gdi_fallback()
            
        except Exception as e:
            self.logger.warning(f"Erro ao inicializar DirectX: {e}")
            self.logger.info("Usando fallback GDI")
            self._use_gdi_fallback()
            
    def _use_gdi_fallback(self):
        """Usar GDI como fallback"""
        try:
            # Importar bibliotecas do Windows
            self.user32 = ctypes.windll.user32
            self.gdi32 = ctypes.windll.gdi32
            
            # Obter dimensões da tela
            self.screen_width = self.user32.GetSystemMetrics(0)
            self.screen_height = self.user32.GetSystemMetrics(1)
            
            # Criar contextos de dispositivo
            self.hdesktop = self.user32.GetDesktopWindow()
            self.hwndDC = self.user32.GetWindowDC(self.hdesktop)
            self.mfcDC = self.gdi32.CreateCompatibleDC(self.hwndDC)
            
            # Criar bitmap
            self.saveBitMap = self.gdi32.CreateCompatibleBitmap(
                self.hwndDC, self.screen_width, self.screen_height)
            self.gdi32.SelectObject(self.mfcDC, self.saveBitMap)
            
            self.logger.info(f"GDI fallback inicializado: {self.screen_width}x{self.screen_height}")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar GDI fallback: {e}")
            raise
            
    def capture(self) -> Optional[np.ndarray]:
        """
        Capturar frame da tela
        
        Returns:
            Array numpy com a imagem capturada ou None em caso de erro
        """
        try:
            return self._capture_gdi()
            
        except Exception as e:
            self.logger.error(f"Erro na captura DirectX: {e}")
            return None
            
    def _capture_gdi(self) -> Optional[np.ndarray]:
        """Capturar usando GDI"""
        try:
            # Copiar tela para bitmap
            result = self.gdi32.BitBlt(
                self.mfcDC, 0, 0, self.screen_width, self.screen_height,
                self.hwndDC, 0, 0, 0x00CC0020)  # SRCCOPY
                
            if not result:
                return None
                
            # Obter dados do bitmap
            bmpinfo = self._get_bitmap_info()
            bmpbytes = ctypes.create_string_buffer(bmpinfo.bmiHeader.biSizeImage)
            
            got_bits = self.gdi32.GetDIBits(
                self.hwndDC, self.saveBitMap, 0, self.screen_height,
                bmpbytes, ctypes.byref(bmpinfo), 0)
                
            if not got_bits:
                return None
                
            # Converter para numpy array
            frame = np.frombuffer(bmpbytes, dtype=np.uint8)
            frame = frame.reshape((self.screen_height, self.screen_width, 4))
            
            # Remover canal alpha e converter BGR
            frame = frame[:, :, :3]
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Flipar verticalmente (GDI retorna imagem invertida)
            frame = cv2.flip(frame, 0)
            
            # Atualizar estatísticas
            self._update_stats()
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Erro na captura GDI: {e}")
            return None
            
    def _get_bitmap_info(self):
        """Obter informações do bitmap"""
        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ('biSize', ctypes.wintypes.DWORD),
                ('biWidth', ctypes.wintypes.LONG),
                ('biHeight', ctypes.wintypes.LONG),
                ('biPlanes', ctypes.wintypes.WORD),
                ('biBitCount', ctypes.wintypes.WORD),
                ('biCompression', ctypes.wintypes.DWORD),
                ('biSizeImage', ctypes.wintypes.DWORD),
                ('biXPelsPerMeter', ctypes.wintypes.LONG),
                ('biYPelsPerMeter', ctypes.wintypes.LONG),
                ('biClrUsed', ctypes.wintypes.DWORD),
                ('biClrImportant', ctypes.wintypes.DWORD)
            ]
            
        class BITMAPINFO(ctypes.Structure):
            _fields_ = [
                ('bmiHeader', BITMAPINFOHEADER),
                ('bmiColors', ctypes.wintypes.DWORD * 3)
            ]
            
        bmpinfo = BITMAPINFO()
        bmpinfo.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmpinfo.bmiHeader.biWidth = self.screen_width
        bmpinfo.bmiHeader.biHeight = self.screen_height
        bmpinfo.bmiHeader.biPlanes = 1
        bmpinfo.bmiHeader.biBitCount = 32
        bmpinfo.bmiHeader.biCompression = 0  # BI_RGB
        bmpinfo.bmiHeader.biSizeImage = self.screen_width * self.screen_height * 4
        
        return bmpinfo
        
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
            # Capturar tela completa primeiro
            full_frame = self.capture()
            if full_frame is None:
                return None
                
            # Recortar região
            y_end = min(y + height, full_frame.shape[0])
            x_end = min(x + width, full_frame.shape[1])
            
            region = full_frame[y:y_end, x:x_end]
            return region
            
        except Exception as e:
            self.logger.error(f"Erro na captura de região: {e}")
            return None
            
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Obter dimensões da tela
        
        Returns:
            Tupla (largura, altura)
        """
        return self.screen_width, self.screen_height
        
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
        self.logger.info(f"Iniciando benchmark DirectX por {duration} segundos...")
        
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
            'capture_method': 'DirectX (GDI Fallback)'
        }
        
        self.logger.info(f"Benchmark concluído: {avg_fps:.2f} FPS, "
                        f"{avg_frame_time:.2f}ms por frame")
        
        return stats
        
    def close(self):
        """Fechar capturador"""
        try:
            if hasattr(self, 'gdi32') and hasattr(self, 'mfcDC'):
                self.gdi32.DeleteObject(self.saveBitMap)
                self.gdi32.DeleteDC(self.mfcDC)
                self.user32.ReleaseDC(self.hdesktop, self.hwndDC)
                
            self.logger.info("Capturador DirectX fechado")
            
        except Exception as e:
            self.logger.error(f"Erro ao fechar capturador: {e}")
