import asyncio
import os
import json
import base64
import time
from playwright.async_api import async_playwright
import google.generativeai as genai
from dotenv import load_dotenv

# Load API Key from .env file
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("⚠️  WARNING: GEMINI_API_KEY not found in .env file.")
    print("Please create a .env file and add: GEMINI_API_KEY=your_key_here")

# Configure Gemini
try:
    genai.configure(api_key=API_KEY)
except:
    pass # Handle later if key is missing

class GeminiAgent:
    def __init__(self, page):
        self.page = page
        self.history = []
        # Use Gemini 1.5 Flash or Pro (Vision capable)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    async def get_screenshot_base64(self):
        """Capture screenshot and convert to base64 for Gemini"""
        screenshot_bytes = await self.page.screenshot(type="jpeg", quality=50)
        return screenshot_bytes

    async def get_interactive_elements(self):
        """Get a list of simplified elements to help the AI map DOM to visual"""
        # This gives the AI 'coordinates' or 'labels' to reason better than just pixels
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

    async def ask_gemini(self, task_description, screenshot_bytes, elements_summary):
        """Send visual + text context to Gemini"""
        
        # Helper to format elements for prompt
        elements_text = "\n".join([f"{e['index']}: <{e['tag']} text='{e['text']}' id='{e['id']}'>" for e in elements_summary[:60]])
        
        prompt = f"""
        You are an autonomous web browsing agent.
        USER TASK: "{task_description}"
        
        You are looking at a screenshot of the browser.
        Here is a list of visible interactive elements (Index: <Tag Text ID>):
        {elements_text}
        ... (list truncated if too long)
        
        Based on the current state and the goal, what is the SINGLE next action?
        Return ONLY valid JSON in this format (no markdown):
        {{
            "thought": "Reasoning why...",
            "action": "click" | "type" | "goto" | "finish",
            "target_index": <index from list> (required for click/type),
            "value": "<text to type>" (only for type action)
        }}
        
        If the task is complete, return action "finish".
        If you need to login, default email: account.test.1@mynes.com, password: StrongPass123!@#
        """
        
        try:
            # Prepare content parts: Text + Image
            response = self.model.generate_content([
                {'mime_type': 'image/jpeg', 'data': screenshot_bytes},
                prompt
            ])
            
            # Clean response
            text = response.text.strip()
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "")
            
            return json.loads(text)
        
        except Exception as e:
            print(f"❌ Gemini Error: {e}")
            return {"action": "wait", "thought": "Error calling AI"}

    async def execute_action(self, decision, elements_map):
        """Execute the JSON instruction from AI"""
        print(f"🤖 Thought: {decision.get('thought')}")
        action = decision.get("action")
        
        if action == "finish":
            return True
            
        elif action == "click":
            idx = decision.get("target_index")
            if idx is not None and idx < len(elements_map):
                # We fetch the fresh element by re-querying or assume stability. 
                # Better: Use robust selectors. For demo, we try to construct a unique selector.
                el_data = elements_map[idx]
                print(f"   👉 Clicking element {idx}: {el_data['tag']} '{el_data['text']}'")
                
                # Construct a selector
                selector = el_data['tag']
                if el_data['id']: selector += f"#{el_data['id']}"
                elif el_data['class']: selector += f".{el_data['class'].split()[0]}"
                
                # Try clicking
                try:
                    # Specific Playwright logic: re-find by text/role to be safe
                    # Or use nth match if we trust the order
                    await self.page.locator(f":nth-match({el_data['tag']}, {idx+1})").click(timeout=3000)
                    # Note: nth-match in CSS is not exactly array index. 
                    # For simplicity in this scaffold, let's use a very generic robust click if possible
                    # or just evaluate js click
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
        
        elif action == "wait":
             print("   ⏳ Waiting (likely due to error/rate limit)...")
             await asyncio.sleep(10)

        elif action == "goto":
             url = decision.get("value")
             if url: await self.page.goto(url)

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
            
            # 1. Observe
            screenshot = await self.get_screenshot_base64()
            elements = await self.get_interactive_elements()
            
            # 2. Think
            decision = await self.ask_gemini(task_objective, screenshot, elements)
            
            # 3. Act
            done = await self.execute_action(decision, elements)
            if done:
                print("✅ Agent confirmed task completion.")
                break

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        agent = GeminiAgent(page)
        
        # Example Task: Search for 'T-Shirt'
        task = "Search for 'T-Shirt' and add the first result to cart."
        await agent.run_task("__PRESTASHOP__", task)
        
        await browser.close()

if __name__ == "__main__":
    if not API_KEY:
        print("❌ Cannot run without API KEY. Please set GEMINI_API_KEY in .env")
    else:
        asyncio.run(main())
