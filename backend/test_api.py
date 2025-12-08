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
if login_response.status_code != 200:
    print(f"Login failed: {login_response.text}")
    exit(1)

login_data = login_response.json()
token = login_data['data']['token']  # Using access token instead of refresh token
print(f"Login successful, access token obtained: {token}")

# Headers for authenticated requests
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Get nodes
print("\nGetting node list...")
nodes_response = requests.get(f'{BASE_URL}/nodes', headers=headers)
if nodes_response.status_code != 200:
    print(f"Failed to get nodes: {nodes_response.text}")
    exit(1)

nodes_data = nodes_response.json()['data']
print(f"Available nodes ({len(nodes_data)}):")
for node in nodes_data:
    print(f"  ID: {node['id']}, Name: {node['name']}, IP: {node['ip_address']}")

# Check if we have enough nodes to test
if len(nodes_data) < 2:
    print("\nError: Need at least 2 nodes to test multi-node functionality!")
    exit(1)

# First, let's try to get existing test cases
print("\nGetting test case list...")
test_cases_response = requests.get(f'{BASE_URL}/io-cases', headers=headers)

created_test_case = None
if test_cases_response.status_code == 200:
    test_cases = test_cases_response.json()['data']
    print(f"Found {len(test_cases)} test cases")
    
    # Check if our test case already exists
    for test_case in test_cases:
        if test_case['name'] == 'Multi-node Test Case':
            created_test_case = test_case
            print(f"Using existing test case: ID={test_case['id']}")
            break

# If test case doesn't exist, create it
if not created_test_case:
    print("\nCreating a test case...")
    test_case_data = {
        'name': 'Multi-node Test Case',
        'description': 'Test case for multi-node task testing',
        'tool': 'fio',
        'parameters': {'rw': 'read', 'size': '1G', 'bs': '4k'},
        'is_public': True
    }
    
    test_case_response = requests.post(f'{BASE_URL}/io-cases', json=test_case_data, headers=headers)
    # 201表示资源创建成功，也是有效的状态码
    if test_case_response.status_code not in [200, 201]:
        print(f"Failed to create test case: {test_case_response.text}")
        exit(1)
    
    created_test_case = test_case_response.json()['data']
    print(f"Test case created successfully: ID={created_test_case['id']}")

# Now create a task with multiple nodes
print("\nCreating task with multiple nodes...")
task_data = {
    'name': 'Multi-node Test Task',
    'description': 'This is a test task with multiple nodes',
    'node_ids': [nodes_data[0]['id'], nodes_data[1]['id']],
    'io_test_case_ids': [created_test_case['id']]
}

create_response = requests.post(f'{BASE_URL}/tasks', json=task_data, headers=headers)
print(f"Task creation response status code: {create_response.status_code}")
print(f"Task creation response headers: {create_response.headers}")
print(f"Task creation response content: {create_response.text}")
if create_response.status_code not in [200, 201]:
    print("Failed to create task!")
    exit(1)

created_task = create_response.json()['data']
print(f"Task created successfully:")
print(f"  ID: {created_task['id']}")
print(f"  Name: {created_task['name']}")
print(f"  Description: {created_task['description']}")
print(f"  Node IDs: {created_task['node_ids']}")
print(f"  Test Cases: {created_task['io_test_case_ids']}")

# Get task details
print("\nGetting task details...")
detail_response = requests.get(f'{BASE_URL}/tasks/{created_task['id']}', headers=headers)
if detail_response.status_code != 200:
    print(f"Failed to get task details: {detail_response.text}")
    exit(1)

task_detail = detail_response.json()['data']
print(f"Task details retrieved successfully:")
print(f"  Node IDs: {task_detail['node_ids']}")

# Update task - add another node if available
if len(nodes_data) >= 3:
    print("\nUpdating task - adding 3rd node...")
    update_data = {
        'node_ids': [nodes_data[0]['id'], nodes_data[1]['id'], nodes_data[2]['id']]
    }
    
    update_response = requests.put(f'{BASE_URL}/tasks/{created_task['id']}', json=update_data, headers=headers)
    if update_response.status_code != 200:
        print(f"Failed to update task: {update_response.text}")
        exit(1)
    
    updated_task = update_response.json()['data']
    print(f"Task updated successfully:")
    print(f"  New Node IDs: {updated_task['node_ids']}")

print("\nAll tests passed! Multi-node task functionality is working correctly.")