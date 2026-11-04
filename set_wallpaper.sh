#!/usr/bin/env bash
# Put the hacker terminal wallpaper on the Galaxy A03s.
#
# The picture is drawn for the screen of the phone (720x1600, held
# upright), so it fills the home screen and the lock screen without
# being cut.
#
#   ./set_wallpaper.sh              # draw the picture and install it
#   ./set_wallpaper.sh --host-only  # install the picture that is already there
#
# The phone is reached over ADB.  The address is found by the CLI, so
# it is not written down here.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="$HERE/terminal_hacker_wallpaper_portrait.png"
REMOTE="/data/local/tmp/terminal_hacker_wallpaper.png"
HOME_DIR="/data/data/com.termux/files/home/wallpaper.png"

if [ "${1:-}" != "--host-only" ]; then
    echo "[*] Drawing the wallpaper..."
    python "$HERE/generate_hacker_wallpaper_portrait.py"
fi

if [ ! -f "$IMAGE" ]; then
    echo "[!] The picture is missing: $IMAGE" >&2
    exit 1
fi

echo "[*] Sending the picture to the phone..."
# Git Bash turns a leading slash into a Windows path, so the path that
# belongs to the phone has to be left alone.  The local path is turned
# into a Windows one first, because the setting would break it.
LOCAL_IMAGE="$(cygpath -m "$IMAGE" 2>/dev/null || echo "$IMAGE")"
MSYS_NO_PATHCONV=1 adb push "$LOCAL_IMAGE" "$REMOTE" >/dev/null

# The Termux app reads the picture from its own directory, so it is
# copied there.  The Termux:API app cannot read /sdcard, because the
# app op MANAGE_EXTERNAL_STORAGE is turned off on it.
echo "[*] Copying the picture into the Termux directory..."
adb shell "run-as com.termux cp $REMOTE $HOME_DIR"

set_wallpaper() {
    local extra="$1"
    echo "[*] Setting the $2 wallpaper..."
    adb shell "run-as com.termux sh -c 'export HOME=/data/data/com.termux/files/home; export PATH=/data/data/com.termux/files/usr/bin:\$PATH; termux-wallpaper $extra -f $HOME_DIR'"
}

set_wallpaper "" "home screen"
set_wallpaper "-l" "lock screen"

echo "[+] Done.  The picture is on the phone."
