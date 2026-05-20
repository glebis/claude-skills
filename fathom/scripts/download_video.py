# download_from_fathom.py

import sys
import subprocess
from urllib.parse import urlparse
import os
import requests
import re
import argparse
from dotenv import load_dotenv


def get_m3u8_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching m3u8 file: {e}")
        sys.exit(1)


def parse_m3u8_chunks(m3u8_content, base_url):
    chunk_urls = []
    # Extract directory path from base_url
    base_path = "/".join(base_url.split("/")[:-1]) + "/"
    for line in m3u8_content.splitlines():
        # Simple check for lines that are not comments or directives
        if not line.startswith("#"):
            # Construct the full URL for the chunk
            chunk_url = base_path + line.strip()
            chunk_urls.append(chunk_url)
    return chunk_urls


def download_fathom_video(url, output_path):
    output_path = os.path.abspath(output_path)
    print(f"Downloading video from: {url}")
    print(f"Output: {output_path}")

    # Get m3u8 content and parse chunks
    m3u8_content = get_m3u8_content(url)
    chunk_list = parse_m3u8_chunks(m3u8_content, url)
    total_chunks = len(chunk_list)
    print(f"Found {total_chunks} video chunks.")

    # Step 1: Download HLS to a raw .ts container.
    # Fathom's HLS server can drop connections on long recordings, so we
    # retry up to 3 times. ffmpeg's resumable HLS download resumes from
    # where it left off when given the same output file.
    raw_output = output_path + ".raw.ts"
    command = [
        "ffmpeg", "-y",
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "30",
        "-http_persistent", "false",
        "-i", url,
        "-c", "copy",
        raw_output,
    ]

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            process = subprocess.Popen(
                command, stderr=subprocess.PIPE, universal_newlines=True
            )

            downloaded_chunks = 0
            chunk_regex = re.compile(r"Opening '(.*?)' for reading")

            while True:
                output = process.stderr.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    match = chunk_regex.search(output)
                    if match:
                        downloaded_chunks += 1
                        print(
                            f"Downloaded chunk {downloaded_chunks}/{total_chunks}", end="\r"
                        )

            print(f"Downloaded chunk {downloaded_chunks}/{total_chunks}")

            if process.returncode == 0:
                print(f"Download complete: {raw_output}")
                break
            elif downloaded_chunks >= total_chunks * 0.85:
                # Got most chunks — treat partial download as usable
                print(f"ffmpeg exited {process.returncode} but got {downloaded_chunks}/{total_chunks} chunks — using partial download")
                break
            else:
                print(f"ffmpeg exited {process.returncode} at chunk {downloaded_chunks}/{total_chunks} (attempt {attempt}/{max_retries})")
                if attempt < max_retries:
                    wait = attempt * 10
                    print(f"Retrying in {wait}s...")
                    import time
                    time.sleep(wait)
                else:
                    print(f"All {max_retries} attempts failed")
                    if os.path.exists(raw_output):
                        os.remove(raw_output)
                    sys.exit(1)

        except subprocess.CalledProcessError as e:
            print(f"ffmpeg failed on attempt {attempt}: {e}")
            if attempt >= max_retries:
                if os.path.exists(raw_output):
                    os.remove(raw_output)
                sys.exit(1)

    if not os.path.exists(raw_output):
        print(f"ERROR: Raw download file not created: {raw_output}")
        sys.exit(1)

    raw_size = os.path.getsize(raw_output) / (1024 * 1024)
    print(f"Raw .ts file: {raw_size:.0f} MB")

    # Step 2: Remux .ts → .mp4 with faststart moov atom
    print("Remuxing to MP4 with faststart...")
    remux_command = [
        "ffmpeg", "-y",
        "-i", raw_output,
        "-c", "copy",
        "-movflags", "faststart",
        output_path,
    ]

    try:
        subprocess.run(remux_command, check=True, capture_output=True)
        os.remove(raw_output)
        print(f"Remux complete: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Remux failed: {e}")
        if os.path.exists(raw_output):
            os.remove(raw_output)
        if os.path.exists(output_path):
            os.remove(output_path)
        sys.exit(1)

    # Validate output file
    _validate_video_output(output_path)


def _validate_video_output(path):
    """Verify the downloaded video is a valid, playable MP4."""
    if not os.path.exists(path):
        print(f"ERROR: Output file not created: {path}")
        sys.exit(1)

    size_mb = os.path.getsize(path) / (1024 * 1024)
    if size_mb < 1:
        print(f"ERROR: Output file too small ({size_mb:.1f} MB): {path}")
        sys.exit(1)

    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-print_format', 'json',
         '-show_format', '-show_streams', path],
        capture_output=True, text=True, timeout=30
    )

    if result.returncode != 0:
        print(f"ERROR: Video file is corrupt: {result.stderr.strip()}")
        print(f"  File: {path} ({size_mb:.1f} MB)")
        print("  The HLS download may have failed silently. Try again or use a different source.")
        sys.exit(1)

    import json as _json
    try:
        probe = _json.loads(result.stdout)
        duration = float(probe.get('format', {}).get('duration', 0))
        streams = probe.get('streams', [])
        has_video = any(s.get('codec_type') == 'video' for s in streams)
        if not has_video:
            print(f"ERROR: No video stream in output file: {path}")
            sys.exit(1)
        print(f"✓ Video validated: {duration/60:.0f} min, {size_mb:.0f} MB")
    except Exception as e:
        print(f"WARNING: Could not parse ffprobe output: {e}")


if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file

    parser = argparse.ArgumentParser(description="Download a Fathom video.")
    parser.add_argument("fathom_url", help="The base URL of the Fathom video.")
    parser.add_argument(
        "--output-name",
        help="Optional name for the output video file (without extension).",
    )
    args = parser.parse_args()

    fathom_url = args.fathom_url
    output_name = args.output_name

    # Clean the URL - remove any query parameters like ?tab=summary
    if "?" in fathom_url:
        fathom_url = fathom_url.split("?")[0]
    
    # Append "/video.m3u8" to the URL
    fathom_url_with_m3u8 = fathom_url.rstrip("/") + "/video.m3u8"

    # Extract the ID from the URL path for default output name
    parsed_url = urlparse(fathom_url_with_m3u8)
    path_segments = parsed_url.path.split("/")
    if len(path_segments) >= 2 and path_segments[-1] == "video.m3u8":
        video_id = path_segments[-2]
    else:
        video_id = "output"  # Fallback if the URL format is unexpected

    # Determine the final output filename
    if output_name:
        final_output_name = output_name
    else:
        final_output_name = video_id

    output_filename = f"{final_output_name}.mp4"

    # Get output directory from environment variable, default to current directory
    output_dir = os.getenv("OUTPUT_DIR", ".")
    os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn't exist

    full_output_path = os.path.join(output_dir, output_filename)

    download_fathom_video(fathom_url_with_m3u8, full_output_path)
