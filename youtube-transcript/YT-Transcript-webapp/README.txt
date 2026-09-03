YT Transcript — YouTube transcript downloader
==============================================

HOW TO USE (Mac):

  1. Open the "web" folder
  2. Double-click "start.command"
  3. A browser window opens automatically
  4. Paste YouTube URLs (one per line), pick options, click Start
  5. Transcripts saved as Markdown files to your Downloads folder

FIRST RUN:
  - The launcher will auto-install Python dependencies (Flask)
  - If yt-dlp is not found, it downloads it automatically from GitHub
  - A virtual environment (.venv) is created inside the web/ folder

FEATURES:
  - Single videos or entire playlists
  - 10 languages (English, Russian, Polish, German, Spanish, French, etc.)
  - Prefers manual captions (human-uploaded) over auto-generated
  - Optional video download (checkbox in the UI)
  - Choose where to save transcripts and videos
  - Real-time progress for each video

REQUIREMENTS:
  - macOS with Python 3.9+
  - Internet connection

OUTPUT:
  - Markdown files with YAML frontmatter (title, channel, date, tags)
  - Timestamped transcript grouped by chapters
  - Compatible with Obsidian, Notion, or any text editor

CLI USAGE (advanced):
  python3 scripts/batch.py videos-example.json
  python3 scripts/extract_transcript.py "https://youtube.com/watch?v=..."

TO STOP THE SERVER:
  - Close the terminal window, or press Ctrl+C
