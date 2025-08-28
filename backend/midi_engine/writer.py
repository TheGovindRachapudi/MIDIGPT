"""
Zero-dependency Standard MIDI File (SMF) writer.

Provides complete MIDI file generation with proper Format 1 structure,
VLQ encoding, meta events, and channel events.
"""

import struct
from typing import List


def encode_vlq(value: int) -> bytes:
    """Encode a value as Variable Length Quantity (VLQ) for MIDI delta-time."""
    if value == 0:
        return bytes([0x00])
    
    result = []
    while value > 0:
        byte = value & 0x7F
        value >>= 7
        if result:  # Not the first byte
            byte |= 0x80
        result.insert(0, byte)
    
    return bytes(result)


def make_header(format_type: int = 1, ntrks: int = 3, division: int = 480) -> bytes:
    """Create MIDI header chunk (MThd)."""
    return b'MThd' + struct.pack('>I', 6) + struct.pack('>HHH', format_type, ntrks, division)


def make_track(events: bytes) -> bytes:
    """Wrap track events in MTrk chunk with length."""
    return b'MTrk' + struct.pack('>I', len(events)) + events


def write_midi(tracks: List[bytes], ppq: int = 480) -> bytes:
    """Write complete MIDI file with header and tracks."""
    midi_data = make_header(format_type=1, ntrks=len(tracks), division=ppq)
    for track in tracks:
        midi_data += make_track(track)
    return midi_data


# Meta Events
def meta_tempo(bpm: int, delta_time: int = 0) -> bytes:
    """Create tempo meta event (0xFF 0x51)."""
    microseconds_per_quarter = int(60_000_000 / bpm)
    return encode_vlq(delta_time) + b'\xFF\x51\x03' + struct.pack('>I', microseconds_per_quarter)[1:]


def meta_time_signature(numerator: int = 4, denominator: int = 4, 
                       metronome_ticks: int = 24, thirty_seconds: int = 8,
                       delta_time: int = 0) -> bytes:
    """Create time signature meta event (0xFF 0x58)."""
    denom_power = 0
    d = denominator
    while d > 1:
        d //= 2
        denom_power += 1
    
    return (encode_vlq(delta_time) + b'\xFF\x58\x04' + 
            bytes([numerator, denom_power, metronome_ticks, thirty_seconds]))


def meta_key_signature(key: str = "C", mode: str = "minor", delta_time: int = 0) -> bytes:
    """Create key signature meta event (0xFF 0x59)."""
    # Key signature mapping: sharps positive, flats negative
    key_map = {
        'C': 0, 'G': 1, 'D': 2, 'A': 3, 'E': 4, 'B': 5, 'F#': 6, 'C#': 7,
        'F': -1, 'Bb': -2, 'Eb': -3, 'Ab': -4, 'Db': -5, 'Gb': -6, 'Cb': -7
    }
    
    sharps_flats = key_map.get(key, 0)
    mode_byte = 0 if mode == "major" else 1
    
    # Convert to signed byte
    if sharps_flats < 0:
        sharps_flats = (256 + sharps_flats) % 256
    
    return encode_vlq(delta_time) + b'\xFF\x59\x02' + bytes([sharps_flats, mode_byte])


def meta_end_of_track(delta_time: int = 0) -> bytes:
    """Create end of track meta event (0xFF 0x2F 0x00)."""
    return encode_vlq(delta_time) + b'\xFF\x2F\x00'


# Channel Events
def program_change(channel: int, program: int, delta_time: int = 0) -> bytes:
    """Create program change event."""
    return encode_vlq(delta_time) + bytes([0xC0 | channel, program])


def note_on(channel: int, note: int, velocity: int, delta_time: int = 0) -> bytes:
    """Create note on event."""
    return encode_vlq(delta_time) + bytes([0x90 | channel, note, velocity])


def note_off(channel: int, note: int, velocity: int = 64, delta_time: int = 0) -> bytes:
    """Create note off event."""
    return encode_vlq(delta_time) + bytes([0x80 | channel, note, velocity])


def control_change(channel: int, controller: int, value: int, delta_time: int = 0) -> bytes:
    """Create control change event."""
    return encode_vlq(delta_time) + bytes([0xB0 | channel, controller, value])


def sustain_pedal(channel: int, on: bool, delta_time: int = 0) -> bytes:
    """Create sustain pedal control change (CC 64)."""
    return control_change(channel, 64, 127 if on else 0, delta_time)


def build_conductor_track(bpm: int, ppq: int, key: str = "C", mode: str = "minor") -> bytes:
    """Build conductor track with tempo, time signature, and key signature."""
    events = b''
    events += meta_tempo(bpm, 0)
    events += meta_time_signature(4, 4, 24, 8, 0) 
    events += meta_key_signature(key, mode, 0)
    events += meta_end_of_track(0)
    return events


def build_note_track(events: List[dict], channel: int, program: int = None) -> bytes:
    """
    Build a MIDI track from note events.
    
    events: List of dicts with keys: start, end, note, vel_on, vel_off (in ticks)
    channel: MIDI channel (0-15)
    program: GM program number (0-127), None to skip program change
    """
    track_events = []
    
    # Add program change if specified
    if program is not None:
        track_events.append((0, 'program', program))
    
    # Convert note events to MIDI events
    for event in events:
        start_tick = event['start']
        end_tick = event['end']
        note = event['note']
        vel_on = event.get('vel_on', 64)
        vel_off = event.get('vel_off', 64)
        
        track_events.append((start_tick, 'note_on', channel, note, vel_on))
        track_events.append((end_tick, 'note_off', channel, note, vel_off))
    
    # Sort by tick, then by event type priority (note_off before note_on at same tick)
    def event_priority(event):
        tick, event_type = event[0], event[1]
        priority = {'note_off': 0, 'note_on': 1, 'program': 2}
        return (tick, priority.get(event_type, 3))
    
    track_events.sort(key=event_priority)
    
    # Generate MIDI bytes
    track_bytes = b''
    current_tick = 0
    
    for event in track_events:
        tick = event[0]
        delta = tick - current_tick
        
        if event[1] == 'program':
            track_bytes += program_change(channel, event[2], delta)
        elif event[1] == 'note_on':
            track_bytes += note_on(event[2], event[3], event[4], delta)
        elif event[1] == 'note_off':
            track_bytes += note_off(event[2], event[3], event[4], delta)
        
        current_tick = tick
    
    # Add end of track
    track_bytes += meta_end_of_track(0)
    
    return track_bytes
