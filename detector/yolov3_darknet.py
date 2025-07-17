#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detector YOLOv3/v4 usando OpenCV DNN
"""

import cv2
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple

class YOLOv3Detector:
    """Detector baseado em YOLOv3/v4 com OpenCV DNN"""
    
    def __init__(self, weights_path: str, config_path: str, names_path: str, backend: str = "CPU"):
        """
        Inicializar detector YOLOv3
        
        Args:
            weights_path: Caminho para arquivo .weights
            config_path: Caminho para arquivo .cfg
            names_path: Caminho para arquivo .names
            backend: Backend para execução (CPU, CUDA, OpenCV)
        """
        self.logger = logging.getLogger(__name__)
        self.weights_path = weights_path
        self.config_path = config_path
        self.names_path = names_path
        self.backend = backend
        
        # Parâmetros de detecção
        self.input_size = (608, 608)
        self.scale_factor = 1/255.0
        self.mean = (0, 0, 0)
        self.swap_rb = True
        
        # Carregar modelo
        self.net = None
        self.class_names = []
        self.output_layers = []
        
        self._load_model()
        self._load_class_names()
        
    def _load_model(self):
        """Carregar modelo DNN"""
        try:
            self.logger.info(f"Carregando modelo YOLOv3: {self.weights_path}")
            
            # Carregar rede
            self.net = cv2.dnn.readNetFromDarknet(self.config_path, self.weights_path)
            
            # Configurar backend
            if self.backend == "CUDA":
                self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
                self.logger.info("Usando backend CUDA")
            elif self.backend == "OpenCV":
                self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            else:
                # CPU padrão
                self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
                self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
                
            # Obter nomes das camadas de saída
            layer_names = self.net.getLayerNames()
            self.output_layers = [layer_names[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]
            
            self.logger.info("Modelo YOLOv3 carregado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar modelo YOLOv3: {e}")
            raise
            
    def _load_class_names(self):
        """Carregar nomes das classes"""
        try:
            with open(self.names_path, 'r') as f:
                self.class_names = [line.strip() for line in f.readlines()]
            self.logger.info(f"Carregadas {len(self.class_names)} classes")
        except Exception as e:
            self.logger.error(f"Erro ao carregar classes: {e}")
            # Classes padrão COCO se falhar
            self.class_names = ['person', 'bicycle', 'car', 'motorcycle']
            
    def detect(self, frame: np.ndarray, confidence_threshold: float = 0.5, 
               nms_threshold: float = 0.4) -> List[Dict]:
        """
        Realizar detecção de objetos
        
        Args:
            frame: Imagem de entrada
            confidence_threshold: Limiar de confiança
            nms_threshold: Limiar para Non-Maximum Suppression
            
        Returns:
            Lista de detecções com informações dos objetos
        """
        if self.net is None:
            return []
            
        try:
            height, width = frame.shape[:2]
            
            # Preparar entrada
            blob = cv2.dnn.blobFromImage(
                frame, self.scale_factor, self.input_size, 
                self.mean, self.swap_rb, crop=False)
            
            # Executar inferência
            self.net.setInput(blob)
            outputs = self.net.forward(self.output_layers)
            
            # Processar saídas
            detections = self._process_outputs(outputs, width, height, 
                                               confidence_threshold, nms_threshold)
            
            return detections
            
        except Exception as e:
            self.logger.error(f"Erro na detecção YOLOv3: {e}")
            return []
            
    def _process_outputs(self, outputs: List[np.ndarray], width: int, height: int,
                        confidence_threshold: float, nms_threshold: float) -> List[Dict]:
        """Processar saídas da rede"""
        boxes = []
        confidences = []
        class_ids = []
        
        # Processar cada saída
        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > confidence_threshold:
                    # Coordenadas do objeto
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    
                    # Coordenadas da caixa delimitadora
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        
        # Aplicar Non-Maximum Suppression
        indices = cv2.dnn.NMSBoxes(boxes, confidences, confidence_threshold, nms_threshold)
        
        detections = []
        if len(indices) > 0:
            for i in indices.flatten():
                x, y, w, h = boxes[i]
                class_id = class_ids[i]
                confidence = confidences[i]
                
                # Calcular centro
                center_x = x + w // 2
                center_y = y + h // 2
                
                detection = {
                    'class_id': class_id,
                    'class_name': self.class_names[class_id] if class_id < len(self.class_names) else 'unknown',
                    'confidence': confidence,
                    'bbox': [x, y, w, h],
                    'center': (center_x, center_y),
                    'area': w * h
                }
                
                detections.append(detection)
        
        return detections
        
    def draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Desenhar detecções na imagem"""
        result_frame = frame.copy()
        
        for detection in detections:
            x, y, w, h = detection['bbox']
            confidence = detection['confidence']
            class_name = detection['class_name']
            
            # Desenhar caixa delimitadora
            cv2.rectangle(result_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Desenhar label
            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(result_frame, (x, y - label_size[1] - 10), 
                         (x + label_size[0], y), (0, 255, 0), -1)
            cv2.putText(result_frame, label, (x, y - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            # Desenhar ponto central
            center_x, center_y = detection['center']
            cv2.circle(result_frame, (center_x, center_y), 5, (0, 0, 255), -1)
        
        return result_frame
        
    def get_model_info(self) -> Dict:
        """Obter informações do modelo"""
        return {
            'type': 'YOLOv3/v4',
            'backend': self.backend,
            'input_size': self.input_size,
            'num_classes': len(self.class_names),
            'class_names': self.class_names
        }
