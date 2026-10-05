import asyncio
import os
import json
import base64
import time
import requests
from playwright.async_api import async_playwright

# Setup for Ollama
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llava" # Default to llava for Vision capabilities

class OllamaAgent:
    def __init__(self, page):
        self.page = page
        self.history = []

    async def get_screenshot_base64(self):
        """Capture screenshot and convert to base64 for Ollama"""
        screenshot_bytes = await self.page.screenshot(type="jpeg", quality=50)
        return base64.b64encode(screenshot_bytes).decode('utf-8')

    async def get_interactive_elements(self):
        """Get a list of simplified elements"""
        return await self.page.evaluate("""
            (() => {
                const elements = document.querySelectorAll('button, a, input, select, textarea, [role="button"]');
                return Array.from(elements).map((el, index) => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0 || window.getComputedStyle(el).visibility === 'hidden') return null;
                    return {
                        index: index,
                        tag: el.tagName.toLowerCase(),
                        text: (el.innerText || el.value || el.placeholder || '').slice(0, 50).replace(/\\n/g, ' '),
                        id: el.id,
                        class: el.className,
                        func_selector: `element_${index}`
                    };
                }).filter(el => el !== null);
            })()
        """)

    async def ask_ollama(self, task_description, screenshot_b64, elements_summary):
        """Send visual + text context to Ollama"""
        
        elements_text = "\n".join([f"{e['index']}: <{e['tag']} text='{e['text']}' id='{e['id']}'>" for e in elements_summary[:60]])
        
        prompt = f"""
        You are an autonomous web browsing agent.
        USER TASK: "{task_description}"
        
        You are looking at a screenshot of the browser.
        Here is a list of visible interactive elements (Index: <Tag Text ID>):
        {elements_text}
        
        Based on the current state and the goal, what is the SINGLE next action?
        Return ONLY valid JSON in this format (no markdown):
        {{
            "thought": "Reasoning...",
            "action": "click" | "type" | "goto" | "finish",
            "target_index": <index> (for click/type),
            "value": "<text>" (for type)
        }}
        
        If the task is complete, return action "finish".
        If you need to login, default email: account.test.1@mynes.com, password: StrongPass123!@#
        """
        
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [screenshot_b64]
                }
            ],
            "stream": False,
            "format": "json" # Force JSON mode if supported by model
        }
        
        try:
            print(f"   Thinking with {OLLAMA_MODEL}...")
            response = requests.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            
            result_json = response.json()
            content = result_json.get("message", {}).get("content", "")
            
            # Clean content if needed
            content = content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            
            return json.loads(content)
        
        except Exception as e:
            print(f"❌ Ollama Error: {e}")
            return {"action": "wait", "thought": f"Error calling Ollama: {e}"}

    async def execute_action(self, decision, elements_map):
        """Execute the JSON instruction from AI"""
        print(f"🤖 Thought: {decision.get('thought')}")
        action = decision.get("action")
        
        if action == "finish":
            return True
            
        elif action == "click":
            idx = decision.get("target_index")
            if idx is not None and idx < len(elements_map):
                el_data = elements_map[idx]
                print(f"   👉 Clicking element {idx}: {el_data['tag']} '{el_data['text']}'")
                try:
                    await self.page.evaluate(f"""
                        const all = document.querySelectorAll('button, a, input, select, textarea, [role="button"]');
                        const el = Array.from(all).filter(el => el.getBoundingClientRect().width > 0)[{idx}];
                        if(el) el.click();
                    """)
                except:
                    print("   ⚠️ Click failed")
                    
        elif action == "type":
            idx = decision.get("target_index")
            val = decision.get("value")
            if idx is not None:
                print(f"   👉 Typing '{val}' into element {idx}")
                await self.page.evaluate(f"""
                        const all = document.querySelectorAll('button, a, input, select, textarea, [role="button"]');
                        const el = Array.from(all).filter(el => el.getBoundingClientRect().width > 0)[{idx}];
                        if(el) {{ el.value = '{val}'; el.dispatchEvent(new Event('input')); }}
                    """)
        
        elif action == "goto":
             url = decision.get("value")
             if url: await self.page.goto(url)

        elif action == "wait":
             print("   ⏳ Waiting...")
             await asyncio.sleep(5)

        await self.page.wait_for_load_state("networkidle")
        await self.page.wait_for_timeout(2000)
        return False

    async def run_task(self, start_url, task_objective):
        if start_url == "__PRESTASHOP__":
            await self.page.goto("http://127.0.0.1:8080")
        else:
            await self.page.goto(start_url)
            
        for i in range(10): # Max 10 steps
            print(f"\n--- Step {i+1} ---")
            
            screenshot = await self.get_screenshot_base64()
            elements = await self.get_interactive_elements()
            
            decision = await self.ask_ollama(task_objective, screenshot, elements)
            
            done = await self.execute_action(decision, elements)
            if done:
                print("✅ Agent confirmed task completion.")
                break

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        agent = OllamaAgent(page)
        
        # Example Task
        task = "Search for 'T-Shirt' and add the first result to cart."
        print(f"Task: {task}")
        await agent.run_task("__PRESTASHOP__", task)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
