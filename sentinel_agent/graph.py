import subprocess
import os
import json
import chromadb
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END

# Prompts file se system instruction load karna
from prompts import SYSTEM_PROMPT 

load_dotenv()

# --- 1. CONFIGURATION & CLIENTS ---
# Groq Client initialize karna
client = Groq()

# ChromaDB Persistent Client (Memory/RAG ke liye)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = None

try:
    # Codebase memory collection fetch karna
    collection = chroma_client.get_collection(name="codebase")
except Exception as e:
    print(f"⚠️ Warning: Collection 'codebase' not found. Run indexer.py first! Error: {e}")

# --- 2. STATE DEFINITION (Common Memory for Agents) ---
class SentinelState(TypedDict):
    issue_type: str         # "CRASH" or "PERFORMANCE"
    file_path: str          # Jis file mein bug hai
    error_log: str          # Error details ya slowness details
    original_code: str      # Purana code
    proposed_fix: str       # Architect ka naya code
    feedback: str           # Reviewer ka feedback (retries ke liye)
    attempts: int           # Kitni baar try kiya
    audit_passed: bool      # Reviewer ne pass kiya ya nahi
    explanation: str        # AI ka explanation

# --- 3. HELPER UTILITIES ---

def get_related_context(query_text):
    """ChromaDB se milta-julta code dhoondna (RAG context)"""
    if collection is None: 
        return "No codebase memory available."
    try:
        print("🧠 Sentinel is searching codebase memory for context...")
        results = collection.query(query_texts=[query_text], n_results=2)
        context_str = ""
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            context_str += f"\n--- RELATED FILE: {meta['path']} ---\n{doc}\n"
        return context_str
    except Exception as e:
        print(f"⚠️ Context Retrieval Failed: {e}")
        return "Context retrieval failed."

def validate_syntax(file_path):
    """Node.js check command se syntax verify karna"""
    try:
        result = subprocess.run(["node", "--check", file_path], capture_output=True, text=True)
        return result.returncode == 0, result.stderr
    except Exception as e: 
        return False, str(e)

def log_fix_to_history(file_path, issue, original_code, corrected_code, mode):
    """Dashboard ke liye JSON history update karna"""
    history_file = "../sentinel-dashboard/public/fixes_history.json"
    new_record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "file_fixed": file_path,
        "issue": issue[:200],
        "status": mode,
        "previous_code": original_code,
        "fixed_code": corrected_code
    }
    history_data = []
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            try:
                history_data = json.load(f)
            except: history_data = []
    
    history_data.append(new_record)
    with open(history_file, "w") as f:
        json.dump(history_data, f, indent=4)
    print(f"📄 Record saved to fixes_history.json as {mode}")

def log_mentor_message(message):
    """Dashboard mentor message update karna"""
    mentor_file = "../sentinel-dashboard/public/sentinel_mentor.txt"
    timestamp = datetime.now().strftime("%H:%M:%S")
    try:
        with open(mentor_file, "a") as f:
            f.write(f"[{timestamp}] 🤖 Sentinel: {message}\n")
    except Exception as e:
        print(f"⚠️ Mentor log failed: {e}")

# --- 4. AGENT NODES (Role-Based Logic) ---

def scout_node(state: SentinelState):
    """Agent A (Scout): Context aur original code gather karta hai"""
    print(f"\n🔭 [Agent: Scout] Analyzing {state['issue_type']} in {state['file_path']}...")
    
    if not os.path.exists(state['file_path']):
        return {"feedback": "File not found", "audit_passed": False}
        
    with open(state['file_path'], "r") as f:
        code = f.read()
    
    # RAG Se context nikalna
    context = get_related_context(state['error_log'])
    
    return {
        "original_code": code,
        "feedback": f"Codebase Context retrieved:\n{context}",
        "attempts": 0
    }

