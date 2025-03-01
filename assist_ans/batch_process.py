import os
import subprocess
import re
import logging
from datetime import datetime

# 配置日志设置
def setup_logger():
    # 创建日志目录（如果不存在）
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 生成带时间戳的日志文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f'daf_processing_{timestamp}.log')

    # 创建 logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # 创建控制台处理器（INFO级别）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # 创建文件处理器（DEBUG级别）
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # 添加处理器到logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# 初始化日志记录器
logger = setup_logger()

# 其他配置保持不变...
data_graph_file = '/home/graph/youtube/youtube.graph'
query_graph_folder = '/home/graph/youtube/query_graph_batches/batch_2/'
output_file = '/home/graph/youtube/query_graph_batches/batch_2_ans.txt'

# 获取所有的查询图文件，并按文件名中的类别和数字部分进行排序
def get_sort_key(filename):
    # 使用正则表达式提取文件名中的类别（如query_dense_4_）和数字部分（如1，2，3...）
    match = re.match(r'(query_(dense|sparse)_(\d+))_(\d+).graph', filename)
    if match:
        # 提取类别（dense/sparse），数字部分（4,8,16,32等），和文件中的数字部分（1到200）
        prefix = match.group(1)  # query_dense_4_，query_dense_8_，query_sparse_4_ 等
        group_number = int(match.group(3))  # 4, 8, 16, 32
        file_number = int(match.group(4))  # 1到200
        
        # 我们可以返回一个元组，让系统首先按文件的类别和组号排序，接着按文件号排序
        return (prefix, group_number, file_number)
    return (filename, 0, 0)  # 默认返回值


try:
    query_graph_files = sorted([f for f in os.listdir(query_graph_folder) if f.endswith('.graph')],
                               key=get_sort_key)
except Exception as e:
    logger.exception("获取查询文件列表时发生错误")
    raise

with open(output_file, 'w') as out_file:
    for query_graph in query_graph_files:
        query_graph_path = os.path.join(query_graph_folder, query_graph)
        logger.info(f"开始处理: {query_graph}")
        
        command = ["./DAF", "-d", data_graph_file, "-q", query_graph_path]
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=600)
            
            # 记录调试信息
            logger.debug(f"{query_graph} 标准输出:\n{result.stdout}")
            if result.stderr:
                logger.debug(f"{query_graph} 标准错误:\n{result.stderr}")

            # 解析结果
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