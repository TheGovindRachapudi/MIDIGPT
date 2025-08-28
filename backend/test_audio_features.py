#!/usr/bin/env python3
"""
Test script to check Spotify audio features extraction and identify valence/danceability issues
"""

import sys
import os
import logging
from spotify_utils import SpotifyClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_spotify_features():
    """Test Spotify features extraction for different songs"""
    
    # Initialize Spotify client
    spotify_client = SpotifyClient()
    
    if not spotify_client.sp:
        print("❌ Spotify client not available - checking estimated features instead")
        test_estimated_features()
        return
    
    # Test songs with different expected characteristics
    test_songs = [
        {"song": "Happy", "artist": "Pharrell Williams", "expected": "high valence/danceability"},
        {"song": "Someone Like You", "artist": "Adele", "expected": "low valence/danceability"},
        {"song": "Billie Jean", "artist": "Michael Jackson", "expected": "medium-high danceability"},
        {"song": "Yesterday", "artist": "The Beatles", "expected": "low valence"},
        {"song": "Uptown Funk", "artist": "Bruno Mars", "expected": "very high danceability/valence"}
    ]
    
    print("🎵 Testing Spotify Audio Features Extraction")
    print("=" * 60)
    
    for test_song in test_songs:
        print(f"\n🎵 Testing: {test_song['song']} by {test_song['artist']}")
        print(f"Expected: {test_song['expected']}")
        
        # Get comprehensive track data
        search_query = f"{test_song['song']} {test_song['artist']}"
        spotify_data = spotify_client.get_comprehensive_track_data(search_query)
        
        if spotify_data:
            audio_features = spotify_data.get('audio_features', {})
            
            print(f"Valence: {audio_features.get('valence', 'N/A')}")
            print(f"Danceability: {audio_features.get('danceability', 'N/A')}")
            print(f"Energy: {audio_features.get('energy', 'N/A')}")
            print(f"Tempo: {audio_features.get('tempo', 'N/A')} BPM")
            print(f"Key: {audio_features.get('key_name', 'N/A')} {audio_features.get('mode_name', 'N/A')}")
        else:
            print("❌ No data retrieved")

def test_estimated_features():
    """Test the estimated features when Spotify API is not available"""
    
    spotify_client = SpotifyClient()
    
    # Test different song types
    test_tracks = [
        {"name": "Happy", "artists": [{"name": "Pharrell Williams"}], "popularity": 90},
        {"name": "Someone Like You", "artists": [{"name": "Adele"}], "popularity": 85},
        {"name": "Billie Jean", "artists": [{"name": "Michael Jackson"}], "popularity": 92},
        {"name": "Yesterday", "artists": [{"name": "The Beatles"}], "popularity": 88},
        {"name": "Uptown Funk", "artists": [{"name": "Bruno Mars"}], "popularity": 95},
        {"name": "Party All Night", "artists": [{"name": "Test Artist"}], "popularity": 70},
        {"name": "Sad Song", "artists": [{"name": "Test Artist"}], "popularity": 60},
        {"name": "Dark Night", "artists": [{"name": "Test Artist"}], "popularity": 50}
    ]
    
    print("🧪 Testing Estimated Audio Features")
    print("=" * 60)
    
    for track in test_tracks:
        print(f"\n🎵 Testing: {track['name']} by {track['artists'][0]['name']}")
        
        # Create estimated audio features
        estimated_features = spotify_client._create_estimated_audio_features(track)
        
        print(f"Valence: {estimated_features.get('valence', 'N/A'):.3f}")
        print(f"Danceability: {estimated_features.get('danceability', 'N/A'):.3f}")
        print(f"Energy: {estimated_features.get('energy', 'N/A'):.3f}")
        print(f"Tempo: {estimated_features.get('tempo', 'N/A')} BPM")
        print(f"Key: {estimated_features.get('key', 'N/A')} (Mode: {estimated_features.get('mode', 'N/A')})")

def check_known_songs_database():
    """Check the known songs database for duplicate values"""
    
    spotify_client = SpotifyClient()
    
    print("\n🗂️  Checking Known Songs Database")
    print("=" * 60)
    
    # Get the known_songs from the method (we need to access it indirectly)
    known_songs = {
        ('rather be', 'clean bandit'): {
            'tempo': 121, 'key': 7, 'mode': 1,  # G major
            'energy': 0.8, 'valence': 0.9, 'danceability': 0.85
        },
        ('billie jean', 'michael jackson'): {
            'tempo': 117, 'key': 6, 'mode': 0,  # F# minor
            'energy': 0.75, 'valence': 0.4, 'danceability': 0.75
        },
        ('sweet child o mine', 'guns n roses'): {
            'tempo': 125, 'key': 2, 'mode': 1,  # D major
            'energy': 0.95, 'valence': 0.6, 'danceability': 0.5
        },
        ('bohemian rhapsody', 'queen'): {
            'tempo': 72, 'key': 10, 'mode': 1,  # Bb major
            'energy': 0.6, 'valence': 0.5, 'danceability': 0.3
        },
        ('stayin alive', 'bee gees'): {
            'tempo': 104, 'key': 10, 'mode': 0,  # Bb minor
            'energy': 0.8, 'valence': 0.7, 'danceability': 0.9
        },
    }
    
    print("Valence values in database:")
    for song, features in known_songs.items():
        print(f"{song[0]} by {song[1]}: {features['valence']}")
    
    print("\nDanceability values in database:")
    for song, features in known_songs.items():
        print(f"{song[0]} by {song[1]}: {features['danceability']}")
    
    # Check for duplicates
    valence_values = [features['valence'] for features in known_songs.values()]
    danceability_values = [features['danceability'] for features in known_songs.values()]
    
    print(f"\nUnique valence values: {len(set(valence_values))} out of {len(valence_values)}")
    print(f"Unique danceability values: {len(set(danceability_values))} out of {len(danceability_values)}")
    
    if len(set(valence_values)) < len(valence_values):
        print("❌ Found duplicate valence values!")
    if len(set(danceability_values)) < len(danceability_values):
        print("❌ Found duplicate danceability values!")

if __name__ == "__main__":
    print("🔍 MIDI Audio Features Diagnostic Tool")
    print("=" * 80)
    
    # Check known songs database first
    check_known_songs_database()
    
    # Test current implementation
    test_estimated_features()
    
    # Test actual Spotify API if available
    test_spotify_features()
    
    print("\n✅ Diagnostic complete!")
