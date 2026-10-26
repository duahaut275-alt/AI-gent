from flask import Flask, request, jsonify
from workflows.order_workflow import run_order_workflow

# Giữ nguyên app hiện tại của bạn
app = Flask(__name__)

@app.route("/api/order/process", methods=["POST"])
def process_order_endpoint():
    data = request.json
    
    # Gọi Workflow Engine, hoàn toàn không làm ảnh hưởng đến các bảng dữ liệu cũ
    result = run_order_workflow(data)
    
    return jsonify({
        "status": "success",
        "workflow_state": result
    }), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)