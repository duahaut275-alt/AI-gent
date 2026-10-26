from workflows.engine import WorkflowEngine
from agents.harness import AgentHarness

def run_order_workflow(input_payload):
    """Luồng xử lý đơn hàng tích hợp Workflow Engine và Agent Harness."""
    engine = WorkflowEngine(state_data=input_payload)
    
    try:
        # Bước 1: Tiếp nhận và Xác thực dữ liệu
        engine.transition("VALIDATING")
        order_info = engine.state_data.get("order_info", "")
        
        if not order_info:
            engine.transition("FAILED", {"error": "Thiếu thông tin đơn hàng"})
            return engine.get_state()

        # Bước 2: Phân tích và Xử lý thông minh bằng Agent Harness
        engine.transition("AGENT_PROCESSING")
        agent_output = AgentHarness.run(
            task=f"Xử lý và kiểm tra đơn hàng: {order_info}",
            context=engine.state_data
        )
        
        # Bước 3: Hoàn thành
        engine.transition("COMPLETED", {"agent_result": agent_output})
        
    except Exception as e:
        engine.transition("ERROR", {"error": str(e)})
        
    return engine.get_state()