# UnCrackable Level 2 — solved: native secret extracted, anti-frida NOPed, Success on device

Ngày: 2026-11-05 · APK 901KB · verify nằm 100% trong native `libfoo.so`
(arm64-v8a). Tool: apktool + jadx + **Ghidra 12.2 headless (JDK 25)** +
llvm-objdump + python + mobilerun Portal.

## 1. Java flow (jadx)

- `MainActivity.onCreate`: native `init()` → root/debuggable checks → watchdog
  `Debug.isDebuggerConnected()`.
- `CodeCheck.a(String)` → **native `bar(byte[])`** — so sánh secret trong native.

## 2. Ghidra headless: bar() lộ secret

Cài đặt lần đầu cần biết (đã mất thời gian debug — ghi lại cho lần sau):

- Ghidra **12.2 yêu cầu JDK 25+** (JDK 21/JRE bị từ chối) → zip JDK 25 từ
  Adoptium API; đường dẫn JDK **không chứa `+`** (LaunchSupport fail với
  `jdk-21.0.13+9`).
- `analyzeHeadless` import xong thì chạy lại bằng **`-process libfoo.so
  -noanalysis`** — `-import` lần 2 sẽ báo "conflicting program file".
- Ghidra 12 đã **bỏ Jython**: post-script `.py` bị từ chối → viết post-script
  **Java** (`DumpDecompiled.java`), Ghidra compile-on-the-fly với JDK 25.

Decompile `Java_sg_vantagepoint_uncrackable2_CodeCheck_bar`:

```c
if ((iVar2 == 0x17) && (strncmp(__s1, &local_50, 0x17) == 0))  // 23 bytes
```

Secret 23 byte = 16 byte literal pool tại `0x100ea0` + 7 byte immediate
`0x68736966206568` ("he fish" LE) — **không có trong strings** vì nhét ngay
trong mã lệnh. Ghép lại:

```
data[0xea0:0xeb0] + b'he fish'  →  "Thanks for all the fish"
```

## 3. Bug tương thích + vá native

L2 gốc **crash ngay trên Android 13**: `RuntimeException: Bad file descriptor`
trong `onCreate` — native `init()` đọc `/proc/net/tcp` (dò frida) nhưng Android
10+ chặn app đọc → throw. Trên máy không frida vẫn crash = bug của crackme.

Vá đúng chuẩn RE (giữ chức năng, bỏ anti-analysis): disassemble
`Java_..._MainActivity_init` bằng llvm-objdump:

```
d94: bl 0x918              ← hàm anti-frida check → NOP
d98: adrp x8, 0x13000
da0: strb w9,[x8,#0xc]     ← DAT_0011300c = 1 (flag mở bar()) — GIỮ
```

Patch `bl` → `nop` (`97fffee1` → `d503201f`) tại file offset **0xd94**,
rebuild + sign + cài → app chạy, `bar()` vẫn hoạt động.

## 4. Xác minh trên thiết bị

Nhập `Thanks for all the fish` qua Portal UI (`input text` với `%s` cho space) →

**"Success! This is the correct secret."** — screenshot:
`D:\Project\re-lab\out\uc2_result.png`.

## 5. Kèm theo: frida-server shell-UID — kết luận thực nghiệm

- `frida-server` chạy dưới shell UID (`/data/local/tmp/fs`): **enumerate
  process OK** qua `frida-ps -H`, nhưng **attach vào untrusted_app treo vĩnh
  viễn** (không ptrace chéo-UID, không avc denial hiển thị). → Frida hoàn toàn
  không khả dụng no-root trên máy này, xác nhận lại kết quả gadget ở L1.

## 6. Bảng chốt

| Bước | Kết quả |
|---|---|
| jadx flow | ✅ verify = native `bar()` |
| Ghidra headless decompile | ✅ (JDK 25 + Java post-script) |
| Trích secret native | ✅ `Thanks for all the fish` |
| Vá crash Android 13 (NOP anti-frida) | ✅ |
| Success trên A03s | ✅ |
| frida-server shell-UID attach | ❌ treo (chốt no-root Frida = không khả thi) |

## Backlog

- UnCrackable Level 3 (Frida anti-detection + custom XOR) — cần Frida → phải đi
  emulator (Genymotion/AVD) thay vì máy thật.
- Đóng gói chuỗi tool "smali/native patch pipeline" thành script chạy 1 lệnh.
