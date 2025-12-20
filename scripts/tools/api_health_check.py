import subprocess

print("=== API ENDPOINT HEALTH CHECK ===")

# Health
result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:5000/api/health'], capture_output=True, text=True)
print(f"GET /api/health: {result.stdout.strip()} (expected 200)")

# Languages  
result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:5000/api/languages'], capture_output=True, text=True)
print(f"GET /api/languages: {result.stdout.strip()} (expected 200)")

# Search Polish
result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:5000/api/search?q=test&lang=pl&limit=1'], capture_output=True, text=True)
print(f"GET /api/search (pl): {result.stdout.strip()} (expected 200)")

# Search English
result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:5000/api/search?q=test&lang=en&limit=1'], capture_output=True, text=True)
print(f"GET /api/search (en): {result.stdout.strip()} (expected 200)")

# Invalid language
result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:5000/api/search?q=test&lang=xx&limit=1'], capture_output=True, text=True)
print(f"GET /api/search (invalid lang): {result.stdout.strip()} (expected 400)")