def architect_node(state: SentinelState):
    """Agent B (Architect): Fix ya Optimization code generate karta hai"""
    print(f"🏗️  [Agent: Architect] Generating solution (Attempt {state['attempts'] + 1})...")
    
    # Dynamic prompt creation
    prompt_type = "Bug Fix" if state['issue_type'] == "CRASH" else "Performance Optimization"
    
    prompt = f"""
    {SYSTEM_PROMPT}
    MODE: {prompt_type}
    ISSUE/LOGS: {state['error_log']}
    FILE PATH: {state['file_path']}
    CURRENT CODE:
    {state['original_code']}

    ADDITIONAL CONTEXT:
    {state['feedback']}
    
    TASK: Provide a complete and working version of the file.
    - If it's a crash, handle the error safely.
    - If it's performance, optimize loops/queries.
    - KEEP original logic intact.

    CRITICAL: 
    - Return ONLY the code inside [FIXED_CODE] and [/FIXED_CODE] tags.
    - Provide a short explanation inside [EXPLANATION] and [/EXPLANATION] tags.
    """
    
    if state['attempts'] > 0:
        prompt += f"\n\n🚨 PREVIOUS ATTEMPT FAILED. FEEDBACK: {state['feedback']}"

    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant"
        ).choices[0].message.content

        # Extraction Logic
        try:
            fix = response.split("[FIXED_CODE]")[1].split("[/FIXED_CODE]")[0].strip()
            # Clean Markdown if AI included it
            if "```" in fix:
                fix = fix.split("```")[1].replace("javascript", "").replace("js", "").strip()
            
            explanation = response.split("[EXPLANATION]")[1].split("[/EXPLANATION]")[0].strip()
        except:
            fix = response.strip()
            explanation = "Automated patch applied."

        return {
            "proposed_fix": fix, 
            "explanation": explanation, 
            "attempts": state['attempts'] + 1
        }
    except Exception as e:
        return {"feedback": f"LLM Error: {str(e)}", "attempts": state['attempts'] + 1}

def reviewer_node(state: SentinelState):
    """Agent C (Reviewer): Code ki syntax aur logic audit karta hai"""
    print("🛡️  [Agent: Reviewer] Auditing the proposed fix...")
    
    proposed = state.get('proposed_fix', "")
    if not proposed:
        return {"audit_passed": False, "feedback": "No code proposed by Architect."}

    # 1. Syntax Validation
    temp_file = state['file_path'].replace(".js", ".tmp_audit.js")
    with open(temp_file, "w") as f:
        f.write(proposed)
    
    is_valid, err_msg = validate_syntax(temp_file)
    os.remove(temp_file) # Cleanup

    if not is_valid:
        print(f"❌ Reviewer rejected: Syntax Error detected.")
        return {"audit_passed": False, "feedback": f"Syntax Error: {err_msg}"}

    # 2. Semantic Logic Audit (LLM Check)
    print("🧠 Reviewer is performing semantic logic check...")
    audit_prompt = f"""
    You are a Senior Security & Logic Auditor.
    Original Code: {state['original_code']}
    Proposed Fix: {proposed}
    Error/Issue: {state['error_log']}

    Does the proposed fix safely solve the issue without breaking other features?
    If yes, reply with 'PASSED'.
    If no, provide a 1-sentence feedback.
    """
    
    try:
        audit_res = client.chat.completions.create(
            messages=[{"role": "user", "content": audit_prompt}],
            model="llama-3.1-8b-instant"
        ).choices[0].message.content

        if "PASSED" in audit_res.upper():
            print("✅ Reviewer Audit: PASSED")
            return {"audit_passed": True, "feedback": "Logic verified and passed."}
        else:
            print(f"❌ Reviewer Audit: REJECTED - {audit_res}")
            return {"audit_passed": False, "feedback": audit_res}
    except:
        # Fallback to syntax only if LLM audit fails
        return {"audit_passed": True, "feedback": "Syntax pass (Audit fallback)."}

# --- 5. GRAPH CONSTRUCTION ---

