#!/usr/bin/env python3
"""
Simple test to debug MIDI generation issues
"""

import os
from music21 import stream, note, tempo, key, meter
import traceback

def test_midi_creation():
    try:
        print("Testing MIDI creation...")
        
        # Create a simple melody
        score = stream.Stream()
        
        # Add basic elements
        score.append(meter.TimeSignature('4/4'))
        score.append(key.Key('C', 'major'))
        score.append(tempo.TempoIndication(number=120))
        
        # Add some notes
        notes_data = [
            {'note': 'C4', 'duration': 1.0, 'velocity': 80},
            {'note': 'D4', 'duration': 1.0, 'velocity': 75},
            {'note': 'E4', 'duration': 1.0, 'velocity': 82},
            {'note': 'F4', 'duration': 1.0, 'velocity': 78}
        ]
        
        for note_info in notes_data:
            n = note.Note(note_info['note'])
            n.quarterLength = note_info['duration']
            n.volume.velocity = note_info['velocity']
            score.append(n)
        
        print("Score created successfully")
        
        # Try to write MIDI file
        output_path = os.path.join('static', 'generated', 'test_output.mid')
        print(f"Attempting to write to: {output_path}")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write MIDI file
        score.write('midi', fp=output_path)
        print(f"MIDI file created successfully: {output_path}")
        
        # Check if file exists
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            print(f"File exists! Size: {size} bytes")
            return True
        else:
            print("File was not created!")
            return False
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_midi_creation()
    print(f"Test result: {'SUCCESS' if success else 'FAILED'}")
