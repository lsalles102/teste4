#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detector YOLOv5 usando PyTorch
"""

import torch
import torch.nn as nn
import numpy as np
import cv2
import logging
from typing import List, Dict, Optional
from pathlib import Path

class YOLOv5Detector:
    """Detector baseado em YOLOv5 com PyTorch"""
    
    def __init__(self, model_path: str, names_path: str, backend: str = "CPU"):
        """
        Inicializar detector YOLOv5
        
        Args:
            model_path: Caminho para arquivo .pt
            names_path: Caminho para arquivo .names
            backend: Backend para execução (CPU, CUDA)
        """
        self.logger = logging.getLogger(__name__)
        self.model_path = model_path
        self.names_path = names_path
        self.backend = backend
        
        # Configurar dispositivo
        self.device = self._setup_device()
        
        # Parâmetros
        self.input_size = 640
        
        # Carregar modelo e classes
        self.model = None
        self.class_names = []
        
        self._load_model()
        self._load_class_names()
        
    def _setup_device(self):
        """Configurar dispositivo de computação"""
        if self.backend == "CUDA" and torch.cuda.is_available():
            device = torch.device('cuda')
            self.logger.info(f"Usando CUDA: {torch.cuda.get_device_name()}")
        else:
            device = torch.device('cpu')
            self.logger.info("Usando CPU")
            
        return device
        
    def _load_model(self):
        """Carregar modelo PyTorch"""
        try:
            self.logger.info(f"Carregando modelo YOLOv5: {self.model_path}")
            
            # Tentar carregar modelo customizado primeiro
            try:
                self.model = torch.load(self.model_path, map_location=self.device)
                if hasattr(self.model, 'model'):
                    self.model = self.model.model
            except:
                # Fallback para torch.hub
                self.logger.info("Tentando carregar via torch.hub")
                self.model = torch.hub.load('ultralytics/yolov5', 'custom', 
                                          path=self.model_path, device=self.device)
                
            # Configurar modelo para inferência
            self.model.eval()
            if hasattr(self.model, 'conf'):
                self.model.conf = 0.25  # Confiança padrão
            if hasattr(self.model, 'iou'):
                self.model.iou = 0.45   # IoU padrão
                
            self.logger.info("Modelo YOLOv5 carregado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar modelo YOLOv5: {e}")
            # Fallback para modelo pré-treinado
            try:
                self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', 
                                          device=self.device)
                self.logger.info("Usando modelo YOLOv5s pré-treinado")
            except Exception as e2:
                self.logger.error(f"Erro ao carregar modelo fallback: {e2}")
                raise
                
    def _load_class_names(self):
        """Carregar nomes das classes"""
        try:
            with open(self.names_path, 'r') as f:
                self.class_names = [line.strip() for line in f.readlines()]
            self.logger.info(f"Carregadas {len(self.class_names)} classes")
        except Exception as e:
            self.logger.warning(f"Erro ao carregar classes: {e}")
            # Usar classes padrão COCO
            self.class_names = [
                'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
                'train', 'truck', 'boat', 'traffic light', 'fire hydrant',
                'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog',
                'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe',
                'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
                'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat',
                'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
                'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl',
                'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot',
                'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
                'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop',
                'mouse', 'remote', 'keyboard', 'cell phone', 'microwave',
                'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock',
                'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
            ]
            
    def detect(self, frame: np.ndarray, confidence_threshold: float = 0.5) -> List[Dict]:
        """
        Realizar detecção de objetos
        
        Args:
            frame: Imagem de entrada
            confidence_threshold: Limiar de confiança
            
        Returns:
            Lista de detecções com informações dos objetos
        """
        if self.model is None:
            return []
            
        try:
            # Executar inferência
            results = self.model(frame)
            
            # Processar resultados
            detections = self._process_results(results, confidence_threshold)
            
            return detections
            
        except Exception as e:
            self.logger.error(f"Erro na detecção YOLOv5: {e}")
            return []
            
    def _process_results(self, results, confidence_threshold: float) -> List[Dict]:
        """Processar resultados da inferência"""
        detections = []
        
        try:
            # Obter dados das detecções
            if hasattr(results, 'pandas'):
                # Usar interface pandas se disponível
                df = results.pandas().xyxy[0]
                
                for _, row in df.iterrows():
                    if row['confidence'] >= confidence_threshold:
                        x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
                        w, h = x2 - x1, y2 - y1
                        center_x, center_y = x1 + w // 2, y1 + h // 2
                        
                        detection = {
                            'class_id': int(row['class']),
                            'class_name': row['name'],
                            'confidence': row['confidence'],
                            'bbox': [x1, y1, w, h],
                            'center': (center_x, center_y),
                            'area': w * h
                        }
                        detections.append(detection)
            else:
                # Processar tensor diretamente
                pred = results.pred[0] if hasattr(results, 'pred') else results
                
                for det in pred:
                    if det[4] >= confidence_threshold:
                        x1, y1, x2, y2, conf, cls = det[:6]
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        w, h = x2 - x1, y2 - y1
                        center_x, center_y = x1 + w // 2, y1 + h // 2
                        
                        class_id = int(cls)
                        class_name = self.class_names[class_id] if class_id < len(self.class_names) else 'unknown'
                        
                        detection = {
                            'class_id': class_id,
                            'class_name': class_name,
                            'confidence': float(conf),
                            'bbox': [x1, y1, w, h],
                            'center': (center_x, center_y),
                            'area': w * h
                        }
                        detections.append(detection)
                        
        except Exception as e:
            self.logger.error(f"Erro ao processar resultados: {e}")
            
        return detections
        
    def draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Desenhar detecções na imagem"""
        result_frame = frame.copy()
        
        for detection in detections:
            x, y, w, h = detection['bbox']
            confidence = detection['confidence']
            class_name = detection['class_name']
            
            # Cores baseadas na classe
            color = self._get_class_color(detection['class_id'])
            
            # Desenhar caixa delimitadora
            cv2.rectangle(result_frame, (x, y), (x + w, y + h), color, 2)
            
            # Desenhar label
            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(result_frame, (x, y - label_size[1] - 10), 
                         (x + label_size[0], y), color, -1)
            cv2.putText(result_frame, label, (x, y - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # Desenhar ponto central
            center_x, center_y = detection['center']
            cv2.circle(result_frame, (center_x, center_y), 5, (0, 0, 255), -1)
        
        return result_frame
        
    def _get_class_color(self, class_id: int) -> tuple:
        """Obter cor para uma classe específica"""
        # Gerar cor baseada no ID da classe
        np.random.seed(class_id)
        color = tuple(map(int, np.random.randint(0, 255, 3)))
        return color
        
    def get_model_info(self) -> Dict:
        """Obter informações do modelo"""
        return {
            'type': 'YOLOv5',
            'backend': self.backend,
            'device': str(self.device),
            'input_size': self.input_size,
            'num_classes': len(self.class_names),
            'class_names': self.class_names
        }
