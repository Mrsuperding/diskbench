# Test script for multi-node task functionality

# Login information
$baseUrl = "http://localhost:5000/api"
$username = "admin"
$password = "adminpassword"

# Login and get JWT token
Write-Host "Logging in..."
$loginResponse = Invoke-WebRequest -Uri "$baseUrl/auth/login" -Method POST -Body (@{username=$username; password=$password} | ConvertTo-Json) -ContentType "application/json"
$loginData = $loginResponse.Content | ConvertFrom-Json
$token = $loginData.refresh_token
Write-Host "Login successful, token: $token"

# Get node list
Write-Host "\nGetting node list..."
$nodesResponse = Invoke-WebRequest -Uri "$baseUrl/nodes" -Method GET -Headers @{"Authorization"="Bearer $token"}
$nodes = $nodesResponse.Content | ConvertFrom-Json
Write-Host "Available nodes:"
$nodes | ForEach-Object { Write-Host "  ID: $($_.id), Name: $($_.name)" }

# Check if we have at least 2 nodes
if ($nodes.Count -lt 2) {
    Write-Host "\nError: Need at least 2 nodes for testing!"
    exit 1
}

# Get test cases
Write-Host "\nGetting test cases..."
$casesResponse = Invoke-WebRequest -Uri "$baseUrl/io-test-cases" -Method GET -Headers @{"Authorization"="Bearer $token"}
$cases = $casesResponse.Content | ConvertFrom-Json
Write-Host "Available test cases:"
$cases | ForEach-Object { Write-Host "  ID: $($_.id), Name: $($_.name)" }

# Check if we have at least 1 test case
if ($cases.Count -lt 1) {
    Write-Host "\nError: Need at least 1 test case for testing!"
    exit 1
}

# Create a new task with 2 nodes
Write-Host "\nCreating new task with 2 nodes..."
$taskData = @{
    name = "Test Multi-node Task"
    description = "This is a test task with multiple nodes"
    node_ids = @($nodes[0].id, $nodes[1].id)
    io_test_case_ids = @($cases[0].id)
}

try {
    $createResponse = Invoke-WebRequest -Uri "$baseUrl/tasks" -Method POST -Body ($taskData | ConvertTo-Json) -ContentType "application/json" -Headers @{"Authorization"="Bearer $token"}
    $createdTask = $createResponse.Content | ConvertFrom-Json
    Write-Host "Task created successfully:"
    Write-Host "  ID: $($createdTask.id)"
    Write-Host "  Name: $($createdTask.name)"
    Write-Host "  Node IDs: $($createdTask.node_ids -join ", ")"
} catch {
    Write-Host "Error creating task:"
    Write-Host $_.Exception.Message
    exit 1
}

# Get task details
Write-Host "\nGetting task details..."
try {
    $detailResponse = Invoke-WebRequest -Uri "$baseUrl/tasks/$($createdTask.id)" -Method GET -Headers @{"Authorization"="Bearer $token"}
    $taskDetail = $detailResponse.Content | ConvertFrom-Json
    Write-Host "Task details:"
    Write-Host "  ID: $($taskDetail.id)"
    Write-Host "  Name: $($taskDetail.name)"
    Write-Host "  Description: $($taskDetail.description)"
    Write-Host "  Node IDs: $($taskDetail.node_ids -join ", ")"
    Write-Host "  Test Cases: $($taskDetail.io_test_cases -join ", ")"
} catch {
    Write-Host "Error getting task details:"
    Write-Host $_.Exception.Message
    exit 1
}

# Update task - add more nodes if available
if ($nodes.Count -ge 3) {
    Write-Host "\nUpdating task - adding 3rd node..."
    $updateData = @{
        node_ids = @($nodes[0].id, $nodes[1].id, $nodes[2].id)
    }
    
    try {
        $updateResponse = Invoke-WebRequest -Uri "$baseUrl/tasks/$($createdTask.id)" -Method PUT -Body ($updateData | ConvertTo-Json) -ContentType "application/json" -Headers @{"Authorization"="Bearer $token"}
        $updatedTask = $updateResponse.Content | ConvertFrom-Json
        Write-Host "Task updated successfully:"
        Write-Host "  New Node IDs: $($updatedTask.node_ids -join ", ")"
    } catch {
        Write-Host "Error updating task:"
        Write-Host $_.Exception.Message
        exit 1
    }
}

Write-Host "\nAll tests completed successfully!"