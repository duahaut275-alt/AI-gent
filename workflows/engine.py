class WorkflowEngine:
    def __init__(self, state_data=None):
        self.state_data = state_data or {}
        self.current_step = "START"
        self.history = []

    def transition(self, next_step, data=None):
        """Chuyển trạng thái tiếp theo trong workflow và ghi lại lịch sử."""
        self.history.append(self.current_step)
        self.current_step = next_step
        if data:
            self.state_data.update(data)
        return self.current_step

    def get_state(self):
        """Lấy trạng thái hiện tại của workflow."""
        return {
            "current_step": self.current_step,
            "data": self.state_data,
            "history": self.history
        }