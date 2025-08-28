#!/usr/bin/env python3
"""
Integration Example: How to replace midi_generator with the new MIDI engine
while preserving your existing Spotify BPM/key/mode extraction logic.

This shows how to integrate midi_engine into your existing Flask app.py
"""

from flask import Flask, request, jsonify
import os
import uuid
import json
import time
from datetime import datetime
import logging

# Import your existing modules
from spotify_utils import SpotifyClient
# from midi_generator import MIDIGenerator  # <-- REMOVE THIS

# Import the new MIDI engine
from midi_engine.api import create_ambient_midi_with_info

# Your existing services
spotify_client = SpotifyClient()
# midi_generator = MIDIGenerator()  # <-- REMOVE THIS

logger = logging.getLogger(__name__)


def analyze_user_mood_keywords(description):
    """
    Extract mood keywords from user description (your existing function)
    Returns mood-based musical parameter overrides
    """
    description_lower = description.lower()
    mood_overrides = {}
    
    # Detect sad/melancholic moods
    sad_keywords = ['sad', 'melancholic', 'depressed', 'somber', 'mournful', 'ambient', 'atmospheric']
    if any(keyword in description_lower for keyword in sad_keywords):
        mood_overrides.update({
            'user_mode': 'minor',
            'user_energy': max(0.1, min(0.4, 0.25)),  # Low energy for sad music
            'user_valence': max(0.05, min(0.3, 0.15)), # Low positivity
            'tempo_modifier': 0.85,  # Slightly slower tempo
            'density_modifier': 0.7   # Sparser melody for ambient feel
        })
    
    # Detect happy/upbeat moods  
    happy_keywords = ['happy', 'upbeat', 'energetic', 'joyful', 'cheerful', 'bright']
    if any(keyword in description_lower for keyword in happy_keywords):
        mood_overrides.update({
            'user_mode': 'major',
            'user_energy': max(0.6, min(1.0, 0.8)),   # High energy
            'user_valence': max(0.7, min(1.0, 0.8)),  # High positivity
            'tempo_modifier': 1.1,    # Slightly faster tempo
            'density_modifier': 1.2   # Denser melody for active feel
        })
    
    # Detect ambient moods
    ambient_keywords = ['ambient', 'atmospheric', 'dreamy', 'floating', 'ethereal']
    if any(keyword in description_lower for keyword in ambient_keywords):
        mood_overrides.update({
            'density_modifier': 0.6,  # Very sparse for ambient
            'ambient_style': True
        })
    
    return mood_overrides


