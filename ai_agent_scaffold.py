import asyncio
import json
from playwright.async_api import async_playwright

# Đây là ví dụ về cấu trúc của một AI Agent thực thụ.
# Thay vì hardcode từng bước (click A, click B), Agent sẽ:
# 1. QUAN SÁT (Observe): Lấy HTML hoặc Screenshot hiện tại.
# 2. SUY NGHĨ (Think): Gửi thông tin cho LLM (như GPT-4, Gemini) hỏi "Tôi nên làm gì tiếp theo?".
# 3. HÀNH ĐỘNG (Act): Thực thi câu trả lời của LLM.

class AIAgent:
    def __init__(self, page):
        self.page = page
        self.history = [] # Lưu lịch sử hành động để Agent nhớ

    async def get_observation(self):
        """Bước 1: Quan sát - Lấy thông tin trang web"""
        # Cách đơn giản: Lấy text hoặc HTML rút gọn
        # Cách xịn hơn: Chụp ảnh màn hình (Vision Model)
        title = await self.page.title()
        url = self.page.url
        # Lấy các phần tử tương tác quan trọng (Button, Link, Input)
        # Đây là ví dụ đơn giản hóa
        interactables = await self.page.evaluate("""
            Array.from(document.querySelectorAll('button, a, input, select')).map(el => {
                return {
                    tag: el.tagName,
                    text: el.innerText || el.value || el.placeholder,
                    selector: el.id ? '#' + el.id : el.className
                }
            }).slice(0, 50) # Lấy 50 cái đầu thôi cho đỡ nặng
        """)
        return {
            "title": title,
            "url": url,
            "elements": interactables
        }

    async def ask_llm(self, task_description, observation):
        """Bước 2: Suy nghĩ - Gọi AI để quyết định (MOCK FUNCTION)"""
        
        prompt = f"""
        Nhiệm vụ: {task_description}
        Trạng thái hiện tại: {json.dumps(observation, indent=2)}
        Lịch sử: {self.history}
        
        Hãy trả về JSON hành động tiếp theo. Ví dụ:
        {{ "type": "click", "selector": "button.login" }}
        hoặc {{ "type": "fill", "selector": "#email", "value": "test@test.com" }}
        hoặc {{ "type": "finish", "reason": "Đã xong" }}
        """
        
        print("\n--- Gửi Prompt cho AI ---")
        # print(prompt) 
        
        # Ở ĐÂY SẼ LÀ CODE GỌI API (OpenAI / Gemini / Anthropic)
        # response = openai.chat.completions.create(...)
        # return json.loads(response.choices[0].message.content)
        
        # Vì không có API key thật, mình sẽ GIẢ LẬP hành động trả về
        # Ví dụ giả vờ AI bảo click vào ô search
        print("(Giả lập AI đang suy nghĩ...)")
        await asyncio.sleep(1)
        
        return {
            "type": "finish", 
            "reason": "Đây là code mẫu, cần API Key để chạy thật"
        }

    async def execute_action(self, action):
        """Bước 3: Hành động - Thực thi lệnh từ AI"""
        print(f"👉 AI quyết định: {action}")
        self.history.append(action)
        
        if action["type"] == "click":
            await self.page.click(action["selector"])
        elif action["type"] == "fill":
            await self.page.fill(action["selector"], action["value"])
        elif action["type"] == "goto":
            await self.page.goto(action["url"])
        elif action["type"] == "finish":
            return True # Đã xong
        
        # Chờ trang load sau hành động
        await self.page.wait_for_load_state("networkidle")
        return False

    async def solve(self, task_description):
        print(f"🚀 Bắt đầu giải task: {task_description}")
        
        max_steps = 10
        for i in range(max_steps):
            print(f"\nStep {i+1}:")
            
            # 1. Quan sát
            obs = await self.get_observation()
            
            # 2. Hỏi AI
            action = await self.ask_llm(task_description, obs)
            
            # 3. Thực thi
            is_done = await self.execute_action(action)
            
            if is_done:
                print("✅ Task hoàn thành!")
                break

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        agent = AIAgent(page)
        
        # Thử chạy Agent với một task
        await page.goto("http://127.0.0.1:8080")
        await agent.solve("Tìm kiếm sản phẩm áo thun (T-Shirt)")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
