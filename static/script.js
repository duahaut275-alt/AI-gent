"use strict";

// ==========================================
// 1. KHAI BAO CAC THANH PHAN HTML
// ==========================================

const orderForm = document.getElementById("orderForm");
const orderIdInput = document.getElementById("orderId");
const customerNameInput = document.getElementById("customerName");
const orderAmountInput = document.getElementById("orderAmount");
const orderStatusInput = document.getElementById("orderStatus");

const ordersTableBody = document.getElementById("ordersTableBody");
const formTitle = document.getElementById("formTitle");
const saveOrderBtn = document.getElementById("saveOrderBtn");
const cancelEditBtn = document.getElementById("cancelEditBtn");
const formMessage = document.getElementById("formMessage");

const orderSearch = document.getElementById("orderSearch");
const visibleOrderCount = document.getElementById("visibleOrderCount");
const refreshOrdersBtn = document.getElementById("refreshOrdersBtn");

let editingOrderId = null;
let allOrders = [];
let isSaving = false;


// ==========================================
// 2. CAC HAM DUNG CHUNG
// ==========================================

function formatMoney(amount) {
    return Number(amount).toLocaleString("vi-VN") + " ₫";
}

function showMessage(message, isError = false) {
    if (!formMessage) return;

    formMessage.textContent = message;
    formMessage.style.color = isError ? "#ff7373" : "#65d6a5";
}

async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            ...(options.body ? { "Content-Type": "application/json" } : {}),
            ...(options.headers || {})
        }
    });

    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error("Máy chủ trả về dữ liệu không hợp lệ.");
    }

    if (!response.ok) {
        throw new Error(
            data.error || data.reply || "Yêu cầu không thành công."
        );
    }

    return data;
}


// ==========================================
// 3. TAI VA HIEN THI DON HANG
// ==========================================

async function loadOrders() {
    if (!ordersTableBody) return;

    try {
        const data = await apiRequest("/api/orders");

        allOrders = Array.isArray(data.orders) ? data.orders : [];

        updateStatistics(data);
        renderOrders();

    } catch (error) {
        console.error("Loi tai don hang:", error);

        ordersTableBody.replaceChildren();

        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = 5;
        cell.textContent = "Không tải được đơn hàng. Hãy thử làm mới.";
        row.appendChild(cell);
        ordersTableBody.appendChild(row);

        if (visibleOrderCount) {
            visibleOrderCount.textContent = "Không tải được dữ liệu";
        }

        showMessage("Lỗi tải đơn hàng: " + error.message, true);
    }
}

function updateStatistics(data) {
    const countElement = document.getElementById("orderCount");
    const totalElement = document.getElementById("totalRevenue");
    const amountElement = document.getElementById("totalAmount");

    if (countElement) {
        countElement.textContent = data.count ?? allOrders.length;
    }

    const total = data.total ??
        allOrders.reduce((sum, order) => sum + Number(order.amount), 0);

    if (totalElement) {
        totalElement.textContent = formatMoney(total);
    }

    if (amountElement) {
        amountElement.textContent = formatMoney(total);
    }
}

