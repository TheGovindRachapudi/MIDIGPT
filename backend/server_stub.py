#!/usr/bin/env python3
"""
Flask integration stub for the MIDI Engine.

Demonstrates how to integrate the MIDI engine with web endpoints.
Run with: python server_stub.py
"""

from flask import Flask, send_file, request, make_response, jsonify
import io
import sys
from pathlib import Path

# Add midi_engine to path
sys.path.insert(0, str(Path(__file__).parent))

from midi_engine.api import create_ambient_midi_with_info, create_ambient_midi

app = Flask(__name__)


@app.route("/")
def index():
    """Basic info page."""
    return """
    <h1>🎵 MIDI Engine API</h1>
    <p>Production-ready ambient MIDI generation</p>
    
    <h2>Endpoints:</h2>
    <ul>
        <li><a href="/api/midi/ambient">/api/midi/ambient</a> - Generate ambient MIDI</li>
        <li><a href="/api/midi/ambient?key=F%23&mode=minor&bpm=60&bars=16">/api/midi/ambient?key=F#&mode=minor&bpm=60&bars=16</a> - Custom parameters</li>
        <li><a href="/api/midi/info?seed=123&key=Bb">/api/midi/info</a> - Generation info (JSON)</li>
    </ul>
    
    <h2>Parameters:</h2>
    <ul>
        <li><b>seed</b>: Random seed (default: 42)</li>
        <li><b>key</b>: Root key - C, C#, Db, D, D#, Eb, E, F, F#, Gb, G, G#, Ab, A, A#, Bb, B (default: C)</li>
        <li><b>mode</b>: minor, major (default: minor)</li>
        <li><b>bpm</b>: Beats per minute (default: 72)</li>
        <li><b>bars</b>: Number of bars (default: 8)</li>
        <li><b>density</b>: Melody density 0.0-1.0 (default: 0.35)</li>
        <li><b>melody_program</b>: GM program 0-127 (default: 0 = Piano)</li>
        <li><b>pad_program</b>: GM program 0-127 (default: 88 = New Age Pad)</li>
    </ul>
    
    <p><em>Perfect for sad, ambient music like "Codeine Crazy" vibes!</em></p>
    """


@app.route("/api/midi/ambient")
def ambient_midi():
    """Generate and return ambient MIDI file."""
    try:
        # Parse parameters with validation
        seed = int(request.args.get("seed", 42))
        key = request.args.get("key", "C")
        mode = request.args.get("mode", "minor")
        bpm = int(request.args.get("bpm", 72))
        bars = int(request.args.get("bars", 8))
        density = float(request.args.get("density", 0.35))
        melody_program = int(request.args.get("melody_program", 0))
        pad_program = int(request.args.get("pad_program", 88))
        
        # Validate parameters
        if key not in ['C', 'C#', 'Db', 'D', 'D#', 'Eb', 'E', 'F', 'F#', 'Gb', 'G', 'G#', 'Ab', 'A', 'A#', 'Bb', 'B']:
            return jsonify({"error": f"Invalid key: {key}"}), 400
        
        if mode not in ['minor', 'major']:
            return jsonify({"error": f"Invalid mode: {mode}"}), 400
        
        if not (30 <= bpm <= 200):
            return jsonify({"error": f"BPM must be between 30-200, got {bpm}"}), 400
        
        if not (1 <= bars <= 64):
            return jsonify({"error": f"Bars must be between 1-64, got {bars}"}), 400
        
        if not (0.0 <= density <= 1.0):
            return jsonify({"error": f"Density must be between 0.0-1.0, got {density}"}), 400
        
        if not (0 <= melody_program <= 127):
            return jsonify({"error": f"Melody program must be 0-127, got {melody_program}"}), 400
        
        if not (0 <= pad_program <= 127):
            return jsonify({"error": f"Pad program must be 0-127, got {pad_program}"}), 400
        
        # Generate MIDI
        midi_data = create_ambient_midi(
            seed=seed,
            key=key,
            mode=mode,
            bpm=bpm,
            bars=bars,
            density=density,
            melody_program=melody_program,
            pad_program=pad_program
        )
        
        # Create response
        filename = f"ambient_{key}_{mode}_{bpm}bpm_{bars}bars.mid"
        
        response = make_response(midi_data)
        response.headers['Content-Type'] = 'audio/midi'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Content-Length'] = len(midi_data)
        
        return response
        
    except ValueError as e:
        return jsonify({"error": f"Invalid parameter: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Generation failed: {str(e)}"}), 500


@app.route("/api/midi/info")
def midi_info():
    """Generate MIDI and return detailed info as JSON."""
    try:
        # Parse parameters (same validation as above)
        seed = int(request.args.get("seed", 42))
        key = request.args.get("key", "C")
        mode = request.args.get("mode", "minor")
        bpm = int(request.args.get("bpm", 72))
        bars = int(request.args.get("bars", 8))
        density = float(request.args.get("density", 0.35))
        melody_program = int(request.args.get("melody_program", 0))
        pad_program = int(request.args.get("pad_program", 88))
        
        # Basic validation (abbreviated for brevity)
        if key not in ['C', 'C#', 'Db', 'D', 'D#', 'Eb', 'E', 'F', 'F#', 'Gb', 'G', 'G#', 'Ab', 'A', 'A#', 'Bb', 'B']:
            return jsonify({"error": f"Invalid key: {key}"}), 400
        
        # Generate with info
        midi_data, info = create_ambient_midi_with_info(
            seed=seed,
            key=key,
            mode=mode,
            bpm=bpm,
            bars=bars,
            density=density,
            melody_program=melody_program,
            pad_program=pad_program
        )
        
        # Add file size to info
        info['file_size'] = len(midi_data)
        info['success'] = True
        
        return jsonify(info)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Generation failed: {str(e)}"
        }), 500


@app.route("/api/health")
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "MIDI Engine API",
        "version": "1.0.0"
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "/api/midi/ambient",
            "/api/midi/info", 
            "/api/health"
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors.""" 
    return jsonify({
        "error": "Internal server error",
        "message": "Something went wrong with MIDI generation"
    }), 500


if __name__ == "__main__":
    print("🎵 Starting MIDI Engine API server...")
    print("🌐 Access at: http://localhost:5001")
    print("📚 API docs at: http://localhost:5001")
    print("🎹 Try: http://localhost:5001/api/midi/ambient?key=C&mode=minor&bpm=72")
    
    app.run(
        host='0.0.0.0',
        port=5001, 
        debug=True,
        threaded=True
    )
