"""
Event to MIDI track renderer.

Converts musical events into properly formatted MIDI track bytes.
"""

from typing import List, Dict
from .writer import build_conductor_track, build_note_track


def render_conductor_track(bpm: int, ppq: int, key: str = "C", mode: str = "minor") -> bytes:
    """
    Build conductor track with tempo, time signature, and key signature.
    
    Args:
        bpm: Beats per minute
        ppq: Pulses per quarter note (ticks)
        key: Key signature root
        mode: Key signature mode ('major' or 'minor')
    
    Returns:
        MIDI track bytes for conductor track
    """
    return build_conductor_track(bpm, ppq, key, mode)


def render_note_track(events: List[Dict], channel: int, program: int = None) -> bytes:
    """
    Render note events into a MIDI track with proper timing and sorting.
    
    Ensures:
    - Events are sorted by time
    - Note-off events occur before note-on at the same tick
    - No overlapping identical notes on the same channel
    - Proper delta-time encoding
    
    Args:
        events: List of note events with keys: start, end, note, vel_on, vel_off
        channel: MIDI channel (0-15)
        program: GM program number (0-127), None to skip program change
    
    Returns:
        MIDI track bytes
    """
    if not events:
        # Empty track with just end-of-track
        from .writer import meta_end_of_track
        return meta_end_of_track(0)
    
    # Sort events and remove overlapping duplicates
    clean_events = remove_overlapping_notes(events)
    
    return build_note_track(clean_events, channel, program)


def remove_overlapping_notes(events: List[Dict]) -> List[Dict]:
    """
    Remove overlapping notes of the same pitch to prevent stuck notes.
    
    If two notes with the same pitch overlap, the first note is shortened
    to end just before the second note starts.
    """
    if not events:
        return events
    
    # Sort events by start time, then by note pitch
    sorted_events = sorted(events, key=lambda e: (e['start'], e['note']))
    
    # Track active notes (pitch -> event)
    active_notes = {}
    clean_events = []
    
    for event in sorted_events:
        pitch = event['note']
        start = event['start']
        
        # If this pitch is already active, end the previous note early
        if pitch in active_notes:
            prev_event = active_notes[pitch]
            # End previous note just before this one starts (minimum 1 tick gap)
            prev_event['end'] = max(prev_event['start'] + 1, start - 1)
            clean_events.append(prev_event)
        
        # Set this note as active
        active_notes[pitch] = event.copy()
    
    # Add remaining active notes
    for event in active_notes.values():
        clean_events.append(event)
    
    return clean_events


def validate_events(events: List[Dict]) -> List[str]:
    """
    Validate a list of note events and return any issues found.
    
    Returns:
        List of validation error messages (empty if no issues)
    """
    issues = []
    
    for i, event in enumerate(events):
        # Check required fields
        required_fields = ['start', 'end', 'note', 'vel_on']
        for field in required_fields:
            if field not in event:
                issues.append(f"Event {i}: Missing required field '{field}'")
                continue
        
        # Check timing
        if event['start'] < 0:
            issues.append(f"Event {i}: Negative start time ({event['start']})")
        
        if event['end'] <= event['start']:
            issues.append(f"Event {i}: End time ({event['end']}) must be after start time ({event['start']})")
        
        # Check MIDI ranges
        if not (0 <= event['note'] <= 127):
            issues.append(f"Event {i}: Note ({event['note']}) out of MIDI range (0-127)")
        
        if not (1 <= event['vel_on'] <= 127):
            issues.append(f"Event {i}: Velocity ({event['vel_on']}) out of range (1-127)")
        
        if 'vel_off' in event and not (0 <= event['vel_off'] <= 127):
            issues.append(f"Event {i}: Release velocity ({event['vel_off']}) out of range (0-127)")
    
    return issues


def calculate_total_ticks(events: List[Dict]) -> int:
    """Calculate the total duration in ticks for a list of events."""
    if not events:
        return 0
    
    return max(event['end'] for event in events)


def events_summary(events: List[Dict]) -> Dict:
    """
    Generate a summary of note events for debugging/logging.
    
    Returns:
        Dictionary with statistics about the events
    """
    if not events:
        return {
            'total_events': 0,
            'total_ticks': 0,
            'note_range': None,
            'velocity_range': None,
            'average_duration': 0
        }
    
    notes = [e['note'] for e in events]
    velocities = [e['vel_on'] for e in events]
    durations = [e['end'] - e['start'] for e in events]
    
    return {
        'total_events': len(events),
        'total_ticks': calculate_total_ticks(events),
        'note_range': (min(notes), max(notes)),
        'velocity_range': (min(velocities), max(velocities)),
        'average_duration': sum(durations) / len(durations) if durations else 0,
        'unique_pitches': len(set(notes))
    }
