import { Midi } from '@tonejs/midi';
import * as Tone from 'tone';
import Soundfont from 'soundfont-player';

/**
 * MIDI Player utility for browser-based MIDI playback
 * Uses Tone.js and Soundfont for high-quality audio synthesis
 */
export class MIDIPlayer {
  constructor() {
    this.midi = null;
    this.isPlaying = false;
    this.isPaused = false;
    this.currentTime = 0;
    this.duration = 0;
    this.bpm = 120;
    this.instruments = {};
    this.scheduledNotes = [];
    this.playbackStartTime = 0;
    this.pausedAt = 0;
    this.volume = 1;
    this.audioContext = null;
    this.soundfonts = {};
    this.onTimeUpdate = null;
    this.onEnded = null;
    this.animationFrameId = null;
  }

  /**
   * Initialize the audio context and instruments
   */
  async initialize() {
    try {
      // Initialize Tone.js
      if (Tone.context.state !== 'running') {
        await Tone.start();
      }
      
      this.audioContext = Tone.context.rawContext;
      
      // Load default acoustic grand piano soundfont
      this.soundfonts['acoustic_grand_piano'] = await Soundfont.instrument(
        this.audioContext, 
        'acoustic_grand_piano',
        {
          gain: this.volume
        }
      );
      
      console.log('MIDI Player initialized successfully');
      return true;
    } catch (error) {
      console.error('Failed to initialize MIDI Player:', error);
      return false;
    }
  }

  /**
   * Load a MIDI file from URL
   */
  async loadMIDI(url) {
    try {
      const response = await fetch(url);
      const arrayBuffer = await response.arrayBuffer();
      
      // Parse MIDI with @tonejs/midi
      this.midi = new Midi(arrayBuffer);
      
      // Calculate duration and BPM
      this.duration = this.midi.duration;
      this.bpm = this.midi.header.tempos[0]?.bpm || 120;
      
      console.log(`MIDI loaded: ${this.duration}s duration, ${this.bpm} BPM`);
      console.log(`Tracks: ${this.midi.tracks.length}`);
      
      // Log track information
      this.midi.tracks.forEach((track, index) => {
        console.log(`Track ${index}: ${track.notes.length} notes, instrument: ${track.instrument.name}`);
      });
      
      return true;
    } catch (error) {
      console.error('Failed to load MIDI file:', error);
      return false;
    }
  }

  /**
   * Start playback
   */
  async play() {
    if (!this.midi) {
      console.error('No MIDI file loaded');
      return false;
    }

    if (!this.soundfonts['acoustic_grand_piano']) {
      const initialized = await this.initialize();
      if (!initialized) return false;
    }

    try {
      this.isPlaying = true;
      this.isPaused = false;
      
      const now = Tone.now();
      this.playbackStartTime = now - this.pausedAt;
      
      // Schedule all notes for playback
      this.scheduleNotes();
      
      // Start time update animation
      this.startTimeUpdates();
      
      console.log('MIDI playback started');
      return true;
    } catch (error) {
      console.error('Failed to start playback:', error);
      this.isPlaying = false;
      return false;
    }
  }

  /**
   * Pause playback
   */
  pause() {
    if (!this.isPlaying) return;
    
    this.isPlaying = false;
    this.isPaused = true;
    this.pausedAt = this.currentTime;
    
    // Stop all scheduled notes
    this.stopScheduledNotes();
    
    // Stop time updates
    this.stopTimeUpdates();
    
    console.log('MIDI playback paused');
  }

  /**
   * Stop playback and reset to beginning
   */
  stop() {
    this.isPlaying = false;
    this.isPaused = false;
    this.currentTime = 0;
    this.pausedAt = 0;
    
    // Stop all scheduled notes
    this.stopScheduledNotes();
    
    // Stop time updates
    this.stopTimeUpdates();
    
    console.log('MIDI playback stopped');
  }

  /**
   * Seek to a specific time
   */
  seekTo(time) {
    const wasPlaying = this.isPlaying;
    
    if (this.isPlaying) {
      this.pause();
    }
    
    this.currentTime = Math.max(0, Math.min(time, this.duration));
    this.pausedAt = this.currentTime;
    
    if (wasPlaying) {
      this.play();
    }
  }

  /**
   * Set volume (0-1)
   */
  setVolume(volume) {
    this.volume = Math.max(0, Math.min(1, volume));
    
    // Update soundfont volumes
    Object.values(this.soundfonts).forEach(instrument => {
      if (instrument && instrument.gainNode) {
        instrument.gainNode.gain.value = this.volume;
      }
    });
  }

  /**
   * Schedule all MIDI notes for playback
   */
  scheduleNotes() {
    if (!this.midi || !this.soundfonts['acoustic_grand_piano']) return;
    
    const instrument = this.soundfonts['acoustic_grand_piano'];
    const startTime = this.currentTime;
    
    // Schedule notes from all tracks
    this.midi.tracks.forEach(track => {
      track.notes.forEach(note => {
        // Only schedule notes that haven't played yet
        if (note.time >= startTime) {
          const scheduleTime = (note.time - startTime) * 1000; // Convert to ms
          
          const noteId = setTimeout(() => {
            if (this.isPlaying) {
              try {
                instrument.play(note.name, Tone.now(), {
                  duration: note.duration,
                  gain: note.velocity * this.volume
                });
              } catch (error) {
                console.warn('Error playing note:', error);
              }
            }
          }, scheduleTime);
          
          this.scheduledNotes.push(noteId);
        }
      });
    });
  }

  /**
   * Stop all scheduled notes
   */
  stopScheduledNotes() {
    this.scheduledNotes.forEach(noteId => clearTimeout(noteId));
    this.scheduledNotes = [];
  }

  /**
   * Start time update animation
   */
  startTimeUpdates() {
    const updateTime = () => {
      if (this.isPlaying) {
        this.currentTime = this.pausedAt + (Tone.now() - this.playbackStartTime);
        
        // Check if playback is complete
        if (this.currentTime >= this.duration) {
          this.stop();
          if (this.onEnded) this.onEnded();
          return;
        }
        
        // Call time update callback
        if (this.onTimeUpdate) {
          this.onTimeUpdate(this.currentTime);
        }
        
        this.animationFrameId = requestAnimationFrame(updateTime);
      }
    };
    
    updateTime();
  }

  /**
   * Stop time update animation
   */
  stopTimeUpdates() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  /**
   * Get current playback state
   */
  getState() {
    return {
      isPlaying: this.isPlaying,
      isPaused: this.isPaused,
      currentTime: this.currentTime,
      duration: this.duration,
      bpm: this.bpm,
      volume: this.volume,
      isLoaded: !!this.midi
    };
  }

  /**
   * Clean up resources
   */
  dispose() {
    this.stop();
    
    // Dispose of soundfonts
    Object.values(this.soundfonts).forEach(instrument => {
      if (instrument && instrument.stop) {
        instrument.stop();
      }
    });
    
    this.soundfonts = {};
    this.midi = null;
    
    console.log('MIDI Player disposed');
  }
}

// Create a singleton instance
export const midiPlayer = new MIDIPlayer();
export default midiPlayer;
