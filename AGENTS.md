# Android Device Bridge & Automation Workspace

## Target Device Specifications
- **Model:** Samsung Galaxy A03s (`SM-A037F` / `a03snnxx`)
- **Serial Number:** `R9PT609NVNT`
- **Chipset:** MediaTek Helio P35 (`MT6765`, 8x ARM Cortex-A53)
- **OS Version:** Android 13, One UI Core 5.1 (Build `A037FXXS7CXK1`)
- **Local Wi-Fi IP:** `192.168.1.188` (Port: `5555`)
- **Tailscale Global IP:** `100.100.241.85` (Port: `5555`, node: `a03s`)
- **Role:** Dedicated Secondary Android Dev & Agent Automation Target (Headless bot, UI Automator, scrcpy mirroring, Termux Linux node, robot controller).

---

## Connection & Operational Modes

### 1. Wireless ADB Connection
- **Local Wi-Fi (Home):**
```powershell
adb connect 192.168.1.188:5555
```
- **Remote / Any Network (Tailscale Mesh):**
```powershell
adb connect 100.100.241.85:5555
```
Or run the workspace scripts: `.\connect.cmd` or `.\connect-tailscale.cmd`.

### 2. High-Performance Screen Mirroring (Scrcpy)
To stream the phone display to a low-latency 60fps Windows window and control with mouse/keyboard:
```powershell
scrcpy -s 100.100.241.85:5555
```
Or simply run:
```powershell
.\mirror.cmd
```

### 3. Safe Debloating & Optimization
To remove invasive background bloatware (Facebook Services, Microsoft apps, Samsung GOS performance throttling) and free up ~1GB RAM:
```powershell
.\debloat.ps1
```

---

## Agent Automation Guidelines
When interacting with this device via Coding Agents:
- Prefer `./a03s-ctl <subcommand>` (or `python a03s-ctl.py <subcommand>` / `.\a03s-ctl.cmd`) for all phone interactions.
- For UI Automation without token cost: ALWAYS run `./a03s-ctl ui-tree` to inspect interactive elements and retrieve exact `[center_x, center_y]` coordinates for `./a03s-ctl tap <x> <y>`.
- For background services, utilize Termux or native Android background daemons.

---

## Galaxy A03s Intelligent Control CLI (`a03s-ctl`)

Bộ công cụ cầu nối tự động hóa độc quyền cho Antigravity Agent tại `D:\Project\android-device`:

| Lệnh | Chức năng | Đầu ra / Mục đích tối ưu Token |
| :--- | :--- | :--- |
| `./a03s-ctl status` | Trích xuất thông số phần cứng | JSON gọn: Pin %, nhiệt độ °C, RAM trống, IP Wi-Fi, IP Tailscale, window đang focus. |
| `./a03s-ctl ui-tree` | Đọc toàn bộ màn hình | JSON chứa danh sách phần tử tương tác (`text`, `desc`, `id`, `bounds`, tọa độ tâm `[x, y]`). Đọc hiểu màn hình với chi phí token tối thiểu, không cần OCR/chụp ảnh. |
| `./a03s-ctl tap <x> <y>` | Chạm vào tọa độ | Thực thi `input tap x y` chính xác theo tọa độ `center` từ `ui-tree`. |
| `./a03s-ctl swipe <x1> <y1> <x2> <y2>` | Vuốt màn hình | Thực thi thao tác cuộn/vuốt màn hình. |
| `./a03s-ctl text "<chuỗi>"` | Nhập văn bản | Nhập liệu nhanh (tự động escape ký tự đặc biệt và dấu cách). |
| `./a03s-ctl key <keycode>` | Phím vật lý | Gửi keycode (ví dụ: `4` = Back, `3` = Home, `26` = Nguồn). |
| `./a03s-ctl screen-mirror` | Mirror màn hình | Khởi chạy `scrcpy` ngầm (tắt màn hình vật lý điện thoại để bảo vệ pin và chống nóng máy). |
| `./a03s-ctl screenshot` | Chụp ảnh màn hình | Lưu ảnh chụp nén nhẹ về `screenshots/a03s_screen.png`. |
| `./a03s-ctl persist-setup` | Gia cố kết nối & Chạy ngầm | Tắt thời gian chờ tự hủy ADB, giữ máy luôn thức khi cắm sạc, tắt Phantom Process Killer. |
| `./a03s-ctl root-check` | Kiểm tra Root | Kiểm tra quyền `su` trên máy. |
| `./a03s-ctl pkg-check` | Kiểm tra gói cài đặt | Kiểm tra trạng thái của `com.termux`, `com.termux.api`, `moe.shizuku.privileged.api`. |
| `./a03s-ctl install-tools` | Cài đặt công cụ tự động | Tự động tải từ GitHub chính thức và chạy `adb install` các công cụ Termux & Shizuku. |

---

## Android Studio & ACP Workflow Standards (Token & UI Velocity Optimization)

### 1. ACP (Agent Client Protocol) Architecture
- **Protocol:** Connected via stdio/JSON-RPC specification configured in `.acp/config.json` and `.idea/acp.xml`.
- **Permissions:**
  - Context Reading: Direct access to Android Studio project index, symbol trees, and syntax hierarchies.
  - Command Execution: Whitelisted for `android preview`, `android studio`, `./gradlew`, `gradlew.bat`, and `adb`.
  - File Editing: Surgical diff-based edits with automatic workspace synchronization.

### 2. Quy chuẩn Vận hành Tối ưu Token
- **Nguyên tắc Đọc Context:** Tuyệt đối không đọc tràn lan toàn bộ kho mã nguồn. Chỉ truy vấn các file/ký hiệu liên quan trực tiếp đến tính năng hoặc màn hình đang xử lý thông qua index/symbol search của IDE hoặc `android studio find-declaration` / `find-usages`.
- **Nguyên tắc Làm UI với `android preview`:** Khi tạo mới hoặc chỉnh sửa giao diện (Jetpack Compose `@Preview` hoặc XML Layout), bắt buộc gọi lệnh `android preview` (hoặc sidecar preview) để kiểm tra kết quả hiển thị và phát hiện lỗi biên dịch cục bộ; **nghiêm cấm chạy full `./gradlew assembleDebug`** chỉ để xem UI.
  - Lệnh preview độc lập: `android preview render --daemon --component-tree <reference> --fqn <target_preview>`
  - Lệnh preview qua Studio: `android studio render-compose-preview <file_path> <composable>`
- **Nguyên tắc Sửa File:** Sửa đổi theo từng khối (diff/patch) nhỏ gọn theo nguyên tắc Ponytail, kiểm tra ngay kết quả chẩn đoán qua IDE diagnostic / `android studio analyze-file <path>` sau khi sửa.

