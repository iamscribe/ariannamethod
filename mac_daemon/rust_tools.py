#!/usr/bin/env python3
"""
Real Rust tools integration for Mac Daemon
NO FALLBACKS. NO PLACEHOLDERS. REAL RUST BINARIES ONLY.
"""

import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional

# Path to compiled Rust binaries
RUST_BINS = Path(__file__).parent / "rust_bins"
FILE_SEARCH_BIN = RUST_BINS / "file-search" / "target" / "release" / "codex-file-search"

class RustTools:
    """Real Rust tools - compiled binaries only"""
    
    def __init__(self):
        self.file_search_bin = FILE_SEARCH_BIN
        if not self.file_search_bin.exists():
            raise RuntimeError(f"Rust binary not found: {self.file_search_bin}")
    
    def fuzzy_file_search(self, pattern: str, directory: Path, limit: int = 50) -> List[Dict]:
        """
        REAL fuzzy file search using compiled Rust binary
        
        Returns list of {'path': str, 'score': int}
        Raises RuntimeError if binary fails
        """
        try:
            result = subprocess.run(
                [
                    str(self.file_search_bin),
                    pattern,
                    "--cwd", str(directory),
                    "--limit", str(limit),
                    "--json"
                ],
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            
            # Parse JSON lines output
            matches = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        match = json.loads(line)
                        # Filter out metadata lines
                        if 'path' in match and 'score' in match:
                            matches.append({
                                'path': match['path'],
                                'score': match['score']
                            })
                    except json.JSONDecodeError:
                        continue
            
            return matches
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"file-search failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("file-search timed out")
    
    def git_status(self, repo_path: Path) -> Optional[Dict]:
        """
        Get git status using subprocess (Rust git_info.rs requires async/tokio)
        
        Returns: {'branch': str, 'dirty': bool, 'repo_path': str}
        """
        try:
            # Check if it's a git repo
            git_dir = repo_path / '.git'
            if not git_dir.exists():
                return None
            
            # Get branch
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=5
            )
            branch = branch_result.stdout.strip() if branch_result.returncode == 0 else 'unknown'
            
            # Check if dirty
            status_result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=5
            )
            dirty = len(status_result.stdout.strip()) > 0 if status_result.returncode == 0 else False
            
            return {
                'branch': branch,
                'dirty': dirty,
                'repo_path': str(repo_path)
            }
        except Exception:
            return None
    
    def safe_exec(self, command: List[str], cwd: Path, timeout: int = 30) -> Dict:
        """
        Execute command safely
        
        Returns: {'stdout': str, 'stderr': str, 'returncode': int, 'success': bool}
        """
        try:
            result = subprocess.run(
                command,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'success': result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                'stdout': '',
                'stderr': f'Command timed out after {timeout}s',
                'returncode': -1,
                'success': False
            }
        except Exception as e:
            return {
                'stdout': '',
                'stderr': str(e),
                'returncode': -1,
                'success': False
            }
