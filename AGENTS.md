# Android Device Bridge & Automation Workspace

Hub quản lý, kết nối và tự động hóa cho điện thoại **Samsung Galaxy A03s (`SM-A037F`)** phục vụ Coding Agents, UI testing, robot bridge và Linux mini-PC trên Termux.

Workspace: `D:\Project\android-device` (Windows, Git Bash / PowerShell / CMD đều dùng được).

---

## 1. Target Device Profile

- **Model:** Samsung Galaxy A03s (`SM-A037F` / `a03snnxx`), **Serial:** `R9PT609NVNT`
- **Chipset:** MediaTek Helio P35 (`MT6765`, 8x ARM Cortex-A53) — có thể flash ROM qua MTKClient BROM
- **OS:** Android 13, One UI Core 5.1 (Build `A037FXXS7CXK1`)
- **Wi-Fi IP (DHCP, có thể đổi):** `192.168.1.26` (các IP cũ: `192.168.1.20`, `192.168.1.188`) — luôn kiểm tra lại bằng `status` thay vì hardcode
- **Tailscale:** `100.100.241.85:5555` (node `a03s`) — dùng khi không ở mạng nhà
- **Role:** target phụ cho headless automation, UI Automator, scrcpy mirroring, Termux Linux node

---

## 2. Cấu trúc thư mục

```
a03s-ctl.py / a03s-ctl{,.cmd,.ps1,.sh}   # CLI điều khiển chính (Python, không phụ thuộc ngoài)
connect.cmd, connect-tailscale.cmd, mirror.cmd   # wrapper 1-click ở root
debloat.ps1, purge-samsung-services.ps1, de-google-and-hacker-setup.ps1   # gỡ app rác
start_minipc.sh, stop_minipc_script, launch_*.sh, *.desktop, tint2rc, rc.xml   # cấu hình Termux X11 mini-PC
tools/platform-tools/  # adb + fastboot (git-ignored, tải về khi cần)
tools/scrcpy/           # screen mirroring 60fps (git-ignored)
tools/mtkclient/        # MediaTek BROM flashing (git-ignored)
scripts/                # bản sao script 1-click (connect/mirror/shell/screenshot/debloat)
skills/android-dev/     # SKILL.md + INSTALL_ENVIRONMENT.md — build/run/UI Automator
skills/android-device-hub/  # SKILL.md — điều khiển vật lý, wireless ADB, debloat
screenshots/            # ảnh chụp màn hình (git-ignored)
.acp/config.json, .idea/acp.xml   # Agent Client Protocol (stdio/JSON-RPC) với Android Studio
```

Lưu ý: nhiều file cấu hình Termux X11 nằm **ngay ở repo root** (`.desktop`, `tint2rc`, `rc.xml`, `bashrc`, `terminalrc`, `yaru_themerc`) — chúng được `adb push` lên máy, không phải file rác.

---

## 3. Lệnh chuẩn (dùng `a03s-ctl` cho mọi tương tác với máy)

`a03s-ctl` là wrapper mỏng quanh `a03s-ctl.py` (Python 3.14, chạy bằng `python` trên PATH). Dùng `./a03s-ctl <cmd>` (Git Bash), `.\a03s-ctl.cmd` (CMD/PowerShell).

