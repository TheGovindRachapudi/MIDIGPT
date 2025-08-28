/**
 * Test script for MIDI playback functionality
 * Run this in the browser console to test MIDI player
 */

async function testMIDIPlayback() {
  try {
    console.log('🎵 Testing MIDI Playback Functionality...');
    
    // Test 1: Import the MIDI player
    console.log('1. Testing MIDI player import...');
    const { MIDIPlayer } = await import('./src/utils/midiPlayer.js');
    const player = new MIDIPlayer();
    console.log('✅ MIDI player imported successfully');
    
    // Test 2: Initialize audio context
    console.log('2. Testing audio context initialization...');
    const initialized = await player.initialize();
    if (initialized) {
      console.log('✅ Audio context and soundfonts loaded');
    } else {
      console.log('❌ Failed to initialize audio context');
      return;
    }
    
    // Test 3: Get player state
    console.log('3. Testing player state...');
    const state = player.getState();
    console.log('Player state:', state);
    console.log('✅ Player state retrieved');
    
    // Test 4: Test volume control
    console.log('4. Testing volume control...');
    player.setVolume(0.8);
    const newState = player.getState();
    if (newState.volume === 0.8) {
      console.log('✅ Volume control working');
    } else {
      console.log('❌ Volume control failed');
    }
    
    // Test 5: Test with a generated MIDI file (if available)
    console.log('5. Testing with actual MIDI file...');
    const midiFiles = document.querySelectorAll('[href*=".mid"]');
    if (midiFiles.length > 0) {
      const midiUrl = midiFiles[0].href;
      console.log(`Found MIDI file: ${midiUrl}`);
      
      const loadSuccess = await player.loadMIDI(midiUrl);
      if (loadSuccess) {
        const loadedState = player.getState();
        console.log(`✅ MIDI file loaded successfully`);
        console.log(`Duration: ${loadedState.duration}s, BPM: ${loadedState.bpm}`);
        
        // Test playback for 2 seconds
        console.log('Starting playback test...');
        await player.play();
        await new Promise(resolve => setTimeout(resolve, 2000));
        player.pause();
        console.log('✅ Playback test completed');
      } else {
        console.log('❌ Failed to load MIDI file');
      }
    } else {
      console.log('⚠️ No MIDI files found for testing');
    }
    
    // Cleanup
    player.dispose();
    console.log('🧹 Cleanup completed');
    
    console.log('🎉 MIDI playback functionality test completed!');
    
  } catch (error) {
    console.error('❌ MIDI playback test failed:', error);
  }
}

// Instructions for manual testing
console.log(`
📋 MIDI Playback Testing Instructions:

1. Open your browser's developer console
2. Navigate to http://localhost:3000
3. Generate a MIDI file using the interface
4. Once a MIDI file is generated, run: testMIDIPlayback()
5. Alternatively, click the play button in the interface to test directly

The MIDI player should:
✅ Load MIDI files from URLs
✅ Parse MIDI data and extract duration/BPM
✅ Play audio using acoustic piano sounds
✅ Support play/pause/seek/volume controls
✅ Display real-time playback progress

Note: 
- First playback may require user interaction (click play button)
- Audio context requires user gesture in modern browsers
- Soundfont loading may take a few seconds on first use
`);

// Export for global access
window.testMIDIPlayback = testMIDIPlayback;
