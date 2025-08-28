import React, { useState, useRef, useEffect } from 'react';
import { Search, Music, Brain, Zap, Loader, Settings, Sparkles } from 'lucide-react';
import './InputForm.css';

const InputForm = ({ onGenerate, isGenerating }) => {
  const [formData, setFormData] = useState({
    description: '',
    song: '',
    artist: '',
    spotify_track_id: '',
    bpm: 120,
    autoBpm: true,
    key: '',
    mode: '',
    duration: 8,
    complexity: 'medium',
    use_spotify_structure: true
  });

  const [searchResults, setSearchResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const searchTimeoutRef = useRef(null);
  const searchInputRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchInputRef.current && !searchInputRef.current.contains(event.target)) {
        setShowResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSearchChange = async (query) => {
    setSearchQuery(query);
    handleInputChange('song', query);

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (query.length < 2) {
      setSearchResults([]);
      setShowResults(false);
      return;
    }

    setIsSearching(true);
    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const response = await fetch('/search-songs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query })
        });

        const result = await response.json();
        if (result.success) {
          setSearchResults(result.tracks || []);
          setShowResults(true);
        }
      } catch (error) {
        console.error('Search failed:', error);
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 500);
  };

  const selectTrack = (track) => {
    setFormData(prev => ({
      ...prev,
      song: track.name,
      artist: track.artist,
      spotify_track_id: track.id
    }));
    setSearchQuery(`${track.name} - ${track.artist}`);
    setShowResults(false);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.description.trim()) {
      alert('Please provide a description of the mood/feeling');
      return;
    }
    onGenerate(formData);
  };

  const complexityOptions = [
    { value: 'simple', label: 'Simple', desc: 'Basic rhythms and melodies' },
    { value: 'medium', label: 'Medium', desc: 'Balanced complexity' },
    { value: 'complex', label: 'Complex', desc: 'Advanced patterns and harmonies' }
  ];

  const keyOptions = [
    'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'
  ];

  const modeOptions = ['major', 'minor'];

  return (
    <form onSubmit={handleSubmit} className="input-form">
      {/* Mood Description */}
      <div className="form-group">
        <label className="form-label">
          <Sparkles size={18} />
          Mood & Feeling
          <span className="required">*</span>
        </label>
        <textarea
          className="form-textarea"
          placeholder="Describe the emotion or mood you want to capture (e.g., 'energetic and uplifting', 'melancholic and introspective', 'dreamy and ethereal')"
          value={formData.description}
          onChange={(e) => handleInputChange('description', e.target.value)}
          rows="3"
          required
        />
      </div>

      {/* Song Search */}
      <div className="form-group">
        <label className="form-label">
          <Search size={18} />
          Reference Track (Optional)
        </label>
        <div className="search-container" ref={searchInputRef}>
          <div className="search-input-wrapper">
            <input
              type="text"
              className="form-input search-input"
              placeholder="Search for a song to use as musical reference..."
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              autoComplete="off"
            />
            {isSearching && (
              <div className="search-loading">
                <Loader size={16} className="spin" />
              </div>
            )}
          </div>
          
          {showResults && searchResults.length > 0 && (
            <div className="search-results">
              {searchResults.slice(0, 6).map((track) => (
                <div
                  key={track.id}
                  className="search-result-item"
                  onClick={() => selectTrack(track)}
                >
                  <div className="track-info">
                    <div className="track-name">{track.name}</div>
                    <div className="track-artist">{track.artist}</div>
                  </div>
                  <div className="track-meta">
                    <span className="track-album">{track.album}</span>
                    {track.popularity && (
                      <span className="popularity-badge">
                        {track.popularity}% popularity
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Settings - Better Horizontal Layout */}
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Duration (bars)</label>
          <input
            type="range"
            className="form-range"
            min="4"
            max="32"
            step="4"
            value={formData.duration}
            onChange={(e) => handleInputChange('duration', parseInt(e.target.value))}
          />
          <div className="range-value">{formData.duration} bars</div>
        </div>
      </div>
      
      <div className="form-group">
        <label className="form-label">Complexity</label>
        <div className="complexity-options">
          {complexityOptions.map((option) => (
            <label
              key={option.value}
              className={`complexity-option ${formData.complexity === option.value ? 'active' : ''}`}
            >
              <input
                type="radio"
                name="complexity"
                value={option.value}
                checked={formData.complexity === option.value}
                onChange={(e) => handleInputChange('complexity', e.target.value)}
              />
              <div className="option-content">
                <span className="option-label">{option.label}</span>
                <span className="option-desc">{option.desc}</span>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Advanced Settings Toggle */}
      <div className="advanced-toggle">
        <button
          type="button"
          className="toggle-button"
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          <Settings size={16} />
          Advanced Settings
          <span className={`toggle-arrow ${showAdvanced ? 'open' : ''}`}>▼</span>
        </button>
      </div>

      {/* Advanced Settings */}
      {showAdvanced && (
        <div className="advanced-settings">
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">
                <input
                  type="checkbox"
                  className="form-checkbox"
                  checked={formData.autoBpm}
                  onChange={(e) => handleInputChange('autoBpm', e.target.checked)}
                />
                Auto-detect BPM from reference
              </label>
            </div>
            
            {!formData.autoBpm && (
              <div className="form-group">
                <label className="form-label">BPM</label>
                <input
                  type="number"
                  className="form-input small"
                  min="60"
                  max="200"
                  value={formData.bpm}
                  onChange={(e) => handleInputChange('bpm', parseInt(e.target.value) || 120)}
                />
              </div>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Key (optional)</label>
              <select
                className="form-select"
                value={formData.key}
                onChange={(e) => handleInputChange('key', e.target.value)}
              >
                <option value="">Auto-detect from reference</option>
                {keyOptions.map((key) => (
                  <option key={key} value={key}>{key}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Mode (optional)</label>
              <select
                className="form-select"
                value={formData.mode}
                onChange={(e) => handleInputChange('mode', e.target.value)}
              >
                <option value="">Auto-detect from reference</option>
                {modeOptions.map((mode) => (
                  <option key={mode} value={mode}>
                    {mode.charAt(0).toUpperCase() + mode.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">
              <input
                type="checkbox"
                className="form-checkbox"
                checked={formData.use_spotify_structure}
                onChange={(e) => handleInputChange('use_spotify_structure', e.target.checked)}
              />
              Use Spotify structural analysis (recommended)
            </label>
          </div>
        </div>
      )}

      {/* Generate Button */}
      <div className="form-actions">
        <button
          type="submit"
          className="generate-button"
          disabled={isGenerating || !formData.description.trim()}
        >
          {isGenerating ? (
            <>
              <Loader size={20} className="spin" />
              <span>Generating Neural Composition...</span>
              <div className="button-glow generating"></div>
            </>
          ) : (
            <>
              <Brain size={20} />
              <span>Generate Music</span>
              <div className="button-glow"></div>
            </>
          )}
        </button>

        {formData.song && formData.artist && (
          <div className="selected-reference">
            <Music size={16} />
            <span>
              Reference: <strong>{formData.song}</strong> by {formData.artist}
            </span>
          </div>
        )}
      </div>
    </form>
  );
};

export default InputForm;
