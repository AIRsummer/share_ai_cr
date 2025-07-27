# AI代码异味检测工具

基于php-parser + scikit-learn的AI驱动代码异味检测系统

## 功能特性

- 🔍 **智能检测**: 使用机器学习模型检测多种代码异味
- 📊 **详细分析**: 提供代码复杂度、结构分析等详细信息
- 📋 **美观报告**: 生成HTML格式的检测报告
- 🎯 **精准建议**: 提供针对性的代码改进建议
- 🚀 **高性能**: 支持批量文件检测

## 支持的代码异味类型

- **长方法** (Long Method): 方法行数过多
- **大类** (Large Class): 类文件过大，职责过多
- **长参数列表** (Long Parameter List): 方法参数过多
- **复杂方法** (Complex Method): 圈复杂度过高
- **命名问题** (Naming Issues): 违反命名约定
- **注释不足** (Low Comment Ratio): 代码注释密度过低

## 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 训练模型（首次使用）

```bash
# 使用合成数据训练模型
python main.py train --synthetic --samples 500 --plot

# 使用网格搜索优化参数（耗时较长但效果更好）
python main.py train --synthetic --samples 1000 --grid-search --plot
```

### 2. 检测代码异味

```bash
# 检测单个文件
python main.py detect -f /path/to/your/file.php

# 检测整个项目目录
python main.py detect -d /path/to/your/project --recursive --verbose

# 生成详细报告
python main.py detect -d /path/to/your/project -o my_report.html --suggestions
```

### 3. 分析代码统计

```bash
# 分析项目代码统计信息
python main.py analyze -d /path/to/your/project --verbose
```

## 使用示例

### 检测单个文件
```bash
python main.py detect -f example.php --verbose --suggestions
```

输出示例：
```
🔍 开始代码异味检测...
📁 找到 1 个PHP文件

📊 检测完成，共检测 1 个文件

🏷️  异味类型分布:
   complex_method: 1 个文件

⚠️  问题统计:
   错误: 0 个
   警告: 2 个
   提示: 1 个

📄 详细结果:

📁 example.php
   异味类型: complex_method (置信度: 85%)
   问题:
   ⚠️ 发现 1 个复杂方法: 最大圈复杂度为 15
   ⚠️ 发现 1 个长参数列表: 最多参数数量为 7
   ℹ️ 发现 2 个命名约定违规: 类名应使用PascalCase，方法名应使用camelCase
   建议:
   💡 减少嵌套层次，使用早期返回
   💡 将复杂条件提取为有意义的方法
   💡 使用参数对象(Parameter Object)重构

📋 检测报告已保存到: code_smell_report.html
```

### 批量检测项目
```bash
python main.py detect -d /path/to/laravel/project --recursive -o laravel_report.html
```

## 项目结构

```
ai_cr_tools/
├── main.py                    # 主程序入口
├── php_parser.py             # PHP代码解析器
├── feature_extractor.py      # 特征提取器
├── model_trainer.py          # 机器学习模型训练器
├── code_smell_detector.py    # 代码异味检测器
├── requirements.txt          # Python依赖
├── README.md                 # 项目说明
└── models/                   # 训练好的模型文件
    ├── best_model_*.pkl      # 最佳模型
    ├── scaler.pkl           # 特征标准化器
    ├── label_encoder.pkl    # 标签编码器
    └── model_info.json      # 模型信息
```

## 技术架构

### 1. PHP代码解析 (php_parser.py)
- 使用PHP内置的`token_get_all`函数解析PHP代码
- 提取类、方法、变量等结构信息
- 计算基础的复杂度指标

### 2. 特征提取 (feature_extractor.py)
- 从解析结果中提取23个代码特征
- 包括代码行数、复杂度、命名约定等
- 生成标准化的特征向量

### 3. 机器学习模型 (model_trainer.py)
- 支持多种算法：随机森林、梯度提升、SVM、逻辑回归
- 自动特征标准化和网格搜索优化
- 交叉验证评估模型性能

### 4. 代码异味检测 (code_smell_detector.py)
- 结合ML模型预测和规则检测
- 生成详细的问题分析和改进建议
- 支持HTML格式的可视化报告

## 特征说明

| 特征名称 | 描述 |
|---------|------|
| lines_of_code | 代码总行数 |
| cyclomatic_complexity | 圈复杂度 |
| number_of_classes | 类的数量 |
| number_of_functions | 函数数量 |
| number_of_methods | 方法数量 |
| avg_method_complexity | 平均方法复杂度 |
| max_method_parameters | 最大方法参数数 |
| long_method_count | 长方法数量 |
| complex_method_count | 复杂方法数量 |
| naming_convention_violations | 命名约定违规数 |
| comment_ratio | 注释密度 |
| ... | 其他特征 |

## 配置说明

### 阈值配置
可以在`FeatureExtractor`类中修改检测阈值：

```python
self.thresholds = {
    'long_method_lines': 50,        # 长方法行数阈值
    'long_class_lines': 500,        # 大类行数阈值
    'large_parameter_count': 5,     # 参数过多阈值
    'complex_method_complexity': 10 # 复杂方法圈复杂度阈值
}
```

### 模型配置
可以在`ModelTrainer`类中调整机器学习模型参数。

## 扩展开发

### 添加新的代码异味类型
1. 在`FeatureExtractor`中添加新的特征提取逻辑
2. 在`CodeSmellDetector`中添加检测规则
3. 更新训练数据和模型

### 支持其他语言
- 修改`php_parser.py`以支持其他语言的解析
- 调整特征提取逻辑适应不同语言特性

## 注意事项

1. **PHP环境**: 虽然工具主要用Python编写，但为了更准确的解析，建议安装PHP环境
2. **训练数据**: 合成数据仅用于演示，实际使用建议用真实项目数据训练
3. **模型性能**: 首次使用需要训练模型，建议使用较大的数据集

## 故障排除

### 常见问题

**Q: 提示"PHP not found"怎么办？**
A: 安装PHP或确保PHP在系统PATH中。工具会自动回退到正则表达式解析。

**Q: 检测结果不准确？**
A: 可以用真实项目数据重新训练模型，或调整检测阈值。

**Q: 处理大项目很慢？**
A: 可以使用多进程并行处理（需要修改代码），或先分析部分关键文件。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个工具！ 