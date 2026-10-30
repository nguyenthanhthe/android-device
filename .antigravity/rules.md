# Quy chuẩn Vận hành Tối ưu Token & Kết nối Android Studio (ACP)

Tài liệu này xác lập quy chuẩn kỹ thuật bắt buộc cho Antigravity Agent khi tương tác với dự án Android và Android Studio qua giao thức ACP (Agent Client Protocol).

---

## 1. Nguyên tắc Đọc Ngữ cảnh (Context Reading Discipline)
- **Cấm đọc tràn lan:** Tuyệt đối không quét (scan) hoặc đọc toàn bộ source code của dự án hay dump cả thư mục vào context window.
- **Truy vấn theo Index/Symbol:** Chỉ truy vấn các file và ký hiệu liên quan trực tiếp đến tính năng hoặc màn hình đang cần sửa đổi thông qua:
  - Cấu trúc Symbol/Index của Android Studio (thông qua ACP IDE Index hoặc lệnh `android studio find-declaration` / `find-usages`).
  - CodeGraph hoặc công cụ tìm kiếm chính xác theo symbol khi cần phân tích luồng dữ liệu liên module.
- **Tiết kiệm Token:** Giữ context gọn gàng; chỉ nạp các file contract (interface, data model) và file UI đang chỉnh sửa trực tiếp.

---

## 2. Nguyên tắc Làm UI với `android preview` (UI Velocity & Token Optimization)
- **Bắt buộc dùng `android preview` thay cho Full Build:** Khi tạo mới hoặc chỉnh sửa giao diện (Jetpack Compose `@Preview` hoặc XML Layout):
  - **Không chạy `./gradlew assembleDebug` hoặc full build** chỉ để kiểm tra UI. Full build làm tiêu tốn tài nguyên máy và mất nhiều phút không cần thiết.
  - **Sử dụng lệnh `android preview`:**
    ```bash
    # Liệt kê danh sách previews có sẵn trong module/target:
    android preview list <reference>

    # Render preview cụ thể với component-tree (không cần mở emulator):
    android preview render --daemon --component-tree <reference> --fqn <package.fileKt.PreviewFunction>
    ```
  - **Kiểm tra Sidecar:** Tận dụng sidecar Compose Preview tại loopback `http://127.0.0.1:<port>` để hiển thị kết quả trực tiếp lên pane giao diện mà không sinh log thừa.
  - **Khi Android Studio đang chạy:** Gọi trực tiếp:
    ```bash
    android studio render-compose-preview <file_path> <composable_name>
    ```
    để tận dụng editor cache sẵn có của IDE, phát hiện tức thì lỗi biên dịch cục bộ và hiển thị semantics tree.

---

## 3. Nguyên tắc Chỉnh sửa File (Surgical Diff & Verification)
- **Sửa theo từng khối nhỏ (Minimal Diff/Patch):**
  - Áp dụng nguyên lý Ponytail: ưu tiên phương án sửa đổi gọn nhất, ít dòng diff nhất đạt được yêu cầu kỹ thuật.
  - Không re-format cả file hoặc đổi thứ tự import không liên quan, tránh làm nhiễu git history và lãng phí token context.
- **Xác minh qua Diagnostic của IDE ngay sau khi sửa:**
  - Ngay sau khi áp dụng diff, kiểm tra lỗi cú pháp và linter thông qua ACP diagnostic của IDE hoặc `android studio analyze-file <path>`.
  - Nếu có cảnh báo hoặc lỗi biên dịch, sửa ngay tại vị trí vừa thay đổi trước khi chuyển sang tác vụ tiếp theo.
