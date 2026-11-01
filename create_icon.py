import os
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont

def generate_icon(output_icns_path):
    size = 1024
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded Squircle base
    margin = 80
    rect = [margin, margin, size - margin, size - margin]
    radius = 200

    # Draw dark metallic / deep obsidian background
    draw.rounded_rectangle(rect, radius=radius, fill=(12, 14, 22, 255), outline=(40, 50, 75, 255), width=6)

    # Inner subtle glow ring
    draw.rounded_rectangle([margin+12, margin+12, size-margin-12, size-margin-12], radius=radius-8, outline=(25, 32, 50, 255), width=3)

    # Draw ambient glowing waves
    cx, cy = size // 2, size // 2
    
    # Soundwave circles
    for r in [280, 220, 160]:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(6, 182, 212, 35), width=4)

    # Draw infinity symbol using parametric curve
    # Lemniscate of Bernoulli: x = a*cos(t)/(1+sin^2(t)), y = a*sin(t)*cos(t)/(1+sin^2(t))
    scale = 260
    num_pts = 400
    pts = []
    for i in range(num_pts):
        t = (2 * math.pi * i) / num_pts
        denom = 1 + (math.sin(t) ** 2)
        x = cx + (scale * math.cos(t)) / denom
        y = cy + (scale * math.sin(t) * math.cos(t)) / denom
        pts.append((x, y))

    # Glow under infinity
    for w, alpha in [(28, 40), (20, 70), (14, 130), (8, 220), (4, 255)]:
        col = (6, 182, 212, alpha) if w > 10 else (220, 245, 255, alpha)
        for i in range(len(pts)):
            p1 = pts[i]
            p2 = pts[(i + 1) % len(pts)]
            # Gradient transition from cyan to purple
            progress = i / len(pts)
            if progress < 0.5:
                r_c = int(6 + (139 - 6) * (progress * 2))
                g_c = int(182 + (92 - 182) * (progress * 2))
                b_c = int(212 + (246 - 212) * (progress * 2))
            else:
                r_c = int(139 + (6 - 139) * ((progress - 0.5) * 2))
                g_c = int(92 + (182 - 92) * ((progress - 0.5) * 2))
                b_c = int(246 + (212 - 246) * ((progress - 0.5) * 2))
            
            draw.line([p1, p2], fill=(r_c, g_c, b_c, alpha), width=w)

    iconset_dir = "/tmp/InfiniteFocus.iconset"
    os.makedirs(iconset_dir, exist_ok=True)

    sizes = [
        ("icon_16x16.png", 16),
        ("icon_16x16@2x.png", 32),
        ("icon_32x32.png", 32),
        ("icon_32x32@2x.png", 64),
        ("icon_128x128.png", 128),
        ("icon_128x128@2x.png", 256),
        ("icon_256x256.png", 256),
        ("icon_256x256@2x.png", 512),
        ("icon_512x512.png", 512),
        ("icon_512x512@2x.png", 1024),
    ]

    for fname, sz in sizes:
        resized = img.resize((sz, sz), Image.Resampling.LANCZOS)
        resized.save(os.path.join(iconset_dir, fname), "PNG")

    subprocess.run(["iconutil", "-c", "icns", iconset_dir, "-o", output_icns_path], check=True)
    print(f"Icon generated at {output_icns_path}")

if __name__ == "__main__":
    dest = os.path.join(os.path.dirname(__file__), "AppIcon.icns")
    generate_icon(dest)
