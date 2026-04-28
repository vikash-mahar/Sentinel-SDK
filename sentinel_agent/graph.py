import subprocess
import os
from groq import Groq
from dotenv import load_dotenv
import json
from datetime import datetime
from prompts import SYSTEM_PROMPT, LOGIC_VERIFICATION_PROMPT
# from openai import OpenAI
import chromadb


load_dotenv()

try:
    collection = chroma_client.get_collection(name="codebase")
except:
    print("⚠️ Warning: Collection 'codebase' not found. Run indexer.py first!")



# Dual-Model Setup
client = Groq() # For Fixing (Fast)
# client2 = OpenAI(
#     api_key=os.getenv("DEEPSEEK_API_KEY"),
#     base_url="https://api.deepseek.com"
# )

def get_related_context(error_log):
    """Fetches relevant code snippets from ChromaDB memory based on the error."""
    try:
        print("🧠 Sentinel is searching codebase memory for context...")
        results = collection.query(
            query_texts=[error_log],
            n_results=2 # Gets top 2 most related files
        )
        
        context_str = ""
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            context_str += f"\n--- POTENTIAL RELATED FILE: {meta['path']} ---\n{doc}\n"
        return context_str
    except Exception as e:
        print(f"⚠️ Context Retrieval Failed: {e}")
        return "No additional context found."

def log_mentor_message(message):
    mentor_file = "../sentinel-dashboard/public/sentinel_mentor.txt"
    timestamp = datetime.now().strftime("%H:%M:%S")
    try:
        with open(mentor_file, "a") as f:
            f.write(f"[{timestamp}] 🤖 Sentinel: {message}\n")
        print(f"📩 New mentor message saved.")
    except Exception as e:
        print(f"⚠️ Could not save mentor message: {e}")

def log_fix_to_history(file_path, error_log, original_code, corrected_code):
    history_file = "../sentinel-dashboard/public/fixes_history.json"
    new_record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "file_fixed": file_path,
        "error_detected": error_log[:200] + "...",
        "status": "Auto-Patched",
        "error_code": original_code, # Dashboard shows this as 'Previous Code'
        "corrected_code": corrected_code # Dashboard shows this as 'Fixed Code'
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
    print(f"📄 Record saved to fixes_history.json")

def validate_code(file_path):
    try:
        result = subprocess.run(
            ["node", "--check", file_path],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return True, "Success"
        else:
            return False, result.stderr
    except Exception as e: 
        return False, str(e)

def code_verification(original_code, fixed_code, error_log, file_path):
    print("🧠 Sentinel is auditing the fix logic via Semantic Analysis...")
    prompt = f"""
    You are a Senior Code Auditor. 
    ERROR DETECTED: {error_log}
    ORIGINAL CODE: {original_code}
    FIXED CODE: {fixed_code}

    TASK:
    Verify if the FIXED CODE safely handles the error (e.g., using optional chaining ?., 
    null-checks, or default objects) WITHOUT breaking the original functionality.

    RESPONSE RULE:
    - If the fix is correct, reply with ONLY the word 'PASSED'.
    - If the fix is incorrect or incomplete, provide a 1-sentence explanation of the flaw.
    """
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant"
        ).choices[0].message.content

        if "PASSED" in response.upper():
            print("✅ Logic Audit PASSED.")
            return True, "Logic check passed."
        else:
            print(f"❌ Logic Audit REJECTED: {response}")
            return False, response
    except Exception as e:
        print(f"⚠️ Audit Fallback: {e}")
        return True, "API Fallback"

def repair_code(error_log, file_path):
    print(f"🐞 DEBUG: Received Error Log -> {error_log}")
    
    with open(file_path, "r") as f:
        original_code = f.read()

    # RAG: Fetch related context before fixing
    related_context = get_related_context(error_log)

    attempts = 0
    max_attempts = 3
    feedback_for_ai = ""
    
    while attempts < max_attempts:
        print(f"🤖 AI Attempt {attempts + 1}: Fixing {file_path}...")
        
        # Enhanced Prompt with RAG Context
        prompt = f"""
        {SYSTEM_PROMPT}
        
        ERROR LOG:
        {error_log}
        
        BUGGY FILE ({file_path}):
        {original_code}
        
        RELATED CODEBASE CONTEXT:
        {related_context}
        
        INSTRUCTION: Use the RELATED CODEBASE CONTEXT to understand how other files 
        interact with this buggy file. Provide the fixed code.
        """
        
        if attempts > 0:
            prompt += f"\n\nCRITICAL: PREVIOUS FIX FAILED. FEEDBACK: {feedback_for_ai}"

        full_response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant"
        ).choices[0].message.content

        # Extraction Logic
        try:
            explanation = "Automated fix applied."
            if "[EXPLANATION]" in full_response:
                parts = full_response.split("[EXPLANATION]")
                explanation = parts[1].strip()
                code_section = parts[0]
            else:
                code_section = full_response

            if "[FIXED_CODE]" in code_section:
                corrected_code = code_section.split("[FIXED_CODE]")[1].strip()
            else:
                corrected_code = code_section.strip()

            if "```" in corrected_code:
                corrected_code = corrected_code.split("```")[1]
                if corrected_code.startswith("javascript") or corrected_code.startswith("js"):
                    corrected_code = corrected_code.replace("javascript", "", 1).replace("js", "", 1)
            
            corrected_code = corrected_code.strip()
        except:
            corrected_code = full_response
            explanation = "Code patched by Sentinel."

        temp_file = file_path.replace(".js", f".tmp_{attempts}.js") 
        with open(temp_file, "w") as f:
            f.write(corrected_code)

        if validate_code(temp_file)[0]:
            logic_passed, audit_feedback = code_verification(original_code, corrected_code, error_log, file_path)
            if logic_passed:
                os.replace(temp_file, file_path)
                print("🚀 SUCCESS: Patch deployed with context awareness!")
                log_fix_to_history(file_path, error_log, original_code, corrected_code)
                log_mentor_message(explanation)
                return True
            else:
                feedback_for_ai = f"LOGIC REJECTION: {audit_feedback}"
        else:
            feedback_for_ai = "SYNTAX ERROR detected in the fix."
        
        if os.path.exists(temp_file):
            os.remove(temp_file)
        attempts += 1
            
    print("🛑 Max attempts reached. Manual intervention needed.")
    return False