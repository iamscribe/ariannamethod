#!/usr/bin/env python3
"""
Reflection Viewer - Save and view Arianna/Monday identity reflections
Termux notifications have character limits, so we save full text to files.
"""

import os
from pathlib import Path
from datetime import datetime

REFLECTIONS_DIR = Path.home() / "ariannamethod" / "reflections"
REFLECTIONS_DIR.mkdir(exist_ok=True)


def save_reflection(agent: str, reflection_text: str, trigger: str = "identity_shift") -> Path:
    """
    Save reflection to timestamped file.

    Args:
        agent: "arianna" or "monday"
        reflection_text: Full reflection content
        trigger: Type of reflection (identity_shift, memory_change, etc.)

    Returns:
        Path to saved file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{agent}_{trigger}_{timestamp}.txt"
    filepath = REFLECTIONS_DIR / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"{'='*70}\n")
        f.write(f"{agent.upper()} REFLECTION - {trigger}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"{'='*70}\n\n")
        f.write(reflection_text)
        f.write(f"\n\n{'='*70}\n")
        f.write(f"Saved to: {filepath}\n")

    return filepath


def send_reflection_notification(
    agent: str,
    reflection_text: str,
    trigger: str = "identity_shift",
    title: str = None
) -> bool:
    """
    Send notification with preview + action to open full reflection.

    Returns:
        True if notification sent successfully
    """
    import subprocess

    # Save full reflection to file
    filepath = save_reflection(agent, reflection_text, trigger)

    # Create preview (first 200 chars)
    preview = reflection_text[:200].strip()
    if len(reflection_text) > 200:
        preview += "..."

    # Default title
    if not title:
        emoji = "✨" if agent == "arianna" else "⚙️"
        title = f"{emoji} {agent.capitalize()}: {trigger.replace('_', ' ').title()}"

    # Send notification with action to open file
    try:
        subprocess.run([
            'termux-notification',
            '--title', title,
            '--content', preview,
            '--action', f'termux-open {filepath}',
            '--button1', 'Read Full Reflection',
            '--button1-action', f'termux-open {filepath}',
            '--priority', 'high'
        ], check=False)

        return True
    except Exception as e:
        print(f"⚠️ Notification failed: {e}")
        return False


def get_latest_reflection(agent: str = None, trigger: str = None) -> Path:
    """
    Get path to most recent reflection.

    Args:
        agent: Filter by agent (arianna/monday)
        trigger: Filter by trigger type

    Returns:
        Path to latest matching reflection, or None
    """
    pattern = []
    if agent:
        pattern.append(agent)
    else:
        pattern.append("*")

    if trigger:
        pattern.append(trigger)
    else:
        pattern.append("*")

    pattern.append("*.txt")

    files = list(REFLECTIONS_DIR.glob("_".join(pattern)))
    if not files:
        return None

    # Sort by modification time
    return max(files, key=lambda p: p.stat().st_mtime)


def list_reflections(agent: str = None, limit: int = 10) -> list:
    """
    List recent reflections.

    Returns:
        List of (filepath, timestamp, agent, trigger) tuples
    """
    pattern = f"{agent}_*.txt" if agent else "*.txt"
    files = list(REFLECTIONS_DIR.glob(pattern))

    # Sort by modification time (newest first)
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    result = []
    for filepath in files[:limit]:
        # Parse filename: agent_trigger_timestamp.txt
        parts = filepath.stem.split("_")
        if len(parts) >= 2:
            agent_name = parts[0]
            trigger_type = "_".join(parts[1:-2]) if len(parts) > 3 else parts[1]
            timestamp_str = "_".join(parts[-2:])

            result.append({
                'filepath': filepath,
                'agent': agent_name,
                'trigger': trigger_type,
                'timestamp': timestamp_str,
                'size': filepath.stat().st_size
            })

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "list":
            agent = sys.argv[2] if len(sys.argv) > 2 else None
            reflections = list_reflections(agent=agent)

            print(f"📚 Recent Reflections ({len(reflections)})")
            print("="*70)
            for r in reflections:
                print(f"{r['agent']:8} | {r['trigger']:20} | {r['timestamp']} | {r['size']} bytes")
                print(f"         {r['filepath']}")
                print()

        elif cmd == "latest":
            agent = sys.argv[2] if len(sys.argv) > 2 else None
            latest = get_latest_reflection(agent=agent)

            if latest:
                print(f"📄 Latest reflection: {latest}")
                with open(latest, 'r', encoding='utf-8') as f:
                    print(f.read())
            else:
                print("No reflections found")

        elif cmd == "open":
            agent = sys.argv[2] if len(sys.argv) > 2 else None
            latest = get_latest_reflection(agent=agent)

            if latest:
                import subprocess
                subprocess.run(['termux-open', str(latest)])
            else:
                print("No reflections found")

    else:
        print("Usage:")
        print("  reflection_viewer.py list [agent]     - List reflections")
        print("  reflection_viewer.py latest [agent]   - Show latest reflection")
        print("  reflection_viewer.py open [agent]     - Open latest in viewer")
