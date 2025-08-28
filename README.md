# MIDIGPT - Neural Music Generation Platform

A sophisticated AI-powered MIDI generation application that combines **React.js**, **Flask**, **Spotify API**, and **OpenAI GPT-4** to create intelligent music compositions based on emotional descriptions and reference tracks.

![MIDIGPT Screenshot](https://via.placeholder.com/800x400/0a0a0f/00bfff?text=MIDIGPT+Neural+Music+Generation)

## 🎵 Features

- **🧠 AI-Powered Composition**: Uses OpenAI GPT-4 for intelligent melody generation
- **🎧 Spotify Integration**: Deep audio analysis extracting tempo, key, energy, and mood characteristics
- **🎹 Professional MIDI Output**: High-quality MIDI files with proper velocities and timing
- **🎨 Futuristic UI**: Modern glassmorphism design with dark theme and neon accents
- **📊 Detailed Analysis**: Comprehensive breakdown of musical parameters and Spotify insights
- **💾 Download & History**: Save generated MIDI files and track generation history
- **📱 Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices

## 🚀 Technology Stack

### Backend
- **Flask** - Python web framework
- **OpenAI GPT-4** - AI music composition
- **Spotify Web API** - Audio feature extraction and analysis
- **music21** - MIDI file creation and music theory processing
- **spotipy** - Python Spotify API wrapper

### Frontend  
- **React 18** - Modern UI framework
- **Vite** - Fast build tool and development server
- **Lucide React** - Beautiful icon library
- **CSS3** - Advanced styling with glassmorphism effects

## 📋 Prerequisites

- **Node.js** 16+ and npm
- **Python** 3.8+
- **Spotify Developer Account** ([Sign up here](https://developer.spotify.com/))
- **OpenAI API Account** ([Get API key here](https://platform.openai.com/api-keys))

## ⚡ Quick Start

### 1. Clone and Setup

```bash
# Navigate to your projects folder
cd /path/to/your/projects

# Clone the repository (if from git)
# git clone <repository-url>
# cd midigpt

# Or if you have the files locally:
cd midigpt
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r ../requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env file with your API keys (see configuration section below)
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install Node.js dependencies
npm install
```

### 4. Configuration

Edit `backend/.env` with your API credentials:

```env
# Spotify API Configuration
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here

# OpenAI API Configuration  
OPENAI_API_KEY=your_openai_api_key_here

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

### 5. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
python app.py
# Server runs on http://localhost:5000
```

**Terminal 2 - Frontend:**
```bash
cd frontend  
npm run dev
# Application runs on http://localhost:3000
```

Visit **http://localhost:3000** to use MIDIGPT!

## 🔧 API Configuration Guide

### Spotify API Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Click "Create App"
3. Fill in app details:
   - **App Name**: MIDIGPT
   - **App Description**: AI-powered MIDI generation platform
   - **Website**: http://localhost:3000 (for development)
   - **Redirect URI**: Not needed for this application
4. Copy **Client ID** and **Client Secret** to your `.env` file

### OpenAI API Setup

1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign up/login to your account
3. Go to [API Keys](https://platform.openai.com/api-keys)
4. Click "Create new secret key"
5. Copy the key to your `.env` file
6. **Important**: Add billing information to your OpenAI account for API access

## 🎯 How to Use

### Basic Usage

1. **Describe Your Mood**: Enter an emotional description (e.g., "upbeat and energetic", "melancholic and dreamy")

2. **Choose Reference Track** (Optional): 
   - Search for a song using the Spotify integration
   - The app will analyze its musical characteristics
   - Auto-detection of BPM, key, and musical features

3. **Configure Parameters**:
   - **Duration**: 4-32 bars
   - **Complexity**: Simple, Medium, or Complex
   - **Advanced Settings**: Manual BPM, key, mode overrides

4. **Generate**: Click "Generate Music" and watch AI create your MIDI

5. **Download**: Save the generated MIDI file to use in your DAW

### Advanced Features

- **Spotify Analysis**: View detailed audio features from your reference track
- **Generation History**: Access your recent creations
- **Musical Insights**: Understand the AI's compositional decisions
- **Real-time Preview**: Basic playback controls (Note: Full MIDI playback requires a DAW)

## 📁 Project Structure

```
midigpt/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── spotify_utils.py       # Spotify API integration
│   ├── midi_generator.py      # MIDI generation with GPT-4
│   ├── static/generated/      # Generated MIDI files
│   ├── .env.example          # Environment template
│   └── .env                  # Your API keys (create this)
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── InputForm.jsx      # Music generation form
│   │   │   ├── InputForm.css      # Form styling
│   │   │   ├── PreviewPlayer.jsx  # MIDI player & analysis
│   │   │   └── PreviewPlayer.css  # Player styling
│   │   ├── App.jsx            # Main React component
│   │   ├── App.css            # Main application styling
│   │   └── main.jsx           # React entry point
│   ├── index.html             # HTML template
│   └── public/                # Static assets
├── requirements.txt           # Python dependencies
├── package.json              # Node.js dependencies
├── vite.config.js            # Vite configuration
└── README.md                 # This file
```

## 🎼 Musical Features

### Spotify Integration
- **Audio Feature Analysis**: Energy, danceability, valence, acousticness
- **Structural Analysis**: Sections, bars, beats, and rhythmic patterns  
- **Harmonic Analysis**: Key detection, mode analysis, chord progressions
- **Genre Classification**: Automatic style detection and influences

### AI Composition
- **Context-Aware Generation**: GPT-4 understands musical theory and context
- **Spotify-Informed Prompts**: Uses extracted features to guide composition
- **Dynamic Expression**: Proper MIDI velocities and timing variations
- **Musical Coherence**: Ensures generated melodies follow music theory principles

### MIDI Output
- **Professional Quality**: Studio-ready MIDI files
- **Proper Timing**: Accurate note durations and positioning
- **Dynamic Expression**: Velocity variations for musical expression
- **DAW Compatible**: Works with all major digital audio workstations

## 🛠️ Development

### Running in Development Mode

```bash
# Backend (with auto-reload)
cd backend
python app.py

# Frontend (with hot reload)
cd frontend
npm run dev
```

### Building for Production

```bash
# Build frontend
cd frontend
npm run build

# The built files will be in frontend/dist/
```

### Common Development Tasks

**Add new dependencies:**
```bash
# Python
pip install package_name
pip freeze > requirements.txt

# Node.js  
npm install package_name
```

**Database/File Management:**
- Generated MIDI files are stored in `backend/static/generated/`
- Generation history is stored in browser localStorage
- No external database required

## 🐛 Troubleshooting

### Common Issues

**"Module not found" errors:**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

**Spotify API errors:**
- Check your Client ID and Client Secret
- Ensure there are no extra spaces in `.env` file
- Verify your Spotify Developer account is active

**OpenAI API errors:**
- Verify API key is correct
- Check your OpenAI account has billing set up
- Ensure you have sufficient API credits

**MIDI playback issues:**
- MIDI files require a DAW or MIDI player for full playback
- The built-in player is for basic demonstration
- Download the file to play in your preferred music software

**Frontend build errors:**
- Ensure Node.js 16+ is installed
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Check for any missing dependencies

### Getting Help

1. Check the browser developer console for errors
2. Check the Flask backend console for API errors
3. Verify all API keys are correctly configured
4. Ensure all dependencies are installed

## 🚀 Deployment

### Environment Variables for Production

```env
FLASK_ENV=production
FLASK_DEBUG=False
SPOTIFY_CLIENT_ID=your_production_spotify_id
SPOTIFY_CLIENT_SECRET=your_production_spotify_secret
OPENAI_API_KEY=your_production_openai_key
```

### Security Considerations

- Never commit `.env` files to version control
- Use environment-specific API keys for production
- Consider implementing rate limiting for API endpoints
- Set up proper CORS policies for production domains

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🎵 Credits

- **OpenAI GPT-4** - AI music composition
- **Spotify Web API** - Audio analysis and music data
- **music21** - Music theory and MIDI processing
- **React** - Frontend framework
- **Flask** - Backend web framework

---

**Built with ❤️ for the music and AI community**

For support or questions, please open an issue in the repository.
