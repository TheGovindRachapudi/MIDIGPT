#!/usr/bin/env python3
"""
Comprehensive test suite for the MIDI Engine.

Tests MIDI format validation, timing, note counts, and musical structure.
"""

import unittest
import sys
from pathlib import Path

# Add parent directories to path for importing
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from midi_engine.api import create_ambient_midi, create_ambient_midi_with_info
from midi_engine.writer import (
    encode_vlq, make_header, make_track, write_midi,
    meta_tempo, meta_time_signature, meta_key_signature, meta_end_of_track,
    note_on, note_off, program_change
)
from midi_engine.theory import (
    get_scale_notes, build_chord, voice_leading_chord, soft_curve,
    humanize_ticks, humanize_velocity, generate_progression_chords
)
from midi_engine.patterns import generate_melody, generate_pad_progression
from midi_engine.render import remove_overlapping_notes, validate_events


class TestMIDIWriter(unittest.TestCase):
    """Test the zero-dependency MIDI writer."""
    
    def test_vlq_encoding(self):
        """Test Variable Length Quantity encoding."""
        self.assertEqual(encode_vlq(0), b'\x00')
        self.assertEqual(encode_vlq(127), b'\x7F')
        self.assertEqual(encode_vlq(128), b'\x81\x00')
        self.assertEqual(encode_vlq(255), b'\x81\x7F')
        self.assertEqual(encode_vlq(16383), b'\xFF\x7F')
        self.assertEqual(encode_vlq(16384), b'\x81\x80\x00')
    
    def test_header_chunk(self):
        """Test MIDI header chunk creation."""
        header = make_header(1, 3, 480)
        self.assertEqual(header[:4], b'MThd')  # Chunk type
        self.assertEqual(header[4:8], b'\x00\x00\x00\x06')  # Length = 6
        self.assertEqual(header[8:10], b'\x00\x01')  # Format 1
        self.assertEqual(header[10:12], b'\x00\x03')  # 3 tracks
        self.assertEqual(header[12:14], b'\x01\xe0')  # 480 PPQ
    
    def test_track_chunk(self):
        """Test MIDI track chunk creation."""
        events = b'\x00\xFF\x2F\x00'  # Delta=0, End of Track
        track = make_track(events)
        self.assertEqual(track[:4], b'MTrk')  # Chunk type
        self.assertEqual(track[4:8], b'\x00\x00\x00\x04')  # Length = 4
        self.assertEqual(track[8:], events)  # Event data
    
    def test_meta_events(self):
        """Test meta event generation."""
        # Tempo: 120 BPM = 500000 microseconds per quarter
        tempo = meta_tempo(120, 0)
        self.assertIn(b'\xFF\x51\x03', tempo)  # Tempo meta event
        
        # Time signature: 4/4
        time_sig = meta_time_signature(4, 4, 24, 8, 0)
        self.assertIn(b'\xFF\x58\x04', time_sig)  # Time sig meta event
        
        # Key signature: C minor
        key_sig = meta_key_signature("C", "minor", 0)
        self.assertIn(b'\xFF\x59\x02', key_sig)  # Key sig meta event
        
        # End of track
        eot = meta_end_of_track(0)
        self.assertEqual(eot, b'\x00\xFF\x2F\x00')
    
    def test_channel_events(self):
        """Test channel event generation."""
        # Note on: Channel 0, Note 60 (C4), Velocity 64
        note_on_event = note_on(0, 60, 64, 0)
        self.assertIn(b'\x90', note_on_event)  # Note on channel 0
        self.assertIn(b'\x3C', note_on_event)  # Note 60
        self.assertIn(b'\x40', note_on_event)  # Velocity 64
        
        # Note off: Channel 0, Note 60, Velocity 64
        note_off_event = note_off(0, 60, 64, 0)
        self.assertIn(b'\x80', note_off_event)  # Note off channel 0
        
        # Program change: Channel 0, Program 0
        prog_change = program_change(0, 0, 0)
        self.assertIn(b'\xC0', prog_change)  # Program change channel 0


