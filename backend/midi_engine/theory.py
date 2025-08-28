"""
Music theory helpers for MIDI generation.

Provides scales, chord builders, velocity shaping, and humanization.
"""

import random
from typing import List, Dict, Tuple


# Note names to MIDI numbers (middle C = 60)
NOTE_TO_MIDI = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5,
    'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
}

# Scale intervals (semitones from root)
SCALE_INTERVALS = {
    'minor': [0, 2, 3, 5, 7, 8, 10],  # Natural minor
    'major': [0, 2, 4, 5, 7, 9, 11],
    'dorian': [0, 2, 3, 5, 7, 9, 10],
    'phrygian': [0, 1, 3, 5, 7, 8, 10],
}

# Chord intervals relative to root
CHORD_INTERVALS = {
    'minor': [0, 3, 7],
    'major': [0, 4, 7],
    'add9': [0, 2, 3, 7],  # minor add9: root, 9th, minor 3rd, 5th  
    'maj7': [0, 4, 7, 11],  # major 7th
    'sus2': [0, 2, 7],      # suspended 2nd
    'sus4': [0, 5, 7],      # suspended 4th
}


def get_scale_notes(root: str, mode: str = "minor", octave: int = 4) -> List[int]:
    """Get MIDI note numbers for a scale."""
    root_midi = NOTE_TO_MIDI[root] + (octave * 12)
    intervals = SCALE_INTERVALS.get(mode, SCALE_INTERVALS['minor'])
    return [root_midi + interval for interval in intervals]


def build_chord(root: str, chord_type: str, octave: int = 4, inversion: int = 0) -> List[int]:
    """
    Build a chord from root note.
    
    Args:
        root: Root note name (e.g., 'C', 'F#')
        chord_type: Type of chord ('minor', 'major', 'add9', 'maj7', 'sus2', 'sus4')
        octave: Base octave for the chord
        inversion: Chord inversion (0=root position, 1=first inversion, etc.)
    """
    root_midi = NOTE_TO_MIDI[root] + (octave * 12)
    intervals = CHORD_INTERVALS.get(chord_type, CHORD_INTERVALS['minor'])
    
    notes = [root_midi + interval for interval in intervals]
    
    # Apply inversion
    if inversion > 0:
        for _ in range(inversion % len(notes)):
            notes[0] += 12
            notes = notes[1:] + [notes[0]]
    
    return sorted(notes)


def voice_leading_chord(current_chord: List[int], target_chord: List[int]) -> List[int]:
    """
    Apply voice leading to move smoothly from current chord to target chord.
    Minimizes movement between chord tones.
    """
    if not current_chord:
        return target_chord
    
    # Try different inversions of target chord to find closest voice leading
    best_chord = target_chord[:]
    best_distance = sum(abs(a - b) for a, b in zip(current_chord, target_chord))
    
    for inversion in range(1, len(target_chord)):
        inverted = target_chord[inversion:] + [note + 12 for note in target_chord[:inversion]]
        distance = sum(abs(a - b) for a, b in zip(current_chord, inverted))
        
        if distance < best_distance:
            best_distance = distance
            best_chord = inverted
    
    return best_chord


def get_color_tones(key: str, mode: str = "minor") -> List[int]:
    """Get color tones (9ths, 11ths) for a key across multiple octaves."""
    scale = get_scale_notes(key, mode, 3)  # Start from octave 3
    scale.extend(get_scale_notes(key, mode, 4))
    scale.extend(get_scale_notes(key, mode, 5))
    
    # Add 9th and 11th intervals
    root_midi = NOTE_TO_MIDI[key]
    color_tones = []
    
    for octave in range(3, 6):
        base = root_midi + (octave * 12)
        color_tones.extend([
            base + 2,   # 9th
            base + 5,   # 11th (or 4th)
            base + 14,  # 9th + octave
        ])
    
    return sorted(list(set(scale + color_tones)))


