
import ollama

# Du lieu don hang thu nghiem
orders = [
    {"id": "DH001", "name": "An", "amount": 150000, "status": "Da giao"},
    {"id": "DH002", "name": "Binh", "amount": 250000, "status": "Dang giao"},
    {"id": "DH003", "name": "Cuong", "amount": 100000, "status": "Da giao"},
    {"id": "DH004", "name": "Dung", "amount": 300000, "status": "Dang xu ly"},
]


def get_revenue() -> str:
    """Tinh tong gia tri cac don hang."""
    total = sum(order["amount"] for order in orders)
    return f"Tong gia tri don hang: {total:,} VND"


def count_orders() -> str:
    """Dem so don hang."""
    return f"So don hang: {len(orders)}"


def find_order(order_id: str) -> str:
    """Tim don hang theo ma, vi du DH001."""
    for order in orders:
        if order["id"].lower() == order_id.lower():
            return str(order)
    return f"Khong tim thay don hang {order_id}"


tools = [get_revenue, count_orders, find_order]

messages = [
    {
        "role": "system",
        "content": (
            "Ban la tro ly quan ly don hang. "
            "Tra loi bang tieng Viet khong dau neu can. "
            "Khi duoc hoi doanh thu, hay goi get_revenue. "
            "Khi duoc hoi so don, hay goi count_orders. "
            "Khi tim ma don, hay goi find_order."
        ),
    },
    {
        "role": "user",
        "content": "Hay tinh tong gia tri cac don hang."
    },
]

try:
    response = ollama.chat(
        model="llama3.2:1b",
        messages=messages,
        tools=tools,
    )

    message = response.message

    if message.tool_calls:
        for call in message.tool_calls:
            name = call.function.name
            args = call.function.arguments

            available_tools = {
                "get_revenue": get_revenue,
                "count_orders": count_orders,
                "find_order": find_order,
            }

            if name in available_tools:
                result = available_tools[name](**args)
                print("AI da goi cong cu:", name)
                print("Ket qua:", result)
    else:
        print("AI tra loi:", message.content)
        print("Mo hinh chua goi cong cu Python trong lan thu nay.")

except Exception as e:
    print("Co loi khi thu nghiem:", e)
