#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilitários para suavização de movimento do mouse
"""

import time
import math
import logging
from typing import List, Tuple, Optional
from collections import deque
import numpy as np

class MovementSmoother:
    """Classe para suavização de movimentos do mouse"""
    
    def __init__(self, window_size: int = 5, smoothing_factor: float = 0.5):
        """
        Inicializar suavizador de movimento
        
        Args:
            window_size: Tamanho da janela para média móvel
            smoothing_factor: Fator de suavização (0.0 a 1.0)
        """
        self.logger = logging.getLogger(__name__)
        self.window_size = max(1, window_size)
        self.smoothing_factor = max(0.0, min(1.0, smoothing_factor))
        
        # Histórico de posições
        self.position_history = deque(maxlen=self.window_size)
        self.velocity_history = deque(maxlen=self.window_size)
        
        # Estado atual
        self.last_position = None
        self.last_time = None
        self.current_velocity = (0.0, 0.0)
        
        # Configurações avançadas
        self.enable_acceleration_smoothing = True
        self.enable_jitter_reduction = True
        self.jitter_threshold = 2.0  # pixels
        self.max_velocity = 1000.0  # pixels por segundo
        
        self.logger.info(f"MovementSmoother inicializado: window={window_size}, factor={smoothing_factor}")
        
    def smooth(self, x: float, y: float, custom_factor: Optional[float] = None) -> Tuple[float, float]:
        """
        Aplicar suavização a uma posição
        
        Args:
            x, y: Coordenadas originais
            custom_factor: Fator de suavização personalizado
            
        Returns:
            Tupla com coordenadas suavizadas (x, y)
        """
        current_time = time.time()
        factor = custom_factor if custom_factor is not None else self.smoothing_factor
        
        # Primeira posição
        if self.last_position is None:
            self.last_position = (x, y)
            self.last_time = current_time
            self.position_history.append((x, y))
            return (x, y)
            
        # Calcular velocidade
        dt = current_time - self.last_time
        if dt > 0:
            dx = x - self.last_position[0]
            dy = y - self.last_position[1]
            velocity = (dx / dt, dy / dt)
            self.velocity_history.append(velocity)
            self.current_velocity = velocity
        else:
            velocity = self.current_velocity
            
        # Aplicar redução de tremulação
        if self.enable_jitter_reduction:
            distance = math.sqrt((x - self.last_position[0])**2 + (y - self.last_position[1])**2)
            if distance < self.jitter_threshold:
                # Movimento muito pequeno, provavelmente tremulação
                factor = min(factor, 0.2)  # Suavização mais agressiva
                
        # Aplicar suavização baseada na velocidade
        if self.enable_acceleration_smoothing:
            velocity_magnitude = math.sqrt(velocity[0]**2 + velocity[1]**2)
            if velocity_magnitude > self.max_velocity:
                # Movimento muito rápido, aplicar mais suavização
                factor = min(factor, 0.3)
                
        # Calcular posição suavizada usando exponential smoothing
        smooth_x = self.last_position[0] + factor * (x - self.last_position[0])
        smooth_y = self.last_position[1] + factor * (y - self.last_position[1])
        
        # Aplicar média móvel se habilitada
        if len(self.position_history) >= 2:
            smooth_x, smooth_y = self._apply_moving_average(smooth_x, smooth_y)
            
        # Atualizar estado
        self.position_history.append((smooth_x, smooth_y))
        self.last_position = (smooth_x, smooth_y)
        self.last_time = current_time
        
        return (smooth_x, smooth_y)
        
    def _apply_moving_average(self, x: float, y: float) -> Tuple[float, float]:
        """Aplicar média móvel às posições"""
        try:
            # Adicionar posição atual temporariamente
            temp_history = list(self.position_history) + [(x, y)]
            
            # Calcular média ponderada (mais peso para posições recentes)
            weights = np.exp(-np.arange(len(temp_history))[::-1] / 2.0)
            weights = weights / np.sum(weights)
            
            avg_x = np.average([pos[0] for pos in temp_history], weights=weights)
            avg_y = np.average([pos[1] for pos in temp_history], weights=weights)
            
            return (avg_x, avg_y)
            
        except Exception as e:
            self.logger.error(f"Erro na média móvel: {e}")
            return (x, y)
            
    def smooth_trajectory(self, points: List[Tuple[float, float]], 
                         iterations: int = 1) -> List[Tuple[float, float]]:
        """
        Suavizar uma trajetória completa
        
        Args:
            points: Lista de pontos (x, y)
            iterations: Número de iterações de suavização
            
        Returns:
            Lista de pontos suavizados
        """
        if len(points) < 3:
            return points
            
        smoothed = list(points)
        
        for _ in range(iterations):
            new_smoothed = [smoothed[0]]  # Manter primeiro ponto
            
            for i in range(1, len(smoothed) - 1):
                # Suavização usando média ponderada dos vizinhos
                prev_point = smoothed[i - 1]
                curr_point = smoothed[i]
                next_point = smoothed[i + 1]
                
                # Pesos: vizinhos 25% cada, atual 50%
                smooth_x = 0.25 * prev_point[0] + 0.5 * curr_point[0] + 0.25 * next_point[0]
                smooth_y = 0.25 * prev_point[1] + 0.5 * curr_point[1] + 0.25 * next_point[1]
                
                new_smoothed.append((smooth_x, smooth_y))
                
            new_smoothed.append(smoothed[-1])  # Manter último ponto
            smoothed = new_smoothed
            
        return smoothed
        
    def bezier_smooth(self, points: List[Tuple[float, float]], 
                     num_segments: int = 10) -> List[Tuple[float, float]]:
        """
        Suavizar trajetória usando curvas de Bézier
        
        Args:
            points: Pontos de controle
            num_segments: Número de segmentos por curva
            
        Returns:
            Trajetória suavizada
        """
        if len(points) < 2:
            return points
            
        smoothed = []
        
        for i in range(len(points) - 1):
            p0 = points[i]
            p1 = points[i + 1]
            
            # Pontos de controle para curva quadrática
            if i > 0:
                # Usar ponto anterior para suavidade
                prev = points[i - 1]
                control = (
                    p0[0] + 0.3 * (p1[0] - prev[0]),
                    p0[1] + 0.3 * (p1[1] - prev[1])
                )
            else:
                control = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
                
            # Gerar pontos da curva
            for t in range(num_segments + 1):
                t_norm = t / num_segments
                
                # Curva de Bézier quadrática
                x = (1 - t_norm)**2 * p0[0] + 2 * (1 - t_norm) * t_norm * control[0] + t_norm**2 * p1[0]
                y = (1 - t_norm)**2 * p0[1] + 2 * (1 - t_norm) * t_norm * control[1] + t_norm**2 * p1[1]
                
                if not smoothed or (x, y) != smoothed[-1]:
                    smoothed.append((x, y))
                    
        return smoothed
        
    def adaptive_smooth(self, x: float, y: float, target_fps: float = 60.0) -> Tuple[float, float]:
        """
        Suavização adaptiva baseada no FPS
        
        Args:
            x, y: Coordenadas originais
            target_fps: FPS alvo para ajustar suavização
            
        Returns:
            Coordenadas suavizadas
        """
        current_time = time.time()
        
        if self.last_time is not None:
            actual_fps = 1.0 / (current_time - self.last_time)
            
            # Ajustar fator de suavização baseado no FPS
            fps_ratio = actual_fps / target_fps
            adaptive_factor = self.smoothing_factor * min(1.0, fps_ratio)
            
            return self.smooth(x, y, adaptive_factor)
        else:
            return self.smooth(x, y)
            
    def predict_position(self, time_ahead: float = 0.016) -> Optional[Tuple[float, float]]:
        """
        Prever posição futura baseada na velocidade atual
        
        Args:
            time_ahead: Tempo em segundos para predição
            
        Returns:
            Posição predita ou None se não há dados suficientes
        """
        if self.last_position is None or not self.velocity_history:
            return None
            
        # Usar velocidade média recente
        recent_velocities = list(self.velocity_history)[-3:]  # Últimas 3 velocidades
        avg_vx = sum(v[0] for v in recent_velocities) / len(recent_velocities)
        avg_vy = sum(v[1] for v in recent_velocities) / len(recent_velocities)
        
        # Predizer posição
        pred_x = self.last_position[0] + avg_vx * time_ahead
        pred_y = self.last_position[1] + avg_vy * time_ahead
        
        return (pred_x, pred_y)
        
    def set_smoothing_factor(self, factor: float):
        """Definir fator de suavização"""
        self.smoothing_factor = max(0.0, min(1.0, factor))
        
    def set_window_size(self, size: int):
        """Definir tamanho da janela"""
        self.window_size = max(1, size)
        self.position_history = deque(self.position_history, maxlen=size)
        self.velocity_history = deque(self.velocity_history, maxlen=size)
        
    def enable_feature(self, feature: str, enabled: bool):
        """Habilitar/desabilitar funcionalidades"""
        if feature == "acceleration_smoothing":
            self.enable_acceleration_smoothing = enabled
        elif feature == "jitter_reduction":
            self.enable_jitter_reduction = enabled
            
    def set_jitter_threshold(self, threshold: float):
        """Definir limiar de tremulação"""
        self.jitter_threshold = max(0.1, threshold)
        
    def set_max_velocity(self, velocity: float):
        """Definir velocidade máxima"""
        self.max_velocity = max(1.0, velocity)
        
    def reset(self):
        """Resetar estado do suavizador"""
        self.position_history.clear()
        self.velocity_history.clear()
        self.last_position = None
        self.last_time = None
        self.current_velocity = (0.0, 0.0)
        
    def get_statistics(self) -> dict:
        """Obter estatísticas do suavizador"""
        avg_velocity = 0.0
        if self.velocity_history:
            velocities = [math.sqrt(v[0]**2 + v[1]**2) for v in self.velocity_history]
            avg_velocity = sum(velocities) / len(velocities)
            
        return {
            'smoothing_factor': self.smoothing_factor,
            'window_size': self.window_size,
            'history_length': len(self.position_history),
            'current_position': self.last_position,
            'current_velocity': self.current_velocity,
            'average_velocity': avg_velocity,
            'jitter_threshold': self.jitter_threshold,
            'max_velocity': self.max_velocity
        }


class EasingFunctions:
    """Funções de easing para movimento suave"""
    
    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """Easing cúbico in-out"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
            
    @staticmethod
    def ease_out_elastic(t: float) -> float:
        """Easing elástico out"""
        c4 = (2 * math.pi) / 3
        if t == 0:
            return 0
        elif t == 1:
            return 1
        else:
            return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1
            
    @staticmethod
    def ease_in_out_back(t: float) -> float:
        """Easing back in-out"""
        c1 = 1.70158
        c2 = c1 * 1.525
        
        if t < 0.5:
            return (pow(2 * t, 2) * ((c2 + 1) * 2 * t - c2)) / 2
        else:
            return (pow(2 * t - 2, 2) * ((c2 + 1) * (t * 2 - 2) + c2) + 2) / 2
            
    @staticmethod
    def ease_out_bounce(t: float) -> float:
        """Easing bounce out"""
        n1 = 7.5625
        d1 = 2.75
        
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            return n1 * (t - 1.5 / d1) * t + 0.75
        elif t < 2.5 / d1:
            return n1 * (t - 2.25 / d1) * t + 0.9375
        else:
            return n1 * (t - 2.625 / d1) * t + 0.984375