function renderOrders() {
    if (!ordersTableBody) return;

    const keyword = orderSearch
        ? orderSearch.value.trim().toLocaleLowerCase("vi")
        : "";

    const filteredOrders = allOrders.filter(order => {
        const searchableText = [
            order.id,
            order.name,
            order.status
        ].join(" ").toLocaleLowerCase("vi");

        return searchableText.includes(keyword);
    });

    ordersTableBody.replaceChildren();

    if (filteredOrders.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = 5;
        cell.textContent = allOrders.length === 0
            ? "Chưa có đơn hàng nào."
            : "Không tìm thấy đơn hàng phù hợp.";

        row.appendChild(cell);
        ordersTableBody.appendChild(row);
    } else {
        filteredOrders.forEach(order => {
            const row = document.createElement("tr");

            // Ma don
            const idCell = document.createElement("td");
            idCell.className = "order-id";
            idCell.textContent = order.id;
            row.appendChild(idCell);

            // Ten khach hang
            const nameCell = document.createElement("td");
            nameCell.textContent = order.name;
            row.appendChild(nameCell);

            // So tien
            const amountCell = document.createElement("td");
            amountCell.textContent = formatMoney(order.amount);
            row.appendChild(amountCell);

            // Trang thai
            const statusCell = document.createElement("td");
            const statusBadge = document.createElement("span");
            statusBadge.className = "status " + getStatusClass(order.status);
            statusBadge.textContent = translateStatus(order.status);
            statusCell.appendChild(statusBadge);
            row.appendChild(statusCell);

            // Nut thao tac
            const actionsCell = document.createElement("td");
            actionsCell.className = "order-actions";

            const editButton = document.createElement("button");
            editButton.type = "button";
            editButton.textContent = "Sửa";
            editButton.setAttribute("aria-label", "Sửa đơn hàng " + order.id);
            editButton.addEventListener("click", () => startEdit(order));

            const deleteButton = document.createElement("button");
            deleteButton.type = "button";
            deleteButton.textContent = "Xóa";
            deleteButton.setAttribute("aria-label", "Xóa đơn hàng " + order.id);
            deleteButton.addEventListener("click", () => removeOrder(order.id));

            actionsCell.append(editButton, deleteButton);
            row.appendChild(actionsCell);

            ordersTableBody.appendChild(row);
        });
    }

    if (visibleOrderCount) {
        visibleOrderCount.textContent =
            `${filteredOrders.length}/${allOrders.length} đơn hàng`;
    }
}

function translateStatus(status) {
    const statuses = {
        "Dang xu ly": "Đang xử lý",
        "Dang giao": "Đang giao",
        "Da giao": "Đã giao",
        "Da huy": "Đã hủy"
    };

    return statuses[status] || status;
}

function getStatusClass(status) {
    const classes = {
        "Dang xu ly": "status-pending",
        "Dang giao": "status-shipping",
        "Da giao": "status-delivered",
        "Da huy": "status-pending"
    };
    return classes[status] || "status-pending";
}


// ==========================================
// 4. TAO VA CAP NHAT DON HANG
// ==========================================

if (orderForm) {
    orderForm.addEventListener("submit", async event => {
        event.preventDefault();

        if (isSaving) return;

        const rawAmount = orderAmountInput.value.trim();
        const amount = Number(rawAmount);

        const order = {
            id: orderIdInput.value.trim().toUpperCase(),
            name: customerNameInput.value.trim(),
            amount: amount,
            status: orderStatusInput.value
        };

        if (!order.id || !order.name || rawAmount === "") {
            showMessage("Vui lòng nhập đầy đủ thông tin.", true);
            return;
        }

        if (!Number.isSafeInteger(amount) || amount < 0) {
            showMessage("Số tiền phải là số nguyên không âm.", true);
            return;
        }

        if (!editingOrderId && !/^DH\d{3,}$/.test(order.id)) {
            showMessage("Mã đơn phải có dạng DH005, DH006...", true);
            return;
        }

        try {
            isSaving = true;
            saveOrderBtn.disabled = true;

            if (editingOrderId) {
                await apiRequest(
                    `/api/orders/${encodeURIComponent(editingOrderId)}`,
                    {
                        method: "PUT",
                        body: JSON.stringify({
                            name: order.name,
                            amount: order.amount,
                            status: order.status
                        })
                    }
                );

                showMessage("Cập nhật đơn hàng thành công!");
            } else {
                await apiRequest("/api/orders", {
                    method: "POST",
                    body: JSON.stringify(order)
                });

                showMessage("Tạo đơn hàng thành công!");
            }

            resetForm();
            await loadOrders();

        } catch (error) {
            showMessage(error.message, true);
        } finally {
            isSaving = false;
            saveOrderBtn.disabled = false;
        }
    });
}


// ==========================================
// 5. SUA DON HANG
// ==========================================

