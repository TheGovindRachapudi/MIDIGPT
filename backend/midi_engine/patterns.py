"""
Pattern generators for ambient/sad MIDI music.

Generates melodies and chord progressions with proper timing and musicality.
"""

import random
from typing import List, Dict
from .theory import (
    get_scale_notes, get_color_tones, build_chord, voice_leading_chord,
    generate_progression_chords, soft_curve, humanize_ticks, humanize_velocity,
    create_sighing_contour
)


def generate_melody(seed: int, key: str = "C", mode: str = "minor", 
                   bpm: int = 72, bars: int = 8, density: float = 0.35, 
                   contour: str = "sigh") -> List[Dict]:
    """
    Generate a sparse, ambient melody with long tones and gaps.
    
    Args:
        seed: Random seed for reproducibility
        key: Root key (e.g., 'C', 'F#') 
        mode: Scale mode ('minor', 'major')
        bpm: Beats per minute
        bars: Number of bars to generate
        density: Note density (0.0-1.0), lower = more sparse
        contour: Melodic shape ('sigh', 'linear', 'arch')
    
    Returns:
        List of note events: {start, end, note, vel_on, vel_off} in ticks
    """
    random.seed(seed)
    ppq = 480  # Pulses per quarter note
    ticks_per_bar = ppq * 4
    total_ticks = bars * ticks_per_bar
    
    # Get scale and color tones
    scale_notes = get_scale_notes(key, mode, 4)  # Octave 4
    scale_notes.extend(get_scale_notes(key, mode, 5))  # Add octave 5
    color_tones = get_color_tones(key, mode)
    
    # Combine scale and color tones, emphasize tonic/third/fifth
    available_notes = scale_notes + color_tones
    
    # Favor certain scale degrees (tonic, minor 3rd, 5th, 7th, 9th)
    root_midi = scale_notes[0]
    emphasized_notes = [
        root_midi,      # Tonic
        root_midi + 3,  # Minor 3rd  
        root_midi + 7,  # Perfect 5th
        root_midi + 10, # Minor 7th
        root_midi + 2,  # 9th (major 2nd)
        root_midi + 12, # Octave
    ]
    
    # Weight the note selection
    weighted_notes = emphasized_notes * 3 + available_notes
    
    events = []
    current_tick = 0
    
    # Calculate approximate number of notes based on density
    max_possible_notes = bars * 4  # 4 quarter notes per bar max
    target_notes = int(max_possible_notes * density)
    
    for note_idx in range(target_notes):
        # Skip some opportunities to create gaps
        if random.random() > density:
            continue
        
        # Choose note duration (long tones for ambient feel)
        duration_choices = [
            ppq * 2,      # Half note
            ppq * 3,      # Dotted half
            ppq * 4,      # Whole note
            int(ppq * 1.5),  # Dotted quarter
            ppq * 6,      # Whole + half
        ]
        duration = random.choice(duration_choices)
        
        # Ensure we don't exceed total length
        if current_tick + duration > total_ticks:
            duration = total_ticks - current_tick
            
        if duration <= 0:
            break
        
        # Choose note based on contour
        if contour == "sigh" and len(events) == 0:
            # Start with a higher note for sighing effect
            start_note = random.choice(emphasized_notes[2:])  # Higher notes
            note = start_note
        elif contour == "sigh" and len(events) < 4:
            # Create sighing contour for first few notes
            if len(events) == 1:
                previous_note = events[0]['note']
                contour_notes = create_sighing_contour(previous_note, 3, seed + note_idx)
                note = contour_notes[1] if len(contour_notes) > 1 else previous_note - 2
            else:
                note = random.choice(weighted_notes)
        else:
            note = random.choice(weighted_notes)
        
        # Ensure note is in valid MIDI range
        note = max(36, min(96, note))
        
        # Generate velocity with soft curve
        base_intensity = random.uniform(0.4, 0.7)  # Soft dynamics
        velocity = soft_curve(base_intensity)
        velocity = humanize_velocity(velocity, 4, seed + note_idx)
        
        # Create note event
        start_tick = humanize_ticks(current_tick, 20, seed + note_idx)
        end_tick = start_tick + duration
        
        events.append({
            'start': start_tick,
            'end': end_tick,
            'note': note,
            'vel_on': velocity,
            'vel_off': max(1, velocity - 10)  # Softer release
        })
        
        # Advance time with gap
        gap_duration = random.choice([
            ppq // 2,  # Eighth note gap
            ppq,       # Quarter note gap  
            ppq * 2,   # Half note gap
            int(ppq * 1.5),  # Dotted quarter gap
        ])
        current_tick += duration + gap_duration
        
        # Stop if we've exceeded the total time
        if current_tick >= total_ticks:
            break
    
    return events


