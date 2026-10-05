# Agent Architecture Analysis: Rule-based vs. Generative vs. SeeAct

This document compares the different approaches to web automation used in this project and contrasts them with state-of-the-art research like **SeeAct**.

## 1. Rule-Based Automation (`run_agent.py`)

*   **Type**: Scripted Automation (Classic).
*   **Mechanism**: explicitly programmed steps (e.g., `page.click('#submit-button')`).
*   **Pros**:
    *   100% Deterministic (if the site doesn't change).
    *   Extremely fast execution.
    *   Low cost (no API calls).
*   **Cons**:
    *   **Brittle**: Breaks if a CSS selector changes (e.g., class name changes from `.btn-primary` to `.btn-blue`).
    *   **Not "Intelligent"**: Cannot handle unseen scenarios or popups it wasn't coded for.
*   **Verdict**: This is **NOT** a cognitive agent. It is an automation script.

## 2. Our AI Agent (`ai_agent_gemini.py`)

*   **Type**: Multimodal Web Agent (VLM - Visual Language Model).
*   **Mechanism**:
    1.  **Observe**: Captures a screenshot + extracts DOM elements text.
    2.  **Think**: Sends image + text list to Gemini (VLM).
    3.  **Act**: Gemini returns a JSON decision (`{"action": "click", "target_index": 5}`).
*   **Architecture**:
    *   Uses a **ReAct** (Reason + Act) loop.
    *   Relies on the Model's internal world knowledge to navigate.
*   **Pros**:
    *   **Generalizable**: Can navigate a site it has never seen before (if the task is clear).
    *   **Resilient**: Doesn't rely on specific CSS classes, relies on visual semantics (e.g., "Click the cart icon").
*   **Cons**:
    *   **Slow**: API calls take 2-5 seconds.
    *   **Costly/limited**: API rate limits.
    *   **Hallucinations**: Might try to click something that isn't clickable.

## 3. Comparison with SeeAct (State-of-the-Art)

**SeeAct** (Generic Generalist Web Agent) is a specific research implementation of a VLM agent (like our `ai_agent_gemini.py`), but with key enhancements:

| Feature | Our `ai_agent_gemini.py` | SeeAct (Research Paper) | Antigravity (You - Rule Based) |
| :--- | :--- | :--- | :--- |
| **Vision Mechanism** | Sends raw screenshot. | Sends screenshot **with Overlay**. | N/A (DOM Selectors) |
| **Grounding (定位)** | **Text-Grounding**: We send a list of element text/IDs separately. | **Visual-Grounding (Set-of-Marks)**: Overlays numeric/text labels *directly on the image* so the AI "sees" the IDs. | Exact CSS/XPath Selectors |
| **Prompt Engineering** | Basic ReAct prompt. | Sophisticated prompting with few-shot examples and self-reflection. | Hardcoded Logic |
| **Action Space** | Click, Type, Goto. | Comprehensive (Hover, Select, Key combinations). | Exact Playwright API |

### Performance Comparison (Hypothetical)
*   **Antigravity (Rule-based)**: 12/20 (60%). High reliability on static elements, fails on missing environment features.
*   **SeeAct (GPT-4V)**: Likely ~70-80% on this dataset (based on paper benchmarks on similar tasks). It handles dynamic changes better but is slower.

## 4. How to Evaluate SeeAct using this Framework

The `WebAppEval` framework designed here is **Agent-Agnostic**. To evaluate official SeeAct code:

1.  **Clone SeeAct**: Get the SeeAct repository.
2.  **Bridge the Driver**:
    *   SeeAct uses Selenium/Playwright.
    *   Pass the active SeeAct `browser` instance to our `evaluator.evaluate_with_playwright(task_id, browser=page)`.
3.  **Run Loop**:
    ```python
    # Pseudo-code for running SeeAct on this benchmark
    from webappeval.evaluator import Evaluator
    import seeact

    tasks = json.load(open("dataset/prestashop_tasks.json"))
    evaluator = Evaluator(tasks)

    for task in tasks:
        # 1. Ask SeeAct to solve it
        seeact_agent.act(url=task['start_url'], goal=task['task_description'])
        
        # 2. Score it using our Evaluator
        is_success = evaluator.evaluate_with_playwright(task['task_id'], browser=seeact_agent.browser)
        print(f"Task {task['task_id']}: {'PASS' if is_success else 'FAIL'}")
    ```

## Conclusion

The `ai_agent_gemini.py` provided in this project is a **simplified implementation of the SeeAct architecture**. To upgrade it to a full "SeeAct" implementation, we would need to:
1.  Draw bounding boxes and ID numbers directly onto the screenshot before sending it to Gemini (Set-of-Marks).
2.  Implement a more complex planning history.