function startEdit(order) {
    editingOrderId = order.id;

    orderIdInput.value = order.id;
    orderIdInput.disabled = true;

    customerNameInput.value = order.name;
    orderAmountInput.value = order.amount;
    orderStatusInput.value = order.status;

    formTitle.textContent = "Sửa đơn hàng " + order.id;
    saveOrderBtn.textContent = "Cập nhật đơn hàng";

    cancelEditBtn.hidden = false;

    showMessage("Bạn đang chỉnh sửa đơn " + order.id + ".");

    orderForm.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });
}

function resetForm() {
    editingOrderId = null;

    orderForm.reset();

    orderIdInput.disabled = false;
    formTitle.textContent = "Tạo đơn hàng mới";
    saveOrderBtn.textContent = "Lưu đơn hàng";
    cancelEditBtn.hidden = true;
}

if (cancelEditBtn) {
    cancelEditBtn.addEventListener("click", () => {
        resetForm();
        showMessage("Đã hủy thao tác sửa.");
    });
}


// ==========================================
// 6. XOA DON HANG
// ==========================================

async function removeOrder(orderId) {
    const confirmed = window.confirm(
        `Bạn có chắc chắn muốn xóa đơn hàng ${orderId} không?`
    );

    if (!confirmed) return;

    try {
        await apiRequest(
            `/api/orders/${encodeURIComponent(orderId)}`,
            { method: "DELETE" }
        );

        if (editingOrderId === orderId) {
            resetForm();
        }

        showMessage(`Đã xóa đơn hàng ${orderId}.`);
        await loadOrders();

    } catch (error) {
        showMessage(error.message, true);
    }
}


// ==========================================
// 7. TIM KIEM VA LAM MOI
// ==========================================

if (orderSearch) {
    orderSearch.addEventListener("input", renderOrders);
}

if (refreshOrdersBtn) {
    refreshOrdersBtn.addEventListener("click", loadOrders);
}


// ==========================================
// 8. TRO LY AI ORDERMIND (CHUAN HOA API)
// ==========================================

const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const chatMessages = document.getElementById("chatMessages");
const sendChatBtn = document.getElementById("sendChatBtn");

function addChatMessage(messageText, sender) {
    if (!chatMessages) return;

    const messageContainer = document.createElement("div");

    // Phân loại class để CSS tự động căn lề (user bên phải, assistant bên trái)
    if (sender === "user") {
        messageContainer.className = "chat-message user-message message";
    } else {
        messageContainer.className = "chat-message assistant-message message";
    }

    // Avatar hiển thị
    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = sender === "user" ? "Bạn" : "✦";
    messageContainer.appendChild(avatar);

    // Nội dung bong bóng chat
    const bubble = document.createElement("div");
    bubble.className = "message-bubble bubble";
    bubble.textContent = messageText;
    messageContainer.appendChild(bubble);

    chatMessages.appendChild(messageContainer);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

if (chatForm) {
    chatForm.addEventListener("submit", async event => {
        event.preventDefault();

        const question = chatInput.value.trim();
        if (!question) return;

        // 1. Hiển thị câu hỏi của người dùng (Nằm bên phải)
        addChatMessage(question, "user");

        chatInput.value = "";
        sendChatBtn.disabled = true;
        sendChatBtn.textContent = "...";

        try {
            // 2. Gửi request đến Flask Backend API
            const data = await apiRequest("/api/chat", {
                method: "POST",
                body: JSON.stringify({ message: question })
            });

            // 3. Hiển thị câu trả lời từ AI (Nằm bên trái)
            addChatMessage(data.reply || "AI chưa có phản hồi.", "assistant");

        } catch (error) {
            addChatMessage(
                "Không thể nhận phản hồi từ AI: " + error.message,
                "assistant"
            );
        } finally {
            sendChatBtn.disabled = false;
            sendChatBtn.textContent = "Gửi ↑";
            chatInput.focus();
        }
    });
}


// ==========================================
// 9. KHOI DONG
// ==========================================

loadOrders();