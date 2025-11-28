"""
檢查敏感資訊是否被誤提交
"""
import os
import sys

SENSITIVE_PATTERNS = [
    "sk-",  # OpenAI API Key
    "AZURE_OPENAI_API_KEY",
    "password",
    "secret",
]

def check_file(filepath):
    """檢查檔案是否包含敏感資訊"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            for pattern in SENSITIVE_PATTERNS:
                if pattern in content and not filepath.endswith('.example'):
                    print(f"⚠️ 警告：{filepath} 可能包含敏感資訊：{pattern}")
                    return True
    except:
        pass
    return False

if __name__ == "__main__":
    # 檢查常見檔案
    files_to_check = [
        "backend/app.py",
        "backend/config.py",
        "backend/.env",
    ]
    
    has_sensitive = False
    for file in files_to_check:
        if os.path.exists(file):
            if check_file(file):
                has_sensitive = True
    
    if has_sensitive:
        print("\n❌ 發現敏感資訊！請檢查後再提交。")
        sys.exit(1)
    else:
        print("✅ 未發現敏感資訊，可以安全提交。")
