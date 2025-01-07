# slide-scraper

This script extracts presentation slides from YouTube videos and converts them into a PDF. It's designed to work with videos where slides are the primary content, and a speaker (or other element) occupies a consistent portion of the screen. The script identifies significant changes between frames to determine slide breaks.

## Dependencies

The project uses the following libraries:

* **numpy:** For numerical operations and array handling
* **opencv-python (cv2):** For video processing and frame extraction
* **Pillow (PIL):** For image manipulation
* **yt-dlp:** For downloading YouTube videos
* **reportlab:** For generating PDF files

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/[your_github_username]/slide-scraper.git
   cd slide-scraper
   ```

2. **Create a virtual environment (recommended):**

   This is recommended for managing dependencies and creating a clean environment for the project.

    Using `uv` (recommended):
   ```bash
   pip install uv  # If you don't have uv installed
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
   OR 

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   
   Using `uv` (recommended):
   ```bash
   uv pip install -e .
   ```
   OR
   ```bash
   pip install -e .
   ```

## Usage

The script is run from the command line. Here's how to use it:

```bash
python main.py -u <YouTube_video_URL> [options]
```

**Required arguments:**

* `-u <YouTube_video_URL>`: The URL of the YouTube video containing the presentation

**Optional arguments:**

* `-o <output_filename.pdf>`: Specifies the output PDF filename. Defaults to `presentation_slides.pdf`
* `--speaker-width <ratio>`: The width of the speaker area as a fraction of the video width (0.0 to 1.0). Defaults to 0.15. Adjust this if the speaker occupies a significant portion of the screen
* `--speaker-height <ratio>`: The height of the speaker area as a fraction of the video height (0.0 to 1.0). Defaults to 0.15
* `--position <position>`: Specifies the location of the speaker area. Options are `top-left`, `top-right`, `bottom-left`, `bottom-right`. Defaults to `top-left`
* `--threshold <value>`: The minimum difference between consecutive frames to be considered a new slide (0.0 to 1.0). A higher value means more significant changes are needed to detect a new slide. Defaults to 0.25. Experiment with this value to find the optimal setting for your video
* `--min-interval <seconds>`: Minimum time (in seconds) between detected slides. This helps prevent the script from creating slides from very small changes. Defaults to 2.0 seconds
* `--keep-temp`: Keeps temporary files (downloaded video and extracted frames) after processing. Use this for debugging purposes only. By default, the temporary files are deleted

**Example:**

```bash
python main.py -u "https://www.youtube.com/watch?v=your_video_id" -o my_presentation.pdf --speaker-width 0.2 --speaker-height 0.3 --threshold 0.15
```

## Notes

* The script's accuracy depends heavily on the quality and consistency of the YouTube video. Videos with inconsistent lighting, fast cuts, or complex backgrounds may yield suboptimal results
* You might need to adjust the `--threshold`, `--speaker-width`, `--speaker-height`, and `--min-interval` parameters to obtain the best results for a specific video. Experiment with different values to achieve optimal slide detection
* The script assumes the speaker area (or any other consistently present element) occupies the same relative position in each frame

## Development

This project uses:
* Python 3.12 or later
* `uv` for dependency management and virtual environments
* `ruff` for code formatting and linting

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

Apache 2.0