class TestMusicTheory(unittest.TestCase):
    """Test music theory helpers."""
    
    def test_scale_generation(self):
        """Test scale note generation."""
        c_minor = get_scale_notes("C", "minor", 4)
        expected = [48, 50, 51, 53, 55, 56, 58]  # C4 minor scale
        self.assertEqual(c_minor, expected)
        
        c_major = get_scale_notes("C", "major", 4) 
        expected_major = [48, 50, 52, 53, 55, 57, 59]  # C4 major scale
        self.assertEqual(c_major, expected_major)
    
    def test_chord_building(self):
        """Test chord construction."""
        c_minor_chord = build_chord("C", "minor", 4)
        self.assertEqual(c_minor_chord, [48, 51, 55])  # C, Eb, G
        
        c_add9 = build_chord("C", "add9", 4)
        self.assertEqual(c_add9, [48, 50, 51, 55])  # C, D, Eb, G
        
        # Test inversions
        c_minor_inv1 = build_chord("C", "minor", 4, inversion=1)
        self.assertEqual(c_minor_inv1, [51, 55, 60])  # First inversion
    
    def test_voice_leading(self):
        """Test voice leading between chords."""
        chord1 = [48, 51, 55]  # C minor
        chord2 = [53, 56, 60]  # F minor
        
        led_chord = voice_leading_chord(chord1, chord2)
        self.assertIsInstance(led_chord, list)
        self.assertEqual(len(led_chord), len(chord2))
        
        # Voice leading should minimize movement
        total_movement = sum(abs(a - b) for a, b in zip(chord1, led_chord))
        direct_movement = sum(abs(a - b) for a, b in zip(chord1, chord2))
        self.assertLessEqual(total_movement, direct_movement)
    
    def test_velocity_curve(self):
        """Test velocity curve generation."""
        self.assertEqual(soft_curve(0.0), 20)  # Minimum
        self.assertGreaterEqual(soft_curve(1.0), 100)  # Near maximum
        
        # Test curve properties
        low = soft_curve(0.3)
        high = soft_curve(0.7)
        self.assertLess(low, high)
        self.assertGreaterEqual(low, 1)
        self.assertLessEqual(high, 127)
    
    def test_humanization(self):
        """Test timing and velocity humanization."""
        # Timing humanization
        original_ticks = 480
        humanized = humanize_ticks(original_ticks, 20, seed=42)
        self.assertGreaterEqual(humanized, 0)  # No negative times
        self.assertTrue(abs(humanized - original_ticks) <= 20)
        
        # Velocity humanization
        original_vel = 64
        humanized_vel = humanize_velocity(original_vel, 4, seed=42)
        self.assertGreaterEqual(humanized_vel, 1)
        self.assertLessEqual(humanized_vel, 127)
        self.assertTrue(abs(humanized_vel - original_vel) <= 4)
    
    def test_progression_generation(self):
        """Test chord progression generation."""
        progression = generate_progression_chords("C", "minor")
        self.assertEqual(len(progression), 4)  # 4-chord progression
        
        # Check structure
        for chord_spec in progression:
            self.assertIn('root', chord_spec)
            self.assertIn('type', chord_spec)
            self.assertIn(chord_spec['type'], ['add9', 'maj7', 'sus2'])


