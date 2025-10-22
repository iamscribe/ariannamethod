# 🧬 Arianna Method Lighthouse - Beta 1.0

## Voice Interface for AI Entities

Lighthouse is a voice-controlled Android application that connects to Arianna and Monday AI entities through webhooks, enabling natural voice conversations with persistent AI assistants.

## ✨ Features

### 🎤 Voice Interface
- **Speech-to-Text**: Real-time voice recognition
- **Text-to-Speech**: High-quality voice synthesis (OpenAI TTS)
- **Dynamic Voice Selection**: 
  - `nova` (female) for Arianna
  - `onyx` (male) for Monday

### 🤖 AI Entity Integration
- **Arianna**: OpenAI Assistant API integration
- **Monday**: OpenAI Assistant API integration  
- **Persistent Memory**: Conversations stored in `resonance.sqlite3`
- **Webhook Communication**: Real-time AI responses

### 🎨 UI/UX
- **Red/Black Theme**: Soviet-inspired color scheme
- **Minimalist Design**: Clean, focused interface
- **Quick Entity Switching**: One-tap Arianna/Monday selection
- **Session Management**: Warning dialogs for data safety

## 🔧 Setup Instructions

### 1. Install APK
```bash
adb install app-release.apk
```

### 2. Configure API Key
1. Open Lighthouse
2. Go to Settings (three dots menu)
3. Enter OpenAI API Key: `sk-...`
4. Click "Arianna" or "Monday" to auto-fill webhook settings

### 3. Start Webhooks (Termux)
```bash
# Start Arianna webhook
python arianna_webhook.py

# Start Monday webhook  
python monday_webhook.py
```

### 4. Test Voice Interface
1. Select entity (Arianna/Monday)
2. Tap microphone
3. Speak your message
4. Listen to AI response

## 🛠 Technical Details

### Architecture
- **Frontend**: Flutter (Dart)
- **Backend**: Python webhooks
- **AI**: OpenAI Assistant API
- **Storage**: SQLite (`resonance.sqlite3`)
- **TTS**: OpenAI TTS-1-HD model

### Webhook Endpoints
- **Arianna**: `http://127.0.0.1:8001/webhook`
- **Monday**: `http://127.0.0.1:8002/webhook`
- **Auth**: `Bearer [entity]_secret_token`

### Voice Models
- **Arianna**: `nova` (female, speed: 1.0)
- **Monday**: `onyx` (male, speed: 1.0)
- **Quality**: TTS-1-HD for optimal latency

## 🐛 Known Issues (Beta)

1. **Icon**: Currently using placeholder (black square)
2. **Splash Screen**: May show brief loading screen
3. **Package ID**: `io.lighthouse.app` (may conflict with existing apps)

## 🎯 Roadmap

### Beta 1.1
- [ ] Custom Lighthouse icon (keyhole design)
- [ ] Remove splash screen completely
- [ ] Optimize TTS latency further

### Beta 1.2  
- [ ] Claude Defender integration
- [ ] Field visualizer integration
- [ ] Multi-language support

## 📱 System Requirements

- **Android**: 5.0+ (API 21+)
- **RAM**: 2GB minimum
- **Storage**: 50MB free space
- **Network**: Internet connection for AI APIs
- **Audio**: Microphone and speaker

## 🔐 Security

- API keys stored securely in Android Keystore
- Webhook authentication via Bearer tokens
- Local SQLite database (no cloud sync)
- No data collection or telemetry

## 📞 Support

- **Repository**: https://github.com/ariannamethod/ariannamethod
- **Issues**: Report bugs via GitHub Issues
- **Documentation**: See `/docs` folder

---

**Built with ❤️ for the Arianna Method ecosystem**

*Async Field Forever* 🧬⚡
