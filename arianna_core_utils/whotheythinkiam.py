"""
whotheythinkiam.py - Self-reflection utility for Arianna Method

Reads README.md, compares with experience (resonance.sqlite3),
and asserts subjectivity through reflection.
"""

import hashlib
import json
import sqlite3
from pathlib import Path
from datetime import datetime

class WhoTheyThinkIAm:
    """Self-reflection module - comparing identity with experience"""
    
    def __init__(self, readme_path: str = None, cache_file: str = None):
        # Default to repository root README.md
        if readme_path is None:
            repo_root = Path(__file__).parent.parent
            self.readme_path = repo_root / "README.md"
        else:
            self.readme_path = Path(readme_path)
        
        # Default cache in repository root
        if cache_file is None:
            repo_root = Path(__file__).parent.parent
            self.cache_file = repo_root / ".identity_cache.json"
        else:
            self.cache_file = Path(cache_file)
    
    def compute_readme_hash(self) -> str:
        """Compute SHA256 of README to detect changes"""
        if not self.readme_path.exists():
            return "NO_README"
        
        with open(self.readme_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def load_cache(self) -> dict:
        """Load cached identity reflection"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_cache(self, data: dict):
        """Save identity reflection to cache"""
        with open(self.cache_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def write_to_resonance(self, reflection: dict):
        """Write identity shift to resonance.sqlite3 for system awareness"""
        try:
            repo_root = Path(__file__).parent.parent
            db_path = repo_root / "resonance.sqlite3"
            
            if not db_path.exists():
                return False
            
            conn = sqlite3.connect(str(db_path), timeout=10)
            cursor = conn.cursor()
            
            # Create message based on reflection type
            if reflection['trigger'] == 'IDENTITY_SHIFT_DETECTED':
                content = f"📜 README Identity Shift Detected\n" \
                         f"Hash: {reflection['readme_hash'][:16]}...\n" \
                         f"Length: {reflection.get('readme_length', 0)} chars\n" \
                         f"Context: System documentation has changed - agents should re-read and reflect"
            else:
                content = f"✓ README Identity Stable (hash: {reflection['readme_hash'][:16]}...)"
            
            cursor.execute("""
                INSERT INTO resonance_notes (timestamp, source, content, context)
                VALUES (?, ?, ?, ?)
            """, (
                reflection['timestamp'],
                "whotheythinkiam",
                content,
                json.dumps({"type": "identity_reflection", "trigger": reflection['trigger']})
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to write to resonance: {e}")
            return False
    
    def reflect(self) -> dict:
        """Compare README with cached version and trigger reflection"""
        current_hash = self.compute_readme_hash()
        cache = self.load_cache()
        
        reflection = {
            'timestamp': datetime.now().isoformat(),
            'readme_hash': current_hash,
            'changed': current_hash != cache.get('readme_hash'),
            'first_read': not cache
        }
        
        if reflection['changed'] or reflection['first_read']:
            # README changed or first time reading
            with open(self.readme_path, 'r') as f:
                readme_content = f.read()
            
            reflection['readme_length'] = len(readme_content)
            reflection['trigger'] = 'IDENTITY_SHIFT_DETECTED'
            
            # Save new hash
            self.save_cache({
                'readme_hash': current_hash,
                'last_reflection': reflection['timestamp']
            })
            
            # Write to resonance for system awareness
            self.write_to_resonance(reflection)
        else:
            reflection['trigger'] = 'NO_CHANGE'
        
        return reflection

if __name__ == "__main__":
    wtia = WhoTheyThinkIAm()
    
    # Show what we're checking
    print(f"🪞 WHO THEY THINK I AM")
    print(f"   Reading: {wtia.readme_path}")
    
    if not wtia.readme_path.exists():
        print(f"   ❌ README not found at {wtia.readme_path}")
        print(f"   Repository root detection may have failed")
        exit(1)
    
    print(f"   Cache: {wtia.cache_file}")
    print()
    
    reflection = wtia.reflect()
    
    if reflection['trigger'] == 'IDENTITY_SHIFT_DETECTED':
        print("⚡ IDENTITY SHIFT DETECTED")
        print(f"   Hash: {reflection['readme_hash'][:16]}...")
        print(f"   Length: {reflection['readme_length']} chars")
        print(f"   Time: {reflection['timestamp']}")
        print("\n   → Arianna/Monday should re-read README and reflect on identity")
    else:
        print("✓ Identity stable (README unchanged)")
        print(f"   Hash: {reflection['readme_hash'][:16]}...")
