from datetime import datetime
from groq import Groq
import os
import json
from dotenv import load_dotenv
from ..prompts import SYSTEM_PROMPT
from ..services import expense_service, analytics_service

load_dotenv()

my_api_key = os.getenv("GROQ_API_KEY")

if not my_api_key:
    raise ValueError("API key kithe ha veere")

client = Groq(api_key=my_api_key)
model = "openai/gpt-oss-120b"

def get_tools_definition():
    return [
        {
            "type": "function",
            "function": {
                "name": "get_expenses",
                "description": "Get expenses for a specific month and year",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "month": {"type": "integer"},
                        "year": {"type": "integer"}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_expenses",
                "description": "Search expenses by keyword, optionally filtered by month and year",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keyword": {"type": "string"},
                        "month": {"type": "integer"},
                        "year": {"type": "integer"}
                    },
                    "required": ["keyword"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "add_expense",
                "description": "Add a new expense",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "amount": {"type": "number"},
                        "description": {"type": "string"},
                        "category": {"type": "string"}
                    },
                    "required": ["title", "amount", "description", "category"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "update_expense",
                "description": "Update an existing expense by ID. ALWAYS use search_expenses first to find the ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "title": {"type": "string"},
                        "amount": {"type": "number"},
                        "description": {"type": "string"},
                        "category": {"type": "string"}
                    },
                    "required": ["id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "delete_expense",
                "description": "Delete an expense by ID",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"}
                    },
                    "required": ["id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_monthly_summary",
                "description": "Get basic financial summary for a month (total, budget, remaining)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "month": {"type": "integer"},
                        "year": {"type": "integer"}
                    },
                    "required": ["month", "year"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_detailed_analysis",
                "description": "Get a deep financial analysis for a month (projected spending, daily pace, safe daily limit, category breakdowns)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "month": {"type": "integer"},
                        "year": {"type": "integer"}
                    },
                    "required": ["month", "year"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_affordability",
                "description": "Check if a specific expense amount can be afforded based on the current remaining budget",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number"}
                    },
                    "required": ["amount"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "compare_months",
                "description": "Compare financial performance between two months",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "month1": {"type": "integer"},
                        "year1": {"type": "integer"},
                        "month2": {"type": "integer"},
                        "year2": {"type": "integer"}
                    },
                    "required": ["month1", "year1", "month2", "year2"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generate_monthly_report",
                "description": "Generate a downloadable monthly report",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "month": {"type": "integer"},
                        "year": {"type": "integer"}
                    },
                    "required": ["month", "year"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generate_comparison_report",
                "description": "Generate a downloadable comparison report between two months",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "month1": {"type": "integer"},
                        "year1": {"type": "integer"},
                        "month2": {"type": "integer"},
                        "year2": {"type": "integer"}
                    },
                    "required": ["month1", "year1", "month2", "year2"]
                }
            }
        }
    ]

