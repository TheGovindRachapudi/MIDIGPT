#!/usr/bin/env python3

import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()
client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

client_credentials_manager = SpotifyClientCredentials(
    client_id=client_id,
    client_secret=client_secret
)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# Test search (we know this works)
print('=== Testing Search ===')
results = sp.search(q="Don't Stop Me Now Queen", type='track', limit=1)
track = results['tracks']['items'][0]
track_id = track['id']
print(f'Found track: {track["name"]} by {track["artists"][0]["name"]}')
print(f'Track ID: {track_id}')

# Test audio features (this is failing)
print('\n=== Testing Audio Features ===')
try:
    audio_features = sp.audio_features([track_id])
    print('Audio features retrieved successfully!')
    if audio_features[0]:
        print(f'Tempo: {audio_features[0]["tempo"]}')
        print(f'Energy: {audio_features[0]["energy"]}')
        print(f'Key: {audio_features[0]["key"]}')
        print(f'Mode: {audio_features[0]["mode"]}')
    else:
        print('Audio features are None')
except Exception as e:
    print(f'Audio features failed: {str(e)}')

# Test audio analysis (this might also fail)
print('\n=== Testing Audio Analysis ===')
try:
    audio_analysis = sp.audio_analysis(track_id)
    print('Audio analysis retrieved successfully!')
    sections = audio_analysis.get("sections", [])
    print(f'Sections: {len(sections)}')
    if sections:
        print(f'First section tempo: {sections[0].get("tempo", "N/A")}')
except Exception as e:
    print(f'Audio analysis failed: {str(e)}')
