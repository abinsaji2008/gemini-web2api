import sys
import os

# Add the project root to the Python path so Vercel can find the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the BaseHTTPRequestHandler class from the main script
import gemini_web2api

# Vercel recognizes a top-level BaseHTTPRequestHandler handler.
handler = gemini_web2api.GeminiHandler