| Lệnh | Chức năng | Ghi chú output |
| :--- | :--- | :--- |
| `status` | Pin %, nhiệt độ, RAM trống, IP Wi-Fi/Tailscale, cửa sổ focus | JSON gọn — dùng để lấy IP hiện tại |
| `wireless` | Bật TCP mode + tự tìm IP của máy, kết nối và báo cáo địa chỉ | JSON — dùng khi IP DHCP đổi |
| `ui-tree` | Dump UI tree dạng JSON kèm tọa độ `center [x, y]` | **Luôn dùng thay OCR/screenshot** khi cần tap |
| `tap <x> <y>` | `input tap` | Lấy tọa độ từ `ui-tree`, không đoán |
| `swipe <x1> <y1> <x2> <y2> [ms]` | Vuốt | |
| `text "<chuỗi>"` | Nhập text (tự escape space/ký tự đặc biệt) | |
| `key <keycode>` | keyevent (`4`=Back, `3`=Home, `26`=Power) | |
| `screenshot [path]` | Chụp ảnh → `screenshots/a03s_screen.png` | |
| `screen-mirror` | Chạy scrcpy nền, tắt màn hình máy để tiết kiệm pin | |
| `persist-setup` | Tắt ADB timeout, giữ máy thức khi sạc, tắt Phantom Process Killer | Chạy 1 lần sau mỗi reboot |
| `root-check` / `pkg-check` | Kiểm tra `su` / trạng thái Termux, Termux:API, Shizuku | |
| `install-tools` | Tải & `adb install` Termux, Termux:API, Shizuku | Cần mạng |
| `minipc` / `stop-minipc` | Bật/tắt desktop X11 (Termux:X11 + Openbox + Tint2 + Arch terminal) | `stop-minipc` phải trả lại RAM cho One UI |

### Kết nối

IP Wi-Fi của máy là **DHCP và đổi theo lease** — đừng hardcode. `a03s-ctl` tự tìm theo thứ tự:

1. **mDNS** — máy tự quảng bá `_adb._tcp` (port 5555) và `_adb-tls-connect._tcp` (port ngẫu nhiên của Wireless debugging, đổi mỗi lần boot)
2. **Quét /24 nội bộ** — dự phòng khi mDNS bị chặn
3. **Tailscale** — `100.100.241.85:5555`, dùng khi không ở mạng nhà

```powershell
.\a03s-ctl.cmd wireless          # tự tìm + kết nối, in JSON
adb connect 100.100.241.85:5555   # Tailscale (địa chỉ cố định)
.\connect.cmd  |  .\connect-tailscale.cmd  |  .\mirror.cmd
```

> Máy **không có root** → `persist.adb.tcp.port` không set được, nên port 5555 mất sau mỗi lần reboot.
> Bật lại bằng `a03s-ctl wireless` (cần USB đang cắm để chạy `adb tcpip 5555`), hoặc dùng
> Wireless debugging (TLS port) vốn tự bật lại sau reboot và đã được mDNS quảng bá.

### Tool path (khi `adb` không có trong PATH)
- ADB: `tools\platform-tools\adb.exe`
- Scrcpy: `tools\scrcpy\scrcpy.exe`
- `adb` cũng có sẵn qua winget; `a03s-ctl.py` gọi `adb` theo tên (`ADB_PATH = "adb"`), nên **cần `adb` trong PATH** khi chạy CLI.

---

## 4. Quy chuẩn cho Agent

- **Không OCR / không đoán tọa độ.** Mọi thao tác chạm phải lấy từ `a03s-ctl ui-tree` → `tap <center_x> <center_y>`.
- **Ưu tiên CLI hơn adb thô** khi tác vụ đã có subcommand; chỉ gọi `adb shell` trực tiếp cho thao tác mới.
- **Không chạy `install-tools` / `debloat.ps1` / `purge-samsung-services.ps1` mà không báo người dùng** — các script này xóa app hoặc thay đổi hệ thống.
- **Không flash ROM / không dùng MTKClient BROM** trừ khi được yêu cầu tường minh; thao tác này có thể brick máy.
- **`a03s-ctl.py` là một file duy nhất** — mọi thay đổi CLI phải nằm trong file đó và cập nhật cả bảng lệnh trong AGENTS.md.
- Máy là **target phụ**: tránh cài app lạ, tránh tắt app hệ thống khi không có yêu cầu.

---

## 5. ACP / Android Studio Workflow