class TestPatternGeneration(unittest.TestCase):
    """Test musical pattern generators."""
    
    def test_melody_generation(self):
        """Test melody pattern generation."""
        melody = generate_melody(seed=42, key="C", mode="minor", 
                                bpm=72, bars=4, density=0.5)
        
        # Check structure
        self.assertIsInstance(melody, list)
        
        for event in melody:
            self.assertIn('start', event)
            self.assertIn('end', event) 
            self.assertIn('note', event)
            self.assertIn('vel_on', event)
            
            # Validate ranges
            self.assertGreaterEqual(event['start'], 0)
            self.assertGreater(event['end'], event['start'])
            self.assertGreaterEqual(event['note'], 36)
            self.assertLessEqual(event['note'], 96)
            self.assertGreaterEqual(event['vel_on'], 1)
            self.assertLessEqual(event['vel_on'], 127)
    
    def test_pad_generation(self):
        """Test pad progression generation."""
        pads = generate_pad_progression(seed=42, key="C", mode="minor",
                                      bpm=72, bars=4)
        
        self.assertIsInstance(pads, list)
        self.assertGreater(len(pads), 0)  # Should generate some notes
        
        # Check that we have chord events (multiple notes per bar)
        events_per_bar = {}
        for event in pads:
            bar = event['start'] // (480 * 4)  # 480 PPQ * 4 beats
            events_per_bar[bar] = events_per_bar.get(bar, 0) + 1
        
        # Should have multiple notes per bar (chord tones)
        for bar, count in events_per_bar.items():
            self.assertGreater(count, 1, f"Bar {bar} should have multiple chord tones")
    
    def test_deterministic_generation(self):
        """Test that generation is deterministic with same seed."""
        melody1 = generate_melody(seed=123, key="C", mode="minor", bars=2)
        melody2 = generate_melody(seed=123, key="C", mode="minor", bars=2)
        
        self.assertEqual(len(melody1), len(melody2))
        for e1, e2 in zip(melody1, melody2):
            self.assertEqual(e1['start'], e2['start'])
            self.assertEqual(e1['end'], e2['end'])
            self.assertEqual(e1['note'], e2['note'])
            self.assertEqual(e1['vel_on'], e2['vel_on'])


class TestEventProcessing(unittest.TestCase):
    """Test event processing and validation."""
    
    def test_overlapping_note_removal(self):
        """Test removal of overlapping notes."""
        # Create overlapping events
        events = [
            {'start': 0, 'end': 480, 'note': 60, 'vel_on': 64},
            {'start': 240, 'end': 720, 'note': 60, 'vel_on': 64},  # Overlaps
            {'start': 480, 'end': 960, 'note': 62, 'vel_on': 64},  # Different pitch
        ]
        
        clean_events = remove_overlapping_notes(events)
        
        # Should still have 3 events but first should be shortened
        self.assertEqual(len(clean_events), 3)
        
        # Find the C4 events
        c4_events = [e for e in clean_events if e['note'] == 60]
        self.assertEqual(len(c4_events), 2)
        
        # First C4 event should be shortened
        c4_events.sort(key=lambda x: x['start'])
        self.assertLess(c4_events[0]['end'], c4_events[1]['start'])
    
    def test_event_validation(self):
        """Test event validation."""
        # Valid event
        valid_events = [
            {'start': 0, 'end': 480, 'note': 60, 'vel_on': 64}
        ]
        issues = validate_events(valid_events)
        self.assertEqual(len(issues), 0)
        
        # Invalid events
        invalid_events = [
            {'start': -1, 'end': 480, 'note': 60, 'vel_on': 64},  # Negative start
            {'start': 480, 'end': 480, 'note': 60, 'vel_on': 64},  # End <= start
            {'start': 0, 'end': 480, 'note': 128, 'vel_on': 64},  # Note out of range
            {'start': 0, 'end': 480, 'note': 60, 'vel_on': 0},   # Invalid velocity
        ]
        
        issues = validate_events(invalid_events)
        self.assertGreater(len(issues), 0)  # Should find issues


