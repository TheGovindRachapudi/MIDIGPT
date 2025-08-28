#!/usr/bin/env python3
"""
Demo CLI for the MIDI Engine.

Generates ambient MIDI files from command line arguments.
"""

import argparse
import sys
import os
import time
from pathlib import Path

# Add the parent directory to sys.path so we can import midi_engine
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from midi_engine.api import create_ambient_midi_with_info


def main():
    parser = argparse.ArgumentParser(
        description="Generate ambient MIDI files using the MIDI Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m midi_engine.examples.demo --out ambient.mid
  python -m midi_engine.examples.demo --key F# --mode minor --bpm 60 --bars 16
  python -m midi_engine.examples.demo --seed 123 --key Bb --bpm 80 --out sad_song.mid
        """
    )
    
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducible generation (default: 42)')
    
    parser.add_argument('--key', default='C',
                       choices=['C', 'C#', 'Db', 'D', 'D#', 'Eb', 'E', 'F', 
                               'F#', 'Gb', 'G', 'G#', 'Ab', 'A', 'A#', 'Bb', 'B'],
                       help='Root key (default: C)')
    
    parser.add_argument('--mode', default='minor',
                       choices=['minor', 'major'],
                       help='Scale mode (default: minor)')
    
    parser.add_argument('--bpm', type=int, default=72,
                       help='Beats per minute (default: 72)')
    
    parser.add_argument('--bars', type=int, default=8,
                       help='Number of bars to generate (default: 8)')
    
    parser.add_argument('--density', type=float, default=0.35,
                       help='Melody note density 0.0-1.0 (default: 0.35)')
    
    parser.add_argument('--melody-program', type=int, default=0,
                       help='GM program for melody (default: 0 = Acoustic Grand Piano)')
    
    parser.add_argument('--pad-program', type=int, default=88,
                       help='GM program for pads (default: 88 = New Age Pad)')
    
    parser.add_argument('--out', default='ambient_demo.mid',
                       help='Output filename (default: ambient_demo.mid)')
    
    parser.add_argument('--info', action='store_true',
                       help='Display detailed generation info')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not (0.0 <= args.density <= 1.0):
        parser.error("Density must be between 0.0 and 1.0")
    
    if not (0 <= args.melody_program <= 127):
        parser.error("Melody program must be between 0 and 127")
    
    if not (0 <= args.pad_program <= 127):
        parser.error("Pad program must be between 0 and 127")
    
    if args.bpm <= 0:
        parser.error("BPM must be positive")
    
    if args.bars <= 0:
        parser.error("Bars must be positive")
    
    # Generate MIDI
    print(f"🎵 Generating ambient MIDI...")
    print(f"   Key: {args.key} {args.mode}")
    print(f"   Tempo: {args.bpm} BPM")
    print(f"   Length: {args.bars} bars")
    print(f"   Seed: {args.seed}")
    print(f"   Density: {args.density:.2f}")
    
    start_time = time.time()
    
    try:
        midi_bytes, info = create_ambient_midi_with_info(
            seed=args.seed,
            key=args.key,
            mode=args.mode,
            bpm=args.bpm,
            bars=args.bars,
            melody_program=args.melody_program,
            pad_program=args.pad_program,
            density=args.density
        )
        
        generation_time = time.time() - start_time
        
        # Write file
        with open(args.out, 'wb') as f:
            f.write(midi_bytes)
        
        # Display results
        print(f"✅ Generated successfully in {generation_time:.2f}s")
        print(f"   Output: {args.out}")
        print(f"   Size: {len(midi_bytes):,} bytes")
        print(f"   Tracks: {info['total_tracks']}")
        
        if args.info:
            print(f"\n📊 Generation Details:")
            
            melody_stats = info['melody_stats']
            print(f"   Melody:")
            print(f"     - Notes: {melody_stats['total_events']}")
            print(f"     - Range: {melody_stats['note_range']}")
            print(f"     - Velocity: {melody_stats['velocity_range']}")
            print(f"     - Avg Duration: {melody_stats['average_duration']:.0f} ticks")
            print(f"     - Unique Pitches: {melody_stats['unique_pitches']}")
            
            pad_stats = info['pad_stats']
            print(f"   Pads:")
            print(f"     - Notes: {pad_stats['total_events']}")
            print(f"     - Range: {pad_stats['note_range']}")
            print(f"     - Velocity: {pad_stats['velocity_range']}")
            print(f"     - Avg Duration: {pad_stats['average_duration']:.0f} ticks")
            print(f"     - Unique Pitches: {pad_stats['unique_pitches']}")
            
            total_duration_bars = max(melody_stats['total_ticks'], 
                                    pad_stats['total_ticks']) / (480 * 4)
            print(f"   Total Duration: {total_duration_bars:.1f} bars")
        
        print(f"\n🎹 Try opening {args.out} in your DAW!")
        print(f"   Expected sound: Sad, ambient, like 'Codeine Crazy' vibes")
        print(f"   Progression: {args.key}m(add9) | {get_progression_chord(args.key, 1)} | {get_progression_chord(args.key, 2)} | {get_progression_chord(args.key, 3)}")
        
    except Exception as e:
        print(f"❌ Generation failed: {str(e)}")
        sys.exit(1)


def get_progression_chord(key: str, position: int) -> str:
    """Get chord name for progression position."""
    # Simple mapping for display purposes
    chord_offsets = [8, 5, 10]  # bVI, iv, bVII relative to minor key
    chord_types = ["maj7", "m(add9)", "sus2"]
    
    if position < len(chord_offsets):
        # This is a simplified display - real chord calculation is in theory.py
        return f"Chord{position + 1}"
    return ""


if __name__ == "__main__":
    main()
