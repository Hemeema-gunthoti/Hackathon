import json
import argparse
from groq import Groq

def build_classification_prompt(log_entries):
    """Build batch prompt for classifying all logs at once."""
    
    logs_text = "\n\n".join([
        f"[LOG {i}]\n{entry['cleaned']}"
        for i, entry in enumerate(log_entries)
    ])
    
    system_prompt = """You are an expert QA automation engineer specializing in CI/CD pipeline analysis.

Your task is to classify CI/CD pipeline logs into TWO categories:

1. **GENUINE_BUG**: Actual application defects that require code changes
   - NullPointerException, IndexOutOfBoundsException, logic errors
   - Type casting errors, constraint violations
   - Unhandled edge cases, memory leaks
   - Database errors from code issues

2. **ENVIRONMENT_FLAKE**: Transient environmental issues (auto-recover or config)
   - Network timeouts, connection pool exhaustion
   - DNS resolution failures, cloud provider throttling
   - Temporary database locks, rate limiting
   - Intermittent service unavailability
   - Build cache issues, temporary file system problems

For EACH log entry, respond ONLY with:
LOG_INDEX: <number>
CLASSIFICATION: <GENUINE_BUG or ENVIRONMENT_FLAKE>
CONFIDENCE: <0.0-1.0>
REASONING: <2-3 sentence explanation>

Rules:
- Be strict in your analysis
- If uncertain, classify as ENVIRONMENT_FLAKE
- Look for error types, keywords, and patterns
- Consider recovery status (if it recovered, likely a flake)"""
    
    user_prompt = f"""Classify these CI/CD logs:

{logs_text}

Respond with the format specified above, one classification per log."""
    
    return system_prompt, user_prompt

def classify_logs(log_entries, api_key):
    """Call Groq to classify logs in a single batch."""
    
    client = Groq(api_key=api_key)
    
    system_prompt, user_prompt = build_classification_prompt(log_entries)
    
    message = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=2000,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    response_text = message.choices[0].message.content
    classifications = parse_classifications(response_text, len(log_entries))
    
    return classifications

def parse_classifications(response_text, num_logs):
    """Parse Groq response into structured classifications."""
    
    classifications = {}
    lines = response_text.strip().split('\n')
    
    current_log_idx = None
    for line in lines:
        line = line.strip()
        
        if line.startswith('LOG_INDEX:'):
            try:
                current_log_idx = int(line.split(':')[1].strip())
                classifications[current_log_idx] = {}
            except (ValueError, IndexError):
                continue
                
        elif line.startswith('CLASSIFICATION:') and current_log_idx is not None:
            value = line.split(':', 1)[1].strip()
            classifications[current_log_idx]['classification'] = value
            
        elif line.startswith('CONFIDENCE:') and current_log_idx is not None:
            try:
                value = float(line.split(':')[1].strip())
                classifications[current_log_idx]['confidence'] = value
            except (ValueError, IndexError):
                classifications[current_log_idx]['confidence'] = 0.5
                
        elif line.startswith('REASONING:') and current_log_idx is not None:
            reasoning = line.split(':', 1)[1].strip()
            classifications[current_log_idx]['reasoning'] = reasoning
    
    return classifications

def main():
    parser = argparse.ArgumentParser(description='SDET 2: LLM Classification (Groq)')
    parser.add_argument('--input', required=True, help='Input JSON from SDET 1')
    parser.add_argument('--output', required=True, help='Output JSON with classifications')
    parser.add_argument('--api-key', required=True, help='Groq API key')
    
    args = parser.parse_args()
    
    print("📖 Reading filtered logs...")
    with open(args.input, 'r') as f:
        data = json.load(f)
    
    entries = data['entries']
    print(f"📊 Entries to classify: {len(entries)}")
    
    print("🤖 Calling Groq API for classification...")
    classifications = classify_logs(entries, args.api_key)
    
    for idx, entry in enumerate(entries):
        if idx in classifications:
            entry.update(classifications[idx])
        else:
            entry['classification'] = 'ENVIRONMENT_FLAKE'
            entry['confidence'] = 0.5
            entry['reasoning'] = 'Unable to classify'
    
    genuine_bugs = sum(1 for e in entries if e.get('classification') == 'GENUINE_BUG')
    environment_flakes = sum(1 for e in entries if e.get('classification') == 'ENVIRONMENT_FLAKE')
    
    output = {
        "classified_at": data['processed_at'],
        "total_entries": len(entries),
        "genuine_bugs": genuine_bugs,
        "environment_flakes": environment_flakes,
        "entries": entries,
    }
    
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Classification complete")
    print(f"   🐛 Genuine bugs: {genuine_bugs}")
    print(f"   🌧️ Environment flakes: {environment_flakes}")

if __name__ == '__main__':
    main()