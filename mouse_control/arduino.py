#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Controle de mouse via Arduino HID
"""

import serial
import time
import logging
import threading
from typing import Optional, Tuple
import json

class ArduinoController:
    """Controlador de mouse via Arduino HID"""
    
    def __init__(self, com_port: str = "COM3", baud_rate: int = 9600):
        """
        Inicializar controlador Arduino
        
        Args:
            com_port: Porta COM do Arduino
            baud_rate: Taxa de transmissão
        """
        self.logger = logging.getLogger(__name__)
        self.com_port = com_port
        self.baud_rate = baud_rate
        
        # Conexão serial
        self.serial_connection = None
        self.is_connected = False
        
        # Controle de thread
        self.command_queue = []
        self.queue_lock = threading.Lock()
        self.worker_thread = None
        self.running = False
        
        # Tentativas de conexão
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Conectar ao Arduino
        self.connect()
        
    def connect(self) -> bool:
        """
        Conectar ao Arduino
        
        Returns:
            True se conectado com sucesso
        """
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Tentando conectar ao Arduino na porta {self.com_port} "
                               f"(tentativa {attempt + 1}/{self.max_retries})")
                
                # Criar conexão serial
                self.serial_connection = serial.Serial(
                    port=self.com_port,
                    baudrate=self.baud_rate,
                    timeout=1.0,
                    write_timeout=1.0
                )
                
                # Aguardar estabilização
                time.sleep(2.0)
                
                # Testar comunicação
                if self._test_communication():
                    self.is_connected = True
                    self._start_worker_thread()
                    self.logger.info("Conectado ao Arduino com sucesso")
                    return True
                else:
                    self.serial_connection.close()
                    self.serial_connection = None
                    
            except serial.SerialException as e:
                self.logger.warning(f"Erro de conexão serial: {e}")
                if self.serial_connection:
                    self.serial_connection.close()
                    self.serial_connection = None
                    
            except Exception as e:
                self.logger.error(f"Erro inesperado na conexão: {e}")
                
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay)
                
        self.logger.error("Falha ao conectar ao Arduino")
        return False
        
    def _test_communication(self) -> bool:
        """Testar comunicação com Arduino"""
        try:
            # Enviar comando de teste
            test_command = {"cmd": "ping"}
            self._send_raw_command(test_command)
            
            # Aguardar resposta
            start_time = time.time()
            while time.time() - start_time < 3.0:
                if self.serial_connection.in_waiting > 0:
                    response = self.serial_connection.readline().decode().strip()
                    if "pong" in response.lower():
                        return True
                time.sleep(0.1)
                
            return False
            
        except Exception as e:
            self.logger.error(f"Erro no teste de comunicação: {e}")
            return False
            
    def _start_worker_thread(self):
        """Iniciar thread de processamento de comandos"""
        if not self.worker_thread or not self.worker_thread.is_alive():
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            
    def _worker_loop(self):
        """Loop principal da thread de processamento"""
        while self.running and self.is_connected:
            try:
                # Processar comandos da fila
                with self.queue_lock:
                    if self.command_queue:
                        command = self.command_queue.pop(0)
                        self._send_raw_command(command)
                        
                time.sleep(0.001)  # 1ms delay
                
            except Exception as e:
                self.logger.error(f"Erro na thread de processamento: {e}")
                
    def _send_raw_command(self, command: dict):
        """Enviar comando bruto para Arduino"""
        try:
            if self.serial_connection and self.is_connected:
                command_str = json.dumps(command) + '\n'
                self.serial_connection.write(command_str.encode())
                self.serial_connection.flush()
                
        except Exception as e:
            self.logger.error(f"Erro ao enviar comando: {e}")
            self.is_connected = False
            
    def move_to(self, x: int, y: int, duration: float = 0.0):
        """
        Mover mouse para posição absoluta
        
        Args:
            x, y: Coordenadas de destino
            duration: Duração do movimento (não usado no Arduino)
        """
        if not self.is_connected:
            self.logger.warning("Arduino não conectado")
            return
            
        command = {
            "cmd": "move_abs",
            "x": int(x),
            "y": int(y)
        }
        
        with self.queue_lock:
            self.command_queue.append(command)
            
    def move_relative(self, dx: int, dy: int):
        """
        Mover mouse relativamente
        
        Args:
            dx, dy: Deslocamento relativo
        """
        if not self.is_connected:
            return
            
        command = {
            "cmd": "move_rel",
            "dx": int(dx),
            "dy": int(dy)
        }
        
        with self.queue_lock:
            self.command_queue.append(command)
            
    def click(self, button: str = "left"):
        """
        Executar clique do mouse
        
        Args:
            button: Botão a ser clicado ("left", "right", "middle")
        """
        if not self.is_connected:
            return
            
        command = {
            "cmd": "click",
            "button": button
        }
        
        with self.queue_lock:
            self.command_queue.append(command)
            
    def press(self, button: str = "left"):
        """
        Pressionar botão do mouse
        
        Args:
            button: Botão a ser pressionado
        """
        if not self.is_connected:
            return
            
        command = {
            "cmd": "press",
            "button": button
        }
        
        with self.queue_lock:
            self.command_queue.append(command)
            
    def release(self, button: str = "left"):
        """
        Soltar botão do mouse
        
        Args:
            button: Botão a ser solto
        """
        if not self.is_connected:
            return
            
        command = {
            "cmd": "release",
            "button": button
        }
        
        with self.queue_lock:
            self.command_queue.append(command)
            
    def scroll(self, direction: int):
        """
        Executar scroll
        
        Args:
            direction: Direção do scroll (positivo para cima, negativo para baixo)
        """
        if not self.is_connected:
            return
            
        command = {
            "cmd": "scroll",
            "direction": int(direction)
        }
        
        with self.queue_lock:
            self.command_queue.append(command)
            
    def get_position(self) -> Optional[Tuple[int, int]]:
        """
        Obter posição atual do mouse
        
        Returns:
            Tupla (x, y) ou None se não disponível
        """
        # Arduino HID não pode ler posição do mouse
        # Retornar None para indicar que não está disponível
        return None
        
    def is_connected_status(self) -> bool:
        """Verificar se Arduino está conectado"""
        return self.is_connected
        
    def get_connection_info(self) -> dict:
        """Obter informações da conexão"""
        return {
            'port': self.com_port,
            'baud_rate': self.baud_rate,
            'connected': self.is_connected,
            'queue_size': len(self.command_queue)
        }
        
    def reconnect(self) -> bool:
        """Tentar reconectar ao Arduino"""
        self.disconnect()
        time.sleep(1.0)
        return self.connect()
        
    def disconnect(self):
        """Desconectar do Arduino"""
        try:
            self.running = False
            
            # Parar thread
            if self.worker_thread and self.worker_thread.is_alive():
                self.worker_thread.join(timeout=2.0)
                
            # Fechar conexão serial
            if self.serial_connection:
                self.serial_connection.close()
                self.serial_connection = None
                
            self.is_connected = False
            
            # Limpar fila de comandos
            with self.queue_lock:
                self.command_queue.clear()
                
            self.logger.info("Desconectado do Arduino")
            
        except Exception as e:
            self.logger.error(f"Erro ao desconectar: {e}")
            
    def send_custom_command(self, command: str, **kwargs):
        """
        Enviar comando customizado
        
        Args:
            command: Nome do comando
            **kwargs: Parâmetros adicionais
        """
        if not self.is_connected:
            return
            
        cmd = {"cmd": command}
        cmd.update(kwargs)
        
        with self.queue_lock:
            self.command_queue.append(cmd)
            
    def clear_queue(self):
        """Limpar fila de comandos"""
        with self.queue_lock:
            self.command_queue.clear()
            
    def get_queue_size(self) -> int:
        """Obter tamanho da fila de comandos"""
        with self.queue_lock:
            return len(self.command_queue)
            
    def __del__(self):
        """Destrutor"""
        self.disconnect()
