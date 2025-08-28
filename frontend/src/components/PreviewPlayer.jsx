import React, { useState, useRef, useEffect } from 'react';
import { 
  Play, 
  Pause, 
  Download, 
  RefreshCw, 
  Music, 
  BarChart3, 
  Clock, 
  Zap,
  Headphones,
  Brain,
  Volume2,
  VolumeX,
  RotateCcw,
  Loader
} from 'lucide-react';
import './PreviewPlayer.css';
import midiPlayer from '../utils/midiPlayer.js';

const PreviewPlayer = ({ generationResult, onRegenerate }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  const progressRef = useRef(null);

  // Initialize MIDI player and load file
  useEffect(() => {
    const initializeMidiPlayer = async () => {
      if (!generationResult?.download_url) return;
      
      setIsLoading(true);
      
      try {
        // Load the MIDI file
        const success = await midiPlayer.loadMIDI(generationResult.download_url);
        
        if (success) {
          const state = midiPlayer.getState();
          setDuration(state.duration);
          setIsInitialized(true);
          
          // Set up callbacks
          midiPlayer.onTimeUpdate = (time) => {
            setCurrentTime(time);
          };
          
          midiPlayer.onEnded = () => {
            setIsPlaying(false);
            setCurrentTime(0);
          };
        }
      } catch (error) {
        console.error('Failed to initialize MIDI player:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeMidiPlayer();

    // Cleanup on unmount
    return () => {
      midiPlayer.stop();
    };
  }, [generationResult]);

  const togglePlayPause = async () => {
    if (!isInitialized) {
      console.error('MIDI player not initialized');
      return;
    }

    try {
      if (isPlaying) {
        midiPlayer.pause();
        setIsPlaying(false);
      } else {
        const success = await midiPlayer.play();
        if (success) {
          setIsPlaying(true);
        } else {
          console.error('Failed to start MIDI playback');
        }
      }
    } catch (error) {
      console.error('Playback error:', error);
    }
  };

  const handleProgressClick = (e) => {
    if (!isInitialized || !progressRef.current) return;

    const rect = progressRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const newTime = (clickX / rect.width) * duration;
    
    midiPlayer.seekTo(newTime);
    setCurrentTime(newTime);
  };

  const handleVolumeChange = (e) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    
    if (isInitialized) {
      midiPlayer.setVolume(newVolume);
    }
    
    setIsMuted(newVolume === 0);
  };

  const toggleMute = () => {
    if (isMuted) {
      setVolume(volume);
      if (isInitialized) {
        midiPlayer.setVolume(volume);
      }
      setIsMuted(false);
    } else {
      if (isInitialized) {
        midiPlayer.setVolume(0);
      }
      setIsMuted(true);
    }
  };

  const formatTime = (time) => {
    if (isNaN(time)) return '0:00';
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const downloadFile = () => {
    const link = document.createElement('a');
    link.href = generationResult.download_url;
    link.download = generationResult.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getProgressPercentage = () => {
    return duration > 0 ? (currentTime / duration) * 100 : 0;
  };

  // Extract analysis data
  const { 
    musical_params = {}, 
    spotify_analysis = {}, 
    generation_info = {} 
  } = generationResult;

  const { audio_features = {}, musical_insights = {} } = spotify_analysis;

  return (
    <div className="preview-player">
      {/* Loading indicator */}
      {isLoading && (
        <div className="loading-indicator">
          <Loader className="spin" size={20} />
          <span>Loading MIDI file...</span>
        </div>
      )}

      {/* Player Header */}
      <div className="player-header">
        <div className="track-info">
          <Music className="track-icon" size={20} />
          <div className="track-details">
            <h3 className="track-title">
              {generationResult.formData?.song || 'AI Generated Composition'}
            </h3>
            <p className="track-subtitle">
              {generationResult.formData?.artist 
                ? `Inspired by ${generationResult.formData.artist}` 
                : 'Neural Music Generation'}
            </p>
          </div>
        </div>
        <div className="generation-badge">
          <Brain size={16} />
          <span>AI Generated</span>
        </div>
      </div>

      {/* Player Controls */}
      <div className="player-controls">
        <div className="main-controls">
          <button 
            className="control-button play-pause"
            onClick={togglePlayPause}
          >
            {isPlaying ? <Pause size={24} /> : <Play size={24} />}
          </button>
          
          <div className="time-info">
            <span className="current-time">{formatTime(currentTime)}</span>
            <span className="separator">/</span>
            <span className="total-time">{formatTime(duration)}</span>
          </div>
        </div>

        <div className="volume-controls">
          <button className="control-button" onClick={toggleMute}>
            {isMuted || volume === 0 ? <VolumeX size={18} /> : <Volume2 size={18} />}
          </button>
          <input
            type="range"
            className="volume-slider"
            min="0"
            max="1"
            step="0.1"
            value={isMuted ? 0 : volume}
            onChange={handleVolumeChange}
          />
        </div>
      </div>

      {/* Progress Bar */}
      <div 
        className="progress-container" 
        ref={progressRef}
        onClick={handleProgressClick}
      >
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${getProgressPercentage()}%` }}
          />
          <div 
            className="progress-handle" 
            style={{ left: `${getProgressPercentage()}%` }}
          />
        </div>
      </div>

      {/* Quick Stats */}
      <div className="quick-stats">
        <div className="stat-item">
          <BarChart3 size={16} />
          <span className="stat-label">Tempo</span>
          <span className="stat-value">{musical_params.tempo || 120} BPM</span>
        </div>
        <div className="stat-item">
          <Music size={16} />
          <span className="stat-label">Key</span>
          <span className="stat-value">
            {musical_params.key || 'C'} {musical_params.mode || 'major'}
          </span>
        </div>
        <div className="stat-item">
          <Clock size={16} />
          <span className="stat-label">Duration</span>
          <span className="stat-value">{musical_params.duration_bars || 8} bars</span>
        </div>
        <div className="stat-item">
          <Zap size={16} />
          <span className="stat-label">Complexity</span>
          <span className="stat-value">{musical_params.complexity || 'medium'}</span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="player-actions">
        <button className="action-button primary" onClick={downloadFile}>
          <Download size={18} />
          Download MIDI
        </button>
        
        <button 
          className="action-button secondary"
          onClick={() => setShowAnalysis(!showAnalysis)}
        >
          <BarChart3 size={18} />
          {showAnalysis ? 'Hide Analysis' : 'Show Analysis'}
        </button>
        
        <button className="action-button secondary" onClick={onRegenerate}>
          <RotateCcw size={18} />
          New Generation
        </button>
      </div>

      {/* Detailed Analysis */}
      {showAnalysis && (
        <div className="detailed-analysis">
          <div className="analysis-header">
            <h4>Generation Analysis</h4>
          </div>
          
          <div className="analysis-grid">
            {/* Generation Info */}
            <div className="analysis-section">
              <h5>
                <Brain size={16} />
                Generation Details
              </h5>
              <div className="analysis-content">
                <div className="detail-item">
                  <span className="detail-label">Processing Time</span>
                  <span className="detail-value">
                    {generation_info.generation_time?.toFixed(2)}s
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Notes Generated</span>
                  <span className="detail-value">{generation_info.notes_generated}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Spotify Enhanced</span>
                  <span className={`detail-value ${generation_info.spotify_enhanced ? 'enabled' : 'disabled'}`}>
                    {generation_info.spotify_enhanced ? 'Yes' : 'No'}
                  </span>
                </div>
              </div>
            </div>

            {/* Musical Parameters */}
            <div className="analysis-section">
              <h5>
                <Music size={16} />
                Musical Structure
              </h5>
              <div className="analysis-content">
                <div className="detail-item">
                  <span className="detail-label">Time Signature</span>
                  <span className="detail-value">
                    {musical_params.time_signature?.[0] || 4}/{musical_params.time_signature?.[1] || 4}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Form</span>
                  <span className="detail-value">{musical_params.complexity} complexity</span>
                </div>
                {musical_params.energy && (
                  <div className="detail-item">
                    <span className="detail-label">Energy Level</span>
                    <div className="energy-bar">
                      <div 
                        className="energy-fill" 
                        style={{ width: `${musical_params.energy * 100}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Spotify Analysis */}
            {spotify_analysis.track_info && (
              <div className="analysis-section">
                <h5>
                  <Headphones size={16} />
                  Reference Track
                </h5>
                <div className="analysis-content">
                  <div className="reference-track">
                    <div className="track-name">{spotify_analysis.track_info.name}</div>
                    <div className="track-artist">{spotify_analysis.track_info.artist}</div>
                  </div>
                  
                  {audio_features.energy !== undefined && (
                    <div className="spotify-features">
                      <div className="feature-bar">
                        <span className="feature-label">Energy</span>
                        <div className="feature-meter">
                          <div 
                            className="feature-fill energy" 
                            style={{ width: `${audio_features.energy * 100}%` }}
                          />
                        </div>
                        <span className="feature-value">{(audio_features.energy * 100).toFixed(0)}%</span>
                      </div>
                      
                      {audio_features.danceability !== undefined && (
                        <div className="feature-bar">
                          <span className="feature-label">Danceability</span>
                          <div className="feature-meter">
                            <div 
                              className="feature-fill danceability" 
                              style={{ width: `${audio_features.danceability * 100}%` }}
                            />
                          </div>
                          <span className="feature-value">{(audio_features.danceability * 100).toFixed(0)}%</span>
                        </div>
                      )}
                      
                      {audio_features.valence !== undefined && (
                        <div className="feature-bar">
                          <span className="feature-label">Positivity</span>
                          <div className="feature-meter">
                            <div 
                              className="feature-fill valence" 
                              style={{ width: `${audio_features.valence * 100}%` }}
                            />
                          </div>
                          <span className="feature-value">{(audio_features.valence * 100).toFixed(0)}%</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Musical Insights */}
            {musical_insights.genre_indicators && (
              <div className="analysis-section full-width">
                <h5>
                  <BarChart3 size={16} />
                  Musical Insights
                </h5>
                <div className="analysis-content">
                  {musical_insights.energy_level && (
                    <div className="insight-item">
                      <span className="insight-label">Energy Classification</span>
                      <span className="insight-value">{musical_insights.energy_level}</span>
                    </div>
                  )}
                  {musical_insights.mood_classification && (
                    <div className="insight-item">
                      <span className="insight-label">Mood Analysis</span>
                      <span className="insight-value">{musical_insights.mood_classification}</span>
                    </div>
                  )}
                  {musical_insights.genre_indicators && (
                    <div className="genre-tags">
                      {musical_insights.genre_indicators.map((genre, index) => (
                        <span key={index} className="genre-tag">
                          {genre.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* MIDI Notice */}
      <div className="midi-notice">
        <Music size={16} />
        <span>
          {isInitialized 
            ? 'MIDI playback enabled with acoustic piano sounds. Click play to listen!' 
            : 'MIDI file ready for playback. Loading audio engine...'}
        </span>
      </div>
    </div>
  );
};

export default PreviewPlayer;
