# 🎙️ Whisper Transcription GUI

A modern, user-friendly desktop app that turns speech into text using OpenAI's Whisper model. No API keys needed - everything runs right on your computer!

![Whisper GUI Screenshot]!(
![WhisperGUI](https://github.com/user-attachments/assets/0417621f-e58c-4956-a2c0-46de8ba9f1f1)


## Features

- 🎨 Clean, modern interface built with CustomTkinter
- 🤖 Support for all Whisper model sizes (tiny, base, small, medium, large, turbo)
- 📁 One-click audio file upload with drag & drop support
- 🎵 Support for multiple audio formats (.mp3, .wav, .m4a, .ogg, .flac)
- 📊 Real-time progress bar with detailed status updates
- ✨ Responsive UI with visual feedback and animations
- 📝 Copy-paste friendly transcript display
- 🎯 Smart model selection with instant feedback
- 🚦 Clear progress tracking from 0% to 100%

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or newer ([Download Python](https://www.python.org/downloads/))
- FFmpeg ([Installation Guide](#installing-ffmpeg))

### Installation Steps
1. Download this app:
   ```bash
   git clone https://github.com/yourusername/whisper-gui.git
   cd whisper-gui
   ```
   Or just download and unzip the code from GitHub

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
   This will install everything you need: Whisper, CustomTkinter, and PyTorch.

### Installing FFmpeg
- **Windows**: 
  1. Download from [FFmpeg website](https://ffmpeg.org/download.html)
  2. Add to your system PATH ([Tutorial](https://www.wikihow.com/Install-FFmpeg-on-Windows))

- **macOS**: 
  ```bash
  brew install ffmpeg
  ```
  Don't have Homebrew? Install it from [brew.sh](https://brew.sh)

- **Linux**: 
  ```bash
  # Ubuntu/Debian:
  sudo apt update && sudo apt install ffmpeg
  
  # Fedora:
  sudo dnf install ffmpeg
  ```

## 🎯 How to Use

1. Start the app:
   ```bash
   python whisper_gui.py
   ```

2. Choose your model:
   | Model | Speed | Accuracy | Memory Needed | Best For |
   |-------|--------|-----------|---------------|----------|
   | Tiny | ⚡️⚡️⚡️ | ⭐️ | ~1 GB | Quick tests, simple audio |
   | Base | ⚡️⚡️ | ⭐️⭐️ | ~1 GB | Short clips, clear speech |
   | Small | ⚡️⚡️ | ⭐️⭐️⭐️ | ~2 GB | General purpose |
   | Medium | ⚡️ | ⭐️⚐️⭐️⭐️ | ~5 GB | Professional use |
   | Large | 🐢 | ⭐️⭐️⭐️⭐️⭐️ | ~10 GB | Highest accuracy needed |
   | Turbo | ⚡️⚡️ | ⭐️⭐️⭐️⭐️ | ~4 GB | Fast & accurate balance |

3. Add your audio:
   - Simply click anywhere in the upload area
   - Or drag & drop your file
   - Watch for the green highlight confirmation
   - Supports: MP3, WAV, M4A, OGG, FLAC
   - Tip: Files under 25MB work best

4. Track the transcription:
   - Progress bar shows real-time status
   - Percentage updates at key stages:
     - 10%: Checking setup
     - 30%: Loading model
     - 50%: Processing audio
     - 70%: Analyzing speech
     - 90%: Generating transcript
     - 100%: Complete!

5. View your transcript:
   - Clean, formatted text output
   - Easy to copy and paste
   - Clear visual indication when complete

### 💡 Pro Tips
- Start with the 'base' model for quick tests
- Use 'small' for everyday transcriptions
- For important or tricky audio, try 'medium' or 'large'
- 'turbo' offers a great balance of speed and accuracy
- Having issues? Hover over model names for detailed info
- Watch the progress bar for real-time transcription status
- The UI provides instant feedback - no need to click multiple times!
- Look for visual cues: buttons highlight on hover and selection

## 💻 System Requirements

- **OS**: Windows 10/11, macOS, or Linux
- **Python**: Version 3.7 or newer
- **RAM**: 
  - Minimum: 8GB
  - Recommended: 16GB for larger models
- **Storage**: 
  - ~1GB for the app
  - 1-10GB per model (downloaded as needed)
- **GPU**: Optional but recommended for faster processing
  - NVIDIA GPU with CUDA support works best
  - Will use CPU if no GPU available

## 🤝 Contributing

Found a bug or want to add a feature? Contributions are welcome!
1. Fork the repo
2. Create your feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is open source under the MIT License - do whatever you want with it! 😊

## 🙏 Acknowledgements

- [OpenAI Whisper](https://github.com/openai/whisper) - The amazing speech recognition model
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Beautiful modern UI components

## ❓ Need Help?

Having issues?
1. Check the [common issues](#common-issues) section
2. Open an issue on GitHub
3. Try the discussion forum

### Common Issues

1. **FFmpeg not found**: Follow the [FFmpeg installation guide](#installing-ffmpeg)
2. **Out of memory**: Try a smaller model size
3. **CUDA errors**: Update your GPU drivers or use CPU mode
4. **Model selection not working**: Just click once - the UI provides instant feedback
5. **Progress bar not visible**: Look for the grey bar below the model selection
6. **Upload not working**: Click anywhere in the upload area, watch for green highlight

### Recent Updates

#### Version 2.0
- ✨ Added real-time progress bar with percentage tracking
- 🎯 Improved model selection with instant feedback
- 🖱️ Enhanced click responsiveness across all buttons
- 💫 Added visual animations and feedback
- 📊 Clear progress stages from 0% to 100%
- 🎨 Refined UI elements for better user experience

### Tips for Best Results

1. **Model Selection**:
   - Models now respond instantly to clicks
   - Watch for the green highlight and bold text
   - Hover for detailed model information

2. **File Upload**:
   - Click anywhere in the upload area
   - Look for the green highlight confirmation
   - File name will appear with a success animation

3. **Transcription Progress**:
   - Watch the grey progress bar fill up
   - Check percentage and stage updates
   - Clear visual feedback at completion
