#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detector YOLOv5 usando ONNX Runtime
"""

import onnxruntime as ort
import numpy as np
import cv2
import logging
from typing import List, Dict, Optional

class YOLOv5ONNXDetector:
    """Detector baseado em YOLOv5 com ONNX Runtime"""
    
    def __init__(self, model_path: str, names_path: str, backend: str = "CPU"):
        """
        Inicializar detector YOLOv5 ONNX
        
        Args:
            model_path: Caminho para arquivo .onnx
            names_path: Caminho para arquivo .names
            backend: Backend para execução (CPU, CUDA, DirectML)
        """
        self.logger = logging.getLogger(__name__)
        self.model_path = model_path
        self.names_path = names_path
        self.backend = backend
        
        # Parâmetros
        self.input_size = (640, 640)
        self.input_name = None
        self.output_names = None
        
        # Carregar modelo e classes
        self.session = None
        self.class_names = []
        
        self._setup_session()
        self._load_class_names()
        
    def _setup_session(self):
        """Configurar sessão ONNX Runtime"""
        try:
            self.logger.info(f"Carregando modelo ONNX: {self.model_path}")
            
            # Configurar provedores baseado no backend
            providers = self._get_providers()
            
            # Criar sessão
            self.session = ort.InferenceSession(self.model_path, providers=providers)
            
            # Obter informações de entrada e saída
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [output.name for output in self.session.get_outputs()]
            
            # Verificar dimensões de entrada
            input_shape = self.session.get_inputs()[0].shape
            if len(input_shape) == 4:
                self.input_size = (input_shape[2], input_shape[3])
                
            self.logger.info(f"Modelo ONNX carregado. Input: {self.input_name}, "
                           f"Outputs: {self.output_names}, Size: {self.input_size}")
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar modelo ONNX: {e}")
            raise
            
    def _get_providers(self):
        """Obter provedores ONNX baseado no backend"""
        providers = []
        
        if self.backend == "CUDA":
            try:
                # Verificar se CUDA está disponível
                if 'CUDAExecutionProvider' in ort.get_available_providers():
                    providers.append('CUDAExecutionProvider')
                    self.logger.info("Usando CUDA para ONNX")
            except:
                pass
                
        elif self.backend == "DirectML":
            try:
                # Verificar se DirectML está disponível
                if 'DmlExecutionProvider' in ort.get_available_providers():
                    providers.append('DmlExecutionProvider')
                    self.logger.info("Usando DirectML para ONNX")
            except:
                pass
        
        # CPU como fallback
        providers.append('CPUExecutionProvider')
        self.logger.info(f"Provedores ONNX: {providers}")
        
        return providers
        
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
                'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe'
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
        if self.session is None:
            return []
            
        try:
            # Pré-processar imagem
            input_tensor = self._preprocess(frame)
            
            # Executar inferência
            outputs = self.session.run(self.output_names, {self.input_name: input_tensor})
            
            # Pós-processar resultados
            detections = self._postprocess(outputs[0], frame.shape, confidence_threshold)
            
            return detections
            
        except Exception as e:
            self.logger.error(f"Erro na detecção ONNX: {e}")
            return []
            
    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Pré-processar imagem para entrada do modelo"""
        # Redimensionar mantendo aspect ratio
        height, width = frame.shape[:2]
        scale = min(self.input_size[0] / width, self.input_size[1] / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        # Redimensionar
        resized = cv2.resize(frame, (new_width, new_height))
        
        # Criar imagem com padding
        input_image = np.ones((self.input_size[1], self.input_size[0], 3), dtype=np.uint8) * 114
        
        # Calcular posição para centrar
        y_offset = (self.input_size[1] - new_height) // 2
        x_offset = (self.input_size[0] - new_width) // 2
        
        # Colocar imagem redimensionada no centro
        input_image[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized
        
        # Converter para formato do modelo (NCHW)
        input_tensor = input_image.transpose(2, 0, 1).astype(np.float32)
        input_tensor = input_tensor / 255.0  # Normalizar
        input_tensor = np.expand_dims(input_tensor, axis=0)
        
        return input_tensor
        
    def _postprocess(self, outputs: np.ndarray, original_shape: tuple, 
                    confidence_threshold: float) -> List[Dict]:
        """Pós-processar saídas do modelo"""
        detections = []
        
        try:
            # Calcular escala para mapear de volta para imagem original
            orig_height, orig_width = original_shape[:2]
            scale = min(self.input_size[0] / orig_width, self.input_size[1] / orig_height)
            
            # Processar cada detecção
            for detection in outputs:
                # YOLOv5 formato: [x_center, y_center, width, height, confidence, class_scores...]
                if len(detection) < 5:
                    continue
                    
                x_center, y_center, width, height, obj_conf = detection[:5]
                class_scores = detection[5:]
                
                # Encontrar classe com maior pontuação
                class_id = np.argmax(class_scores)
                class_conf = class_scores[class_id]
                
                # Calcular confiança final
                confidence = obj_conf * class_conf
                
                if confidence >= confidence_threshold:
                    # Converter coordenadas para imagem original
                    x_center = (x_center - (self.input_size[0] - orig_width * scale) / 2) / scale
                    y_center = (y_center - (self.input_size[1] - orig_height * scale) / 2) / scale
                    width = width / scale
                    height = height / scale
                    
                    # Calcular caixa delimitadora
                    x1 = int(x_center - width / 2)
                    y1 = int(y_center - height / 2)
                    w = int(width)
                    h = int(height)
                    
                    # Garantir que coordenadas estão dentro da imagem
                    x1 = max(0, min(x1, orig_width - 1))
                    y1 = max(0, min(y1, orig_height - 1))
                    w = max(1, min(w, orig_width - x1))
                    h = max(1, min(h, orig_height - y1))
                    
                    class_name = self.class_names[class_id] if class_id < len(self.class_names) else 'unknown'
                    
                    detection_info = {
                        'class_id': class_id,
                        'class_name': class_name,
                        'confidence': float(confidence),
                        'bbox': [x1, y1, w, h],
                        'center': (x1 + w // 2, y1 + h // 2),
                        'area': w * h
                    }
                    
                    detections.append(detection_info)
                    
        except Exception as e:
            self.logger.error(f"Erro no pós-processamento: {e}")
            
        return detections
        
    def draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Desenhar detecções na imagem"""
        result_frame = frame.copy()
        
        for detection in detections:
            x, y, w, h = detection['bbox']
            confidence = detection['confidence']
            class_name = detection['class_name']
            
            # Cor baseada na classe
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
            'type': 'YOLOv5 ONNX',
            'backend': self.backend,
            'input_size': self.input_size,
            'num_classes': len(self.class_names),
            'class_names': self.class_names,
            'providers': self.session.get_providers() if self.session else []
        }