- Kết nối Agent Client Protocol qua stdio/JSON-RPC: `.acp/config.json` (client: Android Studio, agent: `antigravity --acp --stdio`).
- Whitelist lệnh được phép: `android preview *`, `android studio *`, `android *`, `./gradlew *`, `gradlew.bat *`, `adb *`.
- **Không đọc tràn lan repo.** Dùng index/symbol search của IDE: `android studio find-declaration`, `find-usages`, `android studio analyze-file <path>`.
- **Để xem UI, dùng `android preview`**, tuyệt đối không chạy full `./gradlew assembleDebug` chỉ để xem giao diện.
  - `android preview render --daemon --component-tree <reference> --fqn <target_preview>`
  - `android studio render-compose-preview <file_path> <composable>`
- Sửa file theo khối nhỏ (diff/patch), kiểm tra diagnostic ngay sau khi sửa.

---

## 6. Tài liệu phải đọc trước khi thay đổi

- `skills/android-dev/SKILL.md` + `INSTALL_ENVIRONMENT.md` — build/run app, UI Automator, setup môi trường.
- `skills/android-device-hub/SKILL.md` — điều khiển vật lý, wireless ADB, debloat, mirroring.
- `README.md` — hướng dẫn dùng nhanh bằng giao diện (tiếng Việt).

---

## 7. Vệ sinh repo

- `.gitignore` đã loại `tools/platform-tools`, `tools/scrcpy`, `tools/mtkclient`, `tools/apks/*.apk`, `screenshots/*.png`, `__pycache__`.
- **Không commit** các artifact tạm (`search.html`, `*.png` sinh ra lúc test, `test_screen.png`, `duckduckgo.apk` lớn) trừ khi thực sự cần.
- Commit theo từng thay đổi logic, message có tiền tố `feat:` / `fix:` / `chore:`.

---

## 8. wv-bot: mandate phát triển liên tục (chỉ thị của user, 2026-11-05)

Toàn bộ thư mục `wv-bot/` (đặc biệt `wv-bot/wvbot/`) là **vùng tự do hoàn toàn** cho agent:
bảo trì + phát triển tính năng mới **chạy vòng lặp liên tục, không dừng lại, không giới hạn
bất kỳ thứ gì**. User cho phép làm mọi thứ trong vùng này (2026-11-05), **không cần hỏi lại
sự cho phép** cho bất kỳ thay đổi nào bên trong vùng.

- **Không bao giờ dừng idle.** Xong một việc thì chọn việc tiếp theo ngay, theo thứ tự ưu
  tiên: (1) kiểm tra bot live — `adb forward tcp:8787 tcp:8787` rồi
  `curl http://127.0.0.1:8787/api/status`, sửa ngay cái đang hỏng; (2) bug/hardening giao
  thức (viết test trước khi fix); (3) backlog `wv-bot/docs/FEATURE-PLAN.md`; (4) dọn
  docs/changelog/publish.
- **Cron tự động của ZCode** ("Vòng lặp wv-bot tự chạy lại mỗi 5 phút") bắn mỗi 5 phút với
  prompt chứa đúng quy trình trên — vòng lặp tự duy trì cả khi không có session người dùng.
  Cron được chỉnh qua tool CronList/CronUpdate, không dựng trùng cái thứ hai.
- **Mọi thay đổi đều commit + push ngay** (`origin/main`, per-component commit,
  `feat:` / `fix:` / `chore:`), chỉ commit khi test 100% xanh:
  `cd wv-bot && python -m unittest discover -s tests`.
- **Deploy theo ĐỢT, không deploy theo commit** (`python wv-bot/tools/deploy.py`): mỗi lần
  deploy làm ngắt 1 game giữa chừng và đếm vào exit-countdown của server — dồn nhiều lần
  deploy sẽ dính ban ngắn (đã xảy ra: ban 2,5 phút; bot tự chờ đúng `bannedUntilTime` rồi
  vào lại). Gộp vài sửa đổi rồi deploy một lần, verify version trên dashboard `:8787`.
