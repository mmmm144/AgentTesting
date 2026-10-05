import json

json_path_short = "prestashop_tasks_ps_01-20.json"
# Try the full path if relative fails, but we usually run from root
json_path = "/Users/ai/Documents/HCMUS/Nam3/Ki1/NMCNPM/bonus/prestashop_tasks_ps_01-20.json"

try:
    with open(json_path, 'r') as f:
        tasks = json.load(f)
except FileNotFoundError:
    print(f"File not found: {json_path}")
    exit(1)

# Status mapping based on previous execution
status_map = {
    "ps_01": "PASS", "ps_02": "PASS", "ps_03": "PASS", "ps_04": "PASS", "ps_05": "PASS",
    "ps_06": "PASS", "ps_07": "PASS", "ps_08": "PASS",
    "ps_09": "FAIL", "ps_10": "FAIL", 
    "ps_11": "PASS",
    "ps_12": "FAIL", "ps_13": "FAIL", "ps_14": "FAIL", "ps_15": "FAIL",
    "ps_16": "PASS",
    "ps_17": "FAIL", "ps_18": "FAIL", "ps_19": "FAIL",
    "ps_20": "PASS"
}

latex_content = r"""\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{longtable}
\usepackage{geometry}
\usepackage{xcolor}
\usepackage{amssymb}
\usepackage{array}
\usepackage{pdflscape} % For landscape

\geometry{a4paper, margin=0.5in}

\begin{document}

\begin{landscape}
\section*{PrestaShop Agent Test Cases \& Results (Comprehensive)}

\begin{longtable}{|l|p{3cm}|l|l|l|l|l|l|p{4cm}|l|}
\hline
\textbf{ID} & \textbf{Desc} & \textbf{Type} & \textbf{URL} & \textbf{Login} & \textbf{Steps} & \textbf{StrMatch} & \textbf{URLMatch} & \textbf{DomMatch} & \textbf{Status} \\
\hline
\endhead
"""

for task in tasks:
    tid = task['task_id']
    status = status_map.get(tid, "UNKNOWN")
    if "PASS" in status:
        status_tex = r"\textcolor{green}{\checkmark} PASS"
    else:
        status_tex = r"\textcolor{red}{\texttimes} FAIL"
        
    # Map JSON to Excel Columns
    # Headers: task_id, task_desc, task_type, start_url, require_login, steps, string_match, url_match, dom_match, Comments
    
    # 1. task_id
    tid_tex = tid.replace('_', r'\_')
    
    # 2. task_desc
    task_desc = task.get('task_description', '').replace('_', r'\_').replace('%', r'\%')
    
    # 3. task_type
    task_type = task.get('task_type', '').replace('_', r'\_')
    
    # 4. start_url
    start_url = task.get('start_url', '').replace('_', r'\_')
    
    # 5. require_login
    req_login = str(task.get('require_login', '')).replace('_', r'\_')
    
    # 6. steps (Not in JSON, leave empty or infer)
    steps = ""
    
    # 7. string_match (Not used in these tasks primarily, usually empty)
    string_match = ""
    if 'eval' in task and 'string_match' in task['eval']:
         string_match = str(task['eval']['string_match'])
    
    # 8. url_match
    url_match = ""
    if 'eval' in task and 'url_match' in task['eval']:
         url_match = str(task['eval']['url_match'])
    
    # 9. dom_match
    dom_match_str = ""
    if 'eval' in task and 'dom_match' in task['eval']:
        # Format dom_match nicely as key-value pairs
        dm = task['eval']['dom_match']
        dom_match_str = f"Extractor: {dm.get('dom_extractor', '')}, Match: {dm.get('match_value', '')}"
    dom_match_str = dom_match_str.replace('_', r'\_').replace('%', r'\%').replace('$', r'\$').replace('<', r'\textless{}').replace('>', r'\textgreater{}')

    # 10. Comments (Use Status here)
    comments = status_tex
    
    # Row - Note: We might need to adjust column widths in the header
    latex_content += f"{tid_tex} & {task_desc} & {task_type} & {start_url} & {req_login} & {steps} & {string_match} & {url_match} & {dom_match_str} & {comments} \\\\\n\\hline\n"

latex_content += r"""\end{longtable}
\end{landscape}
\end{document}
"""

output_path = "/Users/ai/Documents/HCMUS/Nam3/Ki1/NMCNPM/bonus/WebAppEval/TEST_CASES.tex"
with open(output_path, "w") as f:
    f.write(latex_content)

print(f"Generated {output_path}")
