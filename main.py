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
            "format": "best[ext=mp4]",
            "outtmpl": output_path,
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "merge_output_format": "mp4",
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True

    except Exception as e:
        print(f"Error downloading video: {e}")
        return False


def create_speaker_mask(
    height, width, speaker_width_ratio, speaker_height_ratio, position="top-left"
):
    """
    Create a mask for the speaker region.

    Args:
        height, width: Video dimensions
        speaker_width_ratio, speaker_height_ratio: Size of speaker region as fraction of frame
        position: Location of speaker ('top-left', 'top-right', 'bottom-left', 'bottom-right')
    """
    mask = np.ones((height, width), dtype=np.uint8)

    speaker_height = int(height * speaker_height_ratio)
    speaker_width = int(width * speaker_width_ratio)

    if position == "top-left":
        mask[0:speaker_height, 0:speaker_width] = 0
    elif position == "top-right":
        mask[0:speaker_height, -speaker_width:] = 0
    elif position == "bottom-left":
        mask[-speaker_height:, 0:speaker_width] = 0
    elif position == "bottom-right":
        mask[-speaker_height:, -speaker_width:] = 0

    return mask


def extract_frames(
    video_path,
    output_dir="frames",
    speaker_width_ratio=0.25,
    speaker_height_ratio=0.25,
    position="top-left",
    frame_threshold=0.05,
    min_interval=2.0,
):
    """Extract frames from video and detect significant changes."""
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)

    # Read first frame to get dimensions
    ret, first_frame = cap.read()
    if not ret:
        return []

    height, width = first_frame.shape[:2]

    # Create mask for the main content area
    mask = create_speaker_mask(
        height, width, speaker_width_ratio, speaker_height_ratio, position
    )

    prev_frame = None
    saved_frames = []
    min_time_between_frames = min_interval * 1000  # Convert to milliseconds
    last_saved_time = -min_time_between_frames

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to start
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convert frame to grayscale for comparison
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply mask to focus on main content area
        masked_gray = cv2.multiply(gray, mask)

        if prev_frame is not None:
            # Calculate frame difference in masked area
            diff = cv2.absdiff(masked_gray, cv2.multiply(prev_frame, mask))
            mean_diff = np.sum(diff) / np.sum(mask)  # Normalize by visible area

            # Get current timestamp
            timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)

            # If significant change detected and enough time has passed
            if (
                mean_diff > frame_threshold
                and (timestamp - last_saved_time) >= min_time_between_frames
            ):
                frame_path = os.path.join(
                    output_dir, f"frame_{len(saved_frames):04d}.jpg"
                )
                cv2.imwrite(frame_path, frame)
                saved_frames.append((frame_path, timestamp))
                last_saved_time = timestamp

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


def extract_slides_from_youtube(url, output_pdf="slides.pdf", cleanup=True, **kwargs):
    """Main function to extract slides from YouTube video."""
    # Download video
    video_path = "temp_video.mp4"
    if not download_video(url, video_path):
        return False

    # Extract frames
    frames_dir = "temp_frames"
    frame_paths = extract_frames(video_path, frames_dir, **kwargs)

    # Create PDF
    success = create_pdf(frame_paths, output_pdf)

    # Cleanup temporary files
    if cleanup:
        os.remove(video_path)
        for frame_path, _ in frame_paths:
            os.remove(frame_path)
        os.rmdir(frames_dir)

    return success


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract slides from a YouTube presentation video into a PDF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python script.py -u https://www.youtube.com/watch?v=VIDEO_ID
    python script.py -u https://www.youtube.com/watch?v=VIDEO_ID -o my_slides.pdf
    python script.py -u https://www.youtube.com/watch?v=VIDEO_ID --speaker-width 0.3 --speaker-height 0.2
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
        "--speaker-width",
        type=float,
        default=0.15,
        help="Width of speaker thumbnail as fraction of video width (default: 0.25)",
    )

    parser.add_argument(
        "--speaker-height",
        type=float,
        default=0.15,
        help="Height of speaker thumbnail as fraction of video height (default: 0.25)",
    )

    parser.add_argument(
        "--position",
        choices=["top-left", "top-right", "bottom-left", "bottom-right"],
        default="top-left",
        help="Position of speaker thumbnail (default: top-left)",
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.25,
        help="Frame difference threshold (0.0-1.0, default: 0.25)",
    )

    parser.add_argument(
        "--min-interval",
        type=float,
        default=2.0,
        help="Minimum time between slides in seconds (default: 2.0)",
    )

    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary files (video and frames)",
    )

    args = parser.parse_args()

    success = extract_slides_from_youtube(
        args.url,
        args.output,
        cleanup=not args.keep_temp,
        speaker_width_ratio=args.speaker_width,
        speaker_height_ratio=args.speaker_height,
        position=args.position,
        frame_threshold=args.threshold,
        min_interval=args.min_interval,
    )

    if success:
        print(f"Slides successfully extracted to {args.output}!")
    else:
        print("Failed to extract slides.")
