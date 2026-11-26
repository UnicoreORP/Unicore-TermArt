import os
import sys
import time
import numpy as np
from PIL import Image, ImageEnhance, ImageSequence

RAMP = np.array(list(" .:-=+*#%@"))
EDGE_CHARS = np.array(["-", "\\", "|", "/"])
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

def frame_to_ascii(pil_frame, cols=80, sat=1.3, edge_thresh=0.25, home_cursor=True):
    img = pil_frame.convert("RGB")
    if sat != 1.0:
        img = ImageEnhance.Color(img).enhance(sat)

    # Terminal characters are roughly 2x taller than they are wide
    w, h = img.size
    rows = max(1, int(cols * (h / w) * 0.5))
    img = img.resize((cols, rows), Image.Resampling.BILINEAR)

    rgb_u8 = np.array(img, dtype=np.uint8)
    rgb = rgb_u8.astype(np.float32)

    # 1. Perceived luminance -> base ASCII ramp
    lum = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]) / 255.0
    idx = np.clip((lum * (len(RAMP) - 1) + 0.5).astype(np.int32), 0, len(RAMP) - 1)
    idx[lum < 0.06] = 0
    glyph = RAMP[idx]

    # 2. Vectorized 3x3 Sobel filter for crisp outlines
    p = np.pad(lum, 1, mode="edge")
    gx = (p[:-2, 2:] + 2 * p[1:-1, 2:] + p[2:, 2:]) - (p[:-2, :-2] + 2 * p[1:-1, :-2] + p[2:, :-2])
    gy = (p[2:, :-2] + 2 * p[2:, 1:-1] + p[2:, 2:]) - (p[:-2, :-2] + p[:-2, 1:-1] + p[:-2, 2:])

    mag = np.hypot(gx, gy) / 4.0
    ang = (np.degrees(np.arctan2(gy, gx)) + 90.0) % 180.0
    sel = EDGE_CHARS[(((ang + 22.5) % 180.0) // 45).astype(np.int32)]

    mask = (mag > edge_thresh) & (lum > 0.12)
    glyph = np.where(mask, sel, glyph)

    # 3. Pack into 24-bit ANSI truecolor string
    lines = [
        "".join(f"\x1b[38;2;{r};{g};{b}m{ch}" for (r, g, b), ch in zip(rgb_u8[y], glyph[y]))
        for y in range(rows)
    ]
    prefix = "\x1b[H" if home_cursor else ""
    return prefix + "\n".join(lines) + "\x1b[0m"

def render_static_image(path, cols=80):
    img = Image.open(path)
    print(frame_to_ascii(img, cols=cols, home_cursor=False))

def play_gif(path, cols=80):
    gif = Image.open(path)
    print("Pre-rendering GIF frames...")
    frames = []
    for frame in ImageSequence.Iterator(gif):
        delay = max(frame.info.get("duration", 80), 20) / 1000.0
        frames.append((frame_to_ascii(frame, cols=cols, home_cursor=True), delay))

    sys.stdout.write("\x1b[2J\x1b[?25l")
    try:
        while True:
            for ascii_frame, delay in frames:
                sys.stdout.write(ascii_frame)
                sys.stdout.flush()
                time.sleep(delay)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[?25h\x1b[0m\n")

def play_video_or_cam(source, cols=80):
    try:
        import cv2
    except ImportError:
        print("Video/webcam playback requires OpenCV: pip install opencv-python-headless")
        sys.exit(1)

    cap_source = int(source) if source.isdigit() else source
    cap = cv2.VideoCapture(cap_source)
    if not cap.isOpened():
        print(f"Error: Could not open video/camera source '{source}'")
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS)
    delay = (1.0 / fps) if fps and fps > 0 else 0.033

    sys.stdout.write("\x1b[2J\x1b[?25l")
    try:
        while True:
            ret, bgr_frame = cap.read()
            if not ret:
                if isinstance(cap_source, str):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break
            rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_frame)
            sys.stdout.write(frame_to_ascii(pil_img, cols=cols, home_cursor=True))
            sys.stdout.flush()
            time.sleep(delay)
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        sys.stdout.write("\x1b[?25h\x1b[0m\n")

if __name__ == "__main__":
    os.system("")  # Enable ANSI escape codes on Windows terminals
    if len(sys.argv) < 2:
        print("Usage: python UCI.py <image_gif_video_or_0_for_webcam> [width]")
        sys.exit(1)

    target = sys.argv[1]
    width = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    ext = os.path.splitext(target)[1].lower()

    if ext in IMAGE_EXTS:
        render_static_image(target, cols=width)
    elif ext == ".gif":
        play_gif(target, cols=width)
    else:
        play_video_or_cam(target, cols=width)

