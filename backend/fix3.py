with open(r'C:\Users\Lenovo\Desktop\FAST_API\expense-tracker\backend\app\routers\agents.py', 'r') as f:
    c = f.read()

bad_str = 'current_date_str = datetime.now().strftime("%B %d, %Y")
    formatted_prompt = SYSTEM_PROMPT.replace("{current_date}", current_date_str)
    messages = [{"role": "system", "content": formatted_prompt}]'
good_str = '''current_date_str = datetime.now().strftime("%B %d, %Y")
    formatted_prompt = SYSTEM_PROMPT.replace("{current_date}", current_date_str)
    messages = [{"role": "system", "content": formatted_prompt}]'''

c = c.replace(bad_str, good_str)

with open(r'C:\Users\Lenovo\Desktop\FAST_API\expense-tracker\backend\app\routers\agents.py', 'w') as f:
    f.write(c)
