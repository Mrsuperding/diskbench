#!/usr/bin/env python3
"""
测试执行任务56并捕获详细错误信息
"""

import sys
import os
import logging
import traceback
import time
import json

# 添加backend目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('task_56_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 全局应用实例
app_instance = None

# 初始化应用实例
def init_app():
    """初始化应用实例"""
    global app_instance
    if app_instance is None:
        import sys
        import os
        import importlib.util
        
        # 确保backend目录在Python路径中
        backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        # 直接导入app.py文件
        app_py_path = os.path.join(backend_path, 'app.py')
        spec = importlib.util.spec_from_file_location("app_module", app_py_path)
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        
        app_instance = app_module.app
    return app_instance

def get_task_56_info():
    """获取任务56的详细信息"""
    logger.info("获取任务56的详细信息")
    try:
        # 初始化应用实例
        app = init_app()
        
        with app.app_context():
            from app.models import db, TestTask, IOTestCase, Node
            from sqlalchemy import text
            
            # 获取任务信息
            task = TestTask.query.get(56)
            if not task:
                logger.error("任务56不存在")
                return None
            
            logger.info(f"任务56信息: 名称={task.name}, 状态={task.status}, 创建时间={task.created_at}")
            
            # 获取任务关联的节点
            nodes = task.nodes
            logger.info(f"任务关联的节点数量: {len(nodes)}")
            for node in nodes:
                logger.info(f"节点信息: id={node.id}, 名称={node.name}, IP={node.ip_address}")
                if node.login_credential:
                    logger.info(f"  登录凭证: id={node.login_credential.id}, 别名={node.login_credential.alias}, 主机={node.login_credential.host}")
                else:
                    logger.warning(f"  节点 {node.name} 没有关联登录凭证")
                if node.io_partitions:
                    logger.info(f"  IO分区: {node.io_partitions}")
                else:
                    logger.warning(f"  节点 {node.name} 没有配置IO分区")
            
            # 获取任务关联的IO测试用例
            case_ids = db.session.execute(
                text('SELECT io_test_case_id FROM task_case_association WHERE test_task_id = :task_id'),
                {'task_id': 56}
            ).fetchall()
            io_test_case_ids = [case_id[0] for case_id in case_ids]
            io_test_cases = IOTestCase.query.filter(IOTestCase.id.in_(io_test_case_ids)).all()
            logger.info(f"任务关联的IO测试用例数量: {len(io_test_cases)}")
            for io_test_case in io_test_cases:
                logger.info(f"IO测试用例信息: id={io_test_case.id}, 名称={io_test_case.name}, 工具={io_test_case.tool}")
                logger.info(f"  参数: {json.dumps(io_test_case.parameters, indent=2)}")
            
            return {
                'task': task,
                'nodes': nodes,
                'io_test_cases': io_test_cases
            }
    except Exception as e:
        logger.error(f"获取任务56信息失败: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def test_task_56_execution_api():
    """使用API测试执行任务56"""
    logger.info("开始使用API测试执行任务56")
    
    try:
        # 初始化应用实例
        app = init_app()
        
        # 创建测试客户端
        client = app.test_client()
        
        # 模拟登录
        logger.info("模拟登录...")
        login_data = {
            'username': 'admin',
            'password': 'adminpassword'
        }
        login_response = client.post('/api/auth/login', json=login_data)
        logger.info(f"登录响应状态码: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.get_json()
            access_token = login_result.get('data', {}).get('access_token')
            logger.info("登录成功，获取到访问令牌")
        else:
            logger.warning("登录失败，使用匿名访问")
            access_token = None
        
        # 执行任务56
        logger.info("执行任务56...")
        headers = {}
        if access_token:
            headers['Authorization'] = f'Bearer {access_token}'
        
        # 发送执行任务请求
        execute_response = client.post('/api/tasks/56/execute', headers=headers)
        logger.info(f"执行任务响应状态码: {execute_response.status_code}")
        response_json = execute_response.get_json()
        logger.info(f"执行任务响应内容: {json.dumps(response_json, indent=2)}")
        
        if execute_response.status_code == 200:
            logger.info("任务执行请求发送成功")
            # 等待任务执行完成
            logger.info("等待任务执行完成...")
            time.sleep(60)  # 等待60秒让任务有时间执行
            
            # 查询任务状态
            logger.info("查询任务状态...")
            status_response = client.get('/api/tasks/56', headers=headers)
            logger.info(f"查询任务状态响应状态码: {status_response.status_code}")
            if status_response.status_code == 200:
                task_status = status_response.get_json()
                logger.info(f"任务状态: {task_status.get('data', {}).get('status')}")
                logger.info(f"任务详细信息: {json.dumps(task_status, indent=2)}")
            
            # 查询任务执行记录
            logger.info("查询任务执行记录...")
            executions_response = client.get('/api/tasks/56/executions', headers=headers)
            logger.info(f"查询执行记录响应状态码: {executions_response.status_code}")
            if executions_response.status_code == 200:
                executions = executions_response.get_json()
                logger.info(f"执行记录: {json.dumps(executions, indent=2)}")
            
            # 查询任务结果
            logger.info("查询任务结果...")
            results_response = client.get('/api/tasks/56/results', headers=headers)
            logger.info(f"查询结果响应状态码: {results_response.status_code}")
            if results_response.status_code == 200:
                results = results_response.get_json()
                logger.info(f"任务结果: {json.dumps(results, indent=2)}")
            
            # 查询任务日志
            logger.info("查询任务日志...")
            logs_response = client.get('/api/tasks/56/logs', headers=headers)
            logger.info(f"查询日志响应状态码: {logs_response.status_code}")
            if logs_response.status_code == 200:
                logs = logs_response.get_json()
                logger.info(f"任务日志: {json.dumps(logs, indent=2)}")
        else:
            logger.error(f"执行任务失败: {json.dumps(response_json, indent=2)}")
        
        logger.info("使用API测试任务56执行完成")
        return True
        
    except Exception as e:
        logger.error(f"使用API测试任务56执行失败: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def direct_test_run_task_execution():
    """直接测试run_task_execution函数"""
    logger.info("开始直接测试run_task_execution函数")
    
    try:
        # 初始化应用实例
        app = init_app()
        
        # 导入run_task_execution函数
        from app.views.tasks import run_task_execution
        
        # 导入模型
        from app.models import db, TaskExecution
        from datetime import datetime
        
        with app.app_context():
            # 创建任务执行记录
            task_execution = TaskExecution(
                test_task_id=56,
                status='running',
                start_time=datetime.utcnow()
            )
            db.session.add(task_execution)
            db.session.commit()
            
            logger.info(f"创建执行记录: execution_id={task_execution.id}")
            
            # 执行任务
            logger.info("执行run_task_execution函数...")
            try:
                run_task_execution(56, task_execution.id, app)
                logger.info("run_task_execution函数执行完成")
            except Exception as e:
                logger.error(f"run_task_execution函数执行异常: {str(e)}")
                logger.error(traceback.format_exc())
            
            # 查询执行结果
            updated_execution = TaskExecution.query.get(task_execution.id)
            logger.info(f"执行结果状态: {updated_execution.status}")
            logger.info(f"执行结果错误信息: {updated_execution.error_message}")
            
            # 查询任务状态
            from app.models import TestTask
            task = TestTask.query.get(56)
            logger.info(f"任务状态: {task.status}")
        
        logger.info("直接测试run_task_execution函数完成")
        return True
        
    except Exception as e:
        logger.error(f"直接测试run_task_execution函数失败: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def analyze_task_56_executions():
    """分析任务56的执行历史"""
    logger.info("开始分析任务56的执行历史")
    
    try:
        # 初始化应用实例
        app = init_app()
        
        with app.app_context():
            from app.models import db, TaskExecution, TestResult
            
            # 查询任务56的所有执行记录
            executions = TaskExecution.query.filter_by(test_task_id=56).order_by(TaskExecution.start_time.desc()).all()
            logger.info(f"任务56的执行记录数量: {len(executions)}")
            
            for execution in executions:
                logger.info(f"执行记录: id={execution.id}, 状态={execution.status}, 开始时间={execution.start_time}, 结束时间={execution.end_time}")
                logger.info(f"  错误信息: {execution.error_message}")
                
                # 查询该执行的测试结果
                results = TestResult.query.filter_by(task_execution_id=execution.id).all()
                logger.info(f"  测试结果数量: {len(results)}")
                for result in results:
                    logger.info(f"  结果: id={result.id}, 状态={result.status}, IO测试用例={result.io_test_case_id}, 节点={result.node_id}")
        
        logger.info("分析任务56的执行历史完成")
        return True
        
    except Exception as e:
        logger.error(f"分析任务56的执行历史失败: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # 检查是否只获取信息
    info_only = len(sys.argv) > 1 and sys.argv[1] == "--info-only"
    
    logger.info("=== 测试任务56执行 ===")
    
    # 获取任务56的详细信息
    logger.info("\n=== 获取任务56的详细信息 ===")
    task_info = get_task_56_info()
    
    # 分析任务56的执行历史
    logger.info("\n=== 分析任务56的执行历史 ===")
    analyze_task_56_executions()
    
    if info_only:
        logger.info("\n=== 信息获取完成 ===")
        logger.info("🎉 信息获取完成")
        exit(0)
    
    # 先尝试使用API执行任务
    logger.info("\n=== 使用API执行任务56 ===")
    api_success = test_task_56_execution_api()
    
    # 再尝试直接执行run_task_execution函数
    logger.info("\n=== 直接执行run_task_execution函数 ===")
    direct_success = direct_test_run_task_execution()
    
    # 再次分析执行结果
    logger.info("\n=== 分析执行结果 ===")
    analyze_task_56_executions()
    
    if api_success or direct_success:
        logger.info("🎉 测试完成")
    else:
        logger.error("💥 测试失败")