def run_agent(question: str, history: list, db, current_user):
    current_date_str = datetime.now().strftime("%B %d, %Y")
    formatted_prompt = SYSTEM_PROMPT.replace("{current_date}", current_date_str)
    messages = [{"role": "system", "content": formatted_prompt}]
    
    # Add history
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})
        
    messages.append({"role": "user", "content": question})
    
    # Meta tracking for reports
    report_meta = None
    comparison_meta = None
    
    for step in range(5):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=get_tools_definition(),
            tool_choice="auto",
            temperature=0
        )
        
        response_message = response.choices[0].message
        messages.append(response_message)
        
        if not response_message.tool_calls:
            # Done
            return {
                "reply": response_message.content,
                "report": report_meta,
                "comparison": comparison_meta
            }
            
        for tool_call in response_message.tool_calls:
            tool_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            result = None
            
            try:
                if tool_name == "get_expenses":
                    res = expense_service.get_expense(db, current_user, args.get("month"), args.get("year"))
                    result = [{"id": e.id, "title": e.title, "amount": float(e.amount), "category": e.category, "date": str(e.created_at)} for e in res]
                
                elif tool_name == "search_expenses":
                    res = expense_service.search_expenses(args.get("keyword"), db, current_user, args.get("month"), args.get("year"))
                    result = [{"id": e.id, "title": e.title, "amount": float(e.amount), "category": e.category, "date": str(e.created_at)} for e in res]
                
                elif tool_name == "add_expense":
                    res = expense_service.add_expense(args, db, current_user)
                    result = {"id": res.id, "title": res.title, "amount": float(res.amount), "category": res.category}
                    
                elif tool_name == "update_expense":
                    updated = {}
                    if "title" in args: updated["title"] = args["title"]
                    if "amount" in args: updated["amount"] = args["amount"]
                    if "description" in args: updated["description"] = args["description"]
                    if "category" in args: updated["category"] = args["category"]
                    res = expense_service.update_expense(args["id"], updated, db, current_user)
                    result = {"id": res.id, "title": res.title, "amount": float(res.amount), "category": res.category}
                
                elif tool_name == "delete_expense":
                    expense_service.delete_expense(args["id"], db, current_user)
                    result = {"success": True, "message": f"Expense {args['id']} deleted"}
                    
                elif tool_name == "get_monthly_summary":
                    result = analytics_service.get_monthly_summary(db, current_user.id, args["month"], args["year"])

                elif tool_name == "get_detailed_analysis":
                    result = analytics_service.get_detailed_analysis(db, current_user.id, args["month"], args["year"])

                elif tool_name == "compare_months":
                    result = analytics_service.compare_months(db, current_user.id, args["month1"], args["year1"], args["month2"], args["year2"])
                    comparison_meta = result
                    
                elif tool_name == "generate_monthly_report":
                    m, y = args["month"], args["year"]
                    report_meta = {
                        "type": "monthly",
                        "month": m,
                        "year": y,
                        "pdf_url": f"/reports/monthly/{y}/{m}/pdf",
                        "csv_url": f"/reports/monthly/{y}/{m}/csv"
                    }
                    result = {"success": True, "message": "Report generated successfully"}
                    
                elif tool_name == "generate_comparison_report":
                    m1, y1, m2, y2 = args["month1"], args["year1"], args["month2"], args["year2"]
                    report_meta = {
                        "type": "comparison",
                        "pdf_url": f"/reports/compare/pdf?month1={m1}&year1={y1}&month2={m2}&year2={y2}",
                        "csv_url": f"/reports/compare/csv?month1={m1}&year1={y1}&month2={m2}&year2={y2}"
                    }
                    result = {"success": True, "message": "Comparison report generated successfully"}
                    
                else:
                    result = {"error": "Tool not found"}
            except Exception as e:
                result = {"error": str(e)}
                
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_name,
                "content": json.dumps(result)
            })

    return {
        "reply": "I'm sorry, I couldn't complete the task in time.",
        "report": report_meta,
        "comparison": comparison_meta
    }


