from dotenv import load_dotenv
import os

load_dotenv()
key = os.getenv("OPENAI_API_KEY")
print("API key found:", "YES" if key else "NO")
if key:
    print("Key preview:", key[:20] + "..." if key else "None")
else:
    print(".env not loading - check file format/location")
