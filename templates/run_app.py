import subprocess
import os
import sys

def check_ollama():
    print("Checking Ollama status...")
    try:
        # Verify Llama3 is available
        subprocess.run(["ollama", "pull", "llama3"], check=True)
        print("✅ Ollama is ready.")
    except Exception:
        print("❌ Error: Ollama is not running. Please start the Ollama desktop app.")
        sys.exit(1)

def init_db():
    print("Initializing Database...")
    from server import app, db
    with app.app_context():
        db.create_all()
    print("✅ Database (career_ai.db) is ready.")

if __name__ == "__main__":
    check_ollama()
    init_db()
    print("🚀 Launching AI Career Assistant...")
    subprocess.run(["python", "server.py"])