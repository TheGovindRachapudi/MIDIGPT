"""
Main API for the MIDI Engine.

Single entry point for generating ambient MIDI files.
"""

from typing import Optional
from .patterns import generate_melody, generate_pad_progression
from .render import render_conductor_track, render_note_track, events_summary
from .writer import write_midi


def create_ambient_midi(
    seed: int = 42,
    key: str = "C", 
    mode: str = "minor",
    bpm: int = 72,
    bars: int = 8,
    ppq: int = 480,
    melody_program: int = 0,  # Acoustic Grand Piano
    pad_program: int = 88,    # New Age Pad
    density: float = 0.35
) -> bytes:
    """
    Generate a complete ambient MIDI file.
    
    Creates a Format 1 MIDI file with:
    - Track 0: Conductor (tempo, time signature, key signature)
    - Track 1: Melody (sparse, ambient, with sighing contours)
    - Track 2: Pad chords (lush progression with voice leading)
    
    Args:
        seed: Random seed for reproducible generation
        key: Root key (C, F#, Bb, etc.)
        mode: Scale mode ('minor' or 'major')
        bpm: Beats per minute (default 72 for ambient feel)
        bars: Number of bars to generate
        ppq: Pulses per quarter note (MIDI ticks)
        melody_program: GM program for melody track (0-127)
        pad_program: GM program for pad track (0-127)
        density: Melody note density (0.0-1.0, lower = more sparse)
    
    Returns:
        Complete MIDI file as bytes (ready to save or stream)
    """
    
    # Generate musical patterns
    melody_events = generate_melody(
        seed=seed,
        key=key,
        mode=mode,
        bpm=bpm,
        bars=bars,
        density=density,
        contour="sigh"
    )
    
    pad_events = generate_pad_progression(
        seed=seed + 1000,  # Different seed for variety
        key=key,
        mode=mode,
        bpm=bpm,
        bars=bars
    )
    
    # Render tracks to MIDI bytes
    conductor_track = render_conductor_track(bpm, ppq, key, mode)
    melody_track = render_note_track(melody_events, channel=0, program=melody_program)
    pad_track = render_note_track(pad_events, channel=1, program=pad_program)
    
    # Combine into complete MIDI file
    tracks = [conductor_track, melody_track, pad_track]
    midi_bytes = write_midi(tracks, ppq)
    
    return midi_bytes


def create_ambient_midi_with_info(
    seed: int = 42,
    key: str = "C",
    mode: str = "minor", 
    bpm: int = 72,
    bars: int = 8,
    ppq: int = 480,
    melody_program: int = 0,
    pad_program: int = 88,
    density: float = 0.35
) -> tuple[bytes, dict]:
    """
    Generate ambient MIDI with additional generation info.
    
    Same as create_ambient_midi() but also returns generation statistics.
    
    Returns:
        Tuple of (midi_bytes, info_dict)
        
        info_dict contains:
        - melody_stats: Statistics about melody events
        - pad_stats: Statistics about pad events
        - total_tracks: Number of tracks
        - total_size: Size of MIDI data in bytes
        - parameters: Generation parameters used
    """
    
    # Generate patterns
    melody_events = generate_melody(
        seed=seed, key=key, mode=mode, bpm=bpm, bars=bars, 
        density=density, contour="sigh"
    )
    
    pad_events = generate_pad_progression(
        seed=seed + 1000, key=key, mode=mode, bpm=bpm, bars=bars
    )
    
    # Render tracks
    conductor_track = render_conductor_track(bpm, ppq, key, mode)
    melody_track = render_note_track(melody_events, channel=0, program=melody_program)
    pad_track = render_note_track(pad_events, channel=1, program=pad_program)
    
    # Create MIDI file
    tracks = [conductor_track, melody_track, pad_track]
    midi_bytes = write_midi(tracks, ppq)
    
    # Gather info
    info = {
        'melody_stats': events_summary(melody_events),
        'pad_stats': events_summary(pad_events),
        'total_tracks': len(tracks),
        'total_size': len(midi_bytes),
        'parameters': {
            'seed': seed,
            'key': key,
            'mode': mode,
            'bpm': bpm,
            'bars': bars,
            'ppq': ppq,
            'density': density,
            'melody_program': melody_program,
            'pad_program': pad_program
        }
    }
    
    return midi_bytes, info


