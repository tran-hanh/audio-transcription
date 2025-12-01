#!/usr/bin/env python3
"""
Flask API server for audio transcription
Handles file uploads and transcription requests
"""

import json
import os
import tempfile

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from werkzeug.utils import secure_filename

from transcribe import transcribe_audio

app = Flask(__name__)
CORS(app)  # Enable CORS for GitHub Pages

# Configuration
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB (matching frontend limit)
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'flac', 'ogg', 'aac', 'wma'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def send_progress(progress, message):
    """Send progress update as SSE"""
    return f"data: {json.dumps({'progress': progress, 'message': message})}\n\n"


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200


@app.route('/transcribe', methods=['POST'])
def transcribe():
    """Handle audio file upload and transcription"""
    try:
        # Check if file is present
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        file = request.files['audio']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            allowed_types = ', '.join(ALLOWED_EXTENSIONS)
            return jsonify({
                'error': f'File type not allowed. Allowed types: {allowed_types}'
            }), 400

        # Get API key
        api_key = request.form.get('api_key')
        if not api_key:
            return jsonify({'error': 'API key not provided'}), 400

        # Get chunk length
        chunk_length = int(request.form.get('chunk_length', 12))
        if chunk_length < 1 or chunk_length > 30:
            chunk_length = 12

        # Save uploaded file temporarily
        temp_dir = tempfile.mkdtemp(prefix='audio_upload_')
        temp_input_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(temp_input_path)

        # Check file size
        file_size = os.path.getsize(temp_input_path)
        if file_size > MAX_FILE_SIZE:
            os.remove(temp_input_path)
            os.rmdir(temp_dir)
            max_size_mb = MAX_FILE_SIZE / (1024 * 1024)
            return jsonify({
                'error': f'File too large. Maximum size: {max_size_mb:.0f} MB'
            }), 400

        # Create temporary output path
        temp_output_path = os.path.join(temp_dir, 'transcript.txt')

        def generate():
            """Generator function for streaming response"""
            try:
                # Send initial progress
                yield send_progress(5, 'File uploaded, starting transcription...')

                # Transcribe audio
                yield send_progress(10, 'Processing audio chunks...')

                output_path = transcribe_audio(
                    input_path=temp_input_path,
                    output_path=temp_output_path,
                    api_key=api_key,
                    chunk_length_minutes=chunk_length
                )

                yield send_progress(90, 'Reading transcript...')

                # Read transcript
                with open(output_path, 'r', encoding='utf-8') as f:
                    transcript = f.read()

                # Send final result
                yield send_progress(100, 'Transcription complete!')
                yield f"data: {json.dumps({'transcript': transcript})}\n\n"

            except Exception as e:
                error_msg = str(e)
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
            finally:
                # Cleanup
                try:
                    if os.path.exists(temp_input_path):
                        os.remove(temp_input_path)
                    if os.path.exists(temp_output_path):
                        os.remove(temp_output_path)
                    os.rmdir(temp_dir)
                except OSError:
                    pass

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
