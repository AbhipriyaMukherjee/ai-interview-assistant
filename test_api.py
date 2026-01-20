import requests
import json

url = "http://127.0.0.1:5000/generate-questions"

payload = {
    "profile": {
        "skills": ["Python", "Django", "REST APIs"],
        "summary": "2 years backend developer experience"
    },
    "domain": "backend developer",
    "n": 3
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, data=json.dumps(payload), headers=headers)

print("STATUS:", response.status_code)
print("RESPONSE:")
print(response.text)
