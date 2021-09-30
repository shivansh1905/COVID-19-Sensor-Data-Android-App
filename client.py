import requests
with open('server.py', 'rb') as f:
    r = requests.post('http://localhost:5000/upload', files = {'file': f})
print(r.content.decode('utf-8'))