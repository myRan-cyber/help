import os
import subprocess
import re
import logging
from datetime import datetime

# 配置日志设置（保持不变）
def setup_logger():
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f'daf_processing_{timestamp}.log')

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logger()

# 文件路径保持不变
data_graph_file = '/home/myran/FaSTest_backup/FaSTest/dataset/human/human.graph'
query_graph_folder = '/home/myran/FaSTest_backup/FaSTest/dataset/human/query_graph/'
output_file = '/home/myran/FaSTest_backup/FaSTest/dataset/human/human_ans.txt'

# 修改后的排序函数
def get_sort_key(filename):
    # 调整正则表达式匹配模式
    match = re.match(r'query_(dense|sparse)_(\d+)_(\d+)\.graph', filename)
    if match:
        category = match.group(1)  # 类型：dense/sparse
        group_num = int(match.group(2))  # 组号（4,8,12...）
        file_num = int(match.group(3))   # 文件编号（1-200）
        
        # 优先按类别排序（dense在前），然后按组号升序，最后文件号升序
        return (0 if category == 'dense' else 1, group_num, file_num)
    return (2, 0, 0)  # 无法识别的文件类型排最后

try:
    # 获取并排序文件列表
    query_graph_files = sorted(
        [f for f in os.listdir(query_graph_folder) if f.endswith('.graph')],
        key=get_sort_key
    )
except Exception as e:
    logger.exception("获取查询文件列表时发生错误")
    raise

# 后续处理逻辑保持不变...
with open(output_file, 'w') as out_file:
    for query_graph in query_graph_files:
        query_graph_path = os.path.join(query_graph_folder, query_graph)
        logger.info(f"开始处理: {query_graph}")
        
        command = ["./DAF", "-d", data_graph_file, "-q", query_graph_path]
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=600)
            
            # 调试日志保持不变...
            logger.debug(f"{query_graph} 标准输出:\n{result.stdout}")
            if result.stderr:
                logger.debug(f"{query_graph} 标准错误:\n{result.stderr}")

            # 解析结果保持不变...
            total_time_match = re.search(r'Total time:\s*(\d+\.?\d*)', result.stdout)
            matches_match = re.search(r'#Matches:\s*(\d+)', result.stdout)
            
            if total_time_match and matches_match:
                total_time = float(total_time_match.group(1))
                matches = int(matches_match.group(1))
                formatted_time = f"{total_time:.2f}"
                out_file.write(f"{query_graph} {formatted_time}ms {matches}\n")
                logger.info(f"成功处理: {query_graph} - 时间: {formatted_time}ms 匹配数: {matches}")
            else:
                error_msg = f"解析失败: {query_graph}"
                logger.error(error_msg)
                logger.debug(f"原始输出内容:\n{result.stdout}")
                out_file.write(f"{query_graph} ERROR\n")
                
        except subprocess.TimeoutExpired:
            error_msg = f"处理超时: {query_graph} (超过600秒)"
            logger.error(error_msg)
            out_file.write(f"{query_graph} TIMEOUT\n")
        except Exception as e:
            error_msg = f"处理异常: {query_graph} - {str(e)}"
            logger.exception(error_msg)
            out_file.write(f"{query_graph} ERROR\n")
            
        out_file.flush()

logger.info("处理任务全部完成")