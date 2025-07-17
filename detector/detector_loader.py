#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Carregador automático de detectores baseado no tipo de modelo
"""

import os
import logging
from pathlib import Path
from typing import Optional

from .yolov3_darknet import YOLOv3Detector
from .yolov5_pytorch import YOLOv5Detector
from .yolov5_onnx import YOLOv5ONNXDetector

class DetectorLoader:
    """Carregador automático de detectores"""
    
    @staticmethod
    def detect_model_type(model_path: str) -> str:
        """
        Detectar tipo do modelo baseado na extensão
        
        Args:
            model_path: Caminho para o arquivo do modelo
            
        Returns:
            Tipo do modelo detectado
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Arquivo de modelo não encontrado: {model_path}")
            
        extension = Path(model_path).suffix.lower()
        
        if extension == '.weights':
            return 'darknet'
        elif extension == '.pt':
            return 'pytorch'
        elif extension == '.onnx':
            return 'onnx'
        else:
            raise ValueError(f"Tipo de modelo não suportado: {extension}")
            
    @staticmethod
    def find_config_file(model_path: str) -> Optional[str]:
        """
        Encontrar arquivo de configuração .cfg para modelos Darknet
        
        Args:
            model_path: Caminho para arquivo .weights
            
        Returns:
            Caminho para arquivo .cfg ou None se não encontrado
        """
        model_dir = Path(model_path).parent
        model_name = Path(model_path).stem
        
        # Procurar arquivo .cfg com nome similar
        possible_configs = [
            model_dir / f"{model_name}.cfg",
            model_dir / "yolov3.cfg",
            model_dir / "yolov4.cfg",
            model_dir / "config.cfg"
        ]
        
        for config_path in possible_configs:
            if config_path.exists():
                return str(config_path)
                
        # Procurar qualquer arquivo .cfg no diretório
        for config_file in model_dir.glob("*.cfg"):
            return str(config_file)
            
        return None
        
    @staticmethod
    def load_detector(model_path: str, names_path: str, backend: str = "CPU"):
        """
        Carregar detector automaticamente baseado no tipo do modelo
        
        Args:
            model_path: Caminho para arquivo do modelo
            names_path: Caminho para arquivo de nomes das classes
            backend: Backend para execução
            
        Returns:
            Instância do detector apropriado
        """
        logger = logging.getLogger(__name__)
        
        try:
            # Detectar tipo do modelo
            model_type = DetectorLoader.detect_model_type(model_path)
            logger.info(f"Tipo de modelo detectado: {model_type}")
            
            # Carregar detector apropriado
            if model_type == 'darknet':
                # Encontrar arquivo de configuração
                config_path = DetectorLoader.find_config_file(model_path)
                if not config_path:
                    raise FileNotFoundError("Arquivo .cfg não encontrado para modelo Darknet")
                
                logger.info(f"Usando configuração: {config_path}")
                return YOLOv3Detector(model_path, config_path, names_path, backend)
                
            elif model_type == 'pytorch':
                return YOLOv5Detector(model_path, names_path, backend)
                
            elif model_type == 'onnx':
                return YOLOv5ONNXDetector(model_path, names_path, backend)
                
            else:
                raise ValueError(f"Tipo de modelo não suportado: {model_type}")
                
        except Exception as e:
            logger.error(f"Erro ao carregar detector: {e}")
            raise
            
    @staticmethod
    def validate_model_files(model_path: str, names_path: str) -> dict:
        """
        Validar arquivos do modelo
        
        Args:
            model_path: Caminho para arquivo do modelo
            names_path: Caminho para arquivo de nomes
            
        Returns:
            Dicionário com status da validação
        """
        validation = {
            'model_exists': os.path.exists(model_path),
            'names_exists': os.path.exists(names_path),
            'model_type': None,
            'config_path': None,
            'errors': []
        }
        
        try:
            if validation['model_exists']:
                validation['model_type'] = DetectorLoader.detect_model_type(model_path)
                
                # Para modelos Darknet, verificar arquivo de configuração
                if validation['model_type'] == 'darknet':
                    config_path = DetectorLoader.find_config_file(model_path)
                    validation['config_path'] = config_path
                    if not config_path:
                        validation['errors'].append("Arquivo .cfg não encontrado")
                        
            else:
                validation['errors'].append("Arquivo de modelo não encontrado")
                
            if not validation['names_exists']:
                validation['errors'].append("Arquivo de nomes não encontrado")
                
        except Exception as e:
            validation['errors'].append(str(e))
            
        validation['is_valid'] = len(validation['errors']) == 0
        
        return validation
        
    @staticmethod
    def get_supported_extensions() -> list:
        """Obter lista de extensões suportadas"""
        return ['.weights', '.pt', '.onnx']
        
    @staticmethod
    def get_backend_options() -> list:
        """Obter opções de backend disponíveis"""
        backends = ['CPU']
        
        # Verificar CUDA
        try:
            import torch
            if torch.cuda.is_available():
                backends.append('CUDA')
        except ImportError:
            pass
            
        # Verificar DirectML
        try:
            import onnxruntime as ort
            if 'DmlExecutionProvider' in ort.get_available_providers():
                backends.append('DirectML')
        except ImportError:
            pass
            
        return backends
