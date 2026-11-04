# UnCrackable Level 1 — solved end-to-end (static + UI + smali-instrumentation)

Ngày: 2026-11-05 · Theo ruta luyện tay của
[Awesome-Android-Reverse-Engineering](https://github.com/user1342/Awesome-Android-Reverse-Engineering)
(OWASP MASTG Crackmes). APK 66KB, 14 class — mục tiêu lý tưởng để dựng quy trình.

## 1. Phân tích tĩnh (jadx 1.5.6)

- `MainActivity.onCreate`: root check (`sg.vantagepoint.a.c`) + debuggable check
  (`sg.vantagepoint.a.b`) → alert + `System.exit(0)`.
- `MainActivity.verify()` → `sg.vantagepoint.uncrackable1.a.a(String)`: giải mã
  AES rồi `equals` với input.
- `sg.vantagepoint.uncrackable1.a`: key hex `8d127684cbc37c17616d806cf50473cc`,
  ciphertext Base64 `5UJiFctbmgbDoLXmpL12mkno8HT4Lv8dlat8FxR2GOc=`,
  **AES/ECB/PKCS7Padding**.
- Giải mã:

```bash
echo '5UJiFctbmgbDoLXmpL12mkno8HT4Lv8dlat8FxR2GOc=' | \
  openssl enc -d -aes-128-ecb -K 8d127684cbc37c17616d806cf50473cc -base64 -A
# → I want to believe
```

## 2. Xác nhận qua UI (mobilerun Portal)

Cài APK gốc lên A03s (no root → không alert), nhập secret bằng Portal:

- `mobilerun device ui` → EditText (277,194), VERIFY (637,195)
- `mobilerun device type "I want to believe"` → `device tap 637 195`
- Kết quả: dialog **"Success! This is the correct secret."** (ảnh chụp giữ tại
  `D:\Temp\mobilerun_htblgdrb.png`)

## 3. Frida-gadget repackage — bị chặn bởi SELinux (kết quả âm có giá trị)

Quy trình chuẩn no-root của Awesome-RE **không chạy được trên A03s (One UI 5.1 /
Android 13)**:

1. Inject `System.loadLibrary("frida-gadget")` vào `MainActivity.onCreate`
   (apktool d → sửa smali → `lib/arm64-v8a/libfrida-gadget.so` → apktool b →
   uber-apk-signer) — gadget **load ok** (`nativeloader ... : ok`).
2. Mặc định (listen 27042): `F Frida: Failed to start: Unable to create socket:
   Operation not permitted` — untrusted_app SELinux domain chặn socket của gadget.
3. Chuyển sang **script interaction** (`libfrida-gadget.config.so` trỏ tới
   `/data/data/<pkg>/files/hook.js`, push qua `run-as`) + bật `debuggable=true` +
   **patch out anti-debug check** (`sg.vantagepoint.a.b.a()` → luôn `false`):
   gadget vẫn init im lặng, script không chạy, không có dòng log nào.
4. Kết luận: sandbox Android 13 của máy chặn Frida-gadget ở mức core — con đường
   hook runtime chuẩn không khả thi **trên máy này** mà không có root.

> Ghi chú thao tác: `adb push` từ Git Bash cần `MSYS_NO_PATHCONV=1` để không bị
> biến `/data/...` thành `C:/Program Files/Git/data/...`.

## 4. Smali-level instrumentation — cách THẮNG được

Không có Frida? Instrument thẳng trong smali — sửa `sg/vantagepoint/uncrackable1/a.smali`,
ngay sau `String.<init>([B)` dựng chuỗi secret:

```smali
const-string v2, "SMALIHOOK"
invoke-static {v2, v1}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;)I
```

Rebuild + sign + cài, nhập input SAI, VERIFY — và secret app vừa giải mã
**tự leak ra logcat**:

```
E SMALIHOOK: I want to believe
```

Đây là phân tích động thật sự (hành vi runtime bị thay đổi bởi instrumentation),
vượt qua block của Frida vì không cần socket/ptrace nào.

## 5. Bảng chốt

| Kỹ thuật | Kết quả trên A03s (no root) |
|---|---|
| jadx static → secret | ✅ `I want to believe` |
| Portal UI nhập secret → Success | ✅ |
| frida-gadget listen | ❌ SELinux EPERM khi tạo socket |
| frida-gadget script mode | ❌ init im lặng, script không chạy |
| smali patch (anti-debug bypass + log leak) | ✅ secret leak runtime |

## Backlog tiếp theo

- Thử `frida-server` chạy trong Termux (cùng-UID giới hạn — có thể chỉ hook được
  process của Termux; chuẩn bị kịch bản test).
- Repackage DuckDuckGo với SMALIHOOK-style logging cho các flow autofill.
- UnCrackable Level 2 (có native lib + anti-frida) — cần Ghidra; để wave sau.
