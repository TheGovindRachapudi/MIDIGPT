import requests
import json
import os
import re
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from music21 import stream, note, duration, tempo, key, meter, pitch
import mido

logger = logging.getLogger(__name__)

class MIDIGenerator:
    """
    Advanced MIDI generator that uses OpenAI GPT-4 with Spotify-informed musical parameters
    """
    
    def __init__(self):
        """Initialize the MIDI generator with OpenAI API"""
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.openai_api_key:
            logger.warning("OpenAI API key not found. MIDI generation will be limited.")
            self.client = None
            return
        
        # Test the API key by making a simple request
        try:
            self._test_openai_api()
            self.client = True  # Use as a flag that API is available
            logger.info("MIDI Generator initialized with OpenAI integration")
        except Exception as e:
            logger.error(f"Failed to connect to OpenAI API: {str(e)}")
            self.client = None
    
    def generate_from_gpt_with_spotify(
        self, 
        prompt: str, 
        output_path: str, 
        musical_params: Dict,
        spotify_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Extract and replicate the actual melody from the song using Spotify data
        
        Args:
            prompt: The detailed prompt for GPT-4 (now used for melody extraction)
            output_path: Path to save the MIDI file
            musical_params: Musical parameters from Spotify
            spotify_data: Spotify analysis data for melody extraction
            
        Returns:
            Dictionary with generation results and metadata
        """
        start_time = time.time()
        
        try:
            # Extract the actual melody from Spotify data instead of generating new ones
            notes = self._extract_melody_from_spotify_data(musical_params, spotify_data)
            
            if not notes:
                # Fallback to AI generation only if melody extraction completely fails
                logger.warning("Could not extract melody from Spotify data, falling back to AI generation")
                melody_data = self._generate_melody_with_gpt(prompt, musical_params, spotify_data)
                if melody_data:
                    notes = self._parse_gpt_melody_response(melody_data, musical_params)
            
            if not notes:
                return {
                    'success': False,
                    'error': 'Failed to extract melody from song data',
                    'generation_time': time.time() - start_time
                }
            
            # Create MIDI file with the extracted melody
            midi_created = self._create_enhanced_midi_file(
                notes, 
                output_path, 
                musical_params, 
                spotify_data
            )
            
            if midi_created:
                generation_time = time.time() - start_time
                return {
                    'success': True,
                    'notes_count': len(notes),
                    'generation_time': generation_time,
                    'extraction_method': 'spotify_data' if spotify_data else 'fallback_ai',
                    'musical_enhancements': self._get_applied_enhancements(spotify_data),
                    'file_path': output_path
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create MIDI file',
                    'generation_time': time.time() - start_time
                }
                
        except Exception as e:
            logger.error(f"Error in MIDI generation: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'generation_time': time.time() - start_time
            }
    
    def _generate_melody_with_gpt(
        self, 
        prompt: str, 
        musical_params: Dict,
        spotify_data: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Use GPT-4 to generate a melody based on the comprehensive prompt
        
        Args:
            prompt: Detailed musical prompt
            musical_params: Musical parameters including Spotify data
            spotify_data: Optional Spotify analysis for context
            
        Returns:
            GPT-4 response with melody data
        """
        if not self.client:
            logger.warning("OpenAI client not available, using fallback generation")
            return self._generate_fallback_melody(musical_params)
        
        try:
            # Enhance prompt with additional context if Spotify data is available
            enhanced_prompt = self._enhance_prompt_with_spotify_context(prompt, spotify_data)
            
            # Make direct API request (now only used as fallback)
            response = self._make_openai_request(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a professional music composer with expertise in MIDI composition, music theory, and melody extraction. When song data is unavailable, create melodies that authentically capture the musical characteristics and style of the reference track."
                    },
                    {
                        "role": "user", 
                        "content": enhanced_prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.7,  # Slightly lower for more consistency
                top_p=0.9
            )
            
            if response and response.get('choices') and response['choices'][0].get('message'):
                melody_text = response['choices'][0]['message']['content'].strip()
                logger.info(f"GPT-4 generated melody: {melody_text[:200]}...")
                return melody_text
            else:
                logger.error("Empty response from GPT-4")
                return None
                
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            return self._generate_fallback_melody(musical_params)
    
    def _enhance_prompt_with_spotify_context(
        self, 
        base_prompt: str, 
        spotify_data: Optional[Dict]
    ) -> str:
        """
        Enhance the base prompt with additional Spotify-derived context
        """
        if not spotify_data:
            return base_prompt
        
        enhancements = [base_prompt, "", "ADDITIONAL SPOTIFY INSIGHTS:"]
        
        # Add structural insights
        audio_analysis = spotify_data.get('audio_analysis', {})
        structure = audio_analysis.get('structure', {})
        
        if structure:
            enhancements.append(f"- Song has {structure.get('total_sections', 0)} distinct sections")
            
            if structure.get('key_changes'):
                enhancements.append(f"- Original contains {len(structure['key_changes'])} key changes")
                
            if structure.get('tempo_changes'):
                enhancements.append(f"- Original has {len(structure['tempo_changes'])} tempo variations")
        
        # Add rhythmic insights
        rhythmic = audio_analysis.get('rhythmic_patterns', {})
        if rhythmic:
            complexity = rhythmic.get('rhythmic_complexity', 'medium')
            enhancements.append(f"- Rhythmic complexity: {complexity}")
            
            if rhythmic.get('beat_strength_pattern'):
                avg_strength = sum(rhythmic['beat_strength_pattern']) / len(rhythmic['beat_strength_pattern'])
                if avg_strength > 0.8:
                    enhancements.append("- Strong, consistent beat pattern")
                elif avg_strength < 0.6:
                    enhancements.append("- Complex, syncopated rhythm")
        
        # Add harmonic insights
        harmonic = audio_analysis.get('harmonic_content', {})
        if harmonic:
            stability = harmonic.get('key_stability', 'stable')
            enhancements.append(f"- Harmonic stability: {stability}")
            
            modal_chars = harmonic.get('modal_characteristics', [])
            if modal_chars:
                enhancements.append(f"- Modal character: {', '.join(modal_chars)}")
        
        # Add performance insights
        musical_insights = spotify_data.get('musical_insights', {})
        if musical_insights:
            perf_chars = musical_insights.get('performance_characteristics', {})
            if perf_chars.get('live_feel'):
                enhancements.append("- Incorporate live performance energy")
            if perf_chars.get('vocal_presence'):
                enhancements.append("- Design melody with vocal-like phrasing")
            if perf_chars.get('instrumental_focus'):
                enhancements.append("- Focus on instrumental melodic development")
        
        enhancements.append("")
        enhancements.append("Use these insights to make your generated melody more authentic to the reference track's characteristics.")
        
        return "\n".join(enhancements)
    
    def _parse_gpt_melody_response(
        self, 
        gpt_response: str, 
        musical_params: Dict
    ) -> List[Dict]:
        """
        Parse GPT-4 response into structured note data
        
        Args:
            gpt_response: Raw text response from GPT-4
            musical_params: Musical parameters for context
            
        Returns:
            List of note dictionaries with pitch, duration, velocity, and timing
        """
        notes = []
        current_bar = 1
        current_beat = 0
        
        # Enhanced regex pattern to match note formats
        note_patterns = [
            # Standard format: C4(quarter,80) - with optional whitespace
            r'([A-G][#b]?\d+)\s*\(\s*([^,)]+)\s*,\s*(\d+)\s*\)',
            # Alternative format: C4 quarter 80
            r'([A-G][#b]?\d+)\s+([a-zA-Z][a-zA-Z-]*[a-zA-Z])\s+(\d+)',
            # Simple format: C4-quarter-80
            r'([A-G][#b]?\d+)-([a-zA-Z][a-zA-Z-]*[a-zA-Z])-(\d+)',
            # Loose format: Note(duration,velocity) with more flexible spacing
            r'([A-G][#b]?\d+)\s*\(\s*([a-zA-Z][a-zA-Z-]*[a-zA-Z])\s*,\s*(\d+)\s*\)'
        ]
        
        # Split response into bars
        lines = gpt_response.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Check for bar markers and extract the bar number
            bar_match = re.search(r'Bar\s*(\d+)', line, re.IGNORECASE)
            if bar_match:
                current_bar = int(bar_match.group(1))
                current_beat = 0
                # Don't continue - process the rest of the line for notes after the bar marker
                # Remove the bar marker from the line so we can parse the notes
                line = re.sub(r'Bar\s*\d+\s*:\s*', '', line, flags=re.IGNORECASE)
            
            # Try to match notes with different patterns
            for pattern in note_patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                
                for match in matches:
                    note_name, duration_str, velocity_str = match
                    
                    try:
                        # Parse note information
                        note_info = {
                            'note': note_name.upper(),
                            'duration': self._parse_duration(duration_str.lower().strip()),
                            'velocity': max(1, min(127, int(velocity_str))),
                            'bar': current_bar,
                            'beat': current_beat
                        }
                        
                        # Validate note
                        if self._validate_note(note_info, musical_params):
                            notes.append(note_info)
                            current_beat += note_info['duration']
                        
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Failed to parse note: {match} - {str(e)}")
                        continue
        
        # If no notes were parsed, generate a fallback melody
        if not notes:
            logger.warning(f"No notes parsed from GPT response. Response was: {gpt_response[:500]}...")
            logger.warning("Generating fallback melody")
            notes = self._generate_fallback_melody_notes(musical_params)
        else:
            logger.info(f"Successfully parsed {len(notes)} notes from GPT response")
        
        # Apply Spotify-informed enhancements to the notes
        if notes and musical_params:
            notes = self._apply_spotify_enhancements_to_notes(notes, musical_params)
        
        return notes
    
    def _parse_duration(self, duration_str: str) -> float:
        """
        Parse duration string into beat values
        
        Args:
            duration_str: Duration description (e.g., "quarter", "eighth", "half")
            
        Returns:
            Duration in beats (quarter note = 1.0)
        """
        duration_mapping = {
            'whole': 4.0,
            'half': 2.0,
            'quarter': 1.0,
            'eighth': 0.5,
            'sixteenth': 0.25,
            'thirty-second': 0.125,
            'dotted-whole': 6.0,
            'dotted-half': 3.0,
            'dotted-quarter': 1.5,
            'dotted-eighth': 0.75,
            'triplet-quarter': 0.667,
            'triplet-eighth': 0.333
        }
        
        # Handle dotted notes
        if 'dotted' in duration_str:
            base_duration = duration_str.replace('dotted-', '').replace('dotted', '').strip()
            base_value = duration_mapping.get(base_duration, 1.0)
            return base_value * 1.5
        
        # Handle triplets
        if 'triplet' in duration_str:
            base_duration = duration_str.replace('triplet-', '').replace('triplet', '').strip()
            base_value = duration_mapping.get(base_duration, 1.0)
            return base_value * (2.0 / 3.0)
        
        return duration_mapping.get(duration_str, 1.0)
    
    def _validate_note(self, note_info: Dict, musical_params: Dict) -> bool:
        """
        Validate that a note makes sense given the musical parameters and is in the correct scale
        
        Args:
            note_info: Note information dictionary
            musical_params: Musical parameters including key, mode, etc.
            
        Returns:
            True if note is valid and in scale, False otherwise
        """
        try:
            # Basic validation
            if not note_info.get('note') or note_info.get('duration', 0) <= 0:
                return False
            
            # Validate velocity
            velocity = note_info.get('velocity', 64)
            if velocity < 1 or velocity > 127:
                return False
            
            # Validate note name format
            note_pattern = r'^[A-G][#b]?\d+$'
            if not re.match(note_pattern, note_info['note']):
                return False
            
            # Validate octave range (typically MIDI supports 0-10)
            octave = int(note_info['note'][-1])
            if octave < 0 or octave > 10:
                return False
            
            # CRITICAL: Validate that note is in the scale
            note_name_only = note_info['note'][:-1]  # Remove octave
            key_name = musical_params.get('key', 'C')
            mode_name = musical_params.get('mode', 'major')
            scale_notes = self._get_scale_notes(key_name, mode_name)
            
            if note_name_only not in scale_notes:
                logger.warning(f"Note {note_name_only} not in scale {key_name} {mode_name}, rejecting")
                return False
            
            return True
            
        except (ValueError, KeyError):
            return False
    
    def _apply_spotify_enhancements_to_notes(
        self, 
        notes: List[Dict], 
        musical_params: Dict
    ) -> List[Dict]:
        """
        Apply mood-aware enhancements to the generated notes with user mood priority
        
        Args:
            notes: List of note dictionaries
            musical_params: Musical parameters with user mood overrides and Spotify insights
            
        Returns:
            Enhanced list of notes with proper mood characteristics
        """
        enhanced_notes = []
        
        # Prioritize user mood characteristics over Spotify data
        energy = musical_params.get('user_energy', musical_params.get('energy', 0.5))
        valence = musical_params.get('user_valence', musical_params.get('valence', 0.5))
        danceability = musical_params.get('danceability', 0.5)
        loudness = musical_params.get('loudness', -10.0)
        
        logger.info(f"Applying mood enhancements - Energy: {energy}, Valence: {valence}, Danceability: {danceability}")
        
        for i, note in enumerate(notes):
            enhanced_note = note.copy()
            
            # Adjust velocity based on energy and loudness
            base_velocity = note['velocity']
            
            # Energy influence (0.8-1.2 multiplier)
            energy_multiplier = 0.8 + (energy * 0.4)
            
            # Loudness influence (louder tracks get higher velocities)
            loudness_multiplier = 1.0 + min(0.3, (loudness + 20) / 40)
            
            # Apply velocity adjustments
            enhanced_velocity = int(base_velocity * energy_multiplier * loudness_multiplier)
            enhanced_note['velocity'] = max(20, min(127, enhanced_velocity))
            
            # Add swing/groove based on danceability
            if danceability > 0.6:
                # Add subtle timing variations for groove
                if i % 2 == 1:  # Slightly delay every other note
                    enhanced_note['timing_offset'] = 0.05 * danceability
                else:
                    enhanced_note['timing_offset'] = 0.0
            else:
                enhanced_note['timing_offset'] = 0.0
            
            # Add expression based on valence (mood)
            if valence > 0.7:
                # Happy music - add slight velocity variations for bounce
                enhanced_note['velocity'] += int((i % 4 - 2) * 5 * valence)
                enhanced_note['velocity'] = max(20, min(127, enhanced_note['velocity']))
            elif valence < 0.3:
                # Sad music - slightly reduce and smooth velocities
                enhanced_note['velocity'] = int(enhanced_note['velocity'] * (0.8 + valence * 0.2))
                enhanced_note['velocity'] = max(15, enhanced_note['velocity'])
            
            enhanced_notes.append(enhanced_note)
        
        return enhanced_notes
    
    def _create_enhanced_midi_file(
        self, 
        notes: List[Dict], 
        output_path: str,
        musical_params: Dict,
        spotify_data: Optional[Dict] = None
    ) -> bool:
        """
        Create MIDI file with enhanced musical characteristics from Spotify data
        
        Args:
            notes: List of note dictionaries
            output_path: Path to save the MIDI file  
            musical_params: Musical parameters
            spotify_data: Optional Spotify data for enhancements
            
        Returns:
            True if file was created successfully, False otherwise
        """
        try:
            # Create music21 stream
            score = stream.Stream()
            
            # Set time signature
            time_sig = musical_params.get('time_signature', [4, 4])
            score.append(meter.TimeSignature(f"{time_sig[0]}/{time_sig[1]}"))
            
            # Set key signature
            key_name = musical_params.get('key', 'C')
            mode_name = musical_params.get('mode', 'major')
            score.append(key.Key(key_name, mode_name))
            
            # Set tempo
            tempo_bpm = musical_params.get('tempo', 120)
            score.append(tempo.TempoIndication(number=tempo_bpm))
            
            # Add chord accompaniment if we have Spotify data (inspired by custom MIDI generation)
            if spotify_data:
                chord_track = self._create_chord_accompaniment(musical_params, spotify_data)
                if chord_track:
                    for chord in chord_track:
                        score.append(chord)
            
            # Add melody notes to the score
            for note_info in notes:
                try:
                    # Create note
                    n = note.Note(note_info['note'])
                    n.quarterLength = note_info['duration']
                    n.volume.velocity = note_info['velocity']
                    
                    # Apply timing offset if present (for groove)
                    if 'timing_offset' in note_info and note_info['timing_offset'] != 0:
                        n.offset += note_info['timing_offset']
                    
                    score.append(n)
                    
                except Exception as e:
                    logger.warning(f"Failed to create note {note_info}: {str(e)}")
                    continue
            
            # Apply additional Spotify-informed enhancements to the score
            if spotify_data:
                score = self._apply_score_enhancements(score, spotify_data, musical_params)
            
            # Write MIDI file
            score.write('midi', fp=output_path)
            logger.info(f"MIDI file created successfully: {output_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating MIDI file: {str(e)}")
            return False
    
    def _apply_score_enhancements(
        self, 
        score: stream.Stream, 
        spotify_data: Dict,
        musical_params: Dict
    ) -> stream.Stream:
        """
        Apply additional enhancements to the music21 score based on Spotify data
        
        Args:
            score: music21 Stream object
            spotify_data: Spotify analysis data
            musical_params: Musical parameters
            
        Returns:
            Enhanced Stream object
        """
        try:
            # Get audio features
            audio_features = spotify_data.get('audio_features', {})
            
            # Apply tempo variations if original track has tempo changes
            audio_analysis = spotify_data.get('audio_analysis', {})
            structure = audio_analysis.get('structure', {})
            
            if structure.get('tempo_changes') and len(structure['tempo_changes']) > 0:
                # Add subtle tempo variations
                for i, element in enumerate(score.flat.notes):
                    if i % 8 == 0:  # Every 2 bars in 4/4
                        variation = 1.0 + (audio_features.get('energy', 0.5) - 0.5) * 0.1
                        element.quarterLength *= variation
            
            # Add dynamics based on loudness and energy
            loudness = audio_features.get('loudness', -10)
            energy = audio_features.get('energy', 0.5)
            
            for element in score.flat.notes:
                if hasattr(element, 'volume'):
                    # Adjust based on loudness (louder tracks get higher velocities)
                    loudness_factor = max(0.5, min(1.3, (loudness + 20) / 25))
                    element.volume.velocity = int(element.volume.velocity * loudness_factor)
                    element.volume.velocity = max(10, min(127, element.volume.velocity))
            
            return score
            
        except Exception as e:
            logger.error(f"Error applying score enhancements: {str(e)}")
            return score
    
    def _generate_fallback_melody(self, musical_params: Dict) -> str:
        """
        Generate a simple fallback melody when GPT-4 is not available
        
        Args:
            musical_params: Musical parameters
            
        Returns:
            Simple melody string in the expected format
        """
        key_name = musical_params.get('key', 'C')
        duration_bars = musical_params.get('duration_bars', 4)
        
        # Simple ascending/descending pattern
        notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'F4', 'E4', 'D4']
        melody_parts = []
        
        for bar in range(1, duration_bars + 1):
            bar_notes = []
            for i in range(4):  # 4 quarter notes per bar
                note_idx = (bar * 4 + i) % len(notes)
                velocity = 80 if i % 2 == 0 else 70  # Slight accent pattern
                bar_notes.append(f"{notes[note_idx]}(quarter,{velocity})")
            
            melody_parts.append(f"Bar {bar}: {' '.join(bar_notes)}")
        
        return "\n".join(melody_parts)
    
    def _generate_fallback_melody_notes(self, musical_params: Dict) -> List[Dict]:
        """
        Generate fallback melody notes when parsing fails
        
        Args:
            musical_params: Musical parameters
            
        Returns:
            List of note dictionaries
        """
        notes = []
        key_name = musical_params.get('key', 'C')
        duration_bars = musical_params.get('duration_bars', 4)
        
        # Use proper scale notes for the key
        scale_note_names = self._get_scale_notes(key_name, musical_params.get('mode', 'major'))
        scale_notes = [f"{note}4" for note in scale_note_names]
        
        for bar in range(1, duration_bars + 1):
            for beat in range(4):  # 4 quarter notes per bar
                note_idx = ((bar - 1) * 4 + beat) % len(scale_notes)
                notes.append({
                    'note': scale_notes[note_idx],
                    'duration': 1.0,  # Quarter note
                    'velocity': 80 if beat % 2 == 0 else 65,  # Accent pattern
                    'bar': bar,
                    'beat': beat
                })
        
        return notes
    
    def _test_openai_api(self) -> bool:
        """
        Test the OpenAI API connection with a simple request
        
        Returns:
            True if API is working, False otherwise
        """
        try:
            response = self._make_openai_request(
                model="gpt-4",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return response is not None
        except Exception as e:
            logger.error(f"OpenAI API test failed: {str(e)}")
            return False
    
    def _make_openai_request(
        self, 
        model: str,
        messages: List[Dict], 
        max_tokens: int = 1500,
        temperature: float = 0.8,
        top_p: float = 0.9
    ) -> Optional[Dict]:
        """
        Make a direct request to OpenAI API using requests
        
        Args:
            model: GPT model to use
            messages: List of message dictionaries
            max_tokens: Maximum tokens in response
            temperature: Randomness control
            top_p: Nucleus sampling parameter
            
        Returns:
            API response dictionary or None if failed
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': model,
                'messages': messages,
                'max_tokens': max_tokens,
                'temperature': temperature,
                'top_p': top_p
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Request to OpenAI API failed: {str(e)}")
            return None
    
    def _get_applied_enhancements(self, spotify_data: Optional[Dict]) -> List[str]:
        """
        Get list of enhancements applied based on Spotify data
        
        Args:
            spotify_data: Spotify analysis data
            
        Returns:
            List of applied enhancement descriptions
        """
        enhancements = []
        
        if not spotify_data:
            return ["Basic MIDI generation without Spotify enhancements"]
        
        audio_features = spotify_data.get('audio_features', {})
        
        if audio_features.get('energy', 0) > 0.7:
            enhancements.append("High-energy velocity adjustments")
        
        if audio_features.get('danceability', 0) > 0.6:
            enhancements.append("Groove timing variations")
        
        if audio_features.get('valence', 0) > 0.7:
            enhancements.append("Positive mood expression")
        elif audio_features.get('valence', 0) < 0.3:
            enhancements.append("Melancholic mood expression")
        
        structure = spotify_data.get('audio_analysis', {}).get('structure', {})
        if structure.get('tempo_changes'):
            enhancements.append("Tempo variation patterns")
        
        if structure.get('key_changes'):
            enhancements.append("Harmonic progression insights")
        
        return enhancements or ["Standard Spotify-informed generation"]
    
    def _extract_melody_from_spotify_data(
        self, 
        musical_params: Dict, 
        spotify_data: Optional[Dict]
    ) -> List[Dict]:
        """
        Extract and intelligently compose melody using Spotify data + AI musical intelligence
        
        Args:
            musical_params: Musical parameters from Spotify
            spotify_data: Spotify analysis data with timing and pitch information
            
        Returns:
            List of note dictionaries representing the AI-enhanced extracted melody
        """
        if not spotify_data:
            logger.warning("No Spotify data available for melody extraction")
            return self._generate_intelligent_fallback_melody(musical_params)
        
        logger.info("Creating AI-enhanced melody from Spotify audio analysis data")
        
        try:
            # Use user-specified key/mode if provided, otherwise use Spotify detection
            user_key = musical_params.get('key')
            user_mode = musical_params.get('mode')
            
            if user_key and user_mode:
                key_name = user_key
                mode_name = user_mode
                logger.info(f"Using user-specified key: {key_name} {mode_name}")
            else:
                # Fallback to Spotify detection
                audio_features = spotify_data.get('audio_features', {})
                key_num = audio_features.get('key', 0)  # 0 = C, 1 = C#, 2 = D, etc.
                mode = audio_features.get('mode', 1)  # 1 = major, 0 = minor
                
                # Map Spotify key number to note name
                key_mapping = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                key_name = key_mapping[key_num] if 0 <= key_num < 12 else 'C'
                mode_name = 'major' if mode == 1 else 'minor'
                logger.info(f"Using Spotify-detected key: {key_name} {mode_name}")
            
            tempo = spotify_data.get('audio_features', {}).get('tempo', musical_params.get('tempo', 120))
            logger.info(f"Final key: {key_name} {mode_name}, tempo: {tempo} BPM")
            
            # Get scale notes and chord progressions for the final key
            scale_notes = self._get_scale_notes(key_name, mode_name)
            chord_progression = self._get_intelligent_chord_progression(key_name, mode_name, spotify_data)
            
            # Extract timing information from beats and bars
            audio_analysis = spotify_data.get('audio_analysis', {})
            raw_analysis = audio_analysis.get('raw_analysis', {})
            beats = raw_analysis.get('beats', [])
            bars = raw_analysis.get('bars', [])
            sections = raw_analysis.get('sections', [])
            
            # If we don't have detailed audio analysis, create a melody based on the song's characteristics
            if not beats or not bars:
                logger.info("No detailed audio analysis available, generating melody based on song characteristics")
                return self._generate_characteristic_melody(musical_params, scale_notes, key_name, mode_name, tempo)
            
            # Extract melody from the first 8-16 bars worth of data
            duration_bars = min(musical_params.get('duration_bars', 8), 16)
            melody_notes = []
            
            # Use the beat timing to create a realistic melody pattern
            beats_to_use = beats[:min(len(beats), duration_bars * 4)]  # 4 beats per bar typically
            
            for i, beat in enumerate(beats_to_use):
                bar_number = (i // 4) + 1
                beat_in_bar = (i % 4)
                
                # Determine note based on position in song and musical characteristics
                note_choice = self._choose_melody_note(
                    i, bar_number, beat_in_bar, scale_notes, audio_features, sections
                )
                
                # Determine duration based on beat timing
                if i + 1 < len(beats_to_use):
                    duration = beats_to_use[i + 1]['start'] - beat['start']
                    # Convert to quarter note units (assuming 4/4 time)
                    duration_quarters = (duration * tempo) / 60.0
                    duration_quarters = max(0.25, min(2.0, duration_quarters))  # Clamp between sixteenth and half note
                else:
                    duration_quarters = 1.0  # Default quarter note
                
                # Determine velocity based on beat confidence and song energy
                base_velocity = 70
                confidence_boost = int(beat.get('confidence', 0.5) * 20)
                energy_boost = int(audio_features.get('energy', 0.5) * 30)
                velocity = min(127, max(30, base_velocity + confidence_boost + energy_boost))
                
                melody_notes.append({
                    'note': note_choice,
                    'duration': duration_quarters,
                    'velocity': velocity,
                    'bar': bar_number,
                    'beat': beat_in_bar,
                    'timing': beat.get('start', 0)
                })
                
                if bar_number >= duration_bars:
                    break
            
            logger.info(f"Extracted {len(melody_notes)} notes from Spotify audio analysis")
            return melody_notes
            
        except Exception as e:
            logger.error(f"Error extracting melody from Spotify data: {str(e)}")
            return []
    
    def _get_scale_notes(self, key_name: str, mode_name: str) -> List[str]:
        """
        Get the scale notes for a given key and mode
        
        Args:
            key_name: Root note name (C, D, E, etc.)
            mode_name: Mode name (major, minor)
            
        Returns:
            List of note names in the scale
        """
        # All chromatic notes
        chromatic = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # Get the starting index
        try:
            start_idx = chromatic.index(key_name)
        except ValueError:
            start_idx = 0  # Default to C
        
        # Scale patterns (semitone intervals)
        if mode_name.lower() == 'major':
            intervals = [0, 2, 4, 5, 7, 9, 11]  # Major scale
        else:
            intervals = [0, 2, 3, 5, 7, 8, 10]  # Natural minor scale
        
        # Build the scale
        scale = []
        for interval in intervals:
            note_idx = (start_idx + interval) % 12
            scale.append(chromatic[note_idx])
        
        return scale
    
    def _generate_characteristic_melody(
        self, 
        musical_params: Dict, 
        scale_notes: List[str], 
        key_name: str, 
        mode_name: str, 
        tempo: float
    ) -> List[Dict]:
        """
        Generate a melody that matches the song's characteristics when detailed analysis isn't available
        
        Args:
            musical_params: Musical parameters from Spotify
            scale_notes: Notes in the song's scale
            key_name: Key of the song
            mode_name: Mode of the song
            tempo: Tempo of the song
            
        Returns:
            List of note dictionaries
        """
        logger.info(f"Generating characteristic melody in {key_name} {mode_name}")
        
        notes = []
        duration_bars = musical_params.get('duration_bars', 8)
        energy = musical_params.get('energy', 0.5)
        valence = musical_params.get('valence', 0.5)
        danceability = musical_params.get('danceability', 0.5)
        
        # Add octave numbers to scale notes
        octave = 4 if energy > 0.6 else 3  # Higher energy = higher octave
        scale_with_octaves = [f"{note}{octave}" for note in scale_notes]
        
        # Add some notes from adjacent octaves for variety
        if octave == 4:
            scale_with_octaves.extend([f"{note}5" for note in scale_notes[:4]])  # Add higher notes
        else:
            scale_with_octaves.extend([f"{note}4" for note in scale_notes[:4]])  # Add higher notes
        
        for bar in range(1, duration_bars + 1):
            # Determine rhythm based on danceability
            if danceability > 0.7:
                # More syncopated rhythm
                durations = [0.5, 0.5, 1.0, 1.0]  # eighth, eighth, quarter, quarter
            elif danceability > 0.4:
                # Moderate rhythm
                durations = [1.0, 0.5, 1.0, 1.5]  # quarter, eighth, quarter, dotted quarter
            else:
                # Simpler rhythm
                durations = [1.0, 1.0, 2.0]  # quarter, quarter, half
            
            beat_pos = 0
            for i, dur in enumerate(durations):
                if beat_pos >= 4.0:  # Don't exceed 4 beats per bar
                    break
                
                # Choose note based on position and characteristics
                if bar == 1 and i == 0:
                    # Start on the root note
                    note_idx = 0
                elif valence > 0.6:
                    # Happy songs tend to move upward
                    note_idx = (i + bar + 2) % len(scale_with_octaves)
                elif valence < 0.4:
                    # Sad songs tend to move downward or stay low
                    note_idx = max(0, (len(scale_with_octaves) - i - bar) % len(scale_with_octaves))
                else:
                    # Neutral songs move in patterns
                    note_idx = ((bar - 1) * 2 + i) % len(scale_with_octaves)
                
                # Determine velocity based on energy
                base_velocity = 60 if energy < 0.4 else 80 if energy < 0.7 else 100
                velocity_variation = int((i % 4 - 2) * 10)  # Add some variation
                velocity = max(30, min(127, base_velocity + velocity_variation))
                
                notes.append({
                    'note': scale_with_octaves[note_idx],
                    'duration': min(dur, 4.0 - beat_pos),  # Don't exceed bar length
                    'velocity': velocity,
                    'bar': bar,
                    'beat': beat_pos
                })
                
                beat_pos += dur
        
        logger.info(f"Generated characteristic melody with {len(notes)} notes")
        return notes
    
    def _choose_melody_note(
        self, 
        beat_index: int, 
        bar_number: int, 
        beat_in_bar: int, 
        scale_notes: List[str], 
        audio_features: Dict,
        sections: List[Dict]
    ) -> str:
        """
        Choose an appropriate melody note based on position and musical characteristics
        
        Args:
            beat_index: Overall beat index
            bar_number: Current bar number
            beat_in_bar: Beat position within the bar (0-3)
            scale_notes: Available scale notes
            audio_features: Spotify audio features
            sections: Song sections from analysis
            
        Returns:
            Note name with octave
        """
        energy = audio_features.get('energy', 0.5)
        valence = audio_features.get('valence', 0.5)
        danceability = audio_features.get('danceability', 0.5)
        
        # Determine base octave based on energy
        base_octave = 4 if energy > 0.5 else 3
        
        # Choose scale degree based on various factors
        if beat_in_bar == 0:  # Downbeat - favor stable notes
            scale_degree = [0, 2, 4][beat_index % 3]  # Root, third, fifth
        elif valence > 0.6:  # Happy music - upward movement
            scale_degree = (beat_index + bar_number) % len(scale_notes)
        elif valence < 0.4:  # Sad music - downward movement or lower notes
            scale_degree = max(0, (len(scale_notes) - beat_index + bar_number) % len(scale_notes))
        else:  # Neutral - stepwise movement
            scale_degree = (beat_index + (bar_number - 1) * 2) % len(scale_notes)
        
        # Add some variation based on danceability
        if danceability > 0.7 and beat_in_bar % 2 == 1:
            scale_degree = (scale_degree + 2) % len(scale_notes)  # Add syncopation
        
        note_name = scale_notes[scale_degree]
        
        # Vary octave based on position and energy
        if energy > 0.7 and bar_number > 4:
            octave = base_octave + 1  # Go higher in energetic songs
        elif energy < 0.3:
            octave = base_octave - 1 if base_octave > 2 else base_octave  # Stay lower in low energy
        else:
            octave = base_octave
        
        return f"{note_name}{octave}"
    
    def _get_intelligent_chord_progression(self, key_name: str, mode_name: str, spotify_data: Dict) -> List[str]:
        """
        Generate intelligent chord progressions using only scale notes (diatonic chords)
        Ensures all chord roots are within the specified key/scale
        
        Args:
            key_name: Root note of the key
            mode_name: major or minor mode
            spotify_data: Spotify analysis data for context
            
        Returns:
            List of chord root notes for the progression (all in scale)
        """
        audio_features = spotify_data.get('audio_features', {})
        energy = audio_features.get('energy', 0.5)
        valence = audio_features.get('valence', 0.5)
        danceability = audio_features.get('danceability', 0.5)
        
        # Get scale notes (these are the only valid chord roots)
        scale_notes = self._get_scale_notes(key_name, mode_name)
        
        # Define chord progressions using scale degrees (1-indexed)
        if mode_name.lower() == 'major':
            # Major key diatonic chord progressions
            if energy > 0.7 and danceability > 0.6:
                # High energy, danceable - I-V-vi-IV (C-G-Am-F in C major)
                scale_degrees = [1, 5, 6, 4]  
            elif valence > 0.6:
                # Happy major - I-vi-IV-V (C-Am-F-G in C major)
                scale_degrees = [1, 6, 4, 5]
            else:
                # Standard major progression - I-IV-vi-V (C-F-Am-G in C major)
                scale_degrees = [1, 4, 6, 5]
        else:
            # Minor key diatonic chord progressions
            if energy > 0.7:
                # High energy minor - i-VII-VI-VII (Am-G-F-G in A minor)
                scale_degrees = [1, 7, 6, 7]
            elif valence < 0.4:
                # Sad minor - i-VI-III-VII (Am-F-C-G in A minor)
                scale_degrees = [1, 6, 3, 7]
            else:
                # Standard minor progression - i-iv-V-i (Am-Dm-G-Am in A minor harmonic)
                scale_degrees = [1, 4, 5, 1]
        
        # Convert scale degrees to actual chord roots (ensuring they're in the scale)
        chord_roots = []
        for degree in scale_degrees:
            # Convert 1-indexed scale degree to 0-indexed array position
            scale_idx = (degree - 1) % len(scale_notes)
            chord_root = scale_notes[scale_idx]
            chord_roots.append(chord_root)
        
        logger.info(f"Generated DIATONIC chord progression for {key_name} {mode_name}: {chord_roots} (scale: {scale_notes})")
        return chord_roots
    
    def _generate_intelligent_fallback_melody(self, musical_params: Dict) -> List[Dict]:
        """
        Generate an intelligent fallback melody using musical theory principles
        Inspired by the custom MIDI generation approach with chord progressions and proper scales
        
        Args:
            musical_params: Musical parameters including key, mode, tempo, etc.
            
        Returns:
            List of note dictionaries representing an intelligent melody
        """
        logger.info("Generating intelligent fallback melody using musical theory")
        
        key_name = musical_params.get('key', 'C')
        mode_name = musical_params.get('mode', 'major')
        duration_bars = musical_params.get('duration_bars', 8)
        tempo = musical_params.get('tempo', 120)
        
        # Simulate Spotify characteristics for fallback
        energy = musical_params.get('energy', 0.6)  # Default to medium-high energy
        valence = musical_params.get('valence', 0.5)  # Neutral mood
        danceability = musical_params.get('danceability', 0.5)  # Medium danceability
        
        # Get scale notes and chord progression
        scale_notes = self._get_scale_notes(key_name, mode_name)
        chord_progression = self._get_intelligent_chord_progression(
            key_name, mode_name, 
            {'audio_features': {'energy': energy, 'valence': valence, 'danceability': danceability}}
        )
        
        notes = []
        chord_idx = 0
        
        # Create melody that follows chord progressions (like the custom example)
        for bar in range(1, duration_bars + 1):
            current_chord = chord_progression[chord_idx % len(chord_progression)]
            
            # Get chord tones for the current chord
            chord_tones = self._get_chord_tones(current_chord, key_name, mode_name)
            
            # Determine rhythm pattern based on characteristics
            if danceability > 0.7:
                # Danceable - more syncopated rhythm
                rhythm_pattern = [0.5, 0.5, 0.5, 0.5, 1.0, 1.0]  # More notes, syncopated
            elif energy > 0.7:
                # High energy - driving rhythm
                rhythm_pattern = [0.5, 0.5, 1.0, 1.0, 1.0]  # Energetic pattern
            else:
                # Standard rhythm
                rhythm_pattern = [1.0, 1.0, 1.0, 1.0]  # Quarter notes
            
            beat_pos = 0
            note_in_bar = 0
            
            for duration in rhythm_pattern:
                if beat_pos >= 4.0:  # Don't exceed 4 beats
                    break
                
                # Choose note intelligently
                if note_in_bar == 0:  # First note of bar - use chord tone
                    note_choice = self._choose_chord_tone(chord_tones, 0)  # Root of chord
                elif note_in_bar % 2 == 1:  # Accent beats - use chord tones
                    tone_idx = (note_in_bar // 2) % len(chord_tones)
                    note_choice = self._choose_chord_tone(chord_tones, tone_idx)
                else:  # Passing tones - use scale notes
                    scale_idx = (bar + note_in_bar) % len(scale_notes)
                    octave = 4 if energy > 0.5 else 3
                    note_choice = f"{scale_notes[scale_idx]}{octave}"
                
                # Determine velocity based on position and energy
                base_velocity = 70 if energy < 0.5 else 90
                if note_in_bar == 0:  # Downbeat accent
                    velocity = min(127, base_velocity + 15)
                else:
                    velocity = base_velocity + (note_in_bar % 3) * 5
                
                velocity = max(30, min(127, int(velocity)))
                
                notes.append({
                    'note': note_choice,
                    'duration': min(duration, 4.0 - beat_pos),
                    'velocity': velocity,
                    'bar': bar,
                    'beat': beat_pos
                })
                
                beat_pos += duration
                note_in_bar += 1
            
            # Move to next chord every 2 bars (or based on energy)
            if bar % (1 if energy > 0.8 else 2) == 0:
                chord_idx += 1
        
        logger.info(f"Generated intelligent fallback melody with {len(notes)} notes using chord progression")
        return notes
    
    def _get_chord_tones(self, chord_root: str, key_name: str, mode_name: str) -> List[str]:
        """
        Get the chord tones (triad) for a given root note, ensuring they are in the specified scale
        
        Args:
            chord_root: Root note of the chord
            key_name: Key of the song (for scale validation)
            mode_name: Mode (major/minor) to determine chord quality
            
        Returns:
            List of chord tone note names with octaves, all in the correct scale
        """
        # Get the scale notes for the key
        scale_notes = self._get_scale_notes(key_name, mode_name)
        
        # Find the chord root in the scale
        try:
            root_scale_idx = scale_notes.index(chord_root)
        except ValueError:
            # If chord root is not in scale, use the root of the key instead
            logger.warning(f"Chord root {chord_root} not in {key_name} {mode_name} scale, using key root")
            chord_root = key_name
            root_scale_idx = 0
        
        # Build triad using scale degrees (ensures all notes are in key)
        chord_tones = []
        octave = 4  # Default octave
        
        # Root, third (2 scale degrees up), fifth (4 scale degrees up)
        scale_intervals = [0, 2, 4]  # Scale degrees: 1st, 3rd, 5th
        
        for interval in scale_intervals:
            scale_idx = (root_scale_idx + interval) % len(scale_notes)
            note_name = scale_notes[scale_idx]
            chord_tones.append(f"{note_name}{octave}")
        
        logger.info(f"Generated in-key chord for {chord_root}: {chord_tones} (scale: {scale_notes})")
        return chord_tones
    
    def _choose_chord_tone(self, chord_tones: List[str], preference_idx: int) -> str:
        """
        Choose a chord tone with some intelligent variation
        
        Args:
            chord_tones: Available chord tones
            preference_idx: Preferred index (0 = root, 1 = third, 2 = fifth)
            
        Returns:
            Selected chord tone
        """
        if not chord_tones:
            return "C4"  # Fallback
        
        # Use preference but add some variation
        idx = preference_idx % len(chord_tones)
        return chord_tones[idx]
    
    def _create_chord_accompaniment(self, musical_params: Dict, spotify_data: Dict) -> List:
        """
        Create chord accompaniment similar to the custom MIDI generation approach
        
        Args:
            musical_params: Musical parameters including key, mode, tempo
            spotify_data: Spotify data for determining chord characteristics
            
        Returns:
            List of music21 Chord objects for accompaniment
        """
        from music21 import chord
        
        key_name = musical_params.get('key', 'C')
        mode_name = musical_params.get('mode', 'major')
        duration_bars = musical_params.get('duration_bars', 8)
        
        audio_features = spotify_data.get('audio_features', {})
        energy = audio_features.get('energy', 0.5)
        danceability = audio_features.get('danceability', 0.5)
        
        # Get intelligent chord progression
        chord_progression = self._get_intelligent_chord_progression(key_name, mode_name, spotify_data)
        
        chord_objects = []
        
        # Create chords for each progression step
        for bar in range(duration_bars):
            chord_root = chord_progression[bar % len(chord_progression)]
            
            # Get chord tones for this root
            chord_tones_raw = self._get_chord_tones(chord_root, key_name, mode_name)
            
            # Convert to lower octave for accompaniment (like the custom example)
            chord_tones_low = []
            for tone in chord_tones_raw:
                note_name = tone[:-1]  # Remove octave
                octave = 3 if energy > 0.6 else 2  # Lower octave for accompaniment
                chord_tones_low.append(f"{note_name}{octave}")
            
            # Create chord with appropriate duration and velocity
            if danceability > 0.6:
                # Danceable - shorter chord durations for rhythm
                chord_duration = 2.0  # Half note
            else:
                # Sustained chords
                chord_duration = 4.0  # Whole note
            
            chord_velocity = max(40, min(80, int(60 + energy * 20)))  # Softer than melody
            
            # Create the chord
            chord_obj = chord.Chord(chord_tones_low, quarterLength=chord_duration)
            
            # Set velocity for all notes in the chord
            for n in chord_obj.notes:
                n.volume.velocity = chord_velocity
            
            chord_objects.append(chord_obj)
            
            logger.info(f"Created chord {chord_root} {mode_name} for bar {bar + 1}: {chord_tones_low}")
        
        return chord_objects