def generate_pad_progression(seed: int, key: str = "C", mode: str = "minor", 
                           bpm: int = 72, bars: int = 8) -> List[Dict]:
    """
    Generate ambient pad chord progression.
    
    Standard progression: Cm(add9) | Abmaj7 | Fm(add9) | Bbsus2 (for C minor)
    Each chord sustains for one full bar with voice leading.
    
    Args:
        seed: Random seed for reproducibility
        key: Root key
        mode: Scale mode
        bpm: Beats per minute  
        bars: Number of bars (will loop the 4-bar progression)
    
    Returns:
        List of chord events: {start, end, note, vel_on, vel_off} in ticks
    """
    random.seed(seed)
    ppq = 480
    ticks_per_bar = ppq * 4
    
    # Get the chord progression
    chord_specs = generate_progression_chords(key, mode)
    
    events = []
    current_chord_notes = None
    
    for bar in range(bars):
        # Use modulo to loop the 4-bar progression
        chord_spec = chord_specs[bar % len(chord_specs)]
        
        # Build the chord in octave 3 (lower register for pads)
        chord_notes = build_chord(chord_spec['root'], chord_spec['type'], octave=3)
        
        # Apply voice leading from previous chord
        if current_chord_notes:
            chord_notes = voice_leading_chord(current_chord_notes, chord_notes)
        
        current_chord_notes = chord_notes
        
        # Calculate timing for this bar
        start_tick = bar * ticks_per_bar
        end_tick = start_tick + ticks_per_bar
        
        # Humanize start time slightly
        start_tick = humanize_ticks(start_tick, 10, seed + bar)
        
        # Create note events for each chord tone
        for i, note in enumerate(chord_notes):
            # Generate soft pad velocities
            base_intensity = random.uniform(0.25, 0.45)  # Very soft
            velocity = soft_curve(base_intensity)
            velocity = humanize_velocity(velocity, 3, seed + bar + i)
            
            # Add slight timing offset for each voice (spread the attack)
            voice_offset = i * 15  # Small delay between voices
            note_start = start_tick + voice_offset
            
            events.append({
                'start': note_start,
                'end': end_tick,
                'note': note,
                'vel_on': velocity,
                'vel_off': max(1, velocity - 5)
            })
    
    return events


def generate_bass_line(seed: int, key: str = "C", mode: str = "minor",
                      bpm: int = 72, bars: int = 8) -> List[Dict]:
    """
    Generate a simple bass line following the chord progression.
    Optional - can be used for richer arrangements.
    """
    random.seed(seed)
    ppq = 480
    ticks_per_bar = ppq * 4
    
    chord_specs = generate_progression_chords(key, mode)
    events = []
    
    for bar in range(bars):
        chord_spec = chord_specs[bar % len(chord_specs)]
        
        # Get root note in bass octave (octave 2)
        root_note = build_chord(chord_spec['root'], 'minor', octave=2)[0]
        
        start_tick = bar * ticks_per_bar
        
        # Simple pattern: root on beats 1 and 3
        for beat in [0, 2]:  # Beats 1 and 3
            note_start = start_tick + (beat * ppq)
            note_end = note_start + ppq  # Quarter note duration
            
            velocity = random.randint(45, 65)  # Medium-soft bass
            
            events.append({
                'start': note_start,
                'end': note_end,
                'note': root_note,
                'vel_on': velocity,
                'vel_off': velocity - 10
            })
    
    return events


def create_ambient_arrangement(seed: int, key: str = "C", mode: str = "minor",
                             bpm: int = 72, bars: int = 8, 
                             include_bass: bool = False) -> Dict[str, List[Dict]]:
    """
    Create a complete ambient arrangement with melody and pads.
    
    Returns:
        Dictionary with 'melody' and 'pads' keys (and optionally 'bass')
    """
    arrangement = {
        'melody': generate_melody(seed, key, mode, bpm, bars, density=0.35),
        'pads': generate_pad_progression(seed + 1000, key, mode, bpm, bars)
    }
    
    if include_bass:
        arrangement['bass'] = generate_bass_line(seed + 2000, key, mode, bpm, bars)
    
    return arrangement
