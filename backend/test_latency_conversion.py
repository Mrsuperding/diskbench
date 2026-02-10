# 测试延迟转换函数

def test_convert_lat():
    """测试延迟转换函数"""
    # 模拟convert_lat函数
    def convert_lat(lat_str):
        try:
            lat_val = float(lat_str.strip())
            
            # 检查值的范围和格式
            if lat_val < 0.1:
                # 如果值小于0.1，很可能是秒级，转换为毫秒
                return lat_val * 1000
            elif lat_val < 1000:
                # 如果值在0.1-1000之间，直接返回（已经是毫秒）
                return lat_val
            elif lat_val < 1000000:
                # 如果值在1000-1000000之间，可能是微秒，转换为毫秒
                return lat_val / 1000
            else:
                # 否则是纳秒，转换为毫秒
                return lat_val / 1000000
        except:
            return 0.0
    
    # 测试各种情况
    test_cases = [
        "0.001688",  # 秒级小数
        "0.03649203",  # 秒级小数
        "1688",  # 微秒
        "1688000",  # 纳秒
        "1.688",  # 毫秒
        "0",  # 零值
        "",  # 空字符串
    ]
    
    print("测试延迟转换函数:")
    for test_case in test_cases:
        result = convert_lat(test_case)
        print(f"{test_case} -> {result} ms")

if __name__ == "__main__":
    test_convert_lat()
