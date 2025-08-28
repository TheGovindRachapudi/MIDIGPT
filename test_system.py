#!/usr/bin/env python3
"""
Quick test of the current MIDI generation system
"""

import requests
import json
import time

def test_current_system():
    """Test current system with a known song"""
    
    test_data = {
        "description": "energetic and uplifting pop song",
        "song": "Shape of You",
        "artist": "Ed Sheeran",
        "key": "C#",  # User specified - should be respected
        "mode": "minor",  # User specified - should be respected  
        "bpm": 130,
        "autoBpm": True,
        "duration": 8,
        "complexity": "medium",
        "use_spotify_structure": True
    }
    
    print(f"🎵 Testing with: {test_data['song']} by {test_data['artist']}")
    print(f"User key/mode: {test_data['key']} {test_data['mode']}")
    print("Sending request...")
    
    try:
        response = requests.post("http://127.0.0.1:5000/generate", json=test_data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            musical_params = result.get('musical_params', {})
            
            print("✅ Success!")
            print(f"Generated Key: {musical_params.get('key')}")
            print(f"Generated Mode: {musical_params.get('mode')}")
            print(f"Tempo: {musical_params.get('tempo')} BPM")
            print(f"Notes Count: {result.get('generation_info', {}).get('notes_generated', 0)}")
            
            # Check if user preferences were respected
            if musical_params.get('key') == test_data['key'] and musical_params.get('mode') == test_data['mode']:
                print("✅ User key/mode respected!")
            else:
                print("❌ User key/mode NOT respected")
            
            return result
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    test_current_system()
