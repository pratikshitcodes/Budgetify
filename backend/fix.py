import sys
import re

path = r'C:\Users\Lenovo\Desktop\FAST_API\expense-tracker\backend\app\routers\agents.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# First, let's normalize all the elifs. I'll just find the massive if/elif block and replace it manually for both functions.
# Instead of regex, let's just do simple replacements.

# Let's fix the datetime issue
if 'from datetime import datetime' not in content:
    content = 'from datetime import datetime\n' + content

# Fix the messy prompt injection
prompt_mess = '''current_date_str = datetime.now().strftime("%B %d, %Y")
    formatted_prompt = SYSTEM_PROMPT.replace("{current_date}", current_date_str)
    messages = [{"role": "system", "content": formatted_prompt}]'''

good_prompt = '''current_date_str = datetime.now().strftime("%B %d, %Y")
    formatted_prompt = SYSTEM_PROMPT.replace("{current_date}", current_date_str)
    messages = [{"role": "system", "content": formatted_prompt}]'''

content = content.replace(prompt_mess, good_prompt)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