workflow = StateGraph(SentinelState)

# Define Nodes
workflow.add_node("scout", scout_node)
workflow.add_node("architect", architect_node)
workflow.add_node("reviewer", reviewer_node)

# Define Flow/Edges
workflow.set_entry_point("scout")
workflow.add_edge("scout", "architect")
workflow.add_edge("architect", "reviewer")

# Router logic: Reviewer decide karega aage kahan jana hai
def router_logic(state: SentinelState):
    if state['audit_passed']:
        return "deploy"
    elif state['attempts'] >= 3:
        return "abort"
    else:
        return "retry"

workflow.add_conditional_edges(
    "reviewer",
    router_logic,
    {
        "deploy": END,
        "retry": "architect",
        "abort": END
    }
)

# Graph compile karna
sentinel_agents = workflow.compile()

# --- 6. EXPORTED WRAPPER (For main.py) ---

def run_sentinel_agents(issue_type, file_path, log_content):
    """
    Main entry point for main.py to trigger the multi-agent workflow.
    """
    initial_state = {
        "issue_type": issue_type,
        "file_path": os.path.abspath(file_path),
        "error_log": log_content,
        "attempts": 0,
        "audit_passed": False,
        "proposed_fix": ""
    }
    
    print(f"\n🚀 [Sentinel Core] Dispatching Agents for {issue_type}...")
    final_state = sentinel_agents.invoke(initial_state)
    
    if final_state.get("audit_passed"):
        # Save fixed code to file
        with open(file_path, "w") as f:
            f.write(final_state["proposed_fix"])
        
        # History aur Dashboard update
        mode = "Self-Optimized" if issue_type == "PERFORMANCE" else "Auto-Patched"
        log_fix_to_history(
            file_path, 
            log_content, 
            final_state["original_code"], 
            final_state["proposed_fix"], 
            mode
        )
        log_mentor_message(final_state.get("explanation", "Issue resolved by agents."))
        print(f"🚀 [Sentinel Core] SUCCESS: {mode} deployed to {file_path}")
        return True
    else:
        print(f"❌ [Sentinel Core] ABORTED: Agents could not fix the issue safely.")
        return False

# Legacy support for main.py calls
def repair_code(error_log, file_path):
    return run_sentinel_agents("CRASH", file_path, error_log)

def optimize_code(perf_log, file_path):
    return run_sentinel_agents("PERFORMANCE", file_path, perf_log)

def run_predictive_scan(file_path):
    """SABSE IMPORTANT: Yeh code ko crash hone se pehle analyze karta hai"""
    print(f"\n🔍 [Agent: Scanner] Performing Pre-Emptive scan on {file_path}...")
    
    if not os.path.exists(file_path):
        print("❌ File not found for scanning.")
        return False

    with open(file_path, "r") as f:
        code = f.read()

    # Special Prompt for Vulnerability Prediction
    prompt = f"""
    You are a Senior Security & Stability Auditor. 
    Analyze the following Node.js code and predict potential runtime errors (null pointers, undefined variables, unhandled exceptions).

    CODE:
    {code}

    RESPONSE RULE:
    Return ONLY a JSON object with a key "vulnerabilities" containing an array of issues.
    Each issue must have: "priority" (HIGH/MEDIUM/LOW), "line" (number), "issue" (description), and "fix" (suggestion).
    No markdown, no talk.
    """

    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            response_format={ "type": "json_object" } # Strict JSON format
        ).choices[0].message.content

        # Parse logic
        data = json.loads(response)
        issues = data.get("vulnerabilities", [])

        # Dashboard ke liye file save karna
        scan_results_path = os.path.abspath("../sentinel-dashboard/public/scan_results.json")
        with open(scan_results_path, "w") as f:
            json.dump(issues, f, indent=4)
        
        print(f"✅ Scan Complete: {len(issues)} potential issues detected.")
        return True
    except Exception as e:
        print(f"⚠️ Scan Agent Error: {e}")
        return False