@app.route('/generate', methods=['POST'])
def generate_music():
    """
    Updated generate endpoint using the new MIDI engine
    with your existing Spotify BPM/key/mode extraction
    """
    try:
        data = request.json
        logger.info(f"Received generate request: {json.dumps(data, indent=2)}")
        
        # Extract your existing parameters (unchanged)
        description = data.get('description', '').strip()
        song = data.get('song', '').strip()
        artist = data.get('artist', '').strip()
        spotify_track_id = data.get('spotify_track_id', '').strip()
        user_bpm = data.get('bpm')
        auto_bpm = data.get('autoBpm', True)
        user_key = data.get('key', None)
        user_mode = data.get('mode', None)
        duration = data.get('duration', 8)
        complexity = data.get('complexity', 'medium')
        use_spotify_structure = data.get('use_spotify_structure', True)
        
        if not description:
            return jsonify({'success': False, 'error': 'Description is required'}), 400
        
        # Use YOUR EXISTING Spotify extraction logic (unchanged)
        musical_params = {
            'tempo': 120,  # Default, will be overridden by your logic
            'key': 'C',
            'mode': 'major',
            'duration_bars': max(1, min(32, int(duration))),
            'complexity': complexity if complexity in ['simple', 'medium', 'complex'] else 'medium',
            'time_signature': [4, 4]
        }
        
        # Your existing Spotify integration (unchanged)
        spotify_data = None
        if song or artist or spotify_track_id:
            logger.info("Fetching comprehensive Spotify data...")
            
            if spotify_track_id:
                spotify_data = spotify_client.get_track_by_id(spotify_track_id)
            else:
                search_query = f"{song} {artist}".strip()
                spotify_data = spotify_client.get_comprehensive_track_data(search_query)
            
            if spotify_data:
                logger.info(f"Retrieved Spotify data: {json.dumps(spotify_data, indent=2)}")
                
                audio_features = spotify_data.get('audio_features', {})
                
                # YOUR EXISTING BPM LOGIC (unchanged) - Priority: 1. User manual, 2. Spotify, 3. Default
                if user_bpm and not auto_bpm:
                    musical_params['tempo'] = int(user_bpm)
                    logger.info(f"Using user-specified BPM: {user_bpm}")
                elif auto_bpm and audio_features.get('tempo'):
                    musical_params['tempo'] = int(audio_features['tempo'])
                    logger.info(f"Using Spotify-detected BPM: {audio_features['tempo']}")
                elif user_bpm:
                    musical_params['tempo'] = int(user_bpm)
                    logger.info(f"Using user-specified BPM: {user_bpm}")
                else:
                    musical_params['tempo'] = 120
                    logger.info(f"Using default BPM: 120")
                
                # YOUR EXISTING KEY LOGIC (unchanged)
                if user_key and user_key.strip():
                    musical_params['key'] = user_key.strip()
                    logger.info(f"Using user-specified key: {user_key}")
                elif audio_features.get('key') is not None:
                    detected_key = spotify_client.key_mapping.get(audio_features['key'], 'C')
                    musical_params['key'] = detected_key
                    logger.info(f"Using Spotify-detected key: {detected_key}")
                else:
                    musical_params['key'] = 'C'
                
                # YOUR EXISTING MODE LOGIC (unchanged)
                if user_mode and user_mode.strip():
                    musical_params['mode'] = user_mode.strip()
                    logger.info(f"Using user-specified mode: {user_mode}")
                elif audio_features.get('mode') is not None:
                    detected_mode = 'major' if audio_features['mode'] == 1 else 'minor'
                    musical_params['mode'] = detected_mode
                    logger.info(f"Using Spotify-detected mode: {detected_mode}")
                else:
                    musical_params['mode'] = 'major'
                
                # Your existing additional parameters
                if audio_features.get('time_signature'):
                    musical_params['time_signature'] = [audio_features['time_signature'], 4]
                
                musical_params.update({
                    'energy': audio_features.get('energy', 0.5),
                    'danceability': audio_features.get('danceability', 0.5),
                    'valence': audio_features.get('valence', 0.5),
                    'acousticness': audio_features.get('acousticness', 0.5),
                    'instrumentalness': audio_features.get('instrumentalness', 0.1),
                    'liveness': audio_features.get('liveness', 0.1),
                    'speechiness': audio_features.get('speechiness', 0.1),
                    'loudness': audio_features.get('loudness', -10.0)
                })
        
        else:
            # Your existing fallback logic when no Spotify data
            if user_bpm:
                musical_params['tempo'] = int(user_bpm)
                logger.info(f"Using user-specified BPM (no Spotify data): {user_bpm}")
            else:
                musical_params['tempo'] = 120
            
            if user_key and user_key.strip():
                musical_params['key'] = user_key.strip()
            else:
                musical_params['key'] = 'C'
            
            if user_mode and user_mode.strip():
                musical_params['mode'] = user_mode.strip()
            else:
                musical_params['mode'] = 'major'
        
        # NEW: Analyze mood and apply overrides for better emotional accuracy
        mood_overrides = analyze_user_mood_keywords(description)
        
        # Apply mood-based overrides to musical parameters
        if 'user_mode' in mood_overrides:
            musical_params['mode'] = mood_overrides['user_mode']
            logger.info(f"Mood override: Using {mood_overrides['user_mode']} mode for mood: {description}")
        
        if 'tempo_modifier' in mood_overrides:
            original_tempo = musical_params['tempo']
            musical_params['tempo'] = int(original_tempo * mood_overrides['tempo_modifier'])
            logger.info(f"Mood override: Tempo {original_tempo} -> {musical_params['tempo']}")
        
        # Map complexity to density
        complexity_density_map = {
            'simple': 0.2,
            'medium': 0.35, 
            'complex': 0.5
        }
        base_density = complexity_density_map.get(complexity, 0.35)
        
        # Apply mood density modifier
        if 'density_modifier' in mood_overrides:
            base_density *= mood_overrides['density_modifier']
            logger.info(f"Mood override: Density adjusted to {base_density:.2f}")
        
        # Generate unique filename (your existing logic)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        safe_song = "".join(c for c in (song or "unknown")[:20] if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"midigpt_{safe_song}_{timestamp}_{unique_id}.mid"
        filepath = os.path.join('static', 'generated', filename)
        
        # NEW: Generate MIDI using the new engine instead of midi_generator
        start_time = time.time()
        
        # Convert duration to bars (your duration is likely in sections, so multiply by 2)
        bars = max(1, min(32, int(duration * 2)))
        
        # Create a seed from the song data for reproducibility
        seed = hash(f"{song}_{artist}_{description}") % 10000
        
        try:
            # Generate MIDI using the new engine
            midi_bytes, engine_info = create_ambient_midi_with_info(
                seed=seed,
                key=musical_params['key'],
                mode=musical_params['mode'], 
                bpm=musical_params['tempo'],
                bars=bars,
                density=base_density,
                melody_program=0,   # Acoustic Grand Piano (default)
                pad_program=88     # New Age Pad (perfect for ambient)
            )
            
            generation_time = time.time() - start_time
            
            # Save the MIDI file
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(midi_bytes)
            
            # Build response in your existing format
            response_data = {
                'success': True,
                'filename': filename,
                'download_url': f'/static/generated/{filename}',
                'musical_params': musical_params,  # Your existing format
                'generation_info': {
                    'bars': bars,
                    'complexity': complexity,
                    'spotify_enhanced': spotify_data is not None,
                    'structure_based': use_spotify_structure and spotify_data is not None,
                    'generation_time': generation_time,
                    'notes_generated': engine_info['melody_stats']['total_events'] + engine_info['pad_stats']['total_events'],
                    # NEW: Additional engine stats
                    'melody_notes': engine_info['melody_stats']['total_events'],
                    'pad_notes': engine_info['pad_stats']['total_events'],
                    'file_size': len(midi_bytes),
                    'mood_enhanced': bool(mood_overrides)
                }
            }
            
            # Add your existing Spotify analysis (unchanged)
            if spotify_data:
                track_info = spotify_data.get('track_info', {})
                if isinstance(track_info, dict):
                    artists_list = track_info.get('artists', [])
                    first_artist = artists_list[0] if artists_list else ''
                    artist_name = first_artist if isinstance(first_artist, str) else (first_artist.get('name', '') if isinstance(first_artist, dict) else '')
                    
                    album_info = track_info.get('album', {})
                    album_name = album_info.get('name', '') if isinstance(album_info, dict) else str(album_info)
                    
                    response_data['spotify_analysis'] = {
                        'track_info': {
                            'name': track_info.get('name', ''),
                            'artist': artist_name,
                            'album': album_name,
                            'duration_ms': track_info.get('duration_ms', 0),
                            'popularity': track_info.get('popularity', 0)
                        },
                        'audio_features': spotify_data.get('audio_features', {}),
                        'musical_insights': {
                            'genre_influence': classify_genre_influence(spotify_data.get('audio_features', {})),
                            'energy_level': classify_energy_level(musical_params.get('energy', 0.5)),
                            'mood_classification': classify_mood(musical_params.get('valence', 0.5)),
                            'danceability_level': classify_danceability(musical_params.get('danceability', 0.5))
                        }
                    }
            
            logger.info(f"Successfully generated MIDI with new engine: {filename}")
            return jsonify(response_data)
            
        except Exception as engine_error:
            logger.error(f"MIDI engine error: {str(engine_error)}")
            return jsonify({
                'success': False,
                'error': f'MIDI generation failed: {str(engine_error)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Generate endpoint error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


# Your existing helper functions remain unchanged
def classify_genre_influence(audio_features):
    """Your existing function"""
    pass

def classify_energy_level(energy):
    """Your existing function""" 
    pass

def classify_mood(valence):
    """Your existing function"""
    pass

def classify_danceability(danceability):
    """Your existing function"""
    pass


if __name__ == "__main__":
    print("🎵 Integration example for MIDI Engine")
    print("This shows how to replace midi_generator with the new engine")
    print("while preserving all your existing Spotify BPM extraction logic!")
