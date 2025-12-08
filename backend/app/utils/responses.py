from flask import jsonify

def success_response(data=None, message='Success', code=200):
    """成功响应"""
    response = {
        'code': code,
        'message': message,
        'data': data,
        'success': True
    }
    return jsonify(response), code

def error_response(message='Error', code=400, data=None):
    """错误响应"""
    response = {
        'code': code,
        'message': message,
        'data': data,
        'success': False
    }
    return jsonify(response), code

def paginated_response(data, pagination, message='Success'):
    """分页响应"""
    response = {
        'code': 200,
        'message': message,
        'success': True,
        'data': {
            'items': data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        }
    }
    return jsonify(response), 200

def validation_error(errors, message='Validation failed'):
    """验证错误响应"""
    return error_response(message, 422, {'errors': errors})

def unauthorized_response(message='Unauthorized'):
    """未授权响应"""
    return error_response(message, 401)

def forbidden_response(message='Forbidden'):
    """禁止访问响应"""
    return error_response(message, 403)

def not_found_response(message='Not found'):
    """未找到响应"""
    return error_response(message, 404)

def server_error_response(message='Internal server error'):
    """服务器错误响应"""
    return error_response(message, 500)