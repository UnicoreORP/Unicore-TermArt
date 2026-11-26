import os
import sys
import time
import numpy as np
from PIL import Image, ImageEnhance, ImageSequence

RAMP = np.array(list(" .:-=+*#%@"))
EDGE_CHARS = np.array(["-", "\\", "|", "/"])

def frame_to_ascii(pil_frame, cols=80, sat=1.3, edge_thresh=0.25):
 # Convert to RGB and boost saturation so Aqua's blue pops on a black terminal
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

 # 2. Vectorized 3x3 Sobel filter for crisp anime outlines
 p = np.pad(lum, 1, mode="edge")
 gx = (p[:-2, 2:] + 2 * p[1:-1, 2:] + p[2:, 2:]) - (p[:-2, :-2] + 2 * p[1:-1, :-2] + p[2:, :-2])
 gy = (p[2:, :-2] + 2 * p[2:, 1:-1] + p[2:, 2:]) - (p[:-2, :-2] + 2 * p[:-2, 1:-1] + p[:-2, 2:])

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
 return "\x1b[H" + "\n".join(lines) + "\x1b[0m"

def play_gif(path, cols=80):
 os.system("") # Enables ANSI colors in Windows terminals
 gif = Image.open(path)

 print("Pre-rendering Aqua meltdown...")
 frames = []
 for frame in ImageSequence.Iterator(gif):
 delay = max(frame.info.get("duration", 80), 20) / 1000.0
 frames.append((frame_to_ascii(frame, cols=cols), delay))

 sys.stdout.write("\x1b[2J\x1b[?25l") # Clear screen + hide cursor
 try:
 while True:
 for ascii_frame, delay in frames:
 sys.stdout.write(ascii_frame)
 sys.stdout.flush()
 time.sleep(delay)
 except KeyboardInterrupt:
 pass
 finally:
 sys.stdout.write("\x1b[?25h\x1b[0m\n") # Restore cursor + colors

if __name__ == "__main__":
 if len(sys.argv) < 2:
 print("Usage: python aqua_ascii.py <path_to_gif> [width]")
 sys.exit(1)
 width = int(sys.argv[2]) if len(sys.argv) > 2 else 80
 play_gif(sys.argv[1], cols=width)
