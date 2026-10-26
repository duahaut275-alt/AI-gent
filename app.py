from flask import Flask, render_template, request, jsonify
import sqlite3
import re
import ollama

app = Flask(__name__)

# Duong dan co so du lieu SQLite
DATABASE = "orders.db"


def get_db():
    """Mo ket noi toi SQLite."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Tao bang va du lieu mau neu chua co don hang."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                amount INTEGER NOT NULL CHECK(amount >= 0),
                status TEXT NOT NULL
            )
        """)

        count = conn.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]

        if count == 0:
            sample_orders = [
                ("DH001", "Nguyen Van An", 150000, "Da giao"),
                ("DH002", "Tran Van Binh", 250000, "Dang giao"),
                ("DH003", "Le Minh Cuong", 100000, "Da giao"),
                ("DH004", "Pham Quoc Dung", 300000, "Dang xu ly"),
            ]

            conn.executemany("""
                INSERT INTO orders (id, name, amount, status)
                VALUES (?, ?, ?, ?)
            """, sample_orders)


def get_all_orders():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, name, amount, status
            FROM orders
            ORDER BY id
        """).fetchall()

    return [dict(row) for row in rows]


def get_order(order_id):
    with get_db() as conn:
        row = conn.execute("""
            SELECT id, name, amount, status
            FROM orders
            WHERE id = ?
        """, (order_id,)).fetchone()

    return dict(row) if row else None


def money(value):
    return f"{value:,.0f} VND"


def process_question(question):
    q = question.lower().strip()
    all_orders = get_all_orders()

    # 1. UU TIEN SO 1: Tim don hang co gia tri dat nhat / lon nhat
    if any(word in q for word in ["đắt nhất", "cao nhất", "giá trị lớn nhất", "đơn lớn nhất", "dat nhat", "cao nhat"]):
        if not all_orders:
            return "Hiện chưa có đơn hàng nào trong hệ thống."
        max_order = max(all_orders, key=lambda x: x["amount"])
        return (
            f"Đơn hàng có giá trị lớn nhất là {max_order['id']}:\n"
            f"- Khách hàng: {max_order['name']}\n"
            f"- Giá trị: {money(max_order['amount'])}\n"
            f"- Trạng thái: {max_order['status']}"
        )

    # 2. UU TIEN SO 2: Tinh tong gia tri / doanh thu don hang
    if any(word in q for word in [
        "doanh thu", "tổng giá trị", "tổng tiền",
        "bao nhiêu tiền", "tiền hàng", "tong gia tri", "tong tien"
    ]):
        total = sum(order["amount"] for order in all_orders)
        return f"Tổng giá trị của {len(all_orders)} đơn hàng trong hệ thống là {money(total)}."

    # 3. Tra cuu theo ma don hang cu the (vi du: DH001)
    match = re.search(r"\bdh\s*0*(\d+)\b", q, re.IGNORECASE)

    if match:
        order_id = "DH" + match.group(1).zfill(3)
        order = get_order(order_id)

        if order:
            return (
                f"Thông tin đơn hàng {order['id']}:\n"
                f"- Khách hàng: {order['name']}\n"
                f"- Giá trị: {money(order['amount'])}\n"
                f"- Trạng thái: {order['status']}"
            )

        return f"Không tìm thấy đơn hàng {order_id}."

    # 4. Dem so luong don hang
    if any(word in q for word in [
        "bao nhiêu đơn", "số đơn", "đếm đơn",
        "tổng số đơn", "có mấy đơn", "bao nhieu don"
    ]):
        return f"Hiện tại hệ thống có tổng cộng {len(all_orders)} đơn hàng."

    # 5. Liet ke danh sach don hang
    if "liệt kê" in q or "danh sách đơn" in q or "liet ke" in q or "danh sach" in q:
        if not all_orders:
            return "Hiện chưa có đơn hàng nào."

        lines = ["Danh sách đơn hàng hiện tại:"]
        for order in all_orders:
            lines.append(
                f"- {order['id']}: {order['name']} — "
                f"{money(order['amount'])} ({order['status']})"
            )
        return "\n".join(lines)

    # 6. Cau hoi khac: Goi mo hinh Ollama cuc bo xu ly
    response = ollama.chat(
        model="llama3.2:1b",
        messages=[
            {
                "role": "system",
                "content": (
                    "Bạn là trợ lý AI quản lý đơn hàng. "
                    "Hãy trả lời ngắn gọn, thân thiện bằng tiếng Việt. "
                    "Nếu không biết thông tin thì hãy nói rõ."
                )
            },
            {"role": "user", "content": question}
        ]
    )

    return response.message.content


@app.route("/")
def home():
    return render_template("index.html")


# API: Lay danh sach don hang va thong ke
@app.route("/api/orders", methods=["GET"])
def get_orders():
    all_orders = get_all_orders()
    total = sum(order["amount"] for order in all_orders)

    return jsonify({
        "orders": all_orders,
        "count": len(all_orders),
        "total": total
    })


# API: Tao don hang moi
@app.route("/api/orders", methods=["POST"])
def create_order():
    data = request.get_json(silent=True) or {}

    order_id = str(data.get("id", "")).strip().upper()
    name = str(data.get("name", "")).strip()
    status = str(data.get("status", "Dang xu ly")).strip()

    try:
        amount = int(data.get("amount", -1))
    except (ValueError, TypeError):
        return jsonify({"error": "Số tiền phải là số nguyên."}), 400

    if not re.fullmatch(r"DH\d{3,}", order_id):
        return jsonify({
            "error": "Mã đơn phải có dạng DH001, DH002..."
        }), 400

    if not name:
        return jsonify({"error": "Vui lòng nhập tên khách hàng."}), 400

    if amount < 0:
        return jsonify({"error": "Số tiền không được âm."}), 400

    allowed_statuses = ["Dang xu ly", "Dang giao", "Da giao", "Da huy"]
    if status not in allowed_statuses:
        return jsonify({"error": "Trạng thái không hợp lệ."}), 400

    try:
        with get_db() as conn:
            conn.execute("""
                INSERT INTO orders (id, name, amount, status)
                VALUES (?, ?, ?, ?)
            """, (order_id, name, amount, status))
    except sqlite3.IntegrityError:
        return jsonify({"error": "Mã đơn hàng đã tồn tại."}), 409

    return jsonify({
        "message": "Tạo đơn hàng thành công.",
        "order": get_order(order_id)
    }), 201


# API: Sua don hang
@app.route("/api/orders/<order_id>", methods=["PUT"])
def update_order(order_id):
    data = request.get_json(silent=True) or {}
    order_id = order_id.strip().upper()

    if not get_order(order_id):
        return jsonify({"error": "Không tìm thấy đơn hàng."}), 404

    name = str(data.get("name", "")).strip()
    status = str(data.get("status", "")).strip()

    try:
        amount = int(data.get("amount", -1))
    except (ValueError, TypeError):
        return jsonify({"error": "Số tiền phải là số nguyên."}), 400

    if not name:
        return jsonify({"error": "Vui lòng nhập tên khách hàng."}), 400

    if amount < 0:
        return jsonify({"error": "Số tiền không được âm."}), 400

    allowed_statuses = ["Dang xu ly", "Dang giao", "Da giao", "Da huy"]
    if status not in allowed_statuses:
        return jsonify({"error": "Trạng thái không hợp lệ."}), 400

    with get_db() as conn:
        conn.execute("""
            UPDATE orders
            SET name = ?, amount = ?, status = ?
            WHERE id = ?
        """, (name, amount, status, order_id))

    return jsonify({
        "message": "Cập nhật đơn hàng thành công.",
        "order": get_order(order_id)
    })


# API: Xoa don hang
@app.route("/api/orders/<order_id>", methods=["DELETE"])
def delete_order(order_id):
    order_id = order_id.strip().upper()

    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM orders WHERE id = ?",
            (order_id,)
        )

    if cursor.rowcount == 0:
        return jsonify({"error": "Không tìm thấy đơn hàng."}), 404

    return jsonify({"message": "Xóa đơn hàng thành công."})


# API: Chat voi AI
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    question = str(data.get("message", "")).strip()

    if not question:
        return jsonify({"reply": "Bạn hãy nhập câu hỏi trước nhé."}), 400

    try:
        answer = process_question(question)
        return jsonify({"reply": answer})
    except Exception as error:
        app.logger.exception("Lỗi khi xử lý câu hỏi")
        return jsonify({
            "reply": (
                "Không xử lý được yêu cầu. "
                "Hãy kiểm tra Ollama đang chạy và model đã được tải. "
                f"Chi tiết: {error}"
            )
        }), 500


# Workflow Engine Endpoint tích hợp
from workflows.order_workflow import run_order_workflow

@app.route("/api/order/process", methods=["POST"])
def process_order_endpoint():
    data = request.json
    result = run_order_workflow(data)
    return jsonify({
        "status": "success",
        "workflow_state": result
    }), 200


if __name__ == "__main__":
    init_db()
    print("AI Agent đang khởi động...")
    print("Dữ liệu được lưu trong orders.db")
    print("Mở trình duyệt tại http://127.0.0.1:5000")
    app.run(debug=True)