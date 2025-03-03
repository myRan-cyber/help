import os
import re
import logging
from datetime import datetime

# 配置简易日志
def setup_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    
    logger.addHandler(console_handler)
    return logger

logger = setup_logger()

# 文件路径配置
query_graph_folder = '/home/myran/FaSTest_backup/FaSTest/dataset/human/query_graph/'
output_file = '/home/myran/FaSTest_backup/FaSTest/dataset/human/human_ans.txt'


def sorting_key(filename):
    match = re.match(r'query_(dense|sparse)_(\d+)_(\d+)\.graph', filename)
    if match:
        category = match.group(1)
        group_num = int(match.group(2))
        file_num = int(match.group(3))
        return (0 if category == 'dense' else 1, group_num, file_num)
    return (2, 0, 0)

try:
    # 获取并排序文件列表
    files = sorted(
        [f for f in os.listdir(query_graph_folder) if f.endswith('.graph')],
        key=sorting_key
    )
    
    # 写入结果文件
    with open(output_file, 'w') as f:
        f.write('\n'.join(files))
        
    logger.info(f"成功生成排序文件列表，共 {len(files)} 个文件")
    logger.info(f"输出文件路径：{output_file}")

except Exception as e:
    logger.error(f"处理失败: {str(e)}")
    raise

