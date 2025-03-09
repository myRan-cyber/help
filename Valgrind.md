# Valgrind 使用说明

## 非组织文件使用
   参考链接[https://senlinzhan.github.io/2017/12/31/valgrind/]
   介绍了Valgrind的常见使用方法

## 组织文件使用
   以 FaSTest_backup 项目为例
   
### 1. 确保编译时包含调试符号
在构建项目时，需确保 -g 标志被启用（生成调试符号）。修改你的 CMake 构建命令：
    ```
    cd build
    cmake -DCMAKE_BUILD_TYPE=Debug ..  # 强制开启调试模式
    make clean && make                 # 重新编译
    ```

### 2. 运行 Valgrind 检测内存泄漏
    执行以下命令：
    ```
    valgrind --leak-check=full \
         --show-leak-kinds=all \
         --track-origins=yes \
         --verbose \
         --log-file=valgrind_log.txt \
         ./Fastest -d yeast
    ```

    参数解释：
    |         Argument          |                          Description                          |
    |:-------------------------:|:-------------------------------------------------------------:|
    |  --show-leak-kinds=all    |                显示所有类型的内存泄漏（包括间接泄漏）               |
    |   --track-origins=yes     |                追踪未初始化值的来源（有助于发现野指针问题）          |
    |--log-file=valgrind_log.txt|                将结果保存到日志文件                              |
    |   --track-origins=yes     |                追踪未初始化值的来源（有助于发现野指针问题）          |

### 3. 分析结果
    检查生成的日志文件 valgrind_log.txt，重点关注以下部分：
    ```
    ==12345== LEAK SUMMARY:
    ==12345==    definitely lost: X bytes in Y blocks    # 必须修复的内存泄漏
    ==12345==    indirectly lost: Z bytes in W blocks    # 关联泄漏
    ==12345==    possibly lost: ...                     # 潜在问题
    ==12345==    still reachable: ...                   # 程序结束时未释放的内存（视情况处理）
    ```

### 4. 修复泄漏
    根据 Valgrind 输出的代码行号定位问题，常见原因包括：
    1.new/delete 不匹配
    2.动态数组未释放（忘记 delete[]）
    3.异常分支未释放内存

### 5. 其他
    1.优化调试体验：如果输出过于冗长，可以暂时关闭编译器优化（在 CMake 中设置 -O0）
    2.条件启动：对于大型程序，可通过 --vgdb=yes 启动 Valgrind 的 GDB 调试集成
    3.排除第三方库干扰：使用 --suppressions=suppression_file.txt 忽略已知的第三方库误报
