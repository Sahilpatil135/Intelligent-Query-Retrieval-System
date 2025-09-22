import requests

url = "http://127.0.0.1:5000/query"
payload = {"query": "Define vulnerability", "top_k": 3}

res = requests.post(url, json=payload)
print(res.json())
