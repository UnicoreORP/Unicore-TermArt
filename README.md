# Unicore-TermArt

Open contribution and collaboration effort — zero-prerequisite builder starter kit for terminal computer vision, edge rendering, and hands-on engineering.

## Features
- **Vectorized 3x3 Sobel Edge Detection:** Extracts crisp structural outlines alongside perceived luminance mapping.
- **24-Bit ANSI Truecolor Output:** Renders full-color ASCII directly inside Linux, macOS, Windows, and Termux terminals.
- **Universal Media Support:** Automatically handles static images (`.png`, `.jpg`, `.webp`), animated GIFs, video files (`.mp4`), and live webcam feeds (`0`).

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd Unicore-TermArt
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run `UCI.py` on any media:**
   ```bash
   # Static image
   python UCI.py photo.png 100

   # Animated GIF
   python UCI.py animation.gif 80

   # Video file or live webcam (0)
   python UCI.py video.mp4 80
   python UCI.py 0 80
   ```

## Contributing
Fork the repo, ship something that works, and open a Pull Request. No gatekeeping, no slide decks—just working code.
