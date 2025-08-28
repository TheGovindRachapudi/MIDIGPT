#!/usr/bin/env python3
"""
Extended test to verify improved variety in audio features generation
"""

from spotify_utils import SpotifyClient

def test_audio_feature_variety():
    """Test that different songs produce different audio features"""
    
    spotify_client = SpotifyClient()
    
    # Test a variety of song types
    test_songs = [
        {"name": "All You Need Is Love", "artists": [{"name": "The Beatles"}], "popularity": 90},
        {"name": "Thriller", "artists": [{"name": "Michael Jackson"}], "popularity": 95},
        {"name": "Smells Like Teen Spirit", "artists": [{"name": "Nirvana"}], "popularity": 88},
        {"name": "Hallelujah", "artists": [{"name": "Leonard Cohen"}], "popularity": 85},
        {"name": "I Will Always Love You", "artists": [{"name": "Whitney Houston"}], "popularity": 92},
        {"name": "Bohemian Rhapsody", "artists": [{"name": "Queen"}], "popularity": 94},
        {"name": "Sweet Child O' Mine", "artists": [{"name": "Guns N' Roses"}], "popularity": 89},
        {"name": "Hotel California", "artists": [{"name": "Eagles"}], "popularity": 91},
        {"name": "Imagine", "artists": [{"name": "John Lennon"}], "popularity": 87},
        {"name": "Like a Rolling Stone", "artists": [{"name": "Bob Dylan"}], "popularity": 86},
        # Test newer/different songs
        {"name": "Good 4 U", "artists": [{"name": "Olivia Rodrigo"}], "popularity": 93},
        {"name": "Blinding Lights", "artists": [{"name": "The Weeknd"}], "popularity": 95},
        {"name": "Watermelon Sugar", "artists": [{"name": "Harry Styles"}], "popularity": 90},
        {"name": "Levitating", "artists": [{"name": "Dua Lipa"}], "popularity": 88},
        {"name": "Industry Baby", "artists": [{"name": "Lil Nas X"}], "popularity": 87},
    ]
    
    results = []
    
    print("🎵 Testing Audio Feature Variety")
    print("=" * 80)
    
    for track in test_songs:
        estimated_features = spotify_client._create_estimated_audio_features(track)
        
        result = {
            'song': f"{track['name']} by {track['artists'][0]['name']}",
            'valence': round(estimated_features.get('valence', 0), 3),
            'danceability': round(estimated_features.get('danceability', 0), 3),
            'energy': round(estimated_features.get('energy', 0), 3),
            'tempo': estimated_features.get('tempo', 0),
            'key': estimated_features.get('key', 0),
            'mode': estimated_features.get('mode', 1)
        }
        results.append(result)
        
        print(f"🎵 {result['song']}")
        print(f"   Valence: {result['valence']}, Danceability: {result['danceability']}, Energy: {result['energy']}")
        print(f"   Tempo: {result['tempo']} BPM, Key: {spotify_client.key_mapping[result['key']]} {spotify_client.mode_mapping[result['mode']]}")
        print()
    
    # Analyze variety
    print("📊 Variety Analysis")
    print("=" * 80)
    
    valences = [r['valence'] for r in results]
    danceabilities = [r['danceability'] for r in results]
    energies = [r['energy'] for r in results]
    tempos = [r['tempo'] for r in results]
    
    print(f"Valence values: {sorted(set(valences))}")
    print(f"Danceability values: {sorted(set(danceabilities))}")
    print(f"Energy values: {sorted(set(energies))}")
    print(f"Tempo values: {sorted(set(tempos))}")
    
    unique_valences = len(set(valences))
    unique_danceabilities = len(set(danceabilities))
    unique_energies = len(set(energies))
    unique_tempos = len(set(tempos))
    
    total_songs = len(results)
    
    print(f"\\nUnique valence values: {unique_valences}/{total_songs} ({unique_valences/total_songs*100:.1f}%)")
    print(f"Unique danceability values: {unique_danceabilities}/{total_songs} ({unique_danceabilities/total_songs*100:.1f}%)")
    print(f"Unique energy values: {unique_energies}/{total_songs} ({unique_energies/total_songs*100:.1f}%)")
    print(f"Unique tempo values: {unique_tempos}/{total_songs} ({unique_tempos/total_songs*100:.1f}%)")
    
    # Calculate ranges
    valence_range = max(valences) - min(valences)
    danceability_range = max(danceabilities) - min(danceabilities)
    energy_range = max(energies) - min(energies)
    tempo_range = max(tempos) - min(tempos)
    
    print(f"\\nValue ranges:")
    print(f"Valence range: {valence_range:.3f} (min: {min(valences):.3f}, max: {max(valences):.3f})")
    print(f"Danceability range: {danceability_range:.3f} (min: {min(danceabilities):.3f}, max: {max(danceabilities):.3f})")
    print(f"Energy range: {energy_range:.3f} (min: {min(energies):.3f}, max: {max(energies):.3f})")
    print(f"Tempo range: {tempo_range} BPM (min: {min(tempos)}, max: {max(tempos)})")
    
    # Check for success criteria
    print(f"\\n✅ Success Criteria Check:")
    success = True
    
    if unique_valences < total_songs * 0.8:  # At least 80% unique
        print(f"❌ Valence variety insufficient: {unique_valences}/{total_songs}")
        success = False
    else:
        print(f"✅ Valence variety good: {unique_valences}/{total_songs}")
    
    if unique_danceabilities < total_songs * 0.8:
        print(f"❌ Danceability variety insufficient: {unique_danceabilities}/{total_songs}")
        success = False
    else:
        print(f"✅ Danceability variety good: {unique_danceabilities}/{total_songs}")
    
    if valence_range < 0.4:  # Should have significant range
        print(f"❌ Valence range too narrow: {valence_range:.3f}")
        success = False
    else:
        print(f"✅ Valence range sufficient: {valence_range:.3f}")
        
    if danceability_range < 0.4:
        print(f"❌ Danceability range too narrow: {danceability_range:.3f}")
        success = False
    else:
        print(f"✅ Danceability range sufficient: {danceability_range:.3f}")
    
    if success:
        print("\\n🎉 ALL TESTS PASSED! Audio feature variety has been successfully improved!")
    else:
        print("\\n❌ Some tests failed. Audio feature variety needs more improvement.")
    
    return success

if __name__ == "__main__":
    test_audio_feature_variety()
