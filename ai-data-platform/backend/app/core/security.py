import re
from app.core.config import settings

# 只读SQL关键字黑名单
READ_ONLY_BLACKLIST = [
    'INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE', 'ALTER',
    'CREATE', 'GRANT', 'REVOKE', 'EXECUTE', 'CALL', 'LOAD_FILE',
    'INTO OUTFILE', 'INTO DUMPFILE'
]

# 手机号脱敏正则
PHONE_PATTERN = re.compile(r'(1[3-9]\d)\d{4}(\d{4})')


def validate_read_only(sql: str) -> tuple[bool, str]:
    """
    验证SQL是否为只读查询
    返回: (是否通过, 错误信息)
    """
    if not sql or not sql.strip():
        return False, "SQL查询不能为空"

    upper_sql = sql.upper().strip()

    # 检查黑名单关键字
    for keyword in READ_ONLY_BLACKLIST:
        # 使用正则确保是完整单词匹配
        pattern = r'\b' + keyword + r'\b'
        if re.search(pattern, upper_sql):
            return False, f"检测到危险操作: {keyword}，仅支持只读查询(SELECT)"

    # 必须以SELECT开头
    if not upper_sql.startswith('SELECT'):
        return False, "仅支持SELECT查询"

    return True, ""


def mask_phone_numbers(text: str) -> str:
    """
    对文本中的手机号进行脱敏处理
    13812345678 -> 138****5678
    """
    return PHONE_PATTERN.sub(r'\1****\2', text)


def mask_phone_in_data(data: list[dict]) -> list[dict]:
    """
    对查询结果中的手机号字段进行脱敏
    """
    if not data:
        return data

    masked_data = []
    for row in data:
        masked_row = {}
        for key, value in row.items():
            # 检测字段名是否包含手机/电话相关
            key_lower = str(key).lower()
            if any(kw in key_lower for kw in ['phone', 'mobile', 'tel', '手机', '电话']):
                if value and isinstance(value, str):
                    masked_row[key] = mask_phone_numbers(value)
                else:
                    masked_row[key] = value
            else:
                # 对字符串值也进行手机号检测
                if isinstance(value, str):
                    masked_row[key] = mask_phone_numbers(value)
                else:
                    masked_row[key] = value
        masked_data.append(masked_row)

    return masked_data


def sanitize_sql(sql: str) -> str:
    """
    SQL清理: 去除危险字符，限制长度
    """
    # 去除注释
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
    sql = re.sub(r'--.*?$', '', sql, flags=re.MULTILINE)
    sql = re.sub(r'#.*?$', '', sql, flags=re.MULTILINE)

    # 去除多余空白
    sql = ' '.join(sql.split())

    # 限制长度
    max_length = 5000
    if len(sql) > max_length:
        raise ValueError(f"SQL查询过长，最大支持{max_length}字符")

    return sql.strip()
