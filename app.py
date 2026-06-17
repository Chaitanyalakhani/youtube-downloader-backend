from flask import Flask, request, send_file, jsonify, redirect
from flask_cors import CORS
import yt_dlp
import os
import tempfile
from pathlib import Path
import requests
import re

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    import re
    match = re.search(r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})', url)
    return match.group(1) if match else None

@app.route('/info', methods=['POST'])
def get_video_info():
    try:
        data = request.json
        url = data.get('url')

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL'}), 400

        # Try Invidious API (more reliable than YouTube direct)
        try:
            invidious_url = f'https://api.invidious.io/videos/{video_id}'
            response = requests.get(invidious_url, timeout=5)

            if response.status_code == 200:
                info = response.json()
                return jsonify({
                    'videoId': video_id,
                    'title': info.get('title', 'Video'),
                    'duration': str(info.get('length', 0)),
                    'formats': {
                        '2160': {'height': 2160},
                        '1080': {'height': 1080},
                        '720': {'height': 720},
                    },
                }), 200
        except:
            pass

        # Fallback: just return basic info with video ID
        return jsonify({
            'videoId': video_id,
            'title': f'Video {video_id}',
            'duration': '0',
            'formats': {
                '2160': {'height': 2160},
                '1080': {'height': 1080},
                '720': {'height': 720},
            },
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['GET', 'POST'])
def download_video():
    try:
        if request.method == 'POST':
            data = request.json
            url = data.get('url')
            quality = data.get('quality', '720')
        else:
            url = request.args.get('url')
            quality = request.args.get('quality', '720')

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL'}), 400

        # Get video info from Invidious
        try:
            invidious_url = f'https://api.invidious.io/videos/{video_id}'
            response = requests.get(invidious_url, timeout=10)

            if response.status_code == 200:
                info = response.json()
                title = info.get('title', 'video')

                # Get adaptive formats (video + audio combined)
                formats = info.get('formatStreams', [])

                # Map quality to format
                quality_map = {
                    '2160': 2160,
                    '1080': 1080,
                    '720': 720,
                    '480': 480,
                }

                target_height = quality_map.get(quality, 720)

                # Find best format matching quality
                selected_format = None
                for fmt in formats:
                    if fmt.get('resolution'):
                        height = int(fmt['resolution'].split('x')[1])
                        if height <= target_height:
                            if not selected_format or height > int(selected_format['resolution'].split('x')[1]):
                                selected_format = fmt

                if selected_format and selected_format.get('url'):
                    # Redirect to the Invidious stream URL
                    stream_url = selected_format['url']
                    return send_file(
                        requests.get(stream_url, stream=True, timeout=60).raw,
                        mimetype='video/mp4',
                        as_attachment=True,
                        download_name=f"{title}.mp4"
                    )
        except Exception as e:
            print(f"Invidious error: {e}")

        # Fallback: Redirect to y2meta
        return redirect(
            f"https://y2meta.com/?url={requests.utils.quote(url)}&vt=mp4&q={quality}",
            code=303
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
