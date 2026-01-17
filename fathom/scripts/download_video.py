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
    print(f"Downloading video from: {url}")

    # Get m3u8 content and parse chunks
    m3u8_content = get_m3u8_content(url)
    chunk_list = parse_m3u8_chunks(m3u8_content, url)
    total_chunks = len(chunk_list)
    print(f"Found {total_chunks} video chunks.")

    command = [
        "ffmpeg",
        "-http_persistent",
        "false",
        "-i",
        url,
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        output_path,
    ]

    try:
        # Use subprocess.Popen to capture stderr in real-time
        process = subprocess.Popen(
            command, stderr=subprocess.PIPE, universal_newlines=True
        )

        downloaded_chunks = 0
        # Regex to find the chunk URL in the ffmpeg output
        chunk_regex = re.compile(r"Opening '(.*?)' for reading")

        while True:
            output = process.stderr.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                match = chunk_regex.search(output)
                if match:
                    downloaded_chunks += 1
                    # Simple progress indicator
                    print(
                        f"Downloaded chunk {downloaded_chunks}/{total_chunks}", end="\r"
                    )

        # Ensure the final progress is shown
        print(f"Downloaded chunk {downloaded_chunks}/{total_chunks}")

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)

        print(f"Download complete: {output_path}")

        # Post-process: re-mux to ensure moov atom is at the beginning
        print("Post-processing video for better compatibility...")
        temp_output = output_path + ".tmp"
        remux_command = [
            "ffmpeg",
            "-y",  # Overwrite
            "-i",
            output_path,
            "-c",
            "copy",
            "-movflags",
            "faststart",
            temp_output,
        ]

        try:
            subprocess.run(remux_command, check=True, capture_output=True)
            os.replace(temp_output, output_path)
            print("Post-processing complete")
        except subprocess.CalledProcessError as e:
            print(f"Post-processing failed (video may still be playable): {e}")
            if os.path.exists(temp_output):
                os.remove(temp_output)

    except subprocess.CalledProcessError as e:
        print("ffmpeg failed:", e)
        sys.exit(1)


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
