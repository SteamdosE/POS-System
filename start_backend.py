import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from app import app

if __name__ == "__main__":
    app.run(debug=True, port=5000)
