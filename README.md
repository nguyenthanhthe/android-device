# Samsung Galaxy A03s — Automation & Coding Agent Hub

Hub quản lý, kết nối và tự động hóa chuyên dụng cho điện thoại **Samsung Galaxy A03s (`SM-A037F`)** phục vụ cho Coding Agents, UI testing, robot bridge và server mini.

---

## Cấu trúc thư mục

```
D:\Project\android-device\
├── tools\
│   ├── platform-tools\       # Bộ công cụ ADB và Fastboot chính hãng từ Google
│   ├── scrcpy\               # Công cụ điều khiển và stream màn hình 60fps qua máy tính
│   └── mtkclient\            # Bộ công cụ BootROM MediaTek MT6765 (BROM exploit)
├── skills\
│   ├── android-dev\          # Kỹ năng ZCode Android Dev (build, run, UI Automator)
│   └── android-device-hub\   # Kỹ năng Antigravity điều khiển vật lý Samsung A03s
├── scripts\
│   ├── connect.cmd           # 1-click kết nối lại ADB không dây (192.168.1.188:5555)
│   ├── mirror.cmd            # 1-click mở màn hình điện thoại lên laptop (tự tắt màn hình máy)
│   ├── shell.cmd             # 1-click mở Terminal ADB shell tương tác trực tiếp
│   ├── screenshot.cmd        # 1-click chụp màn hình máy lưu vào thư mục screenshots
│   └── debloat.ps1           # Script gỡ sạch app rác Samsung/Facebook/Microsoft
├── screenshots\              # Nơi lưu ảnh chụp màn hình tự động
└── AGENTS.md                 # Quy chuẩn kỹ thuật dành cho Agent
```

---

## Hướng dẫn sử dụng nhanh

1. **Kết nối không dây (Không cần cáp USB):**
   - Đảm bảo điện thoại và laptop đang chung mạng Wi-Fi.
   - Nhấp đúp chuột vào `scripts\connect.cmd`.
2. **Mở màn hình điều khiển bằng chuột/phím:**
   - Nhấp đúp chuột vào `scripts\mirror.cmd`.
   - Cửa sổ điện thoại sẽ hiện lên laptop với độ trễ 0ms, màn hình thật của điện thoại sẽ tự tắt đen để tiết kiệm pin.
3. **Mở dòng lệnh can thiệp:**
   - Nhấp đúp chuột vào `scripts\shell.cmd`.