def soft_curve(intensity: float) -> int:
    """
    Convert intensity (0.0-1.0) to MIDI velocity using a soft curve.
    Emphasizes lower dynamics for ambient music.
    """
    # Soft curve that emphasizes lower velocities
    curved = intensity ** 1.5
    velocity = int(20 + (curved * 87))  # Range: 20-107
    return max(1, min(127, velocity))


def humanize_ticks(ticks: int, amount: int, seed: int = None) -> int:
    """
    Humanize timing by adding small random variations.
    
    Args:
        ticks: Original tick time
        amount: Maximum variation in ticks (±amount)
        seed: Random seed for reproducibility
    """
    if seed is not None:
        random.seed(f"timing_{seed}_{ticks}")
    
    variation = random.randint(-amount, amount)
    return max(0, ticks + variation)


def humanize_velocity(velocity: int, amount: int = 4, seed: int = None) -> int:
    """
    Humanize velocity with small random variations.
    
    Args:
        velocity: Original velocity
        amount: Maximum variation (±amount)
        seed: Random seed for reproducibility
    """
    if seed is not None:
        random.seed(f"velocity_{seed}_{velocity}")
    
    variation = random.randint(-amount, amount)
    return max(1, min(127, velocity + variation))


def generate_progression_chords(key: str = "C", mode: str = "minor") -> List[Dict]:
    """
    Generate the standard ambient progression: Cm(add9) | Abmaj7 | Fm(add9) | Bbsus2
    Adjusted for the given key.
    """
    # Relative to C minor: i, bVI, iv, bVII
    if mode == "minor":
        scale = get_scale_notes(key, "minor", 0)  # Get intervals only
        root = NOTE_TO_MIDI[key]
        
        progressions = [
            {'root': key, 'type': 'add9'},                    # i(add9)
            {'root': get_note_name(root + 8), 'type': 'maj7'}, # bVI maj7
            {'root': get_note_name(root + 5), 'type': 'add9'}, # iv(add9) 
            {'root': get_note_name(root + 10), 'type': 'sus2'} # bVII sus2
        ]
    else:
        # For major keys, use relative minor progression
        progressions = [
            {'root': key, 'type': 'add9'},
            {'root': get_note_name(NOTE_TO_MIDI[key] + 8), 'type': 'maj7'},
            {'root': get_note_name(NOTE_TO_MIDI[key] + 5), 'type': 'add9'},
            {'root': get_note_name(NOTE_TO_MIDI[key] + 10), 'type': 'sus2'}
        ]
    
    return progressions


def get_note_name(midi_note: int) -> str:
    """Convert MIDI note number to note name."""
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    return note_names[midi_note % 12]


def create_sighing_contour(start_note: int, length: int = 4, seed: int = None) -> List[int]:
    """
    Create a 'sighing' melodic contour that moves down and back up.
    Perfect for sad/ambient melodies.
    """
    if seed is not None:
        random.seed(f"contour_{seed}_{start_note}")
    
    contour = [start_note]
    
    # Move down by 2-4 semitones
    down_amount = random.choice([2, 3, 4])  # Minor 2nd, minor 3rd, or major 3rd
    lowest = start_note - down_amount
    
    # Create shape: start -> down -> up slightly -> end around start
    if length == 2:
        contour.append(lowest)
    elif length == 3:
        contour.extend([lowest, start_note - 1])
    else:  # length >= 4
        mid_points = length - 2
        # Distribute points along the curve
        for i in range(1, mid_points + 1):
            if i <= mid_points // 2:
                # Going down
                note = start_note - int((i / (mid_points // 2 + 1)) * down_amount)
            else:
                # Coming back up
                progress = (i - mid_points // 2) / (mid_points - mid_points // 2)
                note = lowest + int(progress * (down_amount - 1))
            contour.append(note)
        
        # End note
        contour.append(start_note - random.choice([0, 1, 2]))
    
    return contour
