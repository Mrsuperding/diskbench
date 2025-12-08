# 测试任务多节点功能的PowerShell脚本

# 登录信息
$baseUrl = "http://localhost:5000/api"
$username = "admin"
$password = "adminpassword"

# 登录获取JWT令牌
Write-Host "正在登录..."
$loginResponse = Invoke-WebRequest -Uri "$baseUrl/auth/login" -Method POST -Body (@{username=$username; password=$password} | ConvertTo-Json) -ContentType "application/json"
$loginData = $loginResponse.Content | ConvertFrom-Json
$token = $loginData.refresh_token
Write-Host "登录成功，获取到令牌：$token"

# 获取节点列表
Write-Host "\n获取节点列表..."
$nodesResponse = Invoke-WebRequest -Uri "$baseUrl/nodes" -Method GET -Headers @{"Authorization"="Bearer $token"}
$nodes = $nodesResponse.Content | ConvertFrom-Json
Write-Host "可用节点："
$nodes | ForEach-Object { Write-Host "  ID: $($_.id), 名称: $($_.name)" }

# 确保有至少2个节点用于测试
if ($nodes.Count -lt 2) {
    Write-Host "\n错误：需要至少2个节点来测试多节点功能！"
    exit 1
}

# 获取测试用例列表
Write-Host "\n获取测试用例列表..."
$casesResponse = Invoke-WebRequest -Uri "$baseUrl/io-test-cases" -Method GET -Headers @{"Authorization"="Bearer $token"}
$cases = $casesResponse.Content | ConvertFrom-Json
Write-Host "可用测试用例："
$cases | ForEach-Object { Write-Host "  ID: $($_.id), 名称: $($_.name)" }

# 确保有至少1个测试用例用于测试
if ($cases.Count -lt 1) {
    Write-Host "\n错误：需要至少1个测试用例来创建任务！"
    exit 1
}

# 创建任务（使用前2个节点）
Write-Host "\n创建测试任务（使用节点1和节点2）..."
$taskData = @{
    name = "测试多节点任务"
    description = "这是一个测试多节点功能的任务"
    node_ids = @($nodes[0].id, $nodes[1].id)
    io_test_case_ids = @($cases[0].id)
}
$createResponse = Invoke-WebRequest -Uri "$baseUrl/tasks" -Method POST -Body ($taskData | ConvertTo-Json) -ContentType "application/json" -Headers @{"Authorization"="Bearer $token"}
$createdTask = $createResponse.Content | ConvertFrom-Json
Write-Host "任务创建成功："
Write-Host "  ID: $($createdTask.id)"
Write-Host "  名称: $($createdTask.name)"
Write-Host "  节点ID: $($createdTask.node_ids -join ", ")"

# 编辑任务（添加第3个节点，如果有的话）
if ($nodes.Count -ge 3) {
    Write-Host "\n编辑任务（添加第3个节点）..."
    $updateData = @{
        node_ids = @($nodes[0].id, $nodes[1].id, $nodes[2].id)
    }
    $updateResponse = Invoke-WebRequest -Uri "$baseUrl/tasks/$($createdTask.id)" -Method PUT -Body ($updateData | ConvertTo-Json) -ContentType "application/json" -Headers @{"Authorization"="Bearer $token"}
    $updatedTask = $updateResponse.Content | ConvertFrom-Json
    Write-Host "任务更新成功："
    Write-Host "  节点ID: $($updatedTask.node_ids -join ", ")"
}

# 获取任务详情
Write-Host "\n获取任务详情..."
$detailResponse = Invoke-WebRequest -Uri "$baseUrl/tasks/$($createdTask.id)" -Method GET -Headers @{"Authorization"="Bearer $token"}
$taskDetail = $detailResponse.Content | ConvertFrom-Json
Write-Host "任务详情："
Write-Host "  ID: $($taskDetail.id)"
Write-Host "  名称: $($taskDetail.name)"
Write-Host "  描述: $($taskDetail.description)"
Write-Host "  节点ID: $($taskDetail.node_ids -join ", ")"
Write-Host "  测试用例: $($taskDetail.io_test_cases -join ", ")"
Write-Host "  创建时间: $($taskDetail.created_at)"
Write-Host "  更新时间: $($taskDetail.updated_at)"

Write-Host "\n测试完成！任务多节点功能正常工作。"