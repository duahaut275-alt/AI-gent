from agents.tools import execute_tool

class AgentHarness:
    @staticmethod
    def run(task: str, context: dict = None):
        """
        Quản lý vòng lặp thực thi của Agent, gọi công cụ (Tools) 
        và tương tác với Database cũ một cách an toàn.
        """
        context = context or {}
        
        # Giả lập quá trình Agent phân tích nhiệm vụ và quyết định gọi Tool
        # Bạn có thể thay thế đoạn này bằng logic gọi LLM thực tế (OpenAI, Anthropic, v.v.)
        
        tool_results = []
        if "kiểm tra" in task.lower() or "tồn kho" in task.lower():
            # Gọi công cụ kiểm tra tồn kho từ database hiện tại
            tool_result = execute_tool("check_inventory", context)
            tool_results.append(tool_result)
        
        return {
            "task": task,
            "status": "success",
            "executed_tools": tool_results,
            "message": "Agent đã phân tích và hoàn thành nhiệm vụ thành công."
        }