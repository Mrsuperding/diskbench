# 任务状态查询脚本
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 创建一个临时的app.py文件副本，避免导入冲突
temp_app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_app.py")

# 读取原始app.py文件内容
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py"), "r", encoding="utf-8") as f:
    app_content = f.read()

# 修改导入语句，避免循环导入
app_content = app_content.replace("from app.models import db", "from models import db")

# 保存修改后的内容到临时文件
with open(temp_app_path, "w", encoding="utf-8") as f:
    f.write(app_content)

# 导入临时文件中的app实例
try:
    import importlib.util
    
    # 指定temp_app.py文件的路径
    spec = importlib.util.spec_from_file_location("temp_app", temp_app_path)
    temp_app = importlib.util.module_from_spec(spec)
    sys.modules["temp_app"] = temp_app
    spec.loader.exec_module(temp_app)
    
    # 获取app实例
    app = temp_app.app
    
    # 导入模型
    from app.models.test_task import TestTask
    
    with app.app_context():
        # 查询任务ID为3的状态
        task = TestTask.query.get(3)
        if task:
            print(f'Task ID: {task.id}')
            print(f'Task Name: {task.name}')
            print(f'Task Status: {task.status}')
            print(f'Task Created At: {task.created_at}')
            print(f'Task Started At: {task.started_at}')
            print(f'Task Completed At: {task.completed_at}')
        else:
            print('Task with ID 3 not found')
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    # 删除临时文件
    if os.path.exists(temp_app_path):
        os.remove(temp_app_path)