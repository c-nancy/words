import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
from scripts.word import app

if __name__ == "__main__":
    app.launch()