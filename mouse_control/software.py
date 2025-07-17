#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Controle de mouse via software (simulação para sistemas sem hardware específico)
"""

import time
import logging
import threading
import math
from typing import Tuple, Optional
import random

class SoftwareMouseController:
    """Controlador de mouse via software (simulação)"""
    
    def __init__(self):
        """Inicializar controlador de software"""
        self.logger = logging.getLogger(__name__)
        
        # Posição virtual do mouse
        self.virtual_x = 960
        self.virtual_y = 540
        
        # Dimensões virtuais da tela
        self.screen_width = 1920
        self.screen_height = 1080
        
        # Configurações de movimento
        self.movement_speed = 1.0
        self.smooth_movement = True
        self.simulation_mode = True
        
        # Estatísticas
        self.total_movements = 0
        self.total_clicks = 0
        
        # Thread para simulação de movimento
        self.movement_thread = None
        self.movement_queue = []
        self.queue_lock = threading.Lock()
        self.running = False
        
        self.logger.info("Software Mouse Controller inicializado (modo simulação)")
        self._start_simulation_thread()
        
    def _start_simulation_thread(self):
        """Iniciar thread de simulação"""
        if not self.movement_thread or not self.movement_thread.is_alive():
            self.running = True
            self.movement_thread = threading.Thread(target=self._simulation_loop, daemon=True)
            self.movement_thread.start()
            
    def _simulation_loop(self):
        """Loop principal da simulação"""
        while self.running:
            try:
                # Processar movimentos da fila
                with self.queue_lock:
                    if self.movement_queue:
                        movement = self.movement_queue.pop(0)
                        self._execute_movement(movement)
                        
                time.sleep(0.001)  # 1ms delay
                
            except Exception as e:
                self.logger.error(f"Erro na thread de simulação: {e}")
                
    def _execute_movement(self, movement: dict):
        """Executar movimento virtual"""
        try:
            action = movement.get('action')
            
            if action == 'move_to':
                target_x = movement.get('x', self.virtual_x)
                target_y = movement.get('y', self.virtual_y)
                duration = movement.get('duration', 0.0)
                
                if duration > 0 and self.smooth_movement:
                    self._smooth_move(target_x, target_y, duration)
                else:
                    self.virtual_x = target_x
                    self.virtual_y = target_y
                    
                self.total_movements += 1
                
            elif action == 'move_relative':
                dx = movement.get('dx', 0)
                dy = movement.get('dy', 0)
                self.virtual_x += dx
                self.virtual_y += dy
                self._clamp_position()
                self.total_movements += 1
                
            elif action == 'click':
                button = movement.get('button', 'left')
                self.logger.debug(f"Simulando clique {button} em ({self.virtual_x}, {self.virtual_y})")
                self.total_clicks += 1
                
            # Log da ação para debug
            self.logger.debug(f"Executando ação: {action} - Posição: ({self.virtual_x}, {self.virtual_y})")
            
        except Exception as e:
            self.logger.error(f"Erro ao executar movimento: {e}")
            
    def _smooth_move(self, target_x: int, target_y: int, duration: float):
        """Executar movimento suave"""
        start_x, start_y = self.virtual_x, self.virtual_y
        start_time = time.time()
        
        while time.time() - start_time < duration:
            progress = (time.time() - start_time) / duration
            progress = min(1.0, progress)
            
            # Usar curva ease-out
            eased_progress = 1 - (1 - progress) ** 2
            
            self.virtual_x = int(start_x + (target_x - start_x) * eased_progress)
            self.virtual_y = int(start_y + (target_y - start_y) * eased_progress)
            
            time.sleep(0.016)  # ~60 FPS
            
        self.virtual_x = target_x
        self.virtual_y = target_y
        
    def _clamp_position(self):
        """Garantir que posição está dentro da tela virtual"""
        self.virtual_x = max(0, min(self.virtual_x, self.screen_width - 1))
        self.virtual_y = max(0, min(self.virtual_y, self.screen_height - 1))
        
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
            
            movement = {
                'action': 'move_to',
                'x': x,
                'y': y,
                'duration': duration
            }
            
            with self.queue_lock:
                self.movement_queue.append(movement)
                
        except Exception as e:
            self.logger.error(f"Erro ao mover mouse: {e}")
            
    def move_relative(self, dx: int, dy: int):
        """
        Mover mouse relativamente
        
        Args:
            dx, dy: Deslocamento relativo
        """
        try:
            movement = {
                'action': 'move_relative',
                'dx': dx,
                'dy': dy
            }
            
            with self.queue_lock:
                self.movement_queue.append(movement)
                
        except Exception as e:
            self.logger.error(f"Erro no movimento relativo: {e}")
            
    def click(self, button: str = "left"):
        """
        Executar clique do mouse
        
        Args:
            button: Botão a ser clicado ("left", "right", "middle")
        """
        try:
            movement = {
                'action': 'click',
                'button': button
            }
            
            with self.queue_lock:
                self.movement_queue.append(movement)
                
        except Exception as e:
            self.logger.error(f"Erro no clique: {e}")
            
    def press(self, button: str = "left"):
        """
        Pressionar botão do mouse
        
        Args:
            button: Botão a ser pressionado
        """
        try:
            movement = {
                'action': 'press',
                'button': button
            }
            
            with self.queue_lock:
                self.movement_queue.append(movement)
                
        except Exception as e:
            self.logger.error(f"Erro ao pressionar botão: {e}")
            
    def release(self, button: str = "left"):
        """
        Soltar botão do mouse
        
        Args:
            button: Botão a ser solto
        """
        try:
            movement = {
                'action': 'release',
                'button': button
            }
            
            with self.queue_lock:
                self.movement_queue.append(movement)
                
        except Exception as e:
            self.logger.error(f"Erro ao soltar botão: {e}")
            
    def scroll(self, direction: int):
        """
        Executar scroll
        
        Args:
            direction: Direção do scroll (positivo para cima, negativo para baixo)
        """
        try:
            movement = {
                'action': 'scroll',
                'direction': direction
            }
            
            with self.queue_lock:
                self.movement_queue.append(movement)
                
        except Exception as e:
            self.logger.error(f"Erro no scroll: {e}")
            
    def get_position(self) -> Optional[Tuple[int, int]]:
        """
        Obter posição atual do mouse
        
        Returns:
            Tupla (x, y) com a posição virtual atual
        """
        return (self.virtual_x, self.virtual_y)
        
    def set_position(self, x: int, y: int):
        """
        Definir posição do cursor
        
        Args:
            x, y: Coordenadas de destino
        """
        self.move_to(x, y)
        
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Obter dimensões da tela virtual
        
        Returns:
            Tupla (largura, altura)
        """
        return (self.screen_width, self.screen_height)
        
    def set_screen_size(self, width: int, height: int):
        """
        Definir dimensões da tela virtual
        
        Args:
            width, height: Novas dimensões
        """
        self.screen_width = width
        self.screen_height = height
        self._clamp_position()
        
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
            
    def simulate_jitter(self, intensity: float = 1.0):
        """
        Simular tremulação natural do mouse
        
        Args:
            intensity: Intensidade da tremulação
        """
        try:
            jitter_x = random.randint(-int(intensity), int(intensity))
            jitter_y = random.randint(-int(intensity), int(intensity))
            
            new_x = self.virtual_x + jitter_x
            new_y = self.virtual_y + jitter_y
            
            self.move_to(new_x, new_y, 0.1)
            
        except Exception as e:
            self.logger.error(f"Erro na simulação de tremulação: {e}")
            
    def get_statistics(self) -> dict:
        """Obter estatísticas de uso"""
        return {
            'total_movements': self.total_movements,
            'total_clicks': self.total_clicks,
            'current_position': (self.virtual_x, self.virtual_y),
            'queue_size': len(self.movement_queue),
            'simulation_active': self.running
        }
        
    def reset_statistics(self):
        """Resetar estatísticas"""
        self.total_movements = 0
        self.total_clicks = 0
        
    def clear_queue(self):
        """Limpar fila de movimentos"""
        with self.queue_lock:
            self.movement_queue.clear()
            
    def get_queue_size(self) -> int:
        """Obter tamanho da fila"""
        with self.queue_lock:
            return len(self.movement_queue)
            
    def test_pattern(self, pattern: str = "circle"):
        """
        Executar padrão de teste
        
        Args:
            pattern: Tipo de padrão ("circle", "square", "line")
        """
        try:
            center_x = self.screen_width // 2
            center_y = self.screen_height // 2
            
            if pattern == "circle":
                # Desenhar círculo
                radius = 100
                steps = 36
                for i in range(steps + 1):
                    angle = 2 * math.pi * i / steps
                    x = center_x + int(radius * math.cos(angle))
                    y = center_y + int(radius * math.sin(angle))
                    self.move_to(x, y, 0.1)
                    
            elif pattern == "square":
                # Desenhar quadrado
                size = 200
                points = [
                    (center_x - size//2, center_y - size//2),
                    (center_x + size//2, center_y - size//2),
                    (center_x + size//2, center_y + size//2),
                    (center_x - size//2, center_y + size//2),
                    (center_x - size//2, center_y - size//2)
                ]
                for x, y in points:
                    self.move_to(x, y, 0.5)
                    
            elif pattern == "line":
                # Desenhar linha
                start_x = center_x - 200
                end_x = center_x + 200
                self.move_to(start_x, center_y, 0.5)
                self.move_to(end_x, center_y, 1.0)
                self.move_to(center_x, center_y, 0.5)
                
        except Exception as e:
            self.logger.error(f"Erro no padrão de teste: {e}")
            
    def get_info(self) -> dict:
        """Obter informações do controlador"""
        return {
            'type': 'Software Simulation',
            'screen_size': (self.screen_width, self.screen_height),
            'movement_speed': self.movement_speed,
            'smooth_movement': self.smooth_movement,
            'current_position': self.get_position(),
            'simulation_mode': self.simulation_mode,
            'statistics': self.get_statistics()
        }
        
    def stop(self):
        """Parar simulação"""
        self.running = False
        if self.movement_thread and self.movement_thread.is_alive():
            self.movement_thread.join(timeout=1.0)
            
    def __del__(self):
        """Destrutor"""
        self.stop()
