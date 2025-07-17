#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Controle de mouse usando APIs nativas do Windows (DLL)
"""

import time
import logging
from typing import Tuple, Optional
import math
import platform

# Windows específico
if platform.system() == 'Windows':
    import ctypes
    import ctypes.wintypes
else:
    ctypes = None

# Constantes do Windows
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_ABSOLUTE = 0x8000

# Estruturas do Windows
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        class _MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", ctypes.wintypes.LONG),
                ("dy", ctypes.wintypes.LONG),
                ("mouseData", ctypes.wintypes.DWORD),
                ("dwFlags", ctypes.wintypes.DWORD),
                ("time", ctypes.wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.wintypes.ULONG))
            ]
        mi = _MOUSEINPUT
    _fields_ = [("type", ctypes.wintypes.DWORD), ("data", _INPUT)]

class DLLMouseController:
    """Controlador de mouse usando APIs nativas do Windows"""
    
    def __init__(self):
        """Inicializar controlador DLL"""
        self.logger = logging.getLogger(__name__)
        
        # Bibliotecas do Windows
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        
        # Obter dimensões da tela
        self.screen_width = self.user32.GetSystemMetrics(0)
        self.screen_height = self.user32.GetSystemMetrics(1)
        
        # Configurações de movimento
        self.movement_speed = 1.0  # Velocidade base
        self.smooth_movement = True
        
        self.logger.info(f"DLL Mouse Controller inicializado. Tela: {self.screen_width}x{self.screen_height}")
        
    def move_to(self, x: int, y: int, duration: float = 0.0):
        """
        Mover mouse para posição absoluta
        
        Args:
            x, y: Coordenadas de destino
            duration: Duração do movimento em segundos
        """
        try:
            # Garantir que coordenadas estão dentro da tela
            x = max(0, min(x, self.screen_width - 1))
            y = max(0, min(y, self.screen_height - 1))
            
            if duration > 0 and self.smooth_movement:
                self._smooth_move_to(x, y, duration)
            else:
                self._instant_move_to(x, y)
                
        except Exception as e:
            self.logger.error(f"Erro ao mover mouse: {e}")
            
    def _instant_move_to(self, x: int, y: int):
        """Mover mouse instantaneamente"""
        # Converter para coordenadas absolutas normalizadas (0-65535)
        norm_x = int(x * 65535 / self.screen_width)
        norm_y = int(y * 65535 / self.screen_height)
        
        # Usar mouse_event para movimento absoluto
        self.user32.mouse_event(
            MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE,
            norm_x, norm_y, 0, 0
        )
        
    def _smooth_move_to(self, target_x: int, target_y: int, duration: float):
        """Mover mouse suavemente"""
        # Obter posição atual
        current_pos = self.get_position()
        if not current_pos:
            self._instant_move_to(target_x, target_y)
            return
            
        start_x, start_y = current_pos
        
        # Calcular distância e passos
        distance = math.sqrt((target_x - start_x)**2 + (target_y - start_y)**2)
        if distance < 1:
            return
            
        # Número de passos baseado na duração e distância
        steps = max(int(duration * 60), 1)  # 60 FPS
        step_delay = duration / steps
        
        # Mover em passos
        for i in range(steps + 1):
            progress = i / steps
            
            # Usar curva ease-out para movimento mais natural
            progress = 1 - (1 - progress) ** 2
            
            current_x = int(start_x + (target_x - start_x) * progress)
            current_y = int(start_y + (target_y - start_y) * progress)
            
            self._instant_move_to(current_x, current_y)
            
            if i < steps:
                time.sleep(step_delay)
                
    def move_relative(self, dx: int, dy: int):
        """
        Mover mouse relativamente
        
        Args:
            dx, dy: Deslocamento relativo
        """
        try:
            self.user32.mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, 0)
        except Exception as e:
            self.logger.error(f"Erro no movimento relativo: {e}")
            
    def click(self, button: str = "left"):
        """
        Executar clique do mouse
        
        Args:
            button: Botão a ser clicado ("left", "right", "middle")
        """
        try:
            if button == "left":
                self.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(0.01)  # 10ms delay
                self.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            elif button == "right":
                self.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                time.sleep(0.01)
                self.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            elif button == "middle":
                self.user32.mouse_event(MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
                time.sleep(0.01)
                self.user32.mouse_event(MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
                
        except Exception as e:
            self.logger.error(f"Erro no clique: {e}")
            
    def press(self, button: str = "left"):
        """
        Pressionar botão do mouse
        
        Args:
            button: Botão a ser pressionado
        """
        try:
            if button == "left":
                self.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            elif button == "right":
                self.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            elif button == "middle":
                self.user32.mouse_event(MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
                
        except Exception as e:
            self.logger.error(f"Erro ao pressionar botão: {e}")
            
    def release(self, button: str = "left"):
        """
        Soltar botão do mouse
        
        Args:
            button: Botão a ser solto
        """
        try:
            if button == "left":
                self.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            elif button == "right":
                self.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            elif button == "middle":
                self.user32.mouse_event(MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
                
        except Exception as e:
            self.logger.error(f"Erro ao soltar botão: {e}")
            
    def scroll(self, direction: int):
        """
        Executar scroll
        
        Args:
            direction: Direção do scroll (positivo para cima, negativo para baixo)
        """
        try:
            # Cada unidade de scroll é tipicamente 120
            scroll_amount = direction * 120
            self.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, scroll_amount, 0)
            
        except Exception as e:
            self.logger.error(f"Erro no scroll: {e}")
            
    def get_position(self) -> Optional[Tuple[int, int]]:
        """
        Obter posição atual do mouse
        
        Returns:
            Tupla (x, y) com a posição atual
        """
        try:
            point = POINT()
            if self.user32.GetCursorPos(ctypes.byref(point)):
                return (point.x, point.y)
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao obter posição: {e}")
            return None
            
    def set_position(self, x: int, y: int):
        """
        Definir posição do cursor (alternativa para move_to)
        
        Args:
            x, y: Coordenadas de destino
        """
        try:
            self.user32.SetCursorPos(x, y)
        except Exception as e:
            self.logger.error(f"Erro ao definir posição: {e}")
            
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Obter dimensões da tela
        
        Returns:
            Tupla (largura, altura)
        """
        return (self.screen_width, self.screen_height)
        
    def set_movement_speed(self, speed: float):
        """
        Definir velocidade de movimento
        
        Args:
            speed: Multiplicador de velocidade (1.0 = normal)
        """
        self.movement_speed = max(0.1, min(speed, 10.0))
        
    def set_smooth_movement(self, enabled: bool):
        """
        Habilitar/desabilitar movimento suave
        
        Args:
            enabled: True para habilitar movimento suave
        """
        self.smooth_movement = enabled
        
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, 
             button: str = "left", duration: float = 0.5):
        """
        Executar operação de arrastar
        
        Args:
            start_x, start_y: Coordenadas iniciais
            end_x, end_y: Coordenadas finais
            button: Botão do mouse para arrastar
            duration: Duração da operação
        """
        try:
            # Mover para posição inicial
            self.move_to(start_x, start_y)
            time.sleep(0.1)
            
            # Pressionar botão
            self.press(button)
            time.sleep(0.1)
            
            # Mover para posição final
            self.move_to(end_x, end_y, duration)
            time.sleep(0.1)
            
            # Soltar botão
            self.release(button)
            
        except Exception as e:
            self.logger.error(f"Erro na operação de arrastar: {e}")
            
    def double_click(self, button: str = "left"):
        """
        Executar duplo clique
        
        Args:
            button: Botão do mouse
        """
        try:
            self.click(button)
            time.sleep(0.05)  # 50ms entre cliques
            self.click(button)
            
        except Exception as e:
            self.logger.error(f"Erro no duplo clique: {e}")
            
    def is_button_pressed(self, button: str) -> bool:
        """
        Verificar se botão está pressionado
        
        Args:
            button: Botão a verificar
            
        Returns:
            True se o botão estiver pressionado
        """
        try:
            if button == "left":
                return self.user32.GetAsyncKeyState(0x01) & 0x8000 != 0
            elif button == "right":
                return self.user32.GetAsyncKeyState(0x02) & 0x8000 != 0
            elif button == "middle":
                return self.user32.GetAsyncKeyState(0x04) & 0x8000 != 0
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar botão: {e}")
            return False
            
    def get_info(self) -> dict:
        """Obter informações do controlador"""
        return {
            'type': 'DLL Native',
            'screen_size': (self.screen_width, self.screen_height),
            'movement_speed': self.movement_speed,
            'smooth_movement': self.smooth_movement,
            'current_position': self.get_position()
        }
