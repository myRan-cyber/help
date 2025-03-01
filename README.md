# Assistance-for-FaSTest
  记录用来辅助 FaSTest 项目的脚本/工具..

## file folder assist_ans

### batch_process.py
```
python脚本 从查询图文件夹里获取文件进行批量处理
```
### change_format.txt: 如何将下面的.graph文件的第一种格式转换为第二种格式，以满足 DAF 文件的要求

#### format_1:
```
t [#Vertex] [#Edge]
v [ID] [Label] [Degree]
v [ID] [Label] [Degree]
...
e 1235 2586 [EdgeLabel]
```
Edge labels are optional (missing labels are considered as zero).

#### format_2:
```
t [#Vertex] [#Edge]
v [ID] [Label] 
v [ID] [Label] 
...
e 1235 2586 
```

### DAF 
```
准确计算子图匹配基数，以作为 FaSTest 的真实值
```

### 