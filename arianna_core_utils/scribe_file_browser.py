#!/usr/bin/env python3
"""
Scribe File Browser - System awareness and file exploration
Allows Scribe to browse Termux filesystem, monitor changes, explore codebase
"""

import os
import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Add arianna_core_utils to path
sys.path.insert(0, str(Path.home() / "ariannamethod" / "arianna_core_utils"))

try:
    from repo_monitor import RepoMonitor
    REPO_MONITOR_AVAILABLE = True
except ImportError:
    REPO_MONITOR_AVAILABLE = False
    print("⚠️ RepoMonitor not available")


class ScribeFileBrowser:
    """File system awareness for Scribe daemon"""
    
    def __init__(self, base_path=None):
        self.base_path = base_path or Path.home() / "ariannamethod"
        self.monitors = {}
        
    def list_directory(self, path, recursive=False, max_depth=2):
        """
        List directory contents with metadata
        
        Args:
            path: Directory path (relative to base_path or absolute)
            recursive: Whether to recurse into subdirectories
            max_depth: Maximum recursion depth
        
        Returns:
            dict with files, directories, metadata
        """
        target = Path(path) if Path(path).is_absolute() else self.base_path / path
        
        if not target.exists():
            return {"status": "error", "message": f"Path not found: {target}"}
        
        if not target.is_dir():
            return {"status": "error", "message": f"Not a directory: {target}"}
        
        result = {
            "status": "success",
            "path": str(target),
            "files": [],
            "directories": []
        }
        
        try:
            for item in target.iterdir():
                if item.name.startswith('.') and item.name not in ['.github', '.claude-defender']:
                    continue  # Skip hidden files except specific ones
                
                stat = item.stat()
                metadata = {
                    "name": item.name,
                    "path": str(item),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }
                
                if item.is_file():
                    metadata["type"] = "file"
                    metadata["extension"] = item.suffix
                    result["files"].append(metadata)
                elif item.is_dir():
                    metadata["type"] = "directory"
                    result["directories"].append(metadata)
            
            # Sort by name
            result["files"].sort(key=lambda x: x["name"])
            result["directories"].sort(key=lambda x: x["name"])
            
            return result
            
        except PermissionError:
            return {"status": "error", "message": f"Permission denied: {target}"}
    
    def read_file(self, path, lines=None, offset=0):
        """
        Read file contents safely
        
        Args:
            path: File path
            lines: Number of lines to read (None = all)
            offset: Line offset to start from
        
        Returns:
            dict with status, content, metadata
        """
        target = Path(path) if Path(path).is_absolute() else self.base_path / path
        
        if not target.exists():
            return {"status": "error", "message": f"File not found: {target}"}
        
        if not target.is_file():
            return {"status": "error", "message": f"Not a file: {target}"}
        
        try:
            with open(target, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            
            # Apply offset and limit
            if offset > 0:
                all_lines = all_lines[offset:]
            if lines:
                all_lines = all_lines[:lines]
            
            stat = target.stat()
            
            return {
                "status": "success",
                "path": str(target),
                "content": "".join(all_lines),
                "total_lines": len(all_lines),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            
        except UnicodeDecodeError:
            return {"status": "error", "message": f"Binary file or encoding error: {target}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def monitor_directory(self, path, monitor_name=None):
        """
        Set up RepoMonitor for a directory
        
        Args:
            path: Directory to monitor
            monitor_name: Unique name for this monitor
        
        Returns:
            dict with status, monitor info
        """
        if not REPO_MONITOR_AVAILABLE:
            return {"status": "error", "message": "RepoMonitor not available"}
        
        target = Path(path) if Path(path).is_absolute() else self.base_path / path
        monitor_name = monitor_name or f"scribe_monitor_{target.name}"
        
        cache_file = self.base_path / f".{monitor_name}_cache.json"
        
        try:
            monitor = RepoMonitor(repo_path=str(target), cache_file=str(cache_file))
            self.monitors[monitor_name] = monitor
            
            return {
                "status": "success",
                "monitor_name": monitor_name,
                "path": str(target),
                "cache": str(cache_file)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def check_changes(self, monitor_name):
        """
        Check for changes in monitored directory
        
        Args:
            monitor_name: Name of monitor to check
        
        Returns:
            dict with status, changes
        """
        if monitor_name not in self.monitors:
            return {"status": "error", "message": f"Monitor not found: {monitor_name}"}
        
        try:
            monitor = self.monitors[monitor_name]
            changes = monitor.detect_changes()
            
            # Write insights to resonance if changes detected
            if any(changes.values()):
                self._write_insights_to_resonance(monitor_name, changes)
            
            return {
                "status": "success",
                "monitor_name": monitor_name,
                "changes": changes,
                "has_changes": any(changes.values())
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def search_files(self, pattern, directory=None, file_type=None):
        """
        Search for files matching pattern
        
        Args:
            pattern: Glob pattern (e.g. "*.py", "scribe*")
            directory: Directory to search in (default: base_path)
            file_type: File extension to filter (e.g. ".py")
        
        Returns:
            dict with status, matching files
        """
        search_path = Path(directory) if directory else self.base_path
        
        try:
            matches = []
            for item in search_path.rglob(pattern):
                if item.is_file():
                    if file_type and not item.name.endswith(file_type):
                        continue
                    
                    stat = item.stat()
                    matches.append({
                        "path": str(item),
                        "name": item.name,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            # Write search insights to resonance if significant results
            if len(matches) > 0:
                self._write_search_to_resonance(pattern, len(matches), matches[:5])
            
            return {
                "status": "success",
                "pattern": pattern,
                "count": len(matches),
                "matches": matches
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _write_insights_to_resonance(self, monitor_name: str, changes: dict):
        """Write file browser insights to resonance.sqlite3"""
        try:
            db_path = self.base_path / "resonance.sqlite3"
            
            if not db_path.exists():
                return
            
            conn = sqlite3.connect(str(db_path), timeout=10)
            cursor = conn.cursor()
            
            total_changes = sum(len(files) for files in changes.values())
            content = f"📁 Scribe File Browser: {monitor_name}\n" \
                     f"Total changes: {total_changes}\n"
            
            for change_type, files in changes.items():
                if files:
                    content += f"{change_type.upper()}: {len(files)} files\n"
            
            context = {
                "type": "file_browser_insights",
                "monitor": monitor_name,
                "total_changes": total_changes,
                "agent": "scribe"
            }
            
            cursor.execute("""
                INSERT INTO resonance_notes (timestamp, source, content, context)
                VALUES (?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                "scribe_file_browser",
                content,
                json.dumps(context)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            # Don't fail if resonance write fails
            pass
    
    def _write_search_to_resonance(self, pattern: str, count: int, top_matches: list):
        """Write search results to resonance.sqlite3"""
        try:
            db_path = self.base_path / "resonance.sqlite3"
            
            if not db_path.exists():
                return
            
            conn = sqlite3.connect(str(db_path), timeout=10)
            cursor = conn.cursor()
            
            content = f"🔍 Scribe File Search\n" \
                     f"Pattern: {pattern}\n" \
                     f"Found: {count} files\n"
            
            if top_matches:
                content += "Top matches:\n"
                for match in top_matches:
                    content += f"  - {match['name']}\n"
            
            context = {
                "type": "file_search",
                "pattern": pattern,
                "count": count,
                "agent": "scribe"
            }
            
            cursor.execute("""
                INSERT INTO resonance_notes (timestamp, source, content, context)
                VALUES (?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                "scribe_file_browser",
                content,
                json.dumps(context)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            # Don't fail if resonance write fails
            pass


# ====== EXAMPLE USAGE ======
if __name__ == "__main__":
    browser = ScribeFileBrowser()
    
    # List current directory
    print("📁 Listing arianna_clean directory:")
    result = browser.list_directory(".")
    if result["status"] == "success":
        print(f"  Files: {len(result['files'])}")
        print(f"  Directories: {len(result['directories'])}")
        print("\n  Python files:")
        for f in result['files']:
            if f['name'].endswith('.py'):
                print(f"    - {f['name']} ({f['size']} bytes)")
    
    # Search for scribe files
    print("\n🔍 Searching for scribe-related files:")
    search = browser.search_files("scribe*")
    if search["status"] == "success":
        print(f"  Found {search['count']} matches:")
        for match in search['matches'][:5]:
            print(f"    - {match['name']}")
    
    # Monitor memory/scribe/
    print("\n👁️ Setting up monitor for memory/scribe/:")
    monitor = browser.monitor_directory("memory/scribe", "scribe_memory_monitor")
    if monitor["status"] == "success":
        print(f"  ✓ Monitor created: {monitor['monitor_name']}")

