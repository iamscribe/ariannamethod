"""
Mac Daemon Configuration
Reads from .credentials file in parent directory
"""

import os
from pathlib import Path

# Paths
HOME = Path.home()
ARIANNA_PATH = HOME / "Downloads" / "arianna_clean"
CREDENTIALS_FILE = ARIANNA_PATH / ".credentials"

def load_config():
    """Load configuration from .credentials file"""
    config = {
        'ANTHROPIC_API_KEY': None,
        'TERMUX_SSH_USER': 'u0_a311',
        'TERMUX_SSH_HOST': '10.0.0.2',
        'TERMUX_SSH_PORT': 8022,
    }
    
    # Try to read from .credentials
    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE, 'r') as f:
            for line in f:
                if line.startswith('SCRIBE_MAC_API_KEY='):
                    config['ANTHROPIC_API_KEY'] = line.split('=')[1].strip()
    
    # Fallback to environment variable
    if not config['ANTHROPIC_API_KEY']:
        config['ANTHROPIC_API_KEY'] = os.getenv('ANTHROPIC_API_KEY')
    
    return config

# Load on import
CONFIG = load_config()

