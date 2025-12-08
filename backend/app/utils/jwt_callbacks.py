from flask_jwt_extended import verify_jwt_in_request
from app.models import User

# 存储已撤销的token
token_blocklist = set()

def register_jwt_callbacks(jwt):
    """注册JWT回调函数"""
    
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        """将用户对象转换为身份标识"""
        # 如果已经是ID（整数），直接返回
        if isinstance(user, int):
            return user
        # 否则返回用户对象的ID属性
        return user.id
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        """根据身份标识查找用户"""
        identity = jwt_data["sub"]
        return User.query.get(identity)
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        """token过期回调"""
        return {
            'code': 401,
            'message': 'Token已过期',
            'success': False,
            'data': None
        }, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """无效token回调"""
        return {
            'code': 401,
            'message': '无效的Token',
            'success': False,
            'data': None
        }, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """缺少token回调"""
        return {
            'code': 401,
            'message': '缺少Token',
            'success': False,
            'data': None
        }, 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_data):
        """撤销token回调"""
        return {
            'code': 401,
            'message': 'Token已被撤销',
            'success': False,
            'data': None
        }, 401
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(_jwt_header, jwt_data):
        """检查token是否在黑名单中"""
        jti = jwt_data['jti']
        return jti in token_blocklist