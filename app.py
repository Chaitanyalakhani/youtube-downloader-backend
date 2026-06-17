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

@app.route('/info', methods=['POST'])
def get_video_info():
    try:
        data = request.json
        url = data.get('url')

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1',
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Get available formats
            formats = info.get('formats', [])
            video_formats = []

            # Group by quality
            for fmt in formats:
                if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
                    height = fmt.get('height', 0)
                    if height in [2160, 1080, 720, 480]:
                        video_formats.append({
                            'format_id': fmt['format_id'],
                            'height': height,
                            'fps': fmt.get('fps', 30),
                            'filesize': fmt.get('filesize', 0),
                        })

            # Remove duplicates, keep best quality for each height
            best_formats = {}
            for fmt in video_formats:
                height = fmt['height']
                if height not in best_formats or fmt['fps'] > best_formats[height]['fps']:
                    best_formats[height] = fmt

            return jsonify({
                'videoId': info.get('id'),
                'title': info.get('title', 'Video'),
                'duration': str(info.get('duration', 0)),
                'formats': best_formats,
            }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download_video():
    try:
        data = request.json
        url = data.get('url')
        quality = data.get('quality', '720')

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
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1',
            },
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
