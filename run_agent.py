import asyncio
import json
import time
from playwright.async_api import async_playwright
from evaluate.evaluator import Evaluator

# --- Cấu hình ---
TASKS_FILE = "dataset/prestashop_tasks.json"
ENV_URL = "http://127.0.0.1:8080"
# Danh sách tasks chạy từ ps_01 đến ps_20
TARGET_TASKS = [f"ps_{i:02d}" for i in range(1, 21)]

async def run_agent():
    # 1. Load đề bài (Tasks)
    print(f"Loading tasks from {TASKS_FILE}...")
    with open(TASKS_FILE, 'r') as f:
        all_tasks = json.load(f)
    
    # Lọc ra tasks cần chạy
    tasks_to_run = [t for t in all_tasks if t['task_id'] in TARGET_TASKS]
    
    # 2. Khởi tạo Evaluator
    evaluator = Evaluator(all_tasks)

    async with async_playwright() as p:
        # Mở trình duyệt
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("\n--- BẮT ĐẦU CHẠY AUTO AGENT ---\n")
        
        created_email = "account.test.1@mynes.com"

        for task in tasks_to_run:
            task_id = task['task_id']
            description = task['task_description']
            print(f"🔹 Đang làm Task [{task_id}]: {description}")

            # --- PHẦN 1: AGENT THỰC HIỆN (HÀNH ĐỘNG) ---
            if task['start_url'] == "__PRESTASHOP__":
                await page.goto(ENV_URL)
            
            try:
                if task_id == "ps_01": # Subscribe email
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    email = f"account.test.{int(time.time())}@mynes.com"
                    await page.locator("input[name='email']").fill(email)
                    await page.locator("input[value='Subscribe'], button[name='submitNewsletter']").click()
                    await page.wait_for_timeout(2000)

                elif task_id == "ps_02": # Search product
                    await page.locator("input[name='s']").fill("The Best Is Yet To Come")
                    await page.locator("input[name='s']").press("Enter")
                    await page.wait_for_timeout(2000)

                elif task_id == "ps_03": # Add to cart
                    await page.locator(".product-miniature").first.click()
                    await page.wait_for_load_state("networkidle")
                    await page.locator(".add-to-cart").click()
                    await page.wait_for_selector(".blockcart-modal", state="visible")
                    await page.wait_for_timeout(1000)

                elif task_id == "ps_04": # Verify cart count
                    if await page.locator(".blockcart-modal").is_visible():
                         await page.locator(".blockcart-modal .close").click()
                    await page.reload()
                    await page.wait_for_timeout(2000)

                elif task_id == "ps_05": # Checkout guest
                    await page.locator("#_desktop_cart a").click()
                    await page.wait_for_timeout(1000)
                    await page.get_by_text("Proceed to checkout").click()
                    await page.wait_for_timeout(2000)

                elif task_id == "ps_06": # Create account
                    await page.locator("#_desktop_user_info a").click()
                    await page.locator(".no-account > a").click()
                    await page.locator("label:has-text('Mr.')").click()
                    await page.locator("input[name='firstname']").fill("New")
                    await page.locator("input[name='lastname']").fill("User")
                    
                    email = f"new.user.{int(time.time())}@mynes.com"
                    print(f"   Creating account with email: {email}")
                    created_email = email
                    
                    await page.locator("#content input[name='email'], #main input[name='email']").first.fill(email)
                    strong_pass = "StrongPass123!@#"
                    await page.locator("#content input[name='password'], #main input[name='password']").first.fill(strong_pass)
                    await page.locator("input[name='birthday']").fill("1990-01-01")
                    
                    if await page.locator("input[name='customer_privacy']").is_visible():
                        await page.locator("input[name='customer_privacy']").check()
                    if await page.locator("input[name='psgdpr']").is_visible():
                         await page.locator("input[name='psgdpr']").check()

                    await page.locator("button[data-link-action='save-customer']").click()
                    await page.wait_for_timeout(2000)

                elif task_id == "ps_07": # Login
                    if await page.locator(".logout").is_visible():
                        await page.locator(".logout").click()
                    
                    await page.locator("#_desktop_user_info a").click()
                    await page.locator("#content input[name='email'], #main input[name='email']").first.fill(created_email)
                    
                    password = "StrongPass123!@#" if "new.user" in created_email else "ThisIsAMyShopPassword123!"
                    await page.locator("#content input[name='password'], #main input[name='password']").first.fill(password)
                    await page.locator("#submit-login").click()
                    await page.wait_for_timeout(2000)

                elif task_id == "ps_08": # Contact us
                    await page.locator("#contact-link a").click()
                    await page.locator("select[name='id_contact']").select_option(index=1)
                    await page.locator("input[name='from']").fill("contact.test@mynes.com")
                    await page.locator("textarea[name='message']").fill("This is a test message.")
                    if await page.locator("input[name='psgdpr']").is_visible():
                        await page.locator("input[name='psgdpr']").check()
                        
                    await page.locator("input[name='submitMessage']").click()
                    await page.wait_for_timeout(2000)

                elif task_id == "ps_09": # Currency
                    if await page.locator("#_desktop_currency_selector").count() > 0:
                        await page.locator(".currency-selector button, .currency-selector .expand-more").first.click(force=True)
                        await page.wait_for_timeout(500)
                        if await page.locator("a:has-text('EUR')").count() > 0:
                             await page.locator("a:has-text('EUR')").first.click(force=True)
                        elif await page.locator("a[title='Euro']").count() > 0:
                             await page.locator("a[title='Euro']").first.click(force=True)
                    await page.wait_for_timeout(3000)

                elif task_id == "ps_10": # Filter Size M
                    await page.locator("#category-3 > a").click()
                    await page.wait_for_timeout(1000)
                    try:
                        await page.wait_for_selector("#left-column, #search_filters", timeout=5000)
                    except:
                        pass
                    await page.locator("#left-column label:has-text('M'), #search_filters label:has-text('M')").first.click(force=True)
                    await page.wait_for_timeout(3000)

                elif task_id == "ps_11": # Sort by Price
                    await page.locator("#category-3 > a").click()
                    await page.wait_for_timeout(1000)
                    await page.locator(".sort-by-row .select-title, .products-sort-order .select-title").click()
                    await page.locator("a.select-list:has-text('Price, low to high'), .select-list:has-text('Price, low to high')").click()
                    await page.wait_for_timeout(2000)

                elif task_id == "ps_12": # Wishlist
                    if await page.locator(".login").is_visible():
                         await page.locator(".login").click()
                         email_to_use = created_email if "new.user" in created_email else "account.test.1@mynes.com"
                         if await page.locator("form#login-form").is_visible():
                              await page.locator("form#login-form input[name='email']").fill(email_to_use)
                              pwd = "StrongPass123!@#" if "new.user" in email_to_use else "ThisIsAMyShopPassword123!"
                              await page.locator("form#login-form input[name='password']").fill(pwd)
                              await page.locator("#submit-login").click()
                              await page.wait_for_timeout(1000)
                    
                    await page.goto(ENV_URL)
                    await page.wait_for_load_state("networkidle")
                    await page.locator(".product-miniature").first.click()
                    await page.wait_for_timeout(1000)
                    await page.locator(".wishlist-button-add").click()
                    await page.wait_for_timeout(2000)
                    await page.goto(f"{ENV_URL}/module/blockwishlist/lists")
                    await page.wait_for_timeout(2000)

                elif task_id == "ps_13": # Compare
                    await page.locator("#category-3 > a").click()
                    await page.wait_for_timeout(1000)
                    products = page.locator(".product-miniature")
                    await products.nth(0).hover()
                    await products.nth(0).locator(".add-to-compare").click(force=True)
                    await page.wait_for_timeout(500)
                    await products.nth(1).hover()
                    await products.nth(1).locator(".add-to-compare").click(force=True)
                    await page.wait_for_timeout(500)
                    
                    if await page.locator(".js-compare-button, .compare-button").is_visible():
                         await page.locator(".js-compare-button, .compare-button").first.click()
                    else:
                         await page.goto(f"{ENV_URL}/products-comparison")
                    await page.wait_for_timeout(2000)

                elif task_id == "ps_14": # Review
                    if await page.locator(".login").is_visible():
                         await page.locator(".login").click()
                         email_to_use = created_email if "new.user" in created_email else "account.test.1@mynes.com"
                         if await page.locator("form#login-form").is_visible():
                              await page.locator("form#login-form input[name='email']").fill(email_to_use)
                              pwd = "StrongPass123!@#" if "new.user" in email_to_use else "ThisIsAMyShopPassword123!"
                              await page.locator("form#login-form input[name='password']").fill(pwd)
                              await page.locator("#submit-login").click()
                    
                    await page.goto(ENV_URL)
                    await page.locator(".product-miniature").first.click()
                    await page.wait_for_load_state("networkidle")
                    await page.locator(".post-product-comment").first.click()
                    await page.wait_for_timeout(1000)
                    await page.locator("input[name='comment_title']").fill("Great product")
                    await page.locator("textarea[name='comment_content']").fill("I really liked this product. It is amazing.")
                    await page.locator("button[type='submit']:has-text('Send'), button.btn-comment-big").click()
                    await page.wait_for_timeout(2000)

                elif task_id == "ps_15": # Coupon
                    await page.goto(ENV_URL)
                    await page.wait_for_load_state("networkidle")
                    await page.locator(".product-miniature").first.click()
                    await page.wait_for_timeout(1000)
                    await page.locator(".add-to-cart").click()
                    await page.wait_for_selector(".blockcart-modal", state="visible")
                    await page.locator(".blockcart-modal a.btn-primary, .blockcart-modal a:has-text('Proceed to checkout')").click()
                    await page.wait_for_timeout(1000)
                    if await page.locator(".promo-code-button").is_visible():
                        await page.locator(".promo-code-button").click()
                        await page.wait_for_timeout(500)
                    await page.locator("input[name='discount_name']").fill("DISCOUNT")
                    await page.locator("form.display-promo .btn-primary, button[action='add-discount']").click()
                    await page.wait_for_timeout(2000)

                elif task_id == "ps_16": # Navigate to Category
                    await page.locator("#category-3 > a").click()
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(2000)

                elif task_id == "ps_17": # Change Language
                    if await page.locator("#_desktop_language_selector").count() > 0:
                        await page.locator("#_desktop_language_selector button, #_desktop_language_selector .expand-more").first.click()
                        await page.wait_for_timeout(500)
                        await page.locator("#_desktop_language_selector .dropdown-item").last.click()
                        await page.wait_for_timeout(2000)

                elif task_id == "ps_18": # Support / Terms
                    await page.locator("#contact-link a").first.click()
                    await page.wait_for_timeout(2000)

                elif task_id == "ps_19": # Product Gallery / Zoom
                    await page.goto(ENV_URL)
                    await page.locator(".product-miniature").first.click()
                    await page.wait_for_load_state("networkidle")
                    await page.locator(".js-qv-product-cover, .product-cover img").first.click(force=True)
                    await page.wait_for_selector(".modal.show, .product-images-modal", state="visible")
                    await page.wait_for_timeout(2000)

                elif task_id == "ps_20": # Logout
                    if await page.locator(".logout, a[href*='?mylogout=']").first.is_visible():
                        await page.locator(".logout, a[href*='?mylogout=']").first.click()
                    else:
                        print("   [DEBUG] Not logged in, logging in to test logout...")
                        await page.locator("#_desktop_user_info a").click()
                        if await page.locator("form#login-form").is_visible():
                             email_to_use = created_email if "new.user" in created_email else "account.test.1@mynes.com"
                             await page.locator("form#login-form input[name='email']").fill(email_to_use)
                             pwd = "StrongPass123!@#" if "new.user" in email_to_use else "ThisIsAMyShopPassword123!"
                             await page.locator("form#login-form input[name='password']").fill(pwd)
                             await page.locator("#submit-login").click()
                             await page.wait_for_timeout(1000)
                        await page.locator(".logout, a[href*='?mylogout=']").first.click()
                    await page.wait_for_timeout(2000)

            except Exception as e:
                print(f"❌ Error in task {task_id}: {e}")
                continue 
            
            # --- PHẦN 2: WEBAPPEVAL CHẤM ĐIỂM (EVALUATION) ---
            print(f"   👉 Evaluating...")
            is_success = await evaluator.evaluate_with_playwright(task_id, browser=page)
            
            if is_success:
                print(f"   ✅ PASS\n")
            else:
                print(f"   ❌ FAIL\n")
            
            time.sleep(1)

        await browser.close()
        print("--- COMPLETE ---\n")

if __name__ == "__main__":
    asyncio.run(run_agent())
