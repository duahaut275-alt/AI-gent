
# BAI 4: AI AGENT QUAN LY DON HANG
# Tac gia: Hoang Duc Thanh
# Phien ban hoc tap - khong dung API tra phi

# Du lieu don hang mau
orders = [
    {"id": "DH001", "customer": "An", "amount": 150000, "status": "Da giao"},
    {"id": "DH002", "customer": "Binh", "amount": 250000, "status": "Dang giao"},
    {"id": "DH003", "customer": "Cuong", "amount": 100000, "status": "Da giao"},
    {"id": "DH004", "customer": "Dung", "amount": 300000, "status": "Dang xu ly"},
]


# TOOL 1: Tinh tong doanh thu
def get_revenue():
    total = sum(order["amount"] for order in orders)
    return f"Tong gia tri cac don hang mau: {total:,} VND"


# TOOL 2: Tim don hang theo ma
def find_order(order_id):
    for order in orders:
        if order["id"].lower() == order_id.lower():
            return (
                f"Ma don: {order['id']}\n"
                f"Khach hang: {order['customer']}\n"
                f"So tien: {order['amount']:,} VND\n"
                f"Trang thai: {order['status']}"
            )

    return f"Khong tim thay don hang {order_id}."


# TOOL 3: Dem don hang theo trang thai
def count_orders():
    total = len(orders)
    delivered = sum(
        1 for order in orders
        if order["status"] == "Da giao"
    )
    processing = sum(
        1 for order in orders
        if order["status"] == "Dang xu ly"
    )
    shipping = sum(
        1 for order in orders
        if order["status"] == "Dang giao"
    )

    return (
        f"Tong so don: {total}\n"
        f"Da giao: {delivered}\n"
        f"Dang giao: {shipping}\n"
        f"Dang xu ly: {processing}"
    )


# BO NHO DON GIAN TRONG PHIEN LAM VIEC
memory = []


# AGENT: Phan tich yeu cau va chon tool
def run_agent(request):
    text = request.lower().strip()

    print("\n[Agent] Dang phan tich yeu cau...")

    # Bổ sung thêm các từ khóa liên quan đến doanh thu và tổng giá trị
    if any(word in text for word in ["doanh thu", "tong tien", "tong doanh so", "tong gia tri", "gia tri"]):
        print("[Agent] Chon tool: get_revenue")
        result = get_revenue()

    elif "dh" in text and any(
        word in text for word in ["tim", "tra cuu", "thong tin", "don hang", "dat nhat"]
    ):
        order_id = None

        # Xu ly truong hop tim don hang dat nhat hoac theo ma cu the
        if "dat nhat" in text:
            print("[Agent] Chon tool: find_order (Tim don max)")
            # Tim don hang co amount lon nhat
            max_order = max(orders, key=lambda x: x["amount"])
            order_id = max_order["id"]

        # Tim ma don hang trong cau hoi
        for word in request.upper().replace(",", " ").split():
            cleaned = word.strip("?.!,;:")
            if cleaned.startswith("DH") and cleaned[2:].isdigit():
                order_id = cleaned
                break

        if order_id:
            print("[Agent] Chon tool: find_order")
            result = find_order(order_id)
        else:
            result = "Ban hay cung cap ma don hang, vi du DH001."

    elif any(word in text for word in ["bao nhieu don", "dem don", "trang thai cac don", "tong so don"]):
        print("[Agent] Chon tool: count_orders")
        result = count_orders()

    elif any(word in text for word in ["xin chao", "chao agent", "hello", "chào"]):
        result = "Xin chao! Toi co the giup ban tra cuu don hang va tinh doanh thu."

    elif any(word in text for word in ["lich su", "da hoi gi", "nho gi"]):
        if memory:
            result = "Cac yeu cau truoc cua ban:\n" + "\n".join(
                f"- {item}" for item in memory
            )
        else:
            result = "Ban chua co yeu cau nao duoc luu trong phien nay."

    else:
        result = (
            "Toi chua xu ly duoc yeu cau nay.\n"
            "Ban thu: tinh doanh thu, tim don DH001, don dat nhat, dem don hang "
            "hoac xem lich su."
        )

    memory.append(request)

    print("\n[Agent] Ket qua:")
    print(result)
    return result


# CHUONG TRINH CHINH
def main():
    print("=" * 42)
    print(" AI AGENT QUAN LY DON HANG - BAN MIEN PHI")
    print("=" * 42)
    print("Nhap 'thoat' de dung chuong trinh.")

    while True:
        request = input("\nBan: ").strip()

        if request.lower() in ["thoat", "exit", "quit"]:
            print("Agent: Tam biet! Hen gap lai.")
            break

        if not request:
            print("Agent: Ban hay nhap mot yeu cau.")
            continue

        run_agent(request)


if __name__ == "__main__":
    main()