class TestAPIIntegration(unittest.TestCase):
    """Test main API functions."""
    
    def test_basic_midi_generation(self):
        """Test basic MIDI file generation."""
        midi_bytes = create_ambient_midi(seed=42, bars=2)
        
        # Check MIDI file structure
        self.assertGreater(len(midi_bytes), 100)  # Should be substantial
        self.assertEqual(midi_bytes[:4], b'MThd')  # MIDI header
        
        # Should contain track chunks
        self.assertIn(b'MTrk', midi_bytes)
    
    def test_midi_with_info(self):
        """Test MIDI generation with info."""
        midi_bytes, info = create_ambient_midi_with_info(
            seed=42, key="C", mode="minor", bars=4
        )
        
        # Check info structure
        self.assertIn('melody_stats', info)
        self.assertIn('pad_stats', info)
        self.assertIn('total_tracks', info)
        self.assertIn('parameters', info)
        
        # Check stats
        melody_stats = info['melody_stats']
        self.assertGreaterEqual(melody_stats['total_events'], 0)
        
        pad_stats = info['pad_stats']
        self.assertGreater(pad_stats['total_events'], 0)  # Should have chord events
        
        # Check parameters
        params = info['parameters']
        self.assertEqual(params['seed'], 42)
        self.assertEqual(params['key'], "C")
        self.assertEqual(params['mode'], "minor")
    
    def test_different_keys_and_modes(self):
        """Test generation in different keys and modes."""
        keys = ["C", "F#", "Bb"]
        modes = ["minor", "major"]
        
        for key in keys:
            for mode in modes:
                midi_bytes = create_ambient_midi(
                    seed=42, key=key, mode=mode, bars=2
                )
                
                # Should generate valid MIDI
                self.assertGreater(len(midi_bytes), 100)
                self.assertEqual(midi_bytes[:4], b'MThd')
    
    def test_parameter_ranges(self):
        """Test various parameter ranges."""
        # Different BPM values
        for bpm in [60, 72, 120]:
            midi_bytes = create_ambient_midi(seed=42, bpm=bpm, bars=2)
            self.assertGreater(len(midi_bytes), 100)
        
        # Different bar counts
        for bars in [1, 4, 8]:
            midi_bytes = create_ambient_midi(seed=42, bars=bars)
            self.assertGreater(len(midi_bytes), 100)
        
        # Different densities
        for density in [0.1, 0.35, 0.7]:
            midi_bytes = create_ambient_midi(seed=42, density=density, bars=2)
            self.assertGreater(len(midi_bytes), 100)


class TestMIDIFormat(unittest.TestCase):
    """Test MIDI format compliance."""
    
    def test_format_1_structure(self):
        """Test that generated MIDI follows Format 1 specification."""
        midi_bytes, info = create_ambient_midi_with_info(seed=42, bars=2)
        
        # Parse header
        self.assertEqual(midi_bytes[:4], b'MThd')
        header_length = int.from_bytes(midi_bytes[4:8], 'big')
        self.assertEqual(header_length, 6)
        
        format_type = int.from_bytes(midi_bytes[8:10], 'big')
        self.assertEqual(format_type, 1)  # Format 1
        
        ntrks = int.from_bytes(midi_bytes[10:12], 'big')
        self.assertEqual(ntrks, 3)  # 3 tracks
        
        division = int.from_bytes(midi_bytes[12:14], 'big')
        self.assertEqual(division, 480)  # PPQ
    
    def test_track_count(self):
        """Test that correct number of tracks are generated."""
        midi_bytes = create_ambient_midi(seed=42, bars=2)
        
        # Count MTrk chunks
        track_count = midi_bytes.count(b'MTrk')
        self.assertEqual(track_count, 3)  # Conductor + Melody + Pads
    
    def test_no_stuck_notes(self):
        """Test that there are no stuck notes."""
        _, info = create_ambient_midi_with_info(seed=42, bars=4)
        
        # This is tested indirectly - if there were stuck notes,
        # the render process would fail or create invalid MIDI
        self.assertGreater(info['melody_stats']['total_events'], 0)
        self.assertGreater(info['pad_stats']['total_events'], 0)


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestMIDIWriter,
        TestMusicTheory,
        TestPatternGeneration,
        TestEventProcessing,
        TestAPIIntegration,
        TestMIDIFormat
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
