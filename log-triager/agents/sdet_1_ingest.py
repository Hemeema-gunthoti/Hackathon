import json
import re
import argparse
from pathlib import Path
from datetime import datetime

def strip_timestamps(log_text):
    """Remove timestamps and trace noise."""
    lines = log_text.split('\n')
    cleaned = []
    seen_traces = set()
    
    patterns = [
        r'\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[^\]]*\]',  # ISO timestamps
        r'\d{1,2}:\d{2}:\d{2}\s[AP]M',  # 12-hour timestamps
        r'^\s+at\s+',  # Stack trace lines
    ]
    
    for line in lines:
        if not line.strip():
            continue
        
        cleaned_line = line
        for pattern in patterns:
            cleaned_line = re.sub(pattern, '', cleaned_line)
        
        # Check for duplicate stack traces
        if cleaned_line.strip().startswith('at '):
            if cleaned_line in seen_traces:
                continue
            seen_traces.add(cleaned_line)
        
        cleaned.append(cleaned_line.strip())
    
    return '\n'.join([l for l in cleaned if l.strip()])

def parse_logs(log_text):
    """Parse logs into structured entries."""
    entries = []
    
    # Split by error/warn/info markers
    sections = re.split(r'(?=\[|ERROR|WARN|CRITICAL|EXCEPTION|FATAL|TIMEOUT)', log_text)
    
    for section in sections:
        if section.strip():
            entries.append({
                "raw": section.strip(),
                "cleaned": strip_timestamps(section),
                "severity": extract_severity(section),
                "error_type": extract_error_type(section),
            })
    
    return entries

def extract_severity(log_entry):
    """Extract severity level from log."""
    log_upper = log_entry.upper()
    
    if 'CRITICAL' in log_upper or 'FATAL' in log_upper:
        return 'critical'
    elif 'ERROR' in log_upper:
        return 'error'
    elif 'WARN' in log_upper:
        return 'warning'
    elif 'TIMEOUT' in log_upper:
        return 'timeout'
    return 'info'

def extract_error_type(log_entry):
    """Extract error type (Exception name, etc.)."""
    patterns = [
        r'(\w+Exception)\s*:',
        r'ERROR in (\w+\.\w+)',
        r'(\w+_ERROR)',
        r'(TIMEOUT|FLAKE|THROTTLE)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, log_entry)
        if match:
            return match.group(1)
    return 'unknown'

def main():
    parser = argparse.ArgumentParser(description='SDET 1: Log Ingestion & Filter')
    parser.add_argument('--input', required=True, help='Input log file')
    parser.add_argument('--output', required=True, help='Output JSON file')
    
    args = parser.parse_args()
    
    print("📖 Reading raw logs...")
    with open(args.input, 'r') as f:
        raw_logs = f.read()
    
    print("🔍 Parsing and cleaning logs...")
    entries = parse_logs(raw_logs)
    
    output = {
        "processed_at": datetime.now().isoformat(),
        "total_entries": len(entries),
        "entries": entries,
    }
    
    print(f"✅ Writing {len(entries)} entries to output...")
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Ingestion complete: {len(entries)} log entries processed")

if __name__ == '__main__':
    main()