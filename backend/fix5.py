with open(r'C:\Users\Lenovo\Desktop\FAST_API\expense-tracker\backend\app\routers\agents.py', 'r') as f:
    c = f.read()

import re
c = re.sub(r'current_date_str = [^\n]*?formatted_prompt = [^\n]*?messages = \[.*?\]', '''current_date_str = datetime.now().strftime("%B %d, %Y")
    formatted_prompt = SYSTEM_PROMPT.replace("{current_date}", current_date_str)
    messages = [{"role": "system", "content": formatted_prompt}]''', c, flags=re.DOTALL)

with open(r'C:\Users\Lenovo\Desktop\FAST_API\expense-tracker\backend\app\routers\agents.py', 'w') as f:
    f.write(c)
