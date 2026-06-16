# YouTube Downloader Backend

A self-hosted Flask backend for downloading YouTube videos in full quality.

## Features
- Download videos in 4K, 1080p, 720p, and 480p
- Full audio included
- Fast and reliable
- CORS enabled for frontend integration

## Deployment on Railway

### Step 1: Create GitHub Repository

```bash
git init
git add .
git commit -m "Initial commit: YouTube downloader backend"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/youtube-downloader-backend.git
git push -u origin main
```

### Step 2: Deploy to Railway

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub"
4. Connect your GitHub account and select the `youtube-downloader-backend` repository
5. Railway will auto-detect it's a Python app and deploy it
6. Once deployed, you'll get a URL like `https://youtube-downloader-backend-production.up.railway.app`

### Step 3: Update Frontend

Update your Vercel frontend to use the backend URL:

In `app/api/download/route.ts` and `app/api/stream/route.ts`, replace the endpoint URLs with your Railway backend URL.

## Local Testing

```bash
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:5000/health` to verify it's running.

## API Endpoints

### GET /health
Health check endpoint.

**Response:**
```json
{ "status": "ok" }
```

### POST /info
Get video information and available formats.

**Request:**
```json
{ "url": "https://www.youtube.com/watch?v=VIDEO_ID" }
```

**Response:**
```json
{
  "videoId": "VIDEO_ID",
  "title": "Video Title",
  "duration": "180",
  "formats": {
    "2160": { "format_id": "...", "height": 2160 },
    "1080": { "format_id": "...", "height": 1080 }
  }
}
```

### POST /download
Download a video.

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "quality": "720"
}
```

**Response:**
Returns the video file as MP4.

## Cost

Railway.app pricing:
- **Free tier**: $5/month credits (usually enough for moderate usage)
- **Pay as you go**: Additional usage billed at standard rates

## Notes

- Videos are processed on the server and streamed directly
- Large videos may take time to process
- Railway has execution timeouts (~60 seconds for requests)
