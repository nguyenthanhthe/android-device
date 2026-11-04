# Mobilerun + Ollama trên A03s — Quickstart (đã chạy được thật)

Ngày xác minh: 2026-11-05 · Theo [droidrun/mobilerun](https://github.com/droidrun/mobilerun)

## Stack đã dựng

```
[Laptop: i7-13620H + RTX 4050 6GB]
  mobilerun CLI 0.7.4 (uv tool install mobilerun --python 3.12)
  Ollama 0.40.14 (winget) ── model: qwen2.5:7b (4.7 GB, GPU)
        │  adb USB (serial R9PT609NVNT)
        ▼
[Samsung A03s — Android 13, no root]
  Mobilerun Portal 0.7.28 (accessibility service đã bật)
```

- Python host 3.14 không tương thích → cài CLI bằng `--python 3.12` (py launcher có sẵn 3.12).
- Lưu ý: khi ADB có >1 transport (USB + wireless), mọi lệnh mobilerun cần `-d R9PT609NVNT`
  hoặc ngắt bớt wireless (`adb disconnect ...`) — đa transport gây lỗi "more than one device".

## Các lệnh chuẩn

```bash
mobilerun ping                     # kiểm tra Portal
mobilerun devices                  # liệt kê thiết bị
mobilerun device ui                # dump accessibility tree (thay cho OCR/screenshot)
mobilerun device screenshot        # chụp màn hình
mobilerun configure --provider ollama --model qwen2.5:7b --base-url http://localhost:11434
mobilerun run "<task tiếng Anh>" --steps 8 --no-vision   # chạy agent
```

## Kết quả đã xác minh (2026-11-05)

| Task | Bước | Kết quả |
|---|---|---|
| "Unlock the phone by swiping up, then open the Settings app" | 8/8 | ✅ Mở khóa + Settings → "Kết nối", agent tự gọi `complete(success=true)` |
| "Go back to the home screen, then open the Clock app" | 6 | ❌ Click-loop vào "Tin nhắn" (dock cạnh Đồng hồ), cạn bước |
| "Mở ứng dụng Đồng hồ (Clock)" | 10 | ❌ Swiping lan man trong app drawer, không chạm đúng icon |
| "Press home, swipe down to open the notification shade, report notifications" | 5/6 | ✅ Đọc đúng shade: Serial Bluetooth Terminal, Termux:Widget, DuckDuckGo… |

### Bài học thật sự

- **Sở trường của model text-only + a11y tree**: mục tiêu có **text rõ** trong tree
  ("Settings", "Kết nối", nút bấm…) — mở khóa, mở Settings, điều hướng menu → OK.
- **Điểm yếu**: app drawer của One UI — icon app ít text/mèng hơn trong a11y tree,
  7B model không định vị nổi "Đồng hồ" → click-loop rồi cạn `--steps`.
- Agent có xu hướng gọi `complete` sớm khi "vào được một section" — goal cần cụ thể.
- Giải pháp cho task icon-based: `--vision` với model đa phương thức (qwen2.5vl),
  hoặc bỏ qua UI bằng `mobilerun device start <package>` / `mobilerun macro` cho task lặp.
- Mỗi bước ~5–20s inference trên RTX 4050 (q4_K_M) — đủ cho QA/automation chậm-rầm.

## Vì sao chọn đường này

- **Không API key, không cloud** — LLM chạy local, phù hợp thiết bị lab để test suốt ngày.
- **No-root** — Portal chỉ cần accessibility service (mobilerun setup tự bật qua ADB).
- Thay model chỉ bằng 1 cú pull (qwen3:4b, llama3.2:3b, …) — khung agent giữ nguyên.

## Công việc tiếp theo (backlog)

1. Thử `--vision` với model đa phương thức (qwen2.5vl:7b — ~6GB, vừa 6GB VRAM).
2. Trajectory: `--save-trajectory step` để xem agent suy nghĩ từng bước, tune prompt.
3. Kết hợp 2 repo: dùng Agent (mobilerun) tự điền form trong app DuckDuckGo đã repackage
   bằng frida-gadget (xem `2026-11-05-duckduckgo-recon.md`).
4. `mobilerun macro` — ghi chuỗi thao tác rồi replay không cần LLM (rẻ hơn cho task lặp).