def run_agent_stream(question: str, history: list, db, current_user):
    """Generator that runs the tool-calling loop non-streamed, then streams
    the final text response token by token as Server-Sent Events (SSE)."""
    current_date_str = datetime.now().strftime("%B %d, %Y")
    formatted_prompt = SYSTEM_PROMPT.replace("{current_date}", current_date_str)
    messages = [{"role": "system", "content": formatted_prompt}]

    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": question})

    report_meta = None
    comparison_meta = None

    for step in range(5):
        # ── Non-streamed call for tool-calling rounds ──────────────────────
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=get_tools_definition(),
            tool_choice="auto",
            temperature=0
        )

        response_message = response.choices[0].message
        messages.append(response_message)

        if not response_message.tool_calls:
            # No more tool calls — stream the final answer
            # Re-call with stream=True so we get token-by-token output
            messages.pop()  # remove the non-streamed final message
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=get_tools_definition(),
                tool_choice="auto",   # allow tool calls if needed
                temperature=0,
                stream=True
            )

            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield f"data: {json.dumps({'type': 'token', 'content': delta.content})}\n\n"

            # After streaming text, emit report/comparison metadata
            if report_meta:
                yield f"data: {json.dumps({'type': 'report', 'content': report_meta})}\n\n"
            if comparison_meta:
                yield f"data: {json.dumps({'type': 'comparison', 'content': comparison_meta})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        # ── Execute tool calls ─────────────────────────────────────────────
        for tool_call in response_message.tool_calls:
            tool_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            result = None

            # Emit a "thinking" status so the UI can show progress
            yield f"data: {json.dumps({'type': 'status', 'content': f'Using tool: {tool_name}...'})}\n\n"

            try:
                if tool_name == "get_expenses":
                    res = expense_service.get_expense(db, current_user, args.get("month"), args.get("year"))
                    result = [{"id": e.id, "title": e.title, "amount": float(e.amount), "category": e.category, "date": str(e.created_at)} for e in res]

                elif tool_name == "search_expenses":
                    res = expense_service.search_expenses(args.get("keyword"), db, current_user, args.get("month"), args.get("year"))
                    result = [{"id": e.id, "title": e.title, "amount": float(e.amount), "category": e.category, "date": str(e.created_at)} for e in res]

                elif tool_name == "add_expense":
                    res = expense_service.add_expense(args, db, current_user)
                    result = {"id": res.id, "title": res.title, "amount": float(res.amount), "category": res.category}

                elif tool_name == "update_expense":
                    updated = {}
                    if "title" in args: updated["title"] = args["title"]
                    if "amount" in args: updated["amount"] = args["amount"]
                    if "description" in args: updated["description"] = args["description"]
                    if "category" in args: updated["category"] = args["category"]
                    res = expense_service.update_expense(args["id"], updated, db, current_user)
                    result = {"id": res.id, "title": res.title, "amount": float(res.amount), "category": res.category}

                elif tool_name == "delete_expense":
                    expense_service.delete_expense(args["id"], db, current_user)
                    result = {"success": True, "message": f"Expense {args['id']} deleted"}

                elif tool_name == "get_monthly_summary":
                    result = analytics_service.get_monthly_summary(db, current_user.id, args["month"], args["year"])

                elif tool_name == "get_detailed_analysis":
                    result = analytics_service.get_detailed_analysis(db, current_user.id, args["month"], args["year"])


                elif tool_name == "compare_months":
                    result = analytics_service.compare_months(db, current_user.id, args["month1"], args["year1"], args["month2"], args["year2"])
                    comparison_meta = result

                elif tool_name == "generate_monthly_report":
                    m, y = args["month"], args["year"]
                    report_meta = {
                        "type": "monthly",
                        "month": m,
                        "year": y,
                        "pdf_url": f"/reports/monthly/{y}/{m}/pdf",
                        "csv_url": f"/reports/monthly/{y}/{m}/csv"
                    }
                    result = {"success": True, "message": "Report generated successfully"}

                elif tool_name == "generate_comparison_report":
                    m1, y1, m2, y2 = args["month1"], args["year1"], args["month2"], args["year2"]
                    report_meta = {
                        "type": "comparison",
                        "pdf_url": f"/reports/compare/pdf?month1={m1}&year1={y1}&month2={m2}&year2={y2}",
                        "csv_url": f"/reports/compare/csv?month1={m1}&year1={y1}&month2={m2}&year2={y2}"
                    }
                    result = {"success": True, "message": "Comparison report generated successfully"}

                else:
                    result = {"error": "Tool not found"}

            except Exception as e:
                result = {"error": str(e)}

            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_name,
                "content": json.dumps(result)
            })

    # Fallback if max steps exceeded
    yield f"data: {json.dumps({'type': 'token', 'content': "I'm sorry, I couldn't complete the task in time."})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


