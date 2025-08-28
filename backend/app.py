from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
import json
from datetime import datetime
from dotenv import load_dotenv
from spotify_utils import SpotifyClient
from midi_generator import MIDIGenerator
import logging

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Set up logging with improved configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('midigpt.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Suppress warnings from third-party libraries
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('requests').setLevel(logging.ERROR)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Ensure generated directory exists
os.makedirs('static/generated', exist_ok=True)

# Initialize services
spotify_client = SpotifyClient()
midi_generator = MIDIGenerator()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/search-songs', methods=['POST'])
def search_songs():
    """Search for songs on Spotify to help users find accurate references"""
    try:
        data = request.json
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'success': False, 'error': 'Search query is required'}), 400
        
        results = spotify_client.search_tracks(query, limit=10)
        
        return jsonify({
            'success': True,
            'tracks': results
        })
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/generate', methods=['POST'])
def generate_music():
    """
    Generate MIDI music with deep Spotify API integration
    Expected JSON payload:
    {
        "description": "happy and upbeat",
        "song": "Bohemian Rhapsody",
        "artist": "Queen", 
        "spotify_track_id": "3z8h0TU7ReDPLIbEnYhWZb", // Optional but preferred
        "bpm": 120,
        "autoBpm": true,
        "key": "C",
        "mode": "major",
        "duration": 8,
        "complexity": "medium",
        "use_spotify_structure": true
    }
    """
    try:
        data = request.json
        logger.info(f"Received generate request: {json.dumps(data, indent=2)}")
        
        # Extract and validate input parameters
        description = data.get('description', '').strip()
        song = data.get('song', '').strip()
        artist = data.get('artist', '').strip()
        spotify_track_id = data.get('spotify_track_id', '').strip()
        user_bpm = data.get('bpm')  # None if not provided by user
        auto_bpm = data.get('autoBpm', True)  # Default to true for better accuracy
        user_key = data.get('key', None)
        user_mode = data.get('mode', None)
        duration = data.get('duration', 8)
        complexity = data.get('complexity', 'medium')
        use_spotify_structure = data.get('use_spotify_structure', True)
        
        # Validate required fields
        if not description:
            return jsonify({'success': False, 'error': 'Description is required'}), 400
        
        # Initialize musical parameters with defaults (tempo, key, mode will be set properly later)
        musical_params = {
            'tempo': 120,  # Default, will be overridden based on priority logic
            'key': 'C',     # Default, will be overridden based on priority logic
            'mode': 'major', # Default, will be overridden based on priority logic
            'duration_bars': max(1, min(32, int(duration))),
            'complexity': complexity if complexity in ['simple', 'medium', 'complex'] else 'medium',
            'time_signature': [4, 4]  # Default 4/4
        }
        
        # Deep Spotify integration
        spotify_data = None
        if song or artist or spotify_track_id:
            logger.info("Fetching comprehensive Spotify data...")
            
            # Get track data using different methods
            if spotify_track_id:
                spotify_data = spotify_client.get_track_by_id(spotify_track_id)
            else:
                search_query = f"{song} {artist}".strip()
                spotify_data = spotify_client.get_comprehensive_track_data(search_query)
            
            if spotify_data:
                logger.info(f"Retrieved Spotify data: {json.dumps(spotify_data, indent=2)}")
                
                # Update musical parameters with Spotify insights
                audio_features = spotify_data.get('audio_features', {})
                audio_analysis = spotify_data.get('audio_analysis', {})
                
                # Handle BPM with proper priority logic
                # Priority: 1. User manual BPM, 2. Spotify BPM (if auto_bpm), 3. Default 120
                if user_bpm and not auto_bpm:  # User manually set BPM and disabled auto
                    musical_params['tempo'] = int(user_bpm)
                    logger.info(f"Using user-specified BPM: {user_bpm}")
                elif auto_bpm and audio_features.get('tempo'):  # Auto BPM enabled and Spotify has tempo
                    musical_params['tempo'] = int(audio_features['tempo'])
                    logger.info(f"Using Spotify-detected BPM: {audio_features['tempo']}")
                elif user_bpm:  # User provided BPM but auto is also enabled - prefer user
                    musical_params['tempo'] = int(user_bpm)
                    logger.info(f"Using user-specified BPM: {user_bpm} (auto_bpm enabled but user preference prioritized)")
                else:  # No user BPM and no Spotify BPM - use default
                    musical_params['tempo'] = 120
                    logger.info(f"Using default BPM: 120")
                
                # Handle KEY with proper priority logic
                # Priority: 1. User manual key, 2. Spotify key, 3. Default C
                if user_key and user_key.strip():  # User manually selected a key
                    musical_params['key'] = user_key.strip()
                    logger.info(f"Using user-specified key: {user_key}")
                elif audio_features.get('key') is not None:  # Use Spotify's detected key
                    detected_key = spotify_client.key_mapping.get(audio_features['key'], 'C')
                    musical_params['key'] = detected_key
                    logger.info(f"Using Spotify-detected key: {detected_key} (key index: {audio_features['key']})")
                else:  # No user key and no Spotify key - use default
                    musical_params['key'] = 'C'
                    logger.info(f"Using default key: C")
                
                # Handle MODE with proper priority logic
                # Priority: 1. User manual mode, 2. Spotify mode, 3. Default major
                if user_mode and user_mode.strip():  # User manually selected a mode
                    musical_params['mode'] = user_mode.strip()
                    logger.info(f"Using user-specified mode: {user_mode}")
                elif audio_features.get('mode') is not None:  # Use Spotify's detected mode
                    detected_mode = 'major' if audio_features['mode'] == 1 else 'minor'
                    musical_params['mode'] = detected_mode
                    logger.info(f"Using Spotify-detected mode: {detected_mode} (mode index: {audio_features['mode']})")
                else:  # No user mode and no Spotify mode - use default
                    musical_params['mode'] = 'major'
                    logger.info(f"Using default mode: major")
                    
                # Time signature
                if audio_features.get('time_signature'):
                    musical_params['time_signature'] = [audio_features['time_signature'], 4]
                    
                # Advanced musical characteristics from Spotify
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
                    
                # Extract structural information if available
                if use_spotify_structure and audio_analysis:
                    sections = audio_analysis.get('sections', [])
                    beats = audio_analysis.get('beats', [])
                    bars = audio_analysis.get('bars', [])
                    
                    if sections:
                        # Use actual song structure
                        musical_params['structure_info'] = {
                            'sections': sections[:4],  # First 4 sections
                            'has_structure': True
                        }
                    
                    if bars and len(bars) > 0:
                        # Extract rhythmic patterns
                        musical_params['rhythmic_patterns'] = analyze_rhythmic_patterns(bars)
                    
                logger.info(f"Enhanced musical params: {musical_params}")
            else:
                logger.info("No Spotify data retrieved, checking why...")
        else:
            # No Spotify data available, handle BPM, key, and mode based on user input
            if user_bpm:  # User provided BPM
                musical_params['tempo'] = int(user_bpm)
                logger.info(f"Using user-specified BPM (no Spotify data): {user_bpm}")
            else:  # No user BPM and no Spotify data - use default
                musical_params['tempo'] = 120
                logger.info(f"Using default BPM (no Spotify data): 120")
            
            # Handle key when no Spotify data
            if user_key and user_key.strip():  # User provided key
                musical_params['key'] = user_key.strip()
                logger.info(f"Using user-specified key (no Spotify data): {user_key}")
            else:  # No user key and no Spotify data - use default
                musical_params['key'] = 'C'
                logger.info(f"Using default key (no Spotify data): C")
            
            # Handle mode when no Spotify data
            if user_mode and user_mode.strip():  # User provided mode
                musical_params['mode'] = user_mode.strip()
                logger.info(f"Using user-specified mode (no Spotify data): {user_mode}")
            else:  # No user mode and no Spotify data - use default
                musical_params['mode'] = 'major'
                logger.info(f"Using default mode (no Spotify data): major")
        
        # Build sophisticated GPT prompt with Spotify data
        prompt = build_advanced_gpt_prompt(
            description=description,
            song=song,
            artist=artist,
            musical_params=musical_params,
            spotify_data=spotify_data
        )
        
        logger.info(f"Generated advanced prompt: {prompt[:300]}...")
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        safe_song = "".join(c for c in (song or "unknown")[:20] if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"midigpt_{safe_song}_{timestamp}_{unique_id}.mid"
        filepath = os.path.join('static', 'generated', filename)
        
        # Generate MIDI file with Spotify-enhanced parameters
        generation_result = midi_generator.generate_from_gpt_with_spotify(
            prompt=prompt,
            output_path=filepath,
            musical_params=musical_params,
            spotify_data=spotify_data
        )
        
        if generation_result['success']:
            response_data = {
                'success': True,
                'filename': filename,
                'download_url': f'/static/generated/{filename}',
                'musical_params': musical_params,
                'generation_info': {
                    'bars': musical_params['duration_bars'],
                    'complexity': musical_params['complexity'],
                    'spotify_enhanced': spotify_data is not None,
                    'structure_based': use_spotify_structure and spotify_data is not None,
                    'generation_time': generation_result.get('generation_time', 0),
                    'notes_generated': generation_result.get('notes_count', 0)
                }
            }
            
            # Add comprehensive Spotify info
            if spotify_data:
                # Safely extract track info
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
                else:
                    # Fallback if track_info is not a dict
                    response_data['spotify_analysis'] = {
                        'track_info': {
                            'name': song or 'Unknown',
                            'artist': artist or 'Unknown',
                            'album': 'Unknown',
                            'duration_ms': 0,
                            'popularity': 0
                        },
                        'audio_features': spotify_data.get('audio_features', {}),
                        'musical_insights': {
                            'genre_influence': classify_genre_influence(spotify_data.get('audio_features', {})),
                            'energy_level': classify_energy_level(musical_params.get('energy', 0.5)),
                            'mood_classification': classify_mood(musical_params.get('valence', 0.5)),
                            'danceability_level': classify_danceability(musical_params.get('danceability', 0.5))
                        }
                    }
                
                # Add structural analysis if available
                if musical_params.get('structure_info'):
                    response_data['spotify_analysis']['structure'] = musical_params['structure_info']
            
            logger.info(f"Successfully generated Spotify-enhanced MIDI: {filename}")
            return jsonify(response_data)
            
        else:
            error_msg = generation_result.get('error', 'Unknown error occurred')
            logger.error(f"MIDI generation failed: {error_msg}")
            return jsonify({
                'success': False,
                'error': f'Failed to generate MIDI: {error_msg}'
            }), 500
            
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Invalid input: {str(e)}'
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

def analyze_rhythmic_patterns(bars):
    """Analyze rhythmic patterns from Spotify's bar data"""
    if len(bars) < 4:
        return None
        
    patterns = []
    for i, bar in enumerate(bars[:8]):  # Analyze first 8 bars
        confidence = bar.get('confidence', 0)
        duration = bar.get('duration', 0)
        patterns.append({
            'bar': i + 1,
            'confidence': confidence,
            'duration': duration,
            'strong_beat': confidence > 0.8
        })
    
    return patterns

def classify_genre_influence(audio_features):
    """Classify genre influence based on audio features"""
    energy = audio_features.get('energy', 0.5)
    danceability = audio_features.get('danceability', 0.5)
    acousticness = audio_features.get('acousticness', 0.5)
    valence = audio_features.get('valence', 0.5)
    
    if energy > 0.8 and danceability > 0.7:
        return "Electronic/Dance"
    elif acousticness > 0.7:
        return "Folk/Acoustic"
    elif energy > 0.7 and valence < 0.4:
        return "Rock/Alternative" 
    elif danceability > 0.6 and valence > 0.6:
        return "Pop"
    elif energy < 0.4 and valence < 0.4:
        return "Ambient/Chill"
    else:
        return "Contemporary"

def classify_energy_level(energy):
    """Classify energy level"""
    if energy > 0.8:
        return "Very High"
    elif energy > 0.6:
        return "High"
    elif energy > 0.4:
        return "Medium"
    elif energy > 0.2:
        return "Low"
    else:
        return "Very Low"

def classify_mood(valence):
    """Classify mood based on valence"""
    if valence > 0.8:
        return "Very Happy"
    elif valence > 0.6:
        return "Happy"
    elif valence > 0.4:
        return "Neutral"
    elif valence > 0.2:
        return "Sad"
    else:
        return "Very Sad"

def classify_danceability(danceability):
    """Classify danceability level"""
    if danceability > 0.8:
        return "Highly Danceable"
    elif danceability > 0.6:
        return "Danceable"
    elif danceability > 0.4:
        return "Moderately Danceable"
    else:
        return "Not Danceable"

def analyze_user_mood_keywords(description):
    """Analyze user description for mood keywords and return mood characteristics"""
    description_lower = description.lower()
    
    # Define mood keywords and their characteristics
    mood_analysis = {
        'energy': 0.5,  # Default medium energy
        'valence': 0.5, # Default neutral mood  
        'tempo_modifier': 1.0,  # Tempo multiplier
        'key_override': None,  # Force a specific key
        'mode_override': None,  # Force major/minor
        'detected_moods': []
    }
    
    # Sad/melancholic keywords
    sad_keywords = ['sad', 'melancholy', 'melancholic', 'depressed', 'gloomy', 'somber', 'mournful', 'tragic', 'dark', 'blue']
    if any(word in description_lower for word in sad_keywords):
        mood_analysis['valence'] = 0.15  # Very sad
        mood_analysis['energy'] = 0.3   # Low energy
        mood_analysis['tempo_modifier'] = 0.8  # Slower tempo
        mood_analysis['mode_override'] = 'minor'  # Force minor key
        mood_analysis['detected_moods'].append('sad')
    
    # Ambient/chill keywords
    ambient_keywords = ['ambient', 'chill', 'relaxed', 'calm', 'peaceful', 'serene', 'atmospheric', 'dreamy', 'ethereal', 'floating']
    if any(word in description_lower for word in ambient_keywords):
        mood_analysis['energy'] = 0.2   # Very low energy
        mood_analysis['tempo_modifier'] = 0.7  # Much slower
        mood_analysis['detected_moods'].append('ambient')
    
    # Happy/upbeat keywords
    happy_keywords = ['happy', 'upbeat', 'joyful', 'energetic', 'excited', 'cheerful', 'bright', 'positive', 'bouncy']
    if any(word in description_lower for word in happy_keywords):
        mood_analysis['valence'] = 0.8  # Very happy
        mood_analysis['energy'] = 0.8   # High energy
        mood_analysis['tempo_modifier'] = 1.2  # Faster tempo
        mood_analysis['mode_override'] = 'major'  # Force major key
        mood_analysis['detected_moods'].append('happy')
    
    # Aggressive/intense keywords
    intense_keywords = ['aggressive', 'intense', 'driving', 'powerful', 'hard', 'heavy', 'strong', 'bold']
    if any(word in description_lower for word in intense_keywords):
        mood_analysis['energy'] = 0.9   # Very high energy
        mood_analysis['tempo_modifier'] = 1.1  # Slightly faster
        mood_analysis['detected_moods'].append('intense')
    
    # Romantic/soft keywords
    romantic_keywords = ['romantic', 'soft', 'gentle', 'tender', 'sweet', 'loving', 'warm', 'intimate']
    if any(word in description_lower for word in romantic_keywords):
        mood_analysis['valence'] = 0.7  # Pleasant
        mood_analysis['energy'] = 0.4   # Low-medium energy
        mood_analysis['tempo_modifier'] = 0.9  # Slightly slower
        mood_analysis['detected_moods'].append('romantic')
    
    return mood_analysis

def build_advanced_gpt_prompt(description, song, artist, musical_params, spotify_data=None):
    """Build an advanced prompt with comprehensive Spotify integration and mood analysis"""
    
    # Analyze user's mood keywords first
    user_mood = analyze_user_mood_keywords(description)
    
    # Override Spotify characteristics with user's explicit mood requirements
    if user_mood['detected_moods']:
        # User has explicit mood requirements - prioritize these over Spotify data
        if user_mood['mode_override']:
            musical_params['mode'] = user_mood['mode_override']
        
        # Override audio characteristics with mood-based values
        musical_params['user_energy'] = user_mood['energy']
        musical_params['user_valence'] = user_mood['valence']
        musical_params['tempo_modifier'] = user_mood['tempo_modifier']
        
        # Apply tempo modifier
        if 'tempo' in musical_params:
            musical_params['tempo'] = int(musical_params['tempo'] * user_mood['tempo_modifier'])
    
    prompt_parts = [
        "You are an expert music composer with deep understanding of musical emotion and mood. Your PRIMARY GOAL is to create a MIDI melody that PERFECTLY matches the user's emotional description.",
        "",
        "🎯 CRITICAL REQUIREMENT: The generated melody MUST reflect the emotional mood described by the user.",
        "",
        "CORE MUSICAL PARAMETERS:",
        f"- Key: {musical_params['key']} {musical_params['mode']}",
        f"- Tempo: {musical_params['tempo']} BPM",
        f"- Time Signature: {musical_params['time_signature'][0]}/{musical_params['time_signature'][1]}",
        f"- Duration: {musical_params['duration_bars']} bars",
        f"- Complexity: {musical_params['complexity']}",
        "",
        f"🎭 PRIMARY EMOTIONAL DIRECTION (MUST BE FOLLOWED):",
        f"- User's Emotional Description: '{description}'",
        f"- Detected Moods: {', '.join(user_mood['detected_moods']) if user_mood['detected_moods'] else 'neutral'}",
    ]
    
    if song:
        prompt_parts.append(f"- Reference Song: '{song}'")
    if artist:
        prompt_parts.append(f"- Reference Artist: '{artist}'")
    
    # Add comprehensive Spotify analysis
    if spotify_data and spotify_data.get('audio_features'):
        features = spotify_data['audio_features']
        prompt_parts.extend([
            "",
            "SPOTIFY AUDIO ANALYSIS (match these characteristics):",
            f"- Energy: {features.get('energy', 0.5):.2f} ({classify_energy_level(features.get('energy', 0.5))})",
            f"- Danceability: {features.get('danceability', 0.5):.2f} ({classify_danceability(features.get('danceability', 0.5))})",
            f"- Valence (Positivity): {features.get('valence', 0.5):.2f} ({classify_mood(features.get('valence', 0.5))})",
            f"- Acousticness: {features.get('acousticness', 0.5):.2f}",
            f"- Instrumentalness: {features.get('instrumentalness', 0.1):.2f}",
            f"- Loudness: {features.get('loudness', -10.0):.1f} dB",
            f"- Genre Influence: {classify_genre_influence(features)}"
        ])
    
    # Add structural information
    if musical_params.get('structure_info'):
        prompt_parts.extend([
            "",
            "STRUCTURAL GUIDANCE (from original song):",
            f"- Use analyzed sections from the reference track",
            f"- Match the rhythmic confidence patterns where possible"
        ])
    
    # USER MOOD OVERRIDES - These take priority over Spotify data
    if user_mood['detected_moods']:
        prompt_parts.extend([
            "",
            "⚠️  CRITICAL USER MOOD OVERRIDES (MUST FOLLOW THESE FIRST):",
        ])
        
        if 'sad' in user_mood['detected_moods']:
            prompt_parts.extend([
                "- SAD/MELANCHOLIC MOOD REQUIRED:",
                "  * Use ONLY minor scales and dark chord progressions",
                "  * Descending melodic lines and low-register notes",
                "  * Slow, sustained note durations (half notes, whole notes)",
                "  * Low velocities (30-60) for somber expression",
                "  * Avoid bright, ascending patterns",
                "  * Create sense of longing and melancholy"
            ])
        
        if 'ambient' in user_mood['detected_moods']:
            prompt_parts.extend([
                "- AMBIENT/ATMOSPHERIC MOOD REQUIRED:",
                "  * Very slow, floating rhythms with long note values",
                "  * Sparse, spacious melodic patterns",
                "  * Gentle, ethereal note choices",
                "  * Low energy, meditative feeling",
                "  * Avoid rhythmic drive or aggressive patterns",
                "  * Create dreamy, otherworldly atmosphere"
            ])
        
        if 'happy' in user_mood['detected_moods']:
            prompt_parts.extend([
                "- HAPPY/UPBEAT MOOD REQUIRED:",
                "  * Use major scales and bright chord progressions",
                "  * Ascending melodic lines and higher register",
                "  * Bouncy rhythms with clear beat emphasis",
                "  * Higher velocities (80-110) for energy",
                "  * Positive, uplifting melodic contours"
            ])
        
        if 'intense' in user_mood['detected_moods']:
            prompt_parts.extend([
                "- INTENSE/AGGRESSIVE MOOD REQUIRED:",
                "  * Strong rhythmic emphasis and driving patterns",
                "  * Higher velocities (90-127) for power",
                "  * Bold melodic intervals and dynamic contrasts",
                "  * Percussive, accented note delivery"
            ])
    
    # Advanced composition guidelines based on Spotify data (secondary to user mood)
    if spotify_data:
        features = spotify_data.get('audio_features', {})
        energy = features.get('energy', 0.5)
        danceability = features.get('danceability', 0.5)
        valence = features.get('valence', 0.5)
        
        # Only add Spotify guidelines if they don't conflict with user mood
        prompt_parts.extend([
            "",
            "ADDITIONAL SPOTIFY ANALYSIS (secondary to user mood):",
        ])
        
        # Use user mood values if available, otherwise Spotify values
        effective_energy = user_mood.get('energy', energy)
        effective_valence = user_mood.get('valence', valence)
        
        if effective_energy > 0.7:
            prompt_parts.append("- High energy: Use driving rhythms, frequent chord changes, dynamic note patterns")
        elif effective_energy < 0.3:
            prompt_parts.append("- Low energy: Use sustained notes, slower harmonic rhythm, gentle melodic contours")
        
        if danceability > 0.6 and 'ambient' not in user_mood.get('detected_moods', []):
            prompt_parts.append("- High danceability: Emphasize beat 1 and 3, use syncopated rhythms, clear pulse")
        
        if effective_valence > 0.6 and 'sad' not in user_mood.get('detected_moods', []):
            prompt_parts.append("- Positive mood: Use major scales, ascending melodies, bright chord tones")
        elif effective_valence < 0.4:
            prompt_parts.append("- Melancholic mood: Use minor scales, descending melodies, tension and resolution")
        
        if features.get('acousticness', 0) > 0.5:
            prompt_parts.append("- Acoustic influence: Use natural intervals, avoid excessive chromaticism")
    
    complexity_guidelines = {
        'simple': 'Simple rhythms (quarters, halves), stepwise motion, basic chord tones',
        'medium': 'Mixed rhythms including eighths, some leaps, chord tones with passing notes',
        'complex': 'Complex rhythms, syncopation, larger intervals, chromatic passages, extended harmonies'
    }
    
    prompt_parts.extend([
        f"- Complexity level: {complexity_guidelines[musical_params['complexity']]}",
        f"- Maintain musical coherence while reflecting '{description}' mood",
        "",
        "OUTPUT FORMAT:",
        "Generate the melody as a sequence of notes with precise timing and dynamics:",
        "Bar 1: C4(quarter,80) D4(eighth,75) E4(quarter,82) F4(quarter,78)",
        "Bar 2: G4(half,85) E4(quarter,80) C4(quarter,75)",
        "",
        "Note format: NoteName(duration,velocity)",
        "- NoteName: Note + octave (C4, F#5, Bb3)",
        "- Duration: whole, half, quarter, eighth, sixteenth, dotted-quarter, etc.",
        "- Velocity: 1-127 (match the energy and dynamics of the reference)",
        "",
        f"Generate exactly {musical_params['duration_bars']} bars of music that authentically captures the essence of the reference track."
    ])
    
    return "\n".join(prompt_parts)

@app.route('/static/generated/<filename>')
def serve_generated_file(filename):
    """Serve generated MIDI files"""
    try:
        return send_from_directory('static/generated', filename)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

@app.route('/analyze-track/<track_id>', methods=['GET'])
def analyze_track(track_id):
    """Get detailed Spotify analysis for a specific track"""
    try:
        analysis = spotify_client.get_comprehensive_track_data_by_id(track_id)
        
        if analysis:
            return jsonify({
                'success': True,
                'analysis': analysis
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Track not found or analysis unavailable'
            }), 404
            
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Check for required environment variables
    required_vars = ['SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Cannot start server without proper configuration.")
        exit(1)
    
    logger.info("Starting MIDIGPT Flask server with advanced Spotify integration...")
    
    # Suppress Flask development server warning by setting logging level
    import sys
    if not sys.stderr.isatty():
        # Suppress Werkzeug warnings in production-like environments
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.ERROR)
    
    app.run(debug=False, host='127.0.0.1', port=5000)
