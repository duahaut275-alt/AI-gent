
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


def tool_get_revenue() -> str:
    """Tinh tong gia tri cac don hang trong co so du lieu."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS count, COALESCE(SUM(amount), 0) AS total FROM orders"
        ).fetchone()
    return f"So don hang: {row['count']}. Tong gia tri: {money(row['total'])}."


def tool_count_orders() -> str:
    """Dem so don hang hien co trong co so du lieu."""
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    return f"Hien co {count} don hang."


def tool_find_order(order_id: str) -> str:
    """Tim thong tin mot don hang theo ma, vi du DH001."""
    normalized_id = str(order_id).strip().upper()
    if not normalized_id.startswith("DH"):
        normalized_id = "DH" + normalized_id
    match = re.fullmatch(r"DH\s*0*(\d+)", normalized_id)
    if match:
        normalized_id = "DH" + match.group(1).zfill(3)

    order = get_order(normalized_id)
    if not order:
        return f"Khong tim thay don hang {normalized_id}."

    return (
        f"Ma don: {order['id']}; "
        f"Khach hang: {order['name']}; "
        f"Gia tri: {money(order['amount'])}; "
        f"Trang thai: {order['status']}."
    )


def tool_list_orders() -> str:
    """Lay danh sach tat ca don hang, gom ma, khach hang, gia tri va trang thai."""
    orders = get_all_orders()
    if not orders:
        return "Hien chua co don hang nao."
    lines = [
        f"{o['id']} | {o['name']} | {money(o['amount'])} | {o['status']}"
        for o in orders
    ]
    return "Danh sach don hang:\n" + "\n".join(lines)


AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "tool_get_revenue",
            "description": "Tinh tong gia tri va so luong don hang tu co so du lieu.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tool_count_orders",
            "description": "Dem so don hang hien co.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tool_find_order",
            "description": "Tim don hang theo ma don, vi du DH001.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Ma don hang can tim, vi du DH001",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tool_list_orders",
            "description": "Lay danh sach cac don hang hien co.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

AVAILABLE_TOOLS = {
    "tool_get_revenue": tool_get_revenue,
    "tool_count_orders": tool_count_orders,
    "tool_find_order": tool_find_order,
    "tool_list_orders": tool_list_orders,
}


def process_question(question):
    """Vong lap AI Agent: model chon cong cu, Python thuc thi, model tong hop."""
    messages = [
        {
            "role": "system",
            "content": (
                "Ban la OrderMind AI, tro ly quan ly don hang. "
                "Tra loi bang tieng Viet, than thien va de hieu. "
                "Neu cau hoi can thong tin don hang, doanh thu, so don hoac danh sach, "
                "hay goi cong cu phu hop de lay du lieu that tu co so du lieu. "
                "Khong tu phat minh so lieu. Neu cong cu tra ve khong tim thay don, "
                "hay noi ro voi nguoi dung. Chi doc va tra cuu du lieu; khong tu y sua "
                "hoac xoa don hang."
            ),
        },
        {"role": "user", "content": question},
    ]

    # Gioi han so vong de tranh lap vo han neu model cu goi cong cu.
    for _ in range(5):
        response = ollama.chat(
            model="llama3.2:1b",
            messages=messages,
            tools=AGENT_TOOLS,
        )
        message = response.message

        if not message.tool_calls:
            return message.content or "Toi chua tao duoc cau tra loi. Ban thu hoi lai nhe."

        # Them phan hoi cua AI (bao gom cac lenh goi cong cu) vao lich su.
        messages.append(message)

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = tool_call.function.arguments or {}
            tool_function = AVAILABLE_TOOLS.get(tool_name)

            if tool_function is None:
                tool_result = f"Cong cu khong duoc ho tro: {tool_name}"
            else:
                try:
                    tool_result = tool_function(**tool_args)
                except Exception:
                    app.logger.exception("Loi khi chay cong cu AI: %s", tool_name)
                    tool_result = "Cong cu gap loi khi truy van co so du lieu."

            app.logger.info("AI Agent da goi cong cu: %s", tool_name)
            messages.append(
                {
                    "role": "tool",
                    "name": tool_name,
                    "content": str(tool_result),
                }
            )

    return "AI da thuc hien qua nhieu buoc. Ban hay thu dat cau hoi ngan gon hon."


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
        return jsonify({"error": "So tien phai la so nguyen."}), 400

    if not re.fullmatch(r"DH\d{3,}", order_id):
        return jsonify({
            "error": "Ma don phai co dang DH001, DH002..."
        }), 400

    if not name:
        return jsonify({"error": "Vui long nhap ten khach hang."}), 400

    if amount < 0:
        return jsonify({"error": "So tien khong duoc am."}), 400

    allowed_statuses = ["Dang xu ly", "Dang giao", "Da giao", "Da huy"]
    if status not in allowed_statuses:
        return jsonify({"error": "Trang thai khong hop le."}), 400

    try:
        with get_db() as conn:
            conn.execute("""
                INSERT INTO orders (id, name, amount, status)
                VALUES (?, ?, ?, ?)
            """, (order_id, name, amount, status))
    except sqlite3.IntegrityError:
        return jsonify({"error": "Ma don hang da ton tai."}), 409

    return jsonify({
        "message": "Tao don hang thanh cong.",
        "order": get_order(order_id)
    }), 201


# API: Sua don hang
@app.route("/api/orders/<order_id>", methods=["PUT"])
def update_order(order_id):
    data = request.get_json(silent=True) or {}
    order_id = order_id.strip().upper()

    if not get_order(order_id):
        return jsonify({"error": "Khong tim thay don hang."}), 404

    name = str(data.get("name", "")).strip()
    status = str(data.get("status", "")).strip()

    try:
        amount = int(data.get("amount", -1))
    except (ValueError, TypeError):
        return jsonify({"error": "So tien phai la so nguyen."}), 400

    if not name:
        return jsonify({"error": "Vui long nhap ten khach hang."}), 400

    if amount < 0:
        return jsonify({"error": "So tien khong duoc am."}), 400

    allowed_statuses = ["Dang xu ly", "Dang giao", "Da giao", "Da huy"]
    if status not in allowed_statuses:
        return jsonify({"error": "Trang thai khong hop le."}), 400

    with get_db() as conn:
        conn.execute("""
            UPDATE orders
            SET name = ?, amount = ?, status = ?
            WHERE id = ?
        """, (name, amount, status, order_id))

    return jsonify({
        "message": "Cap nhat don hang thanh cong.",
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
        return jsonify({"error": "Khong tim thay don hang."}), 404

    return jsonify({"message": "Xoa don hang thanh cong."})


# API: Chat voi AI
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    question = str(data.get("message", "")).strip()

    if not question:
        return jsonify({"reply": "Ban hay nhap cau hoi truoc nhe."}), 400

    try:
        answer = process_question(question)
        return jsonify({"reply": answer})
    except Exception as error:
        app.logger.exception("Loi khi xu ly cau hoi")
        return jsonify({
            "reply": (
                "Khong xu ly duoc yeu cau. "
                "Hay kiem tra Ollama dang chay va model da duoc tai. "
                f"Chi tiet: {error}"
            )
        }), 500


if __name__ == "__main__":
    init_db()
    print("AI Agent dang khoi dong...")
    print("Du lieu duoc luu trong orders.db")
    print("Mo trinh duyet tai http://127.0.0.1:5000")
    app.run(debug=True)
