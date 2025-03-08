import os
import subprocess
import re
import logging
from datetime import datetime
import argparse

# 配置日志设置
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

# 参数解析函数
def parse_arguments():
    parser = argparse.ArgumentParser(description='处理查询图的脚本')
    parser.add_argument('--file_type', choices=['dense', 'sparse'], default=None,
                        help='处理文件类型:dense或sparse,默认处理所有')
    parser.add_argument('--groups', type=str, default=None,
                        help='指定组号列表,用逗号分隔,如4,8,12')
    parser.add_argument('--file_range', type=str, default='1-200',
                        help='文件编号范围,格式如1-200,默认1-200')
    # 新增输出文件参数
    parser.add_argument('--output', type=str, default='human_ans.txt',
                        help='输出文件名,默认human_ans.txt')
    parser.add_argument('--mode', choices=['w', 'a'], default='w',
                        help='写入模式:w覆盖(默认),a追加')
    
    args = parser.parse_args()
    
    # 解析groups
    groups = []
    if args.groups:
        try:
            groups = list(map(int, args.groups.split(',')))
        except ValueError:
            logger.error("groups参数必须是由逗号分隔的整数列表")
            raise
    
    # 解析file_range
    try:
        file_range_parts = args.file_range.split('-')
        if len(file_range_parts) != 2:
            raise ValueError("文件范围格式错误")
        file_start = int(file_range_parts[0])
        file_end = int(file_range_parts[1])
    except ValueError as e:
        logger.error(f"文件范围解析错误：{e}")
        raise

    return {
        'file_type': args.file_type,
        'groups': groups,
        'file_start': file_start,
        'file_end': file_end,
        'output_file': args.output,
        'write_mode': args.mode
    }

# 文件路径配置（移除了固定的output_file）
data_graph_file = '/home/myran/FaSTest_backup/FaSTest/dataset/human/human.graph'
query_graph_folder = '/home/myran/FaSTest_backup/FaSTest/dataset/human/query_graph/'

# 排序函数保持不变
def get_sort_key(filename):
    match = re.match(r'query_(dense|sparse)_(\d+)_(\d+)\.graph', filename)
    if match:
        category = match.group(1)
        group_num = int(match.group(2))
        file_num = int(match.group(3))
        return (0 if category == 'dense' else 1, group_num, file_num)
    return (2, 0, 0)

try:
    # 解析命令行参数
    args = parse_arguments()
    logger.info(f"处理条件：类型={args['file_type'] or '所有'}, "
                 f"组号={args['groups'] or '所有'}, "
                 f"文件范围={args['file_start']}-{args['file_end']}, "
                 f"输出文件={args['output_file']}, "
                 f"写入模式={'覆盖' if args['write_mode'] == 'w' else '追加'}")

    # 获取并过滤文件列表
    query_graph_files = []
    for f in os.listdir(query_graph_folder):
        if not f.endswith('.graph'):
            continue
        match = re.match(r'query_(dense|sparse)_(\d+)_(\d+)\.graph', f)
        if not match:
            continue
        
        category = match.group(1)
        group_num = int(match.group(2))
        file_num = int(match.group(3))

        if args['file_type'] and category != args['file_type']:
            continue
        if args['groups'] and group_num not in args['groups']:
            continue
        if not (args['file_start'] <= file_num <= args['file_end']):
            continue
        
        query_graph_files.append(f)

    query_graph_files.sort(key=get_sort_key)
    logger.info(f"找到符合条件文件数量：{len(query_graph_files)}")

except Exception as e:
    logger.exception("初始化过程中发生错误")
    raise

# 修改后的处理逻辑（添加输出模式控制）
with open(args['output_file'], args['write_mode']) as out_file:
    # 如果是新文件，写入表头
    if args['write_mode'] == 'w':
        out_file.write("filename\t time(ms)\t matches\n")
    
    for query_graph in query_graph_files:
        query_graph_path = os.path.join(query_graph_folder, query_graph)
        logger.info(f"开始处理: {query_graph}")
        
        command = ["./DAF", "-d", data_graph_file, "-q", query_graph_path]
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=600)
            
            logger.debug(f"{query_graph} 标准输出:\n{result.stdout}")
            if result.stderr:
                logger.debug(f"{query_graph} 标准错误:\n{result.stderr}")

            total_time_match = re.search(r'Total time:\s*(\d+\.?\d*)', result.stdout)
            matches_match = re.search(r'#Matches:\s*(\d+)', result.stdout)
            
            if total_time_match and matches_match:
                total_time = float(total_time_match.group(1))
                matches = int(matches_match.group(1))
                formatted_time = f"{total_time:.2f}"
                out_file.write(f"{query_graph}\t{formatted_time}\t{matches}\n")
                logger.info(f"成功处理: {query_graph} - 时间: {formatted_time}ms 匹配数: {matches}")
            else:
                error_msg = f"解析失败: {query_graph}"
                logger.error(error_msg)
                logger.debug(f"原始输出内容:\n{result.stdout}")
                out_file.write(f"{query_graph}\tERROR\t-\n")
                
        except subprocess.TimeoutExpired:
            error_msg = f"处理超时: {query_graph} (超过 600 秒)"
            logger.error(error_msg)
            out_file.write(f"{query_graph}\tTIMEOUT\t-\n")
        except Exception as e:
            error_msg = f"处理异常: {query_graph} - {str(e)}"
            logger.exception(error_msg)
            out_file.write(f"{query_graph}\tERROR\t-\n")
            
        out_file.flush()

logger.info("处理任务全部完成")