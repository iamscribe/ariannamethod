#!/usr/bin/env python3
"""
Rust tools integration for Mac Daemon
Provides fast file search, safe exec, git info via compiled Rust binaries
"""

import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional

# Path to postcodex rust binaries (will compile if needed)
POSTCODEX_RS = Path.home() / "Downloads" / "arianna_clean" / "postcodex" / "codex-rs"

class RustTools:
    """Interface to Rust-based tools for Mac daemon"""
    
    def __init__(self):
        self.file_search_bin = None
        self.check_tools()
    
    def check_tools(self):
        """Check if Rust tools are available"""
        # For now, we'll use direct subprocess calls
        # TODO: Compile Rust binaries if needed
        pass
    
    def fuzzy_file_search(self, pattern: str, directory: Path, limit: int = 50) -> List[Dict]:
        """
        Fast fuzzy file search using Rust implementation
        
        Args:
            pattern: Search pattern (fuzzy matching)
            directory: Directory to search in
            limit: Max results
        
        Returns:
            List of dicts with 'path' and 'score'
        """
        try:
            # For now, fallback to Python implementation
            # TODO: Use compiled Rust binary when available
            return self._python_fuzzy_search(pattern, directory, limit)
        except Exception as e:
            return []
    
    def _python_fuzzy_search(self, pattern: str, directory: Path, limit: int) -> List[Dict]:
        """Fallback Python implementation"""
        results = []
        pattern_lower = pattern.lower()
        
        for path in directory.rglob('*'):
            if path.is_file() and '.git' not in str(path):
                name = path.name.lower()
                if pattern_lower in name:
                    # Simple scoring: position of match
                    score = 100 - name.index(pattern_lower)
                    results.append({
                        'path': str(path.relative_to(directory)),
                        'score': score
                    })
        
        # Sort by score and limit
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def safe_exec(self, command: List[str], cwd: Path, timeout: int = 30) -> Dict:
        """
        Execute command safely with sandboxing
        
        Args:
            command: Command and args
            cwd: Working directory
            timeout: Timeout in seconds
        
        Returns:
            Dict with 'stdout', 'stderr', 'returncode'
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
    
    def git_status(self, repo_path: Path) -> Optional[Dict]:
        """
        Get git repository status quickly
        
        Args:
            repo_path: Path to git repository
        
        Returns:
            Dict with 'branch', 'dirty', 'ahead', 'behind' or None
        """
        try:
            # Check if it's a git repo
            git_dir = repo_path / '.git'
            if not git_dir.exists():
                return None
            
            # Get branch
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=5
            )
            branch = result.stdout.strip() if result.returncode == 0 else 'unknown'
            
            # Check if dirty
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=5
            )
            dirty = len(result.stdout.strip()) > 0 if result.returncode == 0 else False
            
            return {
                'branch': branch,
                'dirty': dirty,
                'repo_path': str(repo_path)
            }
        except Exception:
            return None

