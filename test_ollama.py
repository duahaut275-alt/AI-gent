
import ollama

print("=" * 40)
print("KIEM TRA AI AGENT - OLLAMA")
print("=" * 40)

try:
    response = ollama.chat(
        model="llama3.2:1b",
        messages=[
            {
                "role": "user",
                "content": "Xin chao! Hay gioi thieu ngan gon bang tieng Viet."
            }
        ]
    )

    print("\nAI tra loi:")
    print(response["message"]["content"])

except Exception as e:
    print("\nKhong ket noi duoc voi AI.")
    print("Chi tiet loi:", e)
