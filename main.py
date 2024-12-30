import os
from datetime import datetime

import cv2
import numpy as np
from PIL import Image
from reportlab.pdfgen import canvas
from yt_dlp import YoutubeDL


def download_video(url, output_path="video.mp4"):
    """Download YouTube video using yt-dlp."""
    try:
        ydl_opts = {
            "format": "best[ext=mp4]",  # Get best quality MP4
            "outtmpl": output_path,  # Output template
            "quiet": True,  # Less verbose output
            "no_warnings": True,  # Don't print warnings
            "extract_flat": False,  # Extract video data
            "merge_output_format": "mp4",  # Ensure MP4 output
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True

    except Exception as e:
        print(f"Error downloading video: {e}")
        return False


def extract_frames(video_path, output_dir="frames"):
    """Extract frames from video and detect significant changes."""
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    prev_frame = None
    saved_frames = []
    frame_threshold = 0.05  # Adjust this value to control sensitivity

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convert frame to grayscale for comparison
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev_frame is not None:
            # Calculate frame difference
            diff = cv2.absdiff(gray, prev_frame)
            mean_diff = np.mean(diff)

            # If significant change detected, save frame
            if mean_diff > frame_threshold:
                timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
                frame_path = os.path.join(
                    output_dir, f"frame_{len(saved_frames):04d}.jpg"
                )
                cv2.imwrite(frame_path, frame)
                saved_frames.append((frame_path, timestamp))

        prev_frame = gray

    cap.release()
    return saved_frames


def create_pdf(frame_paths, output_pdf="slides.pdf"):
    """Convert extracted frames to PDF."""
    if not frame_paths:
        print("No frames to convert to PDF")
        return False

    # Get dimensions from first image
    first_img = Image.open(frame_paths[0][0])
    img_width, img_height = first_img.size

    # Create PDF with same dimensions as images
    c = canvas.Canvas(output_pdf, pagesize=(img_width, img_height))

    for frame_path, timestamp in frame_paths:
        _ = Image.open(frame_path)
        c.drawInlineImage(frame_path, 0, 0, img_width, img_height)

        # Add timestamp to corner
        timestamp_str = str(
            datetime.fromtimestamp(timestamp / 1000).strftime("%H:%M:%S")
        )
        c.drawString(10, 10, f"Time: {timestamp_str}")

        c.showPage()

    c.save()
    return True


def extract_slides_from_youtube(url, output_pdf="slides.pdf", cleanup=True):
    """Main function to extract slides from YouTube video."""
    # Download video
    video_path = "temp_video.mp4"
    if not download_video(url, video_path):
        return False

    # Extract frames
    frames_dir = "temp_frames"
    frame_paths = extract_frames(video_path, frames_dir)

    # Create PDF
    success = create_pdf(frame_paths, output_pdf)

    # Cleanup temporary files
    if cleanup:
        os.remove(video_path)
        for frame_path, _ in frame_paths:
            os.remove(frame_path)
        os.rmdir(frames_dir)

    return success


# Command line argument handling
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract slides from a YouTube presentation video into a PDF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python script.py -u https://www.youtube.com/watch?v=VIDEO_ID
    python script.py -u https://www.youtube.com/watch?v=VIDEO_ID -o my_slides.pdf
    python script.py -u https://www.youtube.com/watch?v=VIDEO_ID -t 0.1 --keep-temp
        """,
    )

    parser.add_argument("-u", "--url", required=True, help="YouTube video URL")

    parser.add_argument(
        "-o",
        "--output",
        default="presentation_slides.pdf",
        help="Output PDF filename (default: presentation_slides.pdf)",
    )

    parser.add_argument(
        "-t",
        "--threshold",
        type=float,
        default=0.05,
        help="Frame difference threshold (0.0-1.0, default: 0.05)",
    )

    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary files (video and frames)",
    )

    args = parser.parse_args()

    # Update frame threshold in extract_frames function
    def extract_frames_with_threshold(video_path, output_dir="frames"):
        """Wrapper to use command-line threshold."""
        global frame_threshold
        frame_threshold = args.threshold
        return extract_frames(video_path, output_dir)

    # Run extraction with provided arguments
    success = extract_slides_from_youtube(
        args.url, args.output, cleanup=not args.keep_temp
    )

    if success:
        print(f"Slides successfully extracted to {args.output}!")
    else:
        print("Failed to extract slides.")