def create_melody_only_midi(
    seed: int = 42,
    key: str = "C",
    mode: str = "minor",
    bpm: int = 72,
    bars: int = 8,
    ppq: int = 480,
    program: int = 0,
    density: float = 0.35
) -> bytes:
    """
    Generate a MIDI file with only melody (no pads).
    
    Useful for simpler arrangements or when you want to add your own backing.
    """
    melody_events = generate_melody(
        seed=seed, key=key, mode=mode, bpm=bpm, bars=bars,
        density=density, contour="sigh"
    )
    
    conductor_track = render_conductor_track(bpm, ppq, key, mode)
    melody_track = render_note_track(melody_events, channel=0, program=program)
    
    tracks = [conductor_track, melody_track]
    return write_midi(tracks, ppq)


def create_pads_only_midi(
    seed: int = 42,
    key: str = "C",
    mode: str = "minor",
    bpm: int = 72,
    bars: int = 8,
    ppq: int = 480,
    program: int = 88
) -> bytes:
    """
    Generate a MIDI file with only pad chords (no melody).
    
    Useful for backing tracks or when you want to add your own lead.
    """
    pad_events = generate_pad_progression(
        seed=seed, key=key, mode=mode, bpm=bpm, bars=bars
    )
    
    conductor_track = render_conductor_track(bpm, ppq, key, mode)
    pad_track = render_note_track(pad_events, channel=0, program=program)
    
    tracks = [conductor_track, pad_track]
    return write_midi(tracks, ppq)


# Optional mido fallback (if available)
def create_ambient_midi_mido(
    seed: int = 42,
    key: str = "C",
    mode: str = "minor",
    bpm: int = 72,
    bars: int = 8,
    ppq: int = 480,
    melody_program: int = 0,
    pad_program: int = 88,
    density: float = 0.35
) -> Optional[bytes]:
    """
    Alternative implementation using mido library (if available).
    
    This is a fallback/debug option that mirrors create_ambient_midi()
    but uses the mido library instead of our zero-dependency writer.
    
    Returns None if mido is not available.
    """
    try:
        import mido
        
        # Generate patterns (same as main function)
        melody_events = generate_melody(
            seed=seed, key=key, mode=mode, bpm=bpm, bars=bars,
            density=density, contour="sigh"
        )
        
        pad_events = generate_pad_progression(
            seed=seed + 1000, key=key, mode=mode, bpm=bpm, bars=bars
        )
        
        # Create MIDI file using mido
        mid = mido.MidiFile(type=1, ticks_per_beat=ppq)
        
        # Conductor track
        conductor = mido.MidiTrack()
        conductor.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=0))
        conductor.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))
        conductor.append(mido.MetaMessage('key_signature', key=key.replace('#', 's'), time=0))
        conductor.append(mido.MetaMessage('end_of_track', time=0))
        mid.tracks.append(conductor)
        
        # Melody track
        melody_track = mido.MidiTrack()
        if melody_program is not None:
            melody_track.append(mido.Message('program_change', channel=0, program=melody_program, time=0))
        
        # Convert events to mido messages
        current_time = 0
        for event in sorted(melody_events, key=lambda x: x['start']):
            # Note on
            delta = event['start'] - current_time
            melody_track.append(mido.Message('note_on', channel=0, note=event['note'], 
                                           velocity=event['vel_on'], time=delta))
            current_time = event['start']
            
            # Note off  
            delta = event['end'] - current_time
            melody_track.append(mido.Message('note_off', channel=0, note=event['note'],
                                           velocity=event.get('vel_off', 64), time=delta))
            current_time = event['end']
        
        melody_track.append(mido.MetaMessage('end_of_track', time=0))
        mid.tracks.append(melody_track)
        
        # Pad track (similar structure)
        pad_track = mido.MidiTrack()
        if pad_program is not None:
            pad_track.append(mido.Message('program_change', channel=1, program=pad_program, time=0))
        
        current_time = 0
        for event in sorted(pad_events, key=lambda x: x['start']):
            delta = event['start'] - current_time
            pad_track.append(mido.Message('note_on', channel=1, note=event['note'],
                                        velocity=event['vel_on'], time=delta))
            current_time = event['start']
            
            delta = event['end'] - current_time  
            pad_track.append(mido.Message('note_off', channel=1, note=event['note'],
                                        velocity=event.get('vel_off', 64), time=delta))
            current_time = event['end']
        
        pad_track.append(mido.MetaMessage('end_of_track', time=0))
        mid.tracks.append(pad_track)
        
        # Return as bytes
        import io
        bytesio = io.BytesIO()
        mid.save(file=bytesio)
        return bytesio.getvalue()
        
    except ImportError:
        return None
