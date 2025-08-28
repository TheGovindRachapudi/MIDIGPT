import React, { useState, useEffect } from 'react';
import InputForm from './components/InputForm';
import PreviewPlayer from './components/PreviewPlayer';
import { Music, Headphones, Activity, TrendingUp, Zap, Brain, Download } from 'lucide-react';
import './App.css';

function App() {
  const [generatedMidi, setGeneratedMidi] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationHistory, setGenerationHistory] = useState([]);
  const [serverHealth, setServerHealth] = useState('unknown');
  const [particles, setParticles] = useState([]);

  useEffect(() => {
    checkServerHealth();
    loadGenerationHistory();
    createParticles();
    
    // Animated background particles
    const interval = setInterval(() => {
      createParticles();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const createParticles = () => {
    const newParticles = Array.from({ length: 20 }, (_, i) => ({
      id: Date.now() + i,
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      size: Math.random() * 3 + 1,
      duration: Math.random() * 10 + 5
    }));
    setParticles(newParticles);
  };

  const checkServerHealth = async () => {
    try {
      const response = await fetch('/health');
      if (response.ok) {
        setServerHealth('healthy');
      } else {
        setServerHealth('unhealthy');
      }
    } catch (error) {
      setServerHealth('offline');
    }
  };

  const loadGenerationHistory = () => {
    const savedHistory = localStorage.getItem('midigpt_history');
    if (savedHistory) {
      try {
        setGenerationHistory(JSON.parse(savedHistory));
      } catch (e) {
        console.error('Failed to parse saved history:', e);
      }
    }
  };

  const handleGeneration = async (formData) => {
    setIsGenerating(true);
    setGeneratedMidi(null);

    try {
      const response = await fetch('/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const result = await response.json();

      if (result.success) {
        const generationResult = {
          ...result,
          timestamp: new Date().toISOString(),
          formData: formData,
          id: Date.now().toString()
        };
        
        setGeneratedMidi(generationResult);
        
        const newHistory = [generationResult, ...generationHistory.slice(0, 9)];
        setGenerationHistory(newHistory);
        localStorage.setItem('midigpt_history', JSON.stringify(newHistory));
      } else {
        throw new Error(result.error || 'Unknown error occurred');
      }
    } catch (error) {
      console.error('Generation failed:', error);
      // Show elegant error notification
      showNotification(`Failed to generate MIDI: ${error.message}`, 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  const showNotification = (message, type = 'info') => {
    // Create floating notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.classList.add('fade-out');
      setTimeout(() => document.body.removeChild(notification), 300);
    }, 4000);
  };

  const loadHistoryItem = (historyItem) => {
    setGeneratedMidi(historyItem);
  };

  const getServerStatusInfo = () => {
    switch (serverHealth) {
      case 'healthy': return { color: '#00ff88', text: 'Online', pulse: true };
      case 'unhealthy': return { color: '#ffaa00', text: 'Warning', pulse: false };
      case 'offline': return { color: '#ff4444', text: 'Offline', pulse: false };
      default: return { color: '#888', text: 'Unknown', pulse: false };
    }
  };

  const statusInfo = getServerStatusInfo();

  return (
    <div className="app">
      {/* Animated Background */}
      <div className="background-container">
        <div className="gradient-bg"></div>
        <div className="particles-container">
          {particles.map(particle => (
            <div
              key={particle.id}
              className="particle"
              style={{
                left: `${particle.x}px`,
                top: `${particle.y}px`,
                width: `${particle.size}px`,
                height: `${particle.size}px`,
                animationDuration: `${particle.duration}s`
              }}
            />
          ))}
        </div>
        <div className="grid-overlay"></div>
      </div>

      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="logo-section">
            <div className="logo-container">
              <Music className="logo-icon" size={36} />
            </div>
            <div className="logo-text">
              <h1>MIDIGPT</h1>
              <span className="tagline">Neural Music Generation Platform</span>
            </div>
          </div>
          
          <div className="status-section">
            <div className="server-status">
              <div 
                className={`status-indicator ${statusInfo.pulse ? 'pulse' : ''}`}
                style={{ backgroundColor: statusInfo.color }}
              />
              <span className="status-text">{statusInfo.text}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Input Form Section */}
        <section className="glass-panel form-section">
          <div className="section-header">
            <Brain size={24} className="section-icon" />
            <h2>AI Music Generator</h2>
            <div className="header-accent"></div>
          </div>
          
          <InputForm 
            onGenerate={handleGeneration}
            isGenerating={isGenerating}
          />
        </section>

        {/* Results Section */}
        <section className="glass-panel results-section">
          <div className="section-header">
            <Zap size={24} className="section-icon" />
            <h2>Generated Output</h2>
            <div className="header-accent"></div>
          </div>
          
          {generatedMidi ? (
            <PreviewPlayer 
              generationResult={generatedMidi}
              onRegenerate={() => setGeneratedMidi(null)}
            />
          ) : (
            <div className="no-results">
              <div className="no-results-animation">
                <Music size={64} className="no-results-icon" />
                <div className="pulse-ring"></div>
              </div>
              <h3>Ready to Create</h3>
              <p>Configure your parameters and generate your first AI-powered MIDI composition</p>
            </div>
          )}
        </section>

        {/* Generation History */}
        {generationHistory.length > 0 && (
          <section className="glass-panel history-section">
            <div className="section-header">
              <TrendingUp size={24} className="section-icon" />
              <h2>Generation History</h2>
              <div className="header-accent"></div>
            </div>
            
            <div className="history-grid">
              {generationHistory.map((item, index) => (
                <div 
                  key={item.id}
                  className="history-item glass-card"
                  onClick={() => loadHistoryItem(item)}
                  style={{ animationDelay: `${index * 0.1}s` }}
                >
                  <div className="history-header">
                    <Music size={18} className="history-icon" />
                    <div className="history-title">
                      <span className="song-name">
                        {item.formData.song || 'Untitled Composition'}
                      </span>
                      {item.formData.artist && (
                        <span className="artist-name">by {item.formData.artist}</span>
                      )}
                    </div>
                  </div>
                  
                  <div className="history-details">
                    <p className="history-description">{item.formData.description}</p>
                    <div className="history-meta">
                      <span className="history-timestamp">
                        {new Date(item.timestamp).toLocaleDateString()}
                      </span>
                      {item.spotify_analysis && (
                        <span className="spotify-badge">
                          <Headphones size={14} />
                          Spotify Enhanced
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="history-hover-overlay">
                    <Download size={20} />
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>

      {/* Features Showcase */}
      <section className="features-section">
        <div className="features-header">
          <h2>Powered by Advanced AI Technology</h2>
          <div className="features-subtitle">
            Next-generation music creation using cutting-edge artificial intelligence
          </div>
        </div>
        
        <div className="features-grid">
          <div className="feature-card glass-card">
            <div className="feature-icon-container">
              <Headphones className="feature-icon" size={32} />
              <div className="feature-glow spotify-glow"></div>
            </div>
            <h3>Spotify Intelligence</h3>
            <p>Deep audio analysis extracting key, tempo, energy patterns, and harmonic structures from your reference tracks</p>
            <div className="feature-tech">
              <span className="tech-tag">Audio Analysis</span>
              <span className="tech-tag">Pattern Recognition</span>
            </div>
          </div>
          
          <div className="feature-card glass-card">
            <div className="feature-icon-container">
              <Brain className="feature-icon" size={32} />
              <div className="feature-glow gpt-glow"></div>
            </div>
            <h3>GPT-4 Composition</h3>
            <p>Advanced language model with deep musical understanding creates contextually aware melodies and harmonies</p>
            <div className="feature-tech">
              <span className="tech-tag">Neural Networks</span>
              <span className="tech-tag">Music Theory</span>
            </div>
          </div>
          
          <div className="feature-card glass-card">
            <div className="feature-icon-container">
              <Music className="feature-icon" size={32} />
              <div className="feature-glow midi-glow"></div>
            </div>
            <h3>Professional MIDI</h3>
            <p>Studio-quality MIDI generation with precise timing, dynamic expression, and production-ready output</p>
            <div className="feature-tech">
              <span className="tech-tag">music21</span>
              <span className="tech-tag">MIDI Protocol</span>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="app-footer">
        <div className="footer-content">
          <div className="footer-text">
            <p>© 2024 MIDIGPT - Neural Music Generation Platform</p>
            <p>Powered by React • Flask • Spotify API • OpenAI GPT-4 • music21</p>
          </div>
          <div className="footer-glow"></div>
        </div>
      </footer>
    </div>
  );
}

export default App;
