"""Draw the hacker terminal wallpaper for the Galaxy A03s.

The phone is held upright, so the picture is made in portrait: the
terminal runs down the whole height and the status box sits under it.
The canvas is a bit larger than the screen so the launcher has room to
crop it without cutting the text.

    python generate_hacker_wallpaper_portrait.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# The screen of the A03s is 720x1600, so the picture is made in exactly
# that size.  Nothing is left to the launcher to crop.
WIDTH, HEIGHT = 720, 1600

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "terminal_hacker_wallpaper_portrait.png"

FONTS = Path("C:/Windows/Fonts")

# The colours of the picture.
BLACK = (6, 8, 10)
GRID = (12, 16, 22)
GREEN = (0, 255, 136)
CYAN = (0, 229, 255)
AMBER = (255, 180, 0)
GAUGE = (100, 220, 100)
DIM = (130, 150, 175)
WHITE = (170, 195, 215)


def load(name: str, size: int):
    """Load a monospace font, falling back to the default one."""
    try:
        return ImageFont.truetype(str(FONTS / name), size)
    except OSError:
        return ImageFont.load_default()


def main() -> None:
    font_code = load("consola.ttf", 13)
    font_bold = load("consolab.ttf", 13)
    font_small = load("consola.ttf", 12)
    font_title = load("consolab.ttf", 20)

    image = Image.new("RGB", (WIDTH, HEIGHT), color=BLACK)
    draw = ImageDraw.Draw(image)

    # A faint grid over the whole picture.
    for x in range(0, WIDTH, 28):
        draw.line([(x, 0), (x, HEIGHT)], fill=GRID, width=1)
    for y in range(0, HEIGHT, 28):
        draw.line([(0, y), (WIDTH, y)], fill=GRID, width=1)

    # The lines of the terminal.  They are short on purpose, so they
    # fit the narrow screen.
    code_lines = [
        "root@a03s:~# uname -a",
        "Linux a03s 6.17.0 aarch64 GNU/Linux",
        "root@a03s:~# cat /proc/cpuinfo | grep -c processor",
        "8",
        "root@a03s:~# systemctl status minipc-core",
        "[+] Core up: MT6765 8-core @ 2.30GHz",
        "[+] Memory: 4GB LPDDR4X",
        "[+] ZRAM swap: 3GB active",
        "[+] DoT: 1.1.1.1:853 ACTIVE",
        "[+] Poisoning: BYPASSED",
        "root@a03s:~# ip -br addr",
        "wlan0  UP  192.168.1.63/24",
        "tun0   UP  100.100.241.85/32",
        "root@a03s:~# ping -c1 1.1.1.1",
        "ttl=58 time=12.4 ms",
        "root@a03s:~# ./a03s-ctl monitor",
        "CPU0-3 [|||||||||......] 36%",
        "CPU4-7 [|||||||||||||...] 48%",
        "RAM    [||||||||||.....] 2.1G free",
        "root@a03s:~# firefox --private &",
        "[*] PID 15506 ARM64 native",
        "[*] TLS 1.3 AES_256_GCM_SHA384",
        "[*] CN=*.cloudflare.com OK",
        "root@a03s:~# tail -f /var/log/syslog",
        "kernel: power throttling off",
        "kernel: zram0 812MB -> 240MB",
        "kernel: DoT mode active",
        "root@a03s:~# whoami",
        "root",
    ]

    start_y = 80
    line_height = 19
    for index, line in enumerate(code_lines):
        y = start_y + index * line_height
        if y > HEIGHT - 560:
            break
        if line.startswith("root@"):
            color = GREEN
        elif "[+]" in line or "[*]" in line:
            color = CYAN
        elif "kernel:" in line:
            color = AMBER
        elif "CPU" in line or "RAM" in line:
            color = GAUGE
        elif line.startswith("  "):
            color = DIM
        else:
            color = WHITE
        draw.text((30, y), line, fill=color, font=font_code)

    # The status box under the terminal.  It is cut into the corners so
    # it looks like a heads-up display.  It starts right below the
    # last line of the terminal, so there is no empty gap.
    box_left, box_right = 36, WIDTH - 36
    box_top = 700
    box_bottom = HEIGHT - 60
    corner = 24

    points = [
        (box_left + corner, box_top),
        (box_right - corner, box_top),
        (box_right, box_top + corner),
        (box_right, box_bottom - corner),
        (box_right - corner, box_bottom),
        (box_left + corner, box_bottom),
        (box_left, box_bottom - corner),
        (box_left, box_top + corner),
    ]
    draw.polygon(points, outline=GREEN, fill=(8, 12, 18), width=2)

    header_y = box_top + 40
    draw.line([(box_left, header_y), (box_right, header_y)], fill=CYAN, width=2)

    title = "SYS_STATUS // ONLINE"
    title_width = draw.textlength(title, font=font_title)
    draw.text(((box_left + box_right - title_width) / 2, box_top + 12), title, fill=GREEN, font=font_title)

    stats = [
        ("PLATFORM", "SAMSUNG A03s"),
        ("CPU", "8x ARM64 @ 2.3G"),
        ("RAM", "3.8 GB LPDDR4"),
        ("SWAP", "3.0 GB ZRAM"),
        ("CONTAINER", "UBUNTU 24.04"),
        ("KERNEL", "GLIBC / PROOT"),
        ("DNS", "CLOUDFLARE DoT"),
        ("PORT", "853 / TLS 1.3"),
        ("BROWSER", "FIREFOX 159"),
        ("DISPLAY", "720x1600 PORT"),
        ("DPI", "300 TOUCH DPI"),
        ("STATUS", "UNRESTRICTED"),
    ]

    label_x = box_left + 26
    value_right = box_right - 26
    for index, (label, value) in enumerate(stats):
        y = header_y + 18 + index * 34
        draw.text((label_x, y), label, fill=DIM, font=font_small)
        width = draw.textlength(value, font=font_bold)
        draw.text((value_right - width, y), value, fill=CYAN, font=font_bold)

    # A blinking cursor right under the last line of the terminal.
    cursor_y = start_y + len(code_lines) * line_height + 4
    draw.rectangle([30, cursor_y, 44, cursor_y + 14], fill=GREEN)

    image.save(OUT, "PNG")
    print(f"[+] {OUT}  {image.size[0]}x{image.size[1]}")


if __name__ == "__main__":
    main()
