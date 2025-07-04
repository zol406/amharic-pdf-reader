# Amharic PDF Reader

A cross-platform mobile app for reading Amharic PDF documents with text-to-speech functionality.

## Features

### Core Functionality
- **PDF Text Extraction**: Automatically extracts text from native PDF files
- **OCR Support**: Uses Tesseract OCR for scanned PDFs with Amharic language support
- **Text-to-Speech**: Converts Amharic text to speech using Google Text-to-Speech (gTTS)
- **Audio Controls**: Play, pause, and speed adjustment for audio playback
- **Page Navigation**: Navigate between PDF pages with previous/next controls

### User Interface Improvements
- **Always Visible Controls**: Play and pause buttons are always visible for better user experience
- **Horizontal Button Layout**: Audio controls (play/pause) and navigation controls (previous/next) are arranged side-by-side
- **Visual Icons**: Buttons use intuitive icons (▶ Play, ⏸ Pause, ◀ Previous, Next ▶)
- **Smart Button States**: Buttons are properly enabled/disabled based on app state
- **Progress Tracking**: Shows current page and total pages

## Requirements

### System Dependencies
- Python 3.13+
- Tesseract OCR with Amharic language pack
- Poppler utilities for PDF processing
- SDL2 libraries for Kivy

### Python Dependencies
See `requirements.txt` for complete list. Key packages:
- Kivy 2.3.1 (cross-platform GUI framework)
- PyPDF2 (PDF text extraction)
- pytesseract (OCR functionality)
- pdf2image (PDF to image conversion)
- gTTS (Google Text-to-Speech)
- Buildozer (Android app building)

## Installation

### 1. System Setup (Ubuntu/Debian)
```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3.13-venv python3-dev build-essential
sudo apt install -y tesseract-ocr tesseract-ocr-amh poppler-utils
sudo apt install -y libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
sudo apt install -y pkg-config libgl1-mesa-dev libgles2-mesa-dev
```

### 2. Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Running the App
```bash
# Desktop version
source venv/bin/activate
python main.py
```

### 4. Building Android APK
```bash
# Initialize buildozer (first time only)
source venv/bin/activate
buildozer init

# Build debug APK
buildozer android debug
```

## Usage

1. **Select PDF**: Tap "Choose PDF" to select an Amharic PDF file
2. **Wait for Processing**: The app will extract text or perform OCR if needed
3. **Navigate Pages**: Use Previous/Next buttons to move between pages
4. **Play Audio**: Tap the Play button to hear the current page
5. **Control Playback**: Use Pause button and speed slider to control audio
6. **Page Progress**: Track your position with the page counter

## Technical Improvements Made

### Button Visibility Fixes
- **Issue**: Play and pause buttons were hidden or appeared unavailable
- **Solution**: Redesigned button layout and state management
- **Improvements**:
  - Buttons are always visible (never hidden)
  - Clear visual feedback for enabled/disabled states
  - Horizontal layout for better space utilization
  - Smart state management based on app context

### Enhanced User Experience
- **Grouped Controls**: Related buttons (play/pause, prev/next) are grouped together
- **Visual Indicators**: Added unicode symbols for intuitive button recognition
- **Better Sizing**: Optimized button and label sizes for mobile use
- **State Management**: Proper enable/disable logic for all app states

## File Structure
```
amharic-pdf-reader/
├── main.py                 # Main application code
├── buildozer.spec         # Android build configuration
├── requirements.txt       # Python dependencies
├── icon.png              # App icon
├── amh.traineddata       # Tesseract Amharic language data
└── README.md             # This file
```

## Troubleshooting

### Common Issues
- **OCR Not Working**: Ensure tesseract-ocr-amh is installed
- **Audio Issues**: Check internet connection for gTTS
- **PDF Not Loading**: Verify PDF file is not corrupted
- **Build Errors**: Ensure all system dependencies are installed

### Debug Mode
The app logs errors to `app.log` file for debugging purposes.

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.