class TrajectoryGenerator:
    """Gerador de trajetórias suaves"""
    
    @staticmethod
    def generate_smooth_path(start: Tuple[float, float], end: Tuple[float, float],
                           curve_type: str = "bezier", num_points: int = 20) -> List[Tuple[float, float]]:
        """
        Gerar caminho suave entre dois pontos
        
        Args:
            start: Ponto inicial
            end: Ponto final
            curve_type: Tipo de curva ("linear", "bezier", "arc")
            num_points: Número de pontos no caminho
            
        Returns:
            Lista de pontos do caminho
        """
        if curve_type == "linear":
            return TrajectoryGenerator._linear_path(start, end, num_points)
        elif curve_type == "bezier":
            return TrajectoryGenerator._bezier_path(start, end, num_points)
        elif curve_type == "arc":
            return TrajectoryGenerator._arc_path(start, end, num_points)
        else:
            return [start, end]
            
    @staticmethod
    def _linear_path(start: Tuple[float, float], end: Tuple[float, float],
                    num_points: int) -> List[Tuple[float, float]]:
        """Gerar caminho linear"""
        path = []
        for i in range(num_points + 1):
            t = i / num_points
            x = start[0] + t * (end[0] - start[0])
            y = start[1] + t * (end[1] - start[1])
            path.append((x, y))
        return path
        
    @staticmethod
    def _bezier_path(start: Tuple[float, float], end: Tuple[float, float],
                    num_points: int) -> List[Tuple[float, float]]:
        """Gerar caminho Bézier"""
        # Ponto de controle no meio com offset
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        
        # Offset perpendicular para criar curva
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.sqrt(dx*dx + dy*dy)
        
        if length > 0:
            offset = length * 0.2
            control_x = mid_x - dy * offset / length
            control_y = mid_y + dx * offset / length
        else:
            control_x, control_y = mid_x, mid_y
            
        path = []
        for i in range(num_points + 1):
            t = i / num_points
            
            # Curva de Bézier quadrática
            x = (1-t)**2 * start[0] + 2*(1-t)*t * control_x + t**2 * end[0]
            y = (1-t)**2 * start[1] + 2*(1-t)*t * control_y + t**2 * end[1]
            
            path.append((x, y))
            
        return path
        
    @staticmethod
    def _arc_path(start: Tuple[float, float], end: Tuple[float, float],
                 num_points: int) -> List[Tuple[float, float]]:
        """Gerar caminho em arco"""
        # Centro do arco
        center_x = (start[0] + end[0]) / 2
        center_y = (start[1] + end[1]) / 2
        
        # Raio baseado na distância
        radius = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2) / 2
        
        # Ângulos
        start_angle = math.atan2(start[1] - center_y, start[0] - center_x)
        end_angle = math.atan2(end[1] - center_y, end[0] - center_x)
        
        # Garantir que o arco não seja muito longo
        angle_diff = end_angle - start_angle
        if abs(angle_diff) > math.pi:
            if angle_diff > 0:
                end_angle -= 2 * math.pi
            else:
                end_angle += 2 * math.pi
                
        path = []
        for i in range(num_points + 1):
            t = i / num_points
            angle = start_angle + t * (end_angle - start_angle)
            
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            
            path.append((x, y))
            
        return path
