# ObjectDetectionAssistant

## Overview

ObjectDetectionAssistant is a modular real-time object detection system designed for automated mouse movement and screen capture. The application supports multiple model formats (Darknet .weights, PyTorch .pt, ONNX .onnx), various screen capture methods (MSS, DirectX), and different mouse control mechanisms (Arduino HID, Windows DLL, Software simulation).

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **GUI Framework**: PyQt5-based desktop application
- **Threading Model**: Separate detection thread for real-time processing to prevent UI blocking
- **Interface Design**: Tabbed interface with grouped controls for different system components
- **Real-time Updates**: Signal-slot mechanism for thread-safe GUI updates

### Backend Architecture
- **Modular Design**: Separate modules for detection, capture, mouse control, and utilities
- **Plugin-like Structure**: Automatic detector loading based on model file extension
- **Factory Pattern**: DetectorLoader automatically selects appropriate detector implementation
- **Configuration Management**: JSON-based configuration with automatic loading/saving

### Detection Engine
- **Multi-format Support**: 
  - YOLOv3/v4 via OpenCV DNN (.weights + .cfg)
  - YOLOv5 via PyTorch (.pt)
  - ONNX models via ONNX Runtime (.onnx)
- **Backend Flexibility**: CPU, CUDA, DirectML support depending on model type
- **Automatic Type Detection**: File extension-based model type identification

## Key Components

### Detection System (`detector/`)
- **DetectorLoader**: Factory class for automatic model type detection and loading
- **YOLOv3Detector**: OpenCV DNN implementation for Darknet models
- **YOLOv5Detector**: PyTorch implementation for .pt models
- **YOLOv5ONNXDetector**: ONNX Runtime implementation for .onnx models

### Screen Capture (`capture/`)
- **ScreenCaptureMSS**: Standard screen capture using MSS library
- **ScreenCaptureDX**: High-performance DirectX Screen Duplication API for gaming applications
- **Fallback Mechanism**: Automatic fallback from DirectX to MSS if DirectX fails

### Mouse Control (`mouse_control/`)
- **ArduinoController**: Hardware-based mouse control via Arduino HID device
- **DLLMouseController**: Windows native API mouse control using SendInput/mouse_event
- **SoftwareMouseController**: Simulation mode for testing without actual mouse movement

### Utilities (`utils/`)
- **MovementSmoother**: Advanced movement smoothing with jitter reduction and velocity limiting
- **Configuration Management**: JSON-based settings with validation

## Data Flow

1. **Initialization**: Load configuration, initialize selected detector, capture method, and mouse controller
2. **Capture Loop**: Continuous screen capture using selected method (MSS/DirectX)
3. **Detection**: Process captured frames through loaded ML model
4. **Filtering**: Apply confidence threshold and target class filtering
5. **Smoothing**: Apply movement smoothing algorithms to reduce jitter
6. **Output**: Send movement commands to selected mouse controller
7. **Feedback**: Update GUI with detection results and performance metrics

## External Dependencies

### Core Libraries
- **PyQt5**: GUI framework for desktop interface
- **OpenCV**: Computer vision operations and DNN inference
- **NumPy**: Numerical computations and array operations
- **MSS**: Cross-platform screen capture

### AI/ML Dependencies
- **PyTorch**: Deep learning framework for .pt models
- **ONNX Runtime**: Optimized inference for ONNX models
- **torchvision**: PyTorch vision utilities

### Hardware Interface
- **pyserial**: Arduino communication via serial port
- **ctypes**: Windows API access for low-level mouse control

### Optional Dependencies
- **DirectX SDK**: For high-performance screen capture in gaming scenarios

## Deployment Strategy

### Development Setup
- **Python Environment**: Python 3.7+ with virtual environment
- **Package Management**: pip-based dependency installation
- **Configuration**: JSON files for persistent settings

### Directory Structure
```
ObjectDetectionAssistant/
├── main.py                 # Application entry point
├── config/                 # Configuration files
├── detector/               # ML model implementations
├── capture/                # Screen capture modules
├── mouse_control/          # Mouse control implementations
├── gui/                    # GUI components
├── utils/                  # Utility functions
├── models/                 # ML model files storage
├── logs/                   # Application logs
└── screenshots/            # Debug screenshots
```

### Hardware Requirements
- **Minimum**: CPU with 4GB RAM for basic operation
- **Recommended**: NVIDIA GPU with CUDA support for accelerated inference
- **Optional**: Arduino-compatible microcontroller for hardware mouse control

### Platform Support
- **Primary**: Windows 10/11 (DirectX capture, Windows APIs)
- **Secondary**: Cross-platform potential via MSS and software mouse control
- **Hardware**: Arduino or compatible HID devices for hardware mouse control

The architecture prioritizes modularity and flexibility, allowing users to mix and match different components based on their specific use case and hardware capabilities.