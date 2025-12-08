import requests
import json

# API base URL
BASE_URL = 'http://localhost:5000/api'

# Login credentials
credentials = {
    'username': 'admin',
    'password': 'adminpassword'
}

# Login and get token
print("Logging in...")
login_response = requests.post(f'{BASE_URL}/auth/login', json=credentials)
print(f"Login status code: {login_response.status_code}")
print(f"Login response: {json.dumps(login_response.json(), indent=2, ensure_ascii=False)}")

# Try to use the token to access nodes API
if login_response.status_code == 200:
    login_data = login_response.json()
    token = login_data['data']['refresh_token']  # Using refresh_token directly
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("\nTesting token with nodes API...")
    nodes_response = requests.get(f'{BASE_URL}/nodes', headers=headers)
    print(f"Nodes API status code: {nodes_response.status_code}")
    print(f"Nodes API response: {json.dumps(nodes_response.json(), indent=2, ensure_ascii=False)}")