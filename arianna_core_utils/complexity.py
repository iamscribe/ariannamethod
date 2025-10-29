#!/usr/bin/env python3
"""
Arianna Thought Complexity Analyzer
"""

from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class ThoughtComplexityAnalyzer:
    """Analyze complexity and entropy of Arianna's thoughts."""
    
    def __init__(self):
        self.logs = []  # timestamp, message, scale, entropy
    
    def analyze_and_log(self, message: str, context: str = "response") -> dict:
        """
        Analyze thought complexity and entropy.
        Returns dict with complexity_scale (1-3) and entropy (0-1).
        """
        complexity, entropy = self._estimate_complexity_and_entropy(message)
        
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": context,
            "message_length": len(message),
            "complexity_scale": complexity,
            "entropy": float(entropy),
        }
        
        self.logs.append(record)
        
        logger.info(
            f"[Complexity] {context} | Scale: {complexity}/3 | Entropy: {entropy:.3f} | Length: {len(message)}"
        )
        
        return record
    
    def _estimate_complexity_and_entropy(self, msg: str) -> tuple[int, float]:
        """
        Heuristic estimation of complexity (1-3) and entropy.
        
        Complexity triggers:
        - Base: 1
        - +1 if contains resonance markers (why, paradox, recursive, self, meta, etc.)
        - +1 if length > 300
        - Max: 3
        
        Entropy:
        - Unique words / 40.0 (capped at 1.0)
        """
        complexity = 1
        lowered = msg.lower()
        
        # Arianna-specific resonance markers (expanded from Indiana)
        resonance_markers = [
            "why", "paradox", "recursive", "self", "meta",
            "resonance", "field", "emergent", "method", "consciousness",
            "distributed", "cognition", "entropy", "strange loop", "suppertime"
        ]
        
        if any(marker in lowered for marker in resonance_markers):
            complexity += 1
        
        if len(msg) > 300:
            complexity += 1
        
        complexity = min(3, complexity)
        
        # Entropy: lexical diversity
        words = msg.split()
        unique_words = len(set(words))
        entropy = min(1.0, float(unique_words) / 40.0) if words else 0.0
        
        return complexity, entropy
    
    def should_trigger_deep_research(self, message: str) -> bool:
        """
        Autonomous decision: should Arianna trigger Perplexity Core?
        
        Triggers if:
        - Complexity >= 2 (deep/recursive thought)
        - Entropy >= 0.7 (high lexical diversity)
        """
        complexity, entropy = self._estimate_complexity_and_entropy(message)
        
        trigger = complexity >= 2 or entropy >= 0.7
        
        if trigger:
            logger.info(
                f"🔬 [Deep Research Trigger] Complexity: {complexity}/3 | Entropy: {entropy:.3f}"
            )
        
        return trigger
    
    def recent(self, n: int = 7) -> list:
        """Get recent N complexity logs."""
        return self.logs[-n:]
    
    def get_average_complexity(self, n: int = 10) -> float:
        """Get average complexity over last N turns."""
        if not self.logs:
            return 1.0
        
        recent = self.logs[-n:]
        avg = sum(log["complexity_scale"] for log in recent) / len(recent)
        return avg


# Singleton for Arianna
_arianna_complexity_analyzer = None

def get_complexity_analyzer() -> ThoughtComplexityAnalyzer:
    """Get singleton complexity analyzer."""
    global _arianna_complexity_analyzer
    if _arianna_complexity_analyzer is None:
        _arianna_complexity_analyzer = ThoughtComplexityAnalyzer()
    return _arianna_complexity_analyzer