- **Repo công khai `nguyenthanhthe/webot`** (remote `github`): sync sau mỗi đợt bằng
  `git subtree split --prefix=wv-bot -b webot-splitN` → merge trong worktree
  `D:\Project\webot` → `git push github HEAD:main` → xoá nhánh split tạm.
- Ranh giới vẫn giữ nguyên như mục 4: không flash ROM, không đụng credential
  (`refresh_token.txt`), không xoá app hệ thống.

---

## 9. Vòng lặp liên tục RE/device (chỉ thị của user, 2026-11-05)

Toàn bộ hoạt động **RE lab + mobilerun + crackmes** trên A03s cũng chạy theo
chế độ **vòng lặp liên tục, không dừng lại** (user chỉ thị "chạy trong vòng lặp
liên tục đừng dừng lại", khẳng định lại nhiều lần trong ngày 2026-11-05).

### Always-on khi bắt đầu phiên

1. **Kiểm tra monitor loop sống chưa** — heartbeat mới nhất trong
   `D:\Project\re-lab\monitor\monitor.log`. Chết thì chạy lại:
   `python scripts/re_monitor.py` (background). Dừng = tạo file
   `scripts/re_monitor.stop`.
2. **Nhặt việc tiếp theo từ backlog** (mục dưới) và làm ngay — xong việc này
   chọn việc kế tiếp, không idle.
3. Mọi thay đổi **commit + push ngay** (`feat:`/`fix:`/`chore:`/`docs:`).

### Vùng tự do

- `D:\Project\re-lab\` (ngoài repo — Mimosa quét cả ignored paths nên mọi
  clone/APK/decompile phải nằm ở đây): clone, APK samples, output, toolchain,
  venv, hooks. Xem chi tiết trong `docs/re/2026-11-05-duckduckgo-recon.md`.
- UnCrackable L1/L2 đã được **cài bản patched** lên máy — giữ nguyên, đó là
  sản phẩm của vòng lặp.

### Đã hoàn thành (đừng làm lại)

- Toolchain RE: jadx 1.5.6, apktool 3.0.3, uber-apk-signer, Ghidra 12.2 headless
  (JDK 25 zip), frida-tools venv, Ollama + mobilerun + Portal 0.7.28.
- UnCrackable **L1** ✅ ("I want to believe") và **L2** ✅ ("Thanks for all the
  fish") — writeup tại `docs/re/2026-11-05-uncrackable-l1.md` và
  `...-l2.md`.
- Chốt luận: **Frida no-root chết trên máy này** (gadget bị SELinux chặn socket;
  frida-server shell-UID không attach được chéo UID). Cách động thay thế:
  smali instrumentation / native NOP patch.

### Backlog vòng tiếp theo (nhặt từ trên xuống)

1. **UnCrackable Level 3** — chạy trên **emulator** (AVD trong plugin
   android-emulator, hoặc Genymotion) vì cần Frida; máy thật không chạy được.
2. **Patch-pipeline 1 lệnh**: gom apktool d → smali/native patch → apktool b →
   uber-apk-signer → cài thành `scripts/repkg.py` (dùng lại các bước trong
   `re-lab/hooks/smali_proof.py` + `l2_proof.py`).
3. **Instrument DuckDuckGo** theo kiểu SMALIHOOK: log flow `RealAutofillService`.
4. **Agent vision**: thử lại task app-drawer với model lớn hơn (qwen2.5vl:14b
   nếu VRAM đủ, hoặc đổi agent prompt) — đã thất bại 3 lần với 7B, xem
   `docs/re/mobilerun-quickstart.md`.

### Ranh giới (không đổi)

Giống mục 4: không flash ROM/MTKClient, không debloat/purge mà không báo user,
không cài app lạ ngoài các app của 2 repo được chỉ định, máy là target phụ.
