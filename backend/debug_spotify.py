#!/usr/bin/env python3

import os
import json
from dotenv import load_dotenv
from spotify_utils import SpotifyClient

# Load environment variables
load_dotenv()

def test_spotify_integration():
    print("=== Testing Spotify Integration ===")
    
    # Initialize Spotify client
    spotify_client = SpotifyClient()
    print(f"Spotify client initialized: {spotify_client.sp is not None}")
    
    if not spotify_client.sp:
        print("ERROR: Spotify client not initialized!")
        return
    
    # Test parameters (same as the failing request)
    song = "Don't Stop Me Now"
    artist = "Queen"
    spotify_track_id = ""
    
    print(f"\nTest parameters:")
    print(f"Song: {song}")
    print(f"Artist: {artist}")
    print(f"Track ID: {spotify_track_id}")
    
    # Test the same logic as in app.py lines 110-121
    spotify_data = None
    if song or artist or spotify_track_id:
        print("\nFetching comprehensive Spotify data...")
        
        # Get track data using different methods
        if spotify_track_id:
            spotify_data = spotify_client.get_track_by_id(spotify_track_id)
            print("Method: get_track_by_id")
        else:
            search_query = f"{song} {artist}".strip()
            print(f"Method: get_comprehensive_track_data with query: '{search_query}'")
            spotify_data = spotify_client.get_comprehensive_track_data(search_query)
    
    if spotify_data:
        print(f"\n✅ SUCCESS: Retrieved Spotify data!")
        print(f"Track name: {spotify_data.get('track_info', {}).get('name')}")
        print(f"Artist: {spotify_data.get('track_info', {}).get('artists', [])}")
        print(f"Audio features available: {spotify_data.get('audio_features') is not None}")
        
        # Check audio features
        audio_features = spotify_data.get('audio_features', {})
        if audio_features:
            print(f"\nAudio Features:")
            print(f"  Tempo: {audio_features.get('tempo', 'N/A')}")
            print(f"  Energy: {audio_features.get('energy', 'N/A')}")
            print(f"  Valence: {audio_features.get('valence', 'N/A')}")
            print(f"  Key: {audio_features.get('key', 'N/A')}")
            print(f"  Mode: {audio_features.get('mode', 'N/A')}")
        else:
            print("❌ No audio features found")
    else:
        print("❌ FAILED: No Spotify data retrieved")

if __name__ == "__main__":
    test_spotify_integration()
