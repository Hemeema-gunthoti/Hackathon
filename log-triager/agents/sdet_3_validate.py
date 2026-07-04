import json
import argparse
import re

def validate_classification(entry):
    """Cross-reference classification against keyword triggers."""
    
    classification = entry.get('classification', 'UNKNOWN')
    cleaned = entry.get('cleaned', '').lower()
    
    bug_keywords = [
        'nullpointer', 'cannot invoke', 'indexoutofbounds',
        'classcast', 'type mismatch', 'logic error',
        'constraint violation', 'foreign key', 'outofmemory',
        'segmentation fault', 'buffer overflow', 'undefined reference',
        'access violation', 'heap corruption'
    ]
    
    flake_keywords = [
        'timeout', 'connection pool', 'rate limit',
        'dns', 'throttle', 'temporary', 'retry',
        'transient', 'recover', 'cloud', 'flake', 'spike',
        'unavailable', 'unreachable', 'packet loss', 'latency'
    ]
    
    bug_score = sum(1 for kw in bug_keywords if kw in cleaned)
    flake_score = sum(1 for kw in flake_keywords if kw in cleaned)
    
    is_valid = True
    recommendation = classification
    
    if classification == 'GENUINE_BUG' and bug_score < 1 and flake_score > bug_score:
        is_valid = False
        recommendation = 'ENVIRONMENT_FLAKE'
    elif classification == 'ENVIRONMENT_FLAKE' and flake_score < 1 and bug_score > flake_score:
        is_valid = False
        recommendation = 'GENUINE_BUG'
    
    return {
        'is_valid': is_valid,
        'bug_keywords_matched': bug_score,
        'flake_keywords_matched': flake_score,
        'recommendation': recommendation
    }

def main():
    parser = argparse.ArgumentParser(description='SDET 3: Validation & Cross-check')
    parser.add_argument('--classified', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--report', required=True)
    
    args = parser.parse_args()
    
    print("📖 Reading classified logs...")
    with open(args.classified, 'r') as f:
        data = json.load(f)
    
    validation_report = []
    corrections = 0
    
    for idx, entry in enumerate(data['entries']):
        validation = validate_classification(entry)
        entry['validation'] = validation
        
        if not validation['is_valid']:
            corrections += 1
            original = entry.get('classification')
            entry['classification'] = validation['recommendation']
            print(f"⚠️  Log {idx}: {original} → {validation['recommendation']}")
        
        validation_report.append({
            'log_index': idx,
            'original': entry.get('classification'),
            'is_valid': validation['is_valid'],
        })
    
    print("💾 Writing validated logs...")
    with open(args.output, 'w') as f:
        json.dump(data, f, indent=2)
    
    print("📊 Writing validation report...")
    with open(args.report, 'w') as f:
        f.write("VALIDATION REPORT\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total entries analyzed: {len(data['entries'])}\n")
        f.write(f"Corrections made: {corrections}\n")
        if len(validation_report) > 0:
            accuracy = ((len(validation_report) - corrections) / len(validation_report) * 100)
            f.write(f"Validation accuracy: {accuracy:.1f}%\n\n")
        else:
            f.write(f"Validation accuracy: N/A\n\n")
        
        if corrections > 0:
            f.write("Classifications corrected:\n")
            f.write("-" * 60 + "\n")
            for item in validation_report:
                if not item['is_valid']:
                    f.write(f"  Log {item['log_index']}: CORRECTED\n")
    
    print(f"✅ Validation complete: {corrections} corrections made")

if __name__ == '__main__':
    main()