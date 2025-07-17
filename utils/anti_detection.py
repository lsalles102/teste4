#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Avançado de Anti-Detecção
Implementa técnicas de hooking, obfuscação e movimentação natural
"""

import random
import time
import base64
import threading
import numpy as np
import cv2
from typing import Tuple, Optional, Callable
import ctypes
import platform
import hashlib
import os


class StringObfuscator:
    """Obfuscação de strings para evitar detecção estática"""
    
    @staticmethod
    def encode(text: str) -> str:
        """Codifica string usando Base64 + XOR"""
        key = 0x42  # Chave XOR simples
        encoded = ''.join(chr(ord(c) ^ key) for c in text)
        return base64.b64encode(encoded.encode()).decode()
    
    @staticmethod
    def decode(encoded: str) -> str:
        """Decodifica string obfuscada"""
        try:
            key = 0x42
            decoded_b64 = base64.b64decode(encoded.encode()).decode()
            return ''.join(chr(ord(c) ^ key) for c in decoded_b64)
        except:
            return ""


class NaturalMouseMovement:
    """Movimentação natural de mouse com jitter e timing humano"""
    
    def __init__(self):
        self.last_move_time = time.time()
        self.movement_history = []
        
        # Strings obfuscadas para evitar detecção
        self._mouse_patterns = [
            StringObfuscator.encode("natural_movement"),
            StringObfuscator.encode("human_behavior"),
            StringObfuscator.encode("anti_detection")
        ]
    
    def calculate_bezier_path(self, start: Tuple[int, int], end: Tuple[int, int], 
                            control_points: int = 3) -> list:
        """Calcula caminho suave usando curvas de Bézier"""
        points = []
        
        # Gerar pontos de controle aleatórios
        controls = []
        for i in range(control_points):
            t = (i + 1) / (control_points + 1)
            x = start[0] + (end[0] - start[0]) * t + random.randint(-20, 20)
            y = start[1] + (end[1] - start[1]) * t + random.randint(-20, 20)
            controls.append((x, y))
        
        # Calcular pontos da curva
        all_points = [start] + controls + [end]
        
        for t in np.linspace(0, 1, 50):
            x, y = self._bezier_point(all_points, t)
            points.append((int(x), int(y)))
            
        return points
    
    def _bezier_point(self, points: list, t: float) -> Tuple[float, float]:
        """Calcula ponto na curva de Bézier"""
        n = len(points) - 1
        x = sum(self._binomial_coefficient(n, i) * (t ** i) * ((1 - t) ** (n - i)) * points[i][0] 
                for i in range(n + 1))
        y = sum(self._binomial_coefficient(n, i) * (t ** i) * ((1 - t) ** (n - i)) * points[i][1] 
                for i in range(n + 1))
        return x, y
    
    def _binomial_coefficient(self, n: int, k: int) -> int:
        """Calcula coeficiente binomial"""
        if k > n - k:
            k = n - k
        result = 1
        for i in range(k):
            result = result * (n - i) // (i + 1)
        return result
    
    def add_human_jitter(self, x: int, y: int) -> Tuple[int, int]:
        """Adiciona jitter natural para simular tremor humano"""
        # Jitter baseado no tempo desde último movimento
        time_factor = min(time.time() - self.last_move_time, 1.0)
        jitter_strength = int(3 * time_factor)
        
        jitter_x = random.randint(-jitter_strength, jitter_strength)
        jitter_y = random.randint(-jitter_strength, jitter_strength)
        
        return x + jitter_x, y + jitter_y
    
    def calculate_human_delay(self, distance: float) -> float:
        """Calcula delay baseado em comportamento humano real"""
        # Delay base proporcional à distância
        base_delay = min(distance / 1000.0, 0.5)
        
        # Adicionar variação aleatória (fadiga, atenção)
        variation = random.uniform(0.8, 1.2)
        
        # Micro-pausas ocasionais (comportamento humano natural)
        if random.random() < 0.05:  # 5% chance
            variation += random.uniform(0.1, 0.3)
        
        return base_delay * variation
    
    def generate_movement_sequence(self, start: Tuple[int, int], 
                                 end: Tuple[int, int]) -> list:
        """Gera sequência completa de movimento natural"""
        # Calcular distância
        distance = ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5
        
        # Gerar caminho suave
        path = self.calculate_bezier_path(start, end)
        
        # Adicionar timing e jitter a cada ponto
        movement_sequence = []
        for i, (x, y) in enumerate(path):
            # Adicionar jitter
            final_x, final_y = self.add_human_jitter(x, y)
            
            # Calcular delay para este segmento
            segment_distance = 10  # Distância aproximada entre pontos
            delay = self.calculate_human_delay(segment_distance)
            
            movement_sequence.append({
                'x': final_x,
                'y': final_y,
                'delay': delay,
                'timestamp': time.time() + (i * delay)
            })
        
        return movement_sequence


class ScreenCaptureHooking:
    """Sistema de hooking para captura de tela furtiva"""
    
    def __init__(self):
        self.is_windows = platform.system() == 'Windows'
        self.hooked_functions = {}
        
        # Strings obfuscadas
        self._capture_methods = [
            StringObfuscator.encode("BitBlt"),
            StringObfuscator.encode("GetDC"),
            StringObfuscator.encode("CreateCompatibleDC")
        ]
    
    def hook_gdi_functions(self):
        """Hook funções GDI32 para captura furtiva"""
        if not self.is_windows:
            return False
            
        try:
            # Carregar biblioteca GDI32
            gdi32 = ctypes.windll.gdi32
            user32 = ctypes.windll.user32
            
            # Definir protótipos de função
            self._setup_function_prototypes(gdi32, user32)
            
            return True
        except Exception as e:
            print(f"Erro no hooking: {e}")
            return False
    
    def _setup_function_prototypes(self, gdi32, user32):
        """Configura protótipos de função para hooking"""
        # BitBlt prototype
        gdi32.BitBlt.argtypes = [
            ctypes.c_void_p,  # HDC hdcDest
            ctypes.c_int,     # int nXDest
            ctypes.c_int,     # int nYDest
            ctypes.c_int,     # int nWidth
            ctypes.c_int,     # int nHeight
            ctypes.c_void_p,  # HDC hdcSrc
            ctypes.c_int,     # int nXSrc
            ctypes.c_int,     # int nYSrc
            ctypes.c_ulong    # DWORD dwRop
        ]
        gdi32.BitBlt.restype = ctypes.c_int
        
        # GetDC prototype
        user32.GetDC.argtypes = [ctypes.c_void_p]
        user32.GetDC.restype = ctypes.c_void_p
    
    def capture_screen_stealthy(self, region: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """Captura de tela usando métodos furtivos"""
        try:
            import mss
            
            # Usar MSS com configurações otimizadas para anti-detecção
            with mss.mss() as sct:
                if region:
                    monitor = {
                        "top": region[1],
                        "left": region[0], 
                        "width": region[2] - region[0],
                        "height": region[3] - region[1]
                    }
                else:
                    monitor = sct.monitors[1]  # Monitor principal
                
                # Capturar com delay aleatório para evitar padrões
                time.sleep(random.uniform(0.001, 0.005))
                
                screenshot = sct.grab(monitor)
                img_array = np.array(screenshot)
                
                # Converter BGR para RGB
                img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGRA2RGB)
                
                return img_rgb
                
        except Exception as e:
            print(f"Erro na captura furtiva: {e}")
            return np.zeros((100, 100, 3), dtype=np.uint8)


class ProcessStealth:
    """Técnicas de furtividade em nível de processo"""
    
    def __init__(self):
        self.process_name = self._generate_random_name()
        self.pid_spoofing_active = False
    
    def _generate_random_name(self) -> str:
        """Gera nome de processo aparentemente legítimo"""
        legitimate_names = [
            "svchost.exe", "explorer.exe", "winlogon.exe",
            "csrss.exe", "lsass.exe", "spoolsv.exe"
        ]
        return random.choice(legitimate_names)
    
    def randomize_memory_layout(self):
        """Randomiza layout de memória para evitar detecção"""
        # Alocar e liberar blocos aleatórios de memória
        dummy_allocations = []
        for _ in range(random.randint(5, 15)):
            size = random.randint(1024, 8192)
            dummy_allocations.append(bytearray(size))
        
        # Liberar algumas alocações aleatoriamente
        for _ in range(len(dummy_allocations) // 2):
            if dummy_allocations:
                dummy_allocations.pop(random.randint(0, len(dummy_allocations) - 1))
    
    def add_fake_api_calls(self):
        """Adiciona chamadas de API falsas para confundir análise"""
        fake_operations = [
            lambda: time.sleep(random.uniform(0.001, 0.005)),
            lambda: hash(str(time.time())),
            lambda: len(str(random.random())),
            lambda: os.path.exists("fake_path.txt")
        ]
        
        # Executar operações falsas aleatórias
        for _ in range(random.randint(3, 8)):
            operation = random.choice(fake_operations)
            operation()


class AntiDetectionManager:
    """Gerenciador principal de anti-detecção"""
    
    def __init__(self):
        self.mouse_movement = NaturalMouseMovement()
        self.screen_capture = ScreenCaptureHooking()
        self.process_stealth = ProcessStealth()
        
        self.active = False
        self.stealth_thread = None
    
    def initialize(self) -> bool:
        """Inicializa todos os sistemas de anti-detecção"""
        try:
            # Configurar hooking de captura
            hook_success = self.screen_capture.hook_gdi_functions()
            
            # Randomizar layout de memória
            self.process_stealth.randomize_memory_layout()
            
            # Iniciar thread de furtividade
            self.active = True
            self.stealth_thread = threading.Thread(target=self._stealth_worker, daemon=True)
            self.stealth_thread.start()
            
            return hook_success
            
        except Exception as e:
            print(f"Erro na inicialização anti-detecção: {e}")
            return False
    
    def _stealth_worker(self):
        """Worker thread para operações contínuas de furtividade"""
        while self.active:
            try:
                # Operações periódicas de furtividade
                self.process_stealth.add_fake_api_calls()
                
                # Randomizar timing
                time.sleep(random.uniform(5.0, 15.0))
                
            except Exception as e:
                print(f"Erro no worker de furtividade: {e}")
                time.sleep(1.0)
    
    def capture_screen_safe(self, region: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """Captura de tela com anti-detecção ativa"""
        return self.screen_capture.capture_screen_stealthy(region)
    
    def move_mouse_natural(self, start: Tuple[int, int], end: Tuple[int, int], 
                          callback: Optional[Callable] = None):
        """Move mouse de forma natural com anti-detecção"""
        sequence = self.mouse_movement.generate_movement_sequence(start, end)
        
        for movement in sequence:
            if callback:
                callback(movement['x'], movement['y'])
            
            time.sleep(movement['delay'])
    
    def shutdown(self):
        """Finaliza sistemas de anti-detecção"""
        self.active = False
        if self.stealth_thread and self.stealth_thread.is_alive():
            self.stealth_thread.join(timeout=1.0)


# Instância global
anti_detection = AntiDetectionManager()