import json
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='SDET 4: Directory Router')
    parser.add_argument('--input', required=True)
    parser.add_argument('--output-dir', required=True)
    
    args = parser.parse_args()
    
    print("📖 Reading validated logs...")
    with open(args.input, 'r') as f:
        data = json.load(f)
    
    bugs_dir = Path(args.output_dir) / 'genuine_bugs'
    flakes_dir = Path(args.output_dir) / 'environment_flakes'
    bugs_dir.mkdir(parents=True, exist_ok=True)
    flakes_dir.mkdir(parents=True, exist_ok=True)
    
    print("📂 Routing logs to directories...")
    bug_count = 0
    flake_count = 0
    
    for idx, entry in enumerate(data['entries']):
        classification = entry.get('classification', 'ENVIRONMENT_FLAKE')
        filename = f"log_{idx:04d}.txt"
        
        if classification == 'GENUINE_BUG':
            target_dir = bugs_dir
            bug_count += 1
        else:
            target_dir = flakes_dir
            flake_count += 1
        
        with open(target_dir / filename, 'w') as f:
            f.write(entry['raw'])
    
    print(f"✅ Routing complete")
    print(f"   🐛 Genuine bugs: {bug_count}")
    print(f"   🌧️ Environment flakes: {flake_count}")

if __name__ == '__main__':
    main()