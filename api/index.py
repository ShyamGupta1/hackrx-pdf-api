# api/index.py - Vercel API handler
from main import app

# Export the FastAPI app for Vercel
def handler(request):
    return app(request)

# Alternative export (try this if above doesn't work)
application = app
