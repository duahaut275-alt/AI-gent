# Nơi định nghĩa các công cụ (Tools) mà Agent được phép gọi.
# Các hàm này sẽ kết nối trực tiếp với Database hiện tại của bạn (giữ nguyên cấu trúc bảng).

def execute_tool(tool_name: str, payload: dict):
    if tool_name == "check_inventory":
        # TODO: Viết câu lệnh truy vấn Database hiện tại của bạn ở đây
        # Ví dụ: kết nối mô hình ORM cũ hoặc raw SQL query
        return {
            "tool": tool_name,
            "result": "Tồn kho hợp lệ (Dữ liệu lấy từ Database hiện tại)"
        }
    
    return {
        "tool": tool_name,
        "result": "Không tìm thấy công cụ phù hợp"
    }