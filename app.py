from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os
import tempfile
from pathlib import Path

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

        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, '%(title)s.%(ext)s')

        # Format selection based on quality
        quality_map = {
            '2160': 'bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]',
            '1080': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]',
            '720': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]',
            '480': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]',
        }

        format_string = quality_map.get(quality, quality_map['720'])

        ydl_opts = {
            'format': format_string,
            'outtmpl': output_path,
            'quiet': False,
            'no_warnings': True,
            'socket_timeout': 60,
            'retries': 3,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1',
                'Referer': 'https://www.youtube.com/',
            },
            'skip_unavailable_fragments': True,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_file = ydl.prepare_filename(info)

            return send_file(
                video_file,
                as_attachment=True,
                download_name=f"{info.get('title', 'video')}.mp4",
                mimetype='video/mp4'
            )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
