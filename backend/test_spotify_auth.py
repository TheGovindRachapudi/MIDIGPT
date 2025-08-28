#!/usr/bin/env python3

import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()
client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

# Define the scope for the permissions we need
scope = "user-library-read"
redirect_uri = "http://localhost:8888/callback"

# Try to authenticate with user authorization
try:
    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        open_browser=False  # Set to True if you want to automatically open the auth URL
    )
    
    # Get the authorization URL
    auth_url = auth_manager.get_authorize_url()
    print("\n=== Spotify Authentication ===")
    print("Please open this URL in your browser to authorize the application:")
    print(auth_url)
    print("\nAfter authorizing, you will be redirected to a URL that starts with 'http://localhost:8888/callback?code='.")
    print("Please copy the full URL and paste it here:")
    
    # Get the redirected URL from the user
    redirected_url = input("\nEnter the redirected URL: ")
    
    # Extract the authorization code
    code = auth_manager.parse_response_code(redirected_url)
    
    # Get the access token
    token_info = auth_manager.get_access_token(code)
    access_token = token_info['access_token']
    
    print("\n✅ Successfully authenticated with Spotify!")
    
    # Create a new Spotify client with the access token
    sp = spotipy.Spotify(auth=access_token)
    
    # Test audio features again
    track_id = "0DrDcqWpokMlhKYJSwoT4B"  # Don't Stop Me Now
    print(f'\nTesting audio features for track ID: {track_id}')
    
    try:
        audio_features = sp.audio_features([track_id])
        if audio_features[0]:
            print('✅ Audio features retrieved successfully!')
            print(f'  Tempo: {audio_features[0]["tempo"]}')
            print(f'  Energy: {audio_features[0]["energy"]}')
            print(f'  Key: {audio_features[0]["key"]}')
            print(f'  Mode: {audio_features[0]["mode"]}')
        else:
            print('❌ Audio features are None')
    except Exception as e:
        print(f'❌ Audio features failed: {str(e)}')
        
except Exception as e:
    print(f"\n❌ Authentication failed: {str(e)}")
