#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
特征提取器
从PHP代码解析结果中提取机器学习特征
"""

import numpy as np
import re
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from php_parser import PHPParser

@dataclass
class CodeFeatures:
    """代码特征"""
    # 基础特征
    lines_of_code: int
    cyclomatic_complexity: int
    number_of_classes: int
    number_of_functions: int
    number_of_methods: int
    number_of_variables: int
    
    # 方法级特征
    avg_method_complexity: float
    max_method_complexity: int
    avg_method_parameters: float
    max_method_parameters: int
    avg_method_length: float
    max_method_length: int
    
    # 类级特征
    avg_class_methods: float
    max_class_methods: int
    avg_class_properties: float
    max_class_properties: int
    inheritance_depth: int
    
    # 代码异味指标
    long_method_count: int
    long_class_count: int
    large_parameter_list_count: int
    complex_method_count: int
    
    # 命名约定
    naming_convention_violations: int
    
    # 注释密度
    comment_ratio: float
    
    def to_vector(self) -> np.ndarray:
        """转换为特征向量"""
        return np.array([
            self.lines_of_code,
            self.cyclomatic_complexity,
            self.number_of_classes,
            self.number_of_functions,
            self.number_of_methods,
            self.number_of_variables,
            self.avg_method_complexity,
            self.max_method_complexity,
            self.avg_method_parameters,
            self.max_method_parameters,
            self.avg_method_length,
            self.max_method_length,
            self.avg_class_methods,
            self.max_class_methods,
            self.avg_class_properties,
            self.max_class_properties,
            self.inheritance_depth,
            self.long_method_count,
            self.long_class_count,
            self.large_parameter_list_count,
            self.complex_method_count,
            self.naming_convention_violations,
            self.comment_ratio
        ])
    
    @classmethod
    def get_feature_names(cls) -> List[str]:
        """获取特征名称"""
        return [
            'lines_of_code',
            'cyclomatic_complexity',
            'number_of_classes',
            'number_of_functions',
            'number_of_methods',
            'number_of_variables',
            'avg_method_complexity',
            'max_method_complexity',
            'avg_method_parameters',
            'max_method_parameters',
            'avg_method_length',
            'max_method_length',
            'avg_class_methods',
            'max_class_methods',
            'avg_class_properties',
            'max_class_properties',
            'inheritance_depth',
            'long_method_count',
            'long_class_count',
            'large_parameter_list_count',
            'complex_method_count',
            'naming_convention_violations',
            'comment_ratio'
        ]

class FeatureExtractor:
    def __init__(self):
        self.parser = PHPParser()
        
        # 阈值配置
        self.thresholds = {
            'long_method_lines': 50,
            'long_class_lines': 500,
            'large_parameter_count': 5,
            'complex_method_complexity': 10
        }
    
    def extract_features(self, file_path: str) -> CodeFeatures:
        """从PHP文件提取特征"""
        # 解析PHP文件
        parse_result = self.parser.parse_file(file_path)
        
        # 读取文件内容用于额外分析
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 保存详细分析结果供后续使用
        self.detailed_analysis = {
            'file_path': file_path,
            'content': content,
            'parse_result': parse_result,
            'lines': content.split('\n')
        }
        
        # 基础特征
        lines_of_code = parse_result.get('lines', 0)
        cyclomatic_complexity = parse_result.get('complexity', 1)
        number_of_classes = len(parse_result.get('classes', []))
        number_of_functions = len(parse_result.get('functions', []))
        number_of_variables = len(parse_result.get('variables', []))
        
        # 计算方法相关特征
        all_methods = []
        for cls in parse_result.get('classes', []):
            all_methods.extend(cls.get('methods', []))
        all_methods.extend(parse_result.get('functions', []))
        
        number_of_methods = len(all_methods)
        
        # 方法级特征计算
        method_complexities = [m.get('complexity', 1) for m in all_methods]
        method_parameters = [m.get('parameters', 0) for m in all_methods]
        method_lengths = [self._estimate_method_length(content, m.get('name', '')) for m in all_methods]
        
        avg_method_complexity = np.mean(method_complexities) if method_complexities else 0
        max_method_complexity = max(method_complexities) if method_complexities else 0
        avg_method_parameters = np.mean(method_parameters) if method_parameters else 0
        max_method_parameters = max(method_parameters) if method_parameters else 0
        avg_method_length = np.mean(method_lengths) if method_lengths else 0
        max_method_length = max(method_lengths) if method_lengths else 0
        
        # 类级特征计算
        classes = parse_result.get('classes', [])
        class_method_counts = [len(cls.get('methods', [])) for cls in classes]
        class_property_counts = [cls.get('properties', 0) for cls in classes]
        
        avg_class_methods = np.mean(class_method_counts) if class_method_counts else 0
        max_class_methods = max(class_method_counts) if class_method_counts else 0
        avg_class_properties = np.mean(class_property_counts) if class_property_counts else 0
        max_class_properties = max(class_property_counts) if class_property_counts else 0
        
        # 继承深度计算
        inheritance_depth = self._calculate_inheritance_depth(classes)
        
        # 代码异味计数
        long_method_count = sum(1 for length in method_lengths if length > self.thresholds['long_method_lines'])
        long_class_count = sum(1 for cls in classes if self._estimate_class_length(content, cls.get('name', '')) > self.thresholds['long_class_lines'])
        large_parameter_list_count = sum(1 for params in method_parameters if params > self.thresholds['large_parameter_count'])
        complex_method_count = sum(1 for complexity in method_complexities if complexity > self.thresholds['complex_method_complexity'])
        
        # 命名约定违规
        naming_convention_violations = self._check_naming_conventions(parse_result)
        
        # 注释密度
        comment_ratio = self._calculate_comment_ratio(content)
        
        return CodeFeatures(
            lines_of_code=lines_of_code,
            cyclomatic_complexity=cyclomatic_complexity,
            number_of_classes=number_of_classes,
            number_of_functions=number_of_functions,
            number_of_methods=number_of_methods,
            number_of_variables=number_of_variables,
            avg_method_complexity=avg_method_complexity,
            max_method_complexity=max_method_complexity,
            avg_method_parameters=avg_method_parameters,
            max_method_parameters=max_method_parameters,
            avg_method_length=avg_method_length,
            max_method_length=max_method_length,
            avg_class_methods=avg_class_methods,
            max_class_methods=max_class_methods,
            avg_class_properties=avg_class_properties,
            max_class_properties=max_class_properties,
            inheritance_depth=inheritance_depth,
            long_method_count=long_method_count,
            long_class_count=long_class_count,
            large_parameter_list_count=large_parameter_list_count,
            complex_method_count=complex_method_count,
            naming_convention_violations=naming_convention_violations,
            comment_ratio=comment_ratio
        )
    
    def _estimate_method_length(self, content: str, method_name: str) -> int:
        """估算方法长度"""
        if not method_name:
            return 0
        
        # 查找方法定义
        pattern = rf'function\s+{re.escape(method_name)}\s*\([^)]*\)\s*\{{'
        match = re.search(pattern, content, re.IGNORECASE)
        if not match:
            return 0
        
        start_pos = match.end()
        brace_count = 1
        current_pos = start_pos
        
        # 找到方法结束位置
        while current_pos < len(content) and brace_count > 0:
            if content[current_pos] == '{':
                brace_count += 1
            elif content[current_pos] == '}':
                brace_count -= 1
            current_pos += 1
        
        if brace_count == 0:
            method_content = content[start_pos:current_pos-1]
            return method_content.count('\n') + 1
        
        return 0
    
    def _estimate_class_length(self, content: str, class_name: str) -> int:
        """估算类长度"""
        if not class_name:
            return 0
        
        pattern = rf'class\s+{re.escape(class_name)}(?:\s+extends\s+\w+)?(?:\s+implements\s+[^{{]+)?\s*\{{'
        match = re.search(pattern, content, re.IGNORECASE)
        if not match:
            return 0
        
        start_pos = match.end()
        brace_count = 1
        current_pos = start_pos
        
        while current_pos < len(content) and brace_count > 0:
            if content[current_pos] == '{':
                brace_count += 1
            elif content[current_pos] == '}':
                brace_count -= 1
            current_pos += 1
        
        if brace_count == 0:
            class_content = content[start_pos:current_pos-1]
            return class_content.count('\n') + 1
        
        return 0
    
    def _calculate_inheritance_depth(self, classes: List[Dict]) -> int:
        """计算继承深度"""
        max_depth = 0
        
        for cls in classes:
            depth = 1
            current_extends = cls.get('extends')
            
            # 简单的继承深度计算（在当前类列表中查找）
            while current_extends:
                found = False
                for other_cls in classes:
                    if other_cls.get('name') == current_extends:
                        depth += 1
                        current_extends = other_cls.get('extends')
                        found = True
                        break
                if not found:
                    depth += 1  # 假设继承了外部类
                    break
            
            max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _check_naming_conventions(self, parse_result: Dict) -> int:
        """检查命名约定违规"""
        violations = 0
        
        # 检查类名（应该是PascalCase）
        for cls in parse_result.get('classes', []):
            class_name = cls.get('name', '')
            if not re.match(r'^[A-Z][a-zA-Z0-9]*$', class_name):
                violations += 1
        
        # 检查方法名（应该是camelCase）
        all_methods = []
        for cls in parse_result.get('classes', []):
            all_methods.extend(cls.get('methods', []))
        all_methods.extend(parse_result.get('functions', []))
        
        for method in all_methods:
            method_name = method.get('name', '')
            # 排除魔术方法
            if not method_name.startswith('__') and not re.match(r'^[a-z][a-zA-Z0-9]*$', method_name):
                violations += 1
        
        # 检查变量名（应该以$开头，然后是camelCase或snake_case）
        for var in parse_result.get('variables', []):
            if not re.match(r'^\$[a-z][a-zA-Z0-9_]*$', var):
                violations += 1
        
        return violations
    
    def _calculate_comment_ratio(self, content: str) -> float:
        """计算注释密度"""
        lines = content.split('\n')
        total_lines = len(lines)
        comment_lines = 0
        
        in_block_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            # 块注释
            if '/*' in stripped:
                in_block_comment = True
            if '*/' in stripped:
                in_block_comment = False
                comment_lines += 1
                continue
            
            if in_block_comment:
                comment_lines += 1
                continue
            
            # 单行注释
            if stripped.startswith('//') or stripped.startswith('#'):
                comment_lines += 1
        
        return comment_lines / total_lines if total_lines > 0 else 0

def main():
    """测试特征提取器"""
    extractor = FeatureExtractor()
    
    # 创建测试PHP文件
    test_php = '''<?php
/**
 * 测试类
 * 这是一个用于演示的测试类
 */
class BadCodeExample {
    private $veryLongVariableNameThatViolatesConventions;
    private $another_variable;
    public $publicProperty;
    
    /**
     * 构造函数
     */
    public function __construct($param1, $param2, $param3, $param4, $param5, $param6) {
        $this->veryLongVariableNameThatViolatesConventions = $param1;
        $this->another_variable = $param2;
        // 太多参数的方法
    }
    
    // 这是一个复杂且长的方法
    public function VeryComplexMethod($data) {
        if ($data > 100) {
            for ($i = 0; $i < $data; $i++) {
                if ($i % 2 == 0) {
                    if ($i % 4 == 0) {
                        if ($i % 8 == 0) {
                            echo "复杂的嵌套逻辑";
                            for ($j = 0; $j < 10; $j++) {
                                switch ($j) {
                                    case 1:
                                        echo "case 1";
                                        break;
                                    case 2:
                                        echo "case 2";
                                        break;
                                    case 3:
                                        echo "case 3";
                                        break;
                                    default:
                                        echo "default";
                                }
                            }
                        } else {
                            echo "不是8的倍数";
                        }
                    } else {
                        echo "不是4的倍数";
                    }
                } else {
                    echo "奇数";
                }
            }
        } elseif ($data < 0) {
            while ($data < 0) {
                $data++;
                if ($data % 10 == 0) {
                    echo "10的倍数";
                }
            }
        } else {
            echo "数据为0";
        }
        return $data;
    }
    
    public function shortMethod() {
        return "简短方法";
    }
}

function bad_function_name($too, $many, $parameters, $in, $this, $function) {
    // 函数名违反约定，参数过多
    return $too + $many + $parameters;
}
?>'''
    
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False) as f:
        f.write(test_php)
        test_file = f.name
    
    try:
        features = extractor.extract_features(test_file)
        print("提取的特征:")
        print(f"代码行数: {features.lines_of_code}")
        print(f"圈复杂度: {features.cyclomatic_complexity}")
        print(f"类数量: {features.number_of_classes}")
        print(f"方法数量: {features.number_of_methods}")
        print(f"长方法数量: {features.long_method_count}")
        print(f"复杂方法数量: {features.complex_method_count}")
        print(f"大参数列表数量: {features.large_parameter_list_count}")
        print(f"命名约定违规: {features.naming_convention_violations}")
        print(f"注释密度: {features.comment_ratio:.2f}")
        print(f"平均方法复杂度: {features.avg_method_complexity:.2f}")
        print(f"最大方法参数数: {features.max_method_parameters}")
        
        print("\n特征向量:")
        print(features.to_vector())
        
        print("\n特征名称:")
        print(CodeFeatures.get_feature_names())
        
    finally:
        os.unlink(test_file)

if __name__ == '__main__':
    main() 