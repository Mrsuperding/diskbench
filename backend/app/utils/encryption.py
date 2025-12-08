import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class EncryptionManager:
    """加密管理器"""
    
    def __init__(self):
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self):
        """获取或创建加密密钥"""
        key_file = 'encryption.key'
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # 生成新密钥
            password = os.environ.get('ENCRYPTION_PASSWORD', 'default-password').encode()
            salt = os.environ.get('ENCRYPTION_SALT', 'default-salt').encode()
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            
            # 保存密钥
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # 设置文件权限（仅所有者可读写）
            os.chmod(key_file, 0o600)
            
            return key
    
    def encrypt(self, data):
        """加密数据"""
        if not data:
            return None
        
        if isinstance(data, str):
            data = data.encode()
        
        encrypted = self.cipher.encrypt(data)
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data):
        """解密数据"""
        if not encrypted_data:
            return None
        
        try:
            encrypted = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            print(f"Decryption error: {e}")
            return None

# 创建全局加密管理器实例
encryption_manager = EncryptionManager()

def encrypt_password(password):
    """加密密码"""
    return encryption_manager.encrypt(password)

def decrypt_password(encrypted_password):
    """解密密码"""
    return encryption_manager.decrypt(encrypted_password)

def encrypt_data(data):
    """加密通用数据"""
    return encryption_manager.encrypt(data)

def decrypt_data(encrypted_data):
    """解密通用数据"""
    return encryption_manager.decrypt(encrypted_data)