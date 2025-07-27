#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码异味检测器
集成PHP解析器和机器学习模型进行代码异味检测
"""

import os
import re
import json
import pickle
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

from php_parser import PHPParser
from feature_extractor import FeatureExtractor, CodeFeatures

@dataclass
class CodeIssue:
    """具体的代码问题"""
    type: str
    severity: str
    message: str
    line_number: int
    line_content: str
    suggestion: str
    code_snippet: List[str]  # 问题代码片段（包含上下文）

@dataclass
class SmellDetectionResult:
    """代码异味检测结果"""
    file_path: str
    smell_type: str
    confidence: float
    features: CodeFeatures
    issues: List[Dict[str, Any]]
    suggestions: List[str]
    detailed_issues: List[CodeIssue]  # 新增：详细问题列表

class CodeSmellDetector:
    def __init__(self, models_dir: str = "models"):
        """
        初始化代码异味检测器
        
        Args:
            models_dir: 模型目录路径
        """
        self.models_dir = models_dir
        self.feature_extractor = FeatureExtractor()
        
        # 加载训练好的模型和预处理器
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.model_info = None
        
        # 代码异味类型中文映射
        self.smell_type_descriptions = {
            'clean': '清洁代码',
            'long_method': '长方法',
            'large_class': '大类',
            'long_parameter_list': '长参数列表',
            'complex_method': '复杂方法',
            'naming_issues': '命名问题',
            'low_cohesion': '低内聚',
            'high_coupling': '高耦合',
            'duplicate_code': '重复代码',
            'security_issues': '安全问题',
            'logic_errors': '逻辑错误',
            'error_handling_issues': '错误处理问题',
            'performance_issues': '性能问题',
            'critical_issues': '严重问题',
            'code_quality_issues': '代码质量问题'
        }
        
        # 代码异味检测规则
        self.smell_rules = {
            'long_method': {
                'threshold': 50,
                'description': '方法过长',
                'suggestion': '考虑将长方法分解为多个小方法'
            },
            'large_class': {
                'threshold': 500,
                'description': '类过大',
                'suggestion': '考虑将大类分解为多个小类'
            },
            'long_parameter_list': {
                'threshold': 5,
                'description': '参数列表过长',
                'suggestion': '考虑使用参数对象或配置类'
            },
            'complex_method': {
                'threshold': 10,
                'description': '方法复杂度过高',
                'suggestion': '简化方法逻辑，减少嵌套层次'
            },
            'naming_issues': {
                'threshold': 0,
                'description': '命名约定违规',
                'suggestion': '遵循PSR-1/PSR-12命名规范'
            },
            'low_comment_ratio': {
                'threshold': 0.1,
                'description': '注释不足',
                'suggestion': '添加必要的代码注释和文档'
            }
        }
        
        self._load_model()
    
    def get_smell_description(self, smell_type: str) -> str:
        """获取代码异味类型的中文描述"""
        return self.smell_type_descriptions.get(smell_type, smell_type)
    
    def _load_model(self):
        """加载训练好的模型"""
        try:
            # 加载模型信息
            info_path = os.path.join(self.models_dir, 'model_info.json')
            if os.path.exists(info_path):
                with open(info_path, 'r', encoding='utf-8') as f:
                    self.model_info = json.load(f)
                
                # 加载最佳模型
                model_name = self.model_info['model_name']
                model_path = os.path.join(self.models_dir, f'best_model_{model_name}.pkl')
                
                if os.path.exists(model_path):
                    with open(model_path, 'rb') as f:
                        self.model = pickle.load(f)
                    print(f"已加载模型: {model_name}")
            
            # 加载预处理器
            scaler_path = os.path.join(self.models_dir, 'scaler.pkl')
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
            
            encoder_path = os.path.join(self.models_dir, 'label_encoder.pkl')
            if os.path.exists(encoder_path):
                with open(encoder_path, 'rb') as f:
                    self.label_encoder = pickle.load(f)
        
        except Exception as e:
            print(f"加载模型时出错: {e}")
            print("将使用规则基础的检测方法")
    
    def detect_smells(self, file_path: str) -> SmellDetectionResult:
        """
        检测代码异味
        
        Args:
            file_path: PHP文件路径
            
        Returns:
            检测结果
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 提取特征
        features = self.feature_extractor.extract_features(file_path)
        
        # 检测详细问题（规则引擎）
        detailed_issues = self._detect_detailed_issues(file_path)
        
        # 检测具体问题
        issues = self._detect_specific_issues(features, file_path)
        
        # 首先检查是否有严重错误（规则引擎优先）
        critical_issues = [issue for issue in detailed_issues if issue.severity == 'error']
        
        if critical_issues:
            # 有严重错误，直接标记为相应的问题类型
            smell_type = self._determine_critical_smell_type(critical_issues)
            confidence = 0.95  # 规则引擎的置信度很高
        else:
            # 没有严重错误，使用ML模型预测
            if self.model and self.scaler and self.label_encoder:
                smell_type, confidence = self._predict_with_model(features)
            else:
                # 使用规则基础的检测
                smell_type, confidence = self._predict_with_rules(features)
            
            # 如果有中等严重度问题，调整结果
            warning_issues = [issue for issue in detailed_issues if issue.severity == 'warning']
            if warning_issues and smell_type == 'clean':
                smell_type = self._determine_warning_smell_type(warning_issues)
                confidence = max(0.75, confidence)  # 提高置信度
        
        # 生成建议
        suggestions = self._generate_suggestions(issues, smell_type)
        
        return SmellDetectionResult(
            file_path=file_path,
            smell_type=smell_type,
            confidence=confidence,
            features=features,
            issues=issues,
            suggestions=suggestions,
            detailed_issues=detailed_issues
        )
    
    def _determine_critical_smell_type(self, critical_issues: List[CodeIssue]) -> str:
        """根据严重错误确定代码异味类型"""
        issue_types = [issue.type for issue in critical_issues]
        
        # 根据错误类型映射到代码异味
        if any('sql_injection' in t or 'xss' in t or 'security' in t for t in issue_types):
            return 'security_issues'
        elif any('infinite' in t or 'loop' in t for t in issue_types):
            return 'logic_errors'
        elif any('empty_catch' in t for t in issue_types):
            return 'error_handling_issues'
        elif any('performance' in t or 'query_in_loop' in t for t in issue_types):
            return 'performance_issues'
        else:
            return 'critical_issues'
    
    def _determine_warning_smell_type(self, warning_issues: List[CodeIssue]) -> str:
        """根据警告问题确定代码异味类型"""
        issue_types = [issue.type for issue in warning_issues]
        
        if any('long_method' in t for t in issue_types):
            return 'long_method'
        elif any('long_parameter' in t for t in issue_types):
            return 'long_parameter_list'
        elif any('naming' in t for t in issue_types):
            return 'naming_issues'
        elif any('missing_comment' in t for t in issue_types):
            return 'low_cohesion'
        else:
            return 'code_quality_issues'
    
    def _predict_with_model(self, features: CodeFeatures) -> Tuple[str, float]:
        """使用机器学习模型预测"""
        try:
            # 转换特征为向量
            feature_vector = features.to_vector().reshape(1, -1)
            
            # 标准化特征
            feature_vector_scaled = self.scaler.transform(feature_vector)
            
            # 预测
            prediction = self.model.predict(feature_vector_scaled)[0]
            probabilities = self.model.predict_proba(feature_vector_scaled)[0]
            
            # 获取预测的类别和置信度
            smell_type = self.label_encoder.inverse_transform([prediction])[0]
            confidence = max(probabilities)
            
            return smell_type, confidence
            
        except Exception as e:
            print(f"模型预测出错: {e}")
            return self._predict_with_rules(features)
    
    def _predict_with_rules(self, features: CodeFeatures) -> Tuple[str, float]:
        """使用规则基础的预测"""
        # 检查各种代码异味
        smell_scores = {}
        
        # 长方法检测
        if features.long_method_count > 0:
            smell_scores['long_method'] = min(features.long_method_count / 5.0, 1.0)
        
        # 复杂方法检测
        if features.complex_method_count > 0:
            smell_scores['complex_method'] = min(features.complex_method_count / 3.0, 1.0)
        
        # 长参数列表检测
        if features.large_parameter_list_count > 0:
            smell_scores['long_parameter_list'] = min(features.large_parameter_list_count / 3.0, 1.0)
        
        # 命名问题检测
        if features.naming_convention_violations > 0:
            smell_scores['naming_issues'] = min(features.naming_convention_violations / 10.0, 1.0)
        
        # 大类检测
        if features.long_class_count > 0:
            smell_scores['large_class'] = min(features.long_class_count / 2.0, 1.0)
        
        # 低注释密度检测
        if features.comment_ratio < 0.1:
            smell_scores['low_comment_ratio'] = (0.1 - features.comment_ratio) / 0.1
        
        # 如果没有发现明显问题，标记为清洁代码
        if not smell_scores:
            return 'clean', 0.8
        
        # 找到得分最高的异味类型
        best_smell = max(smell_scores.items(), key=lambda x: x[1])
        return best_smell[0], best_smell[1]
    
    def _detect_specific_issues(self, features: CodeFeatures, file_path: str) -> List[Dict[str, Any]]:
        """检测具体的代码问题"""
        issues = []
        
        # 长方法问题
        if features.long_method_count > 0:
            issues.append({
                'type': 'long_method',
                'severity': 'warning',
                'message': f'发现 {features.long_method_count} 个长方法',
                'details': f'最长方法有 {features.max_method_length} 行',
                'metric': features.max_method_length
            })
        
        # 复杂方法问题
        if features.complex_method_count > 0:
            issues.append({
                'type': 'complex_method',
                'severity': 'warning',
                'message': f'发现 {features.complex_method_count} 个复杂方法',
                'details': f'最大圈复杂度为 {features.max_method_complexity}',
                'metric': features.max_method_complexity
            })
        
        # 长参数列表问题
        if features.large_parameter_list_count > 0:
            issues.append({
                'type': 'long_parameter_list',
                'severity': 'warning',
                'message': f'发现 {features.large_parameter_list_count} 个长参数列表',
                'details': f'最多参数数量为 {features.max_method_parameters}',
                'metric': features.max_method_parameters
            })
        
        # 命名约定问题
        if features.naming_convention_violations > 0:
            issues.append({
                'type': 'naming_issues',
                'severity': 'info',
                'message': f'发现 {features.naming_convention_violations} 个命名约定违规',
                'details': '类名应使用PascalCase，方法名应使用camelCase',
                'metric': features.naming_convention_violations
            })
        
        # 大类问题
        if features.long_class_count > 0:
            issues.append({
                'type': 'large_class',
                'severity': 'warning',
                'message': f'发现 {features.long_class_count} 个大类',
                'details': '类可能承担了过多职责',
                'metric': features.long_class_count
            })
        
        # 注释不足问题
        if features.comment_ratio < 0.1:
            issues.append({
                'type': 'low_comment_ratio',
                'severity': 'info',
                'message': '注释密度过低',
                'details': f'当前注释密度: {features.comment_ratio:.2%}',
                'metric': features.comment_ratio
            })
        
        # 高圈复杂度问题
        if features.cyclomatic_complexity > 20:
            issues.append({
                'type': 'high_complexity',
                'severity': 'error',
                'message': '文件整体复杂度过高',
                'details': f'圈复杂度: {features.cyclomatic_complexity}',
                'metric': features.cyclomatic_complexity
            })
        
        return issues
    
    def _generate_suggestions(self, issues: List[Dict[str, Any]], smell_type: str) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 根据检测到的问题生成建议
        for issue in issues:
            issue_type = issue['type']
            if issue_type in self.smell_rules:
                suggestions.append(self.smell_rules[issue_type]['suggestion'])
        
        # 根据主要异味类型添加通用建议
        general_suggestions = {
            'long_method': [
                '使用Extract Method重构技术分解长方法',
                '确保每个方法只做一件事（单一职责原则）',
                '考虑使用Template Method模式处理重复逻辑'
            ],
            'complex_method': [
                '减少嵌套层次，使用早期返回',
                '将复杂条件提取为有意义的方法',
                '考虑使用策略模式替换复杂的条件逻辑'
            ],
            'long_parameter_list': [
                '使用参数对象(Parameter Object)重构',
                '考虑使用Builder模式构造复杂对象',
                '检查是否违反了单一职责原则'
            ],
            'large_class': [
                '使用Extract Class重构分解大类',
                '识别类的不同职责并分离',
                '考虑使用组合代替继承'
            ],
            'naming_issues': [
                '遵循PSR-1和PSR-12编码规范',
                '使用有意义的名称描述变量和方法的用途',
                '保持命名风格的一致性'
            ]
        }
        
        if smell_type in general_suggestions:
            suggestions.extend(general_suggestions[smell_type])
        
        # 去重并限制建议数量
        suggestions = list(set(suggestions))[:5]
        
        return suggestions
    
    def _detect_detailed_issues(self, file_path: str) -> List[CodeIssue]:
        """检测具体的代码问题并定位到行号"""
        detailed_issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # 1. 检测长方法
            detailed_issues.extend(self._find_long_methods(lines))
            
            # 2. 检测复杂方法
            detailed_issues.extend(self._find_complex_methods(lines))
            
            # 3. 检测长参数列表
            detailed_issues.extend(self._find_long_parameter_lists(lines))
            
            # 4. 检测命名问题
            detailed_issues.extend(self._find_naming_issues(lines))
            
            # 5. 检测注释不足的方法
            detailed_issues.extend(self._find_uncommented_methods(lines))
            
            # 6. 检测SQL注入风险
            detailed_issues.extend(self._find_sql_injection_risks(lines))
            
            # 7. 检测其他安全问题
            detailed_issues.extend(self._find_security_issues(lines))
            
            # 8. 检测代码质量问题
            detailed_issues.extend(self._find_code_quality_issues(lines))
            
            # 9. 检测逻辑错误和危险模式
            detailed_issues.extend(self._find_logic_errors(lines))
            
            # 10. 检测性能问题
            detailed_issues.extend(self._find_performance_issues(lines))
            
        except Exception as e:
            print(f"分析文件 {file_path} 时出错: {e}")
        
        return detailed_issues
    
    def _find_long_methods(self, lines: List[str]) -> List[CodeIssue]:
        """查找长方法"""
        issues = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 检测方法开始 - 简化的正则表达式
            method_match = re.search(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)', stripped, re.IGNORECASE)
            if method_match:
                method_name = method_match.group(1)
                params_str = method_match.group(2)
                method_start = i
                
                # 简单地向下查找方法结束 - 查找匹配的大括号
                brace_count = 0
                method_end = i
                found_start_brace = False
                
                # 从方法开始行开始计算
                for j in range(i, len(lines)):
                    current_line = lines[j]
                    brace_count += current_line.count('{')
                    brace_count -= current_line.count('}')
                    
                    if brace_count > 0:
                        found_start_brace = True
                    
                    if found_start_brace and brace_count == 0:
                        method_end = j
                        break
                
                method_length = method_end - method_start + 1
                
                # 获取完整的方法签名（可能跨多行）
                method_signature = stripped
                if ')' not in method_signature and i + 1 < len(lines):
                    method_signature += " " + lines[i + 1].strip()
                
                # 检查长方法
                if method_length > 20:
                    code_snippet = lines[method_start:min(method_start + 10, len(lines))]
                    issues.append(CodeIssue(
                        type="long_method",
                        severity="warning",
                        message=f"长方法 '{method_name}' ({method_length} 行，第{method_start + 1}-{method_end + 1}行)",
                        line_number=method_start + 1,
                        line_content=method_signature,
                        suggestion=f"将 '{method_name}' 方法分解为多个较小的方法。建议:\n1. 提取验证逻辑为独立方法\n2. 提取数据处理逻辑\n3. 提取通知发送逻辑\n4. 每个方法应少于30行",
                        code_snippet=[line.rstrip() for line in code_snippet]
                    ))
                
                # 检查参数数量
                if params_str.strip():
                    # 处理跨行参数
                    full_params = params_str
                    if ')' not in line and i + 1 < len(lines):
                        for k in range(i + 1, min(i + 10, len(lines))):
                            full_params += " " + lines[k].strip()
                            if ')' in lines[k]:
                                break
                    
                    # 清理参数字符串
                    full_params = re.sub(r'\).*$', '', full_params)  # 移除)后的内容
                    param_list = [p.strip() for p in full_params.split(',') if p.strip()]
                    
                    if len(param_list) > 4:
                        # 提取参数名
                        param_names = []
                        for param in param_list:
                            param_clean = re.sub(r'^\s*\$?', '$', param.strip())  # 确保有$符号
                            param_clean = re.sub(r'\s*=.*$', '', param_clean)      # 去掉默认值
                            param_names.append(param_clean)
                        
                        issues.append(CodeIssue(
                            type="long_parameter_list",
                            severity="warning",
                            message=f"方法 '{method_name}' 参数过多 ({len(param_list)} 个参数)",
                            line_number=method_start + 1,
                            line_content=method_signature,
                            suggestion=f"重构 '{method_name}' 的参数列表:\n1. 创建配置对象: UserData, ValidationConfig, EmailConfig等\n2. 使用数组或对象传递相关参数\n3. 考虑方法是否职责过多\n\n当前参数:\n{chr(10).join(f'  - {param}' for param in param_names)}",
                            code_snippet=[method_signature]
                        ))
        
        return issues
    
    def _find_complex_methods(self, lines: List[str]) -> List[CodeIssue]:
        """查找复杂方法（基于嵌套层次）"""
        issues = []
        in_method = False
        method_start = 0
        method_name = ""
        max_nesting = 0
        current_nesting = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 检测方法开始
            method_match = re.search(r'function\s+(\w+)\s*\(', stripped, re.IGNORECASE)
            if method_match and not in_method:
                method_name = method_match.group(1)
                method_start = i
                in_method = True
                max_nesting = 0
                current_nesting = 0
            
            if in_method:
                # 检测控制结构
                if re.search(r'\b(if|for|foreach|while|switch)\b', stripped, re.IGNORECASE):
                    current_nesting += 1
                    max_nesting = max(max_nesting, current_nesting)
                
                # 减少嵌套（简化版）
                if stripped.startswith('}'):
                    current_nesting = max(0, current_nesting - 1)
                
                # 方法结束检测
                if stripped.startswith('}') and current_nesting == 0:
                    if max_nesting > 4:  # 复杂度阈值
                        code_snippet = lines[method_start:min(method_start + 10, len(lines))]
                        issues.append(CodeIssue(
                            type="complex_method",
                            severity="error",
                            message=f"方法 '{method_name}' 嵌套过深 (最大嵌套层次: {max_nesting})",
                            line_number=method_start + 1,
                            line_content=lines[method_start].strip(),
                            suggestion=f"简化 {method_name} 方法：使用早期返回减少嵌套，将复杂逻辑提取为独立方法",
                            code_snippet=[line.rstrip() for line in code_snippet]
                        ))
                    
                    in_method = False
        
        return issues
    
    def _find_long_parameter_lists(self, lines: List[str]) -> List[CodeIssue]:
        """查找长参数列表"""
        issues = []
        
        for i, line in enumerate(lines):
            # 查找函数定义
            method_match = re.search(r'function\s+(\w+)\s*\(([^)]*)\)', line, re.IGNORECASE)
            if method_match:
                method_name = method_match.group(1)
                params_str = method_match.group(2)
                
                # 计算参数数量
                if params_str.strip():
                    params = [p.strip() for p in params_str.split(',') if p.strip()]
                    param_count = len(params)
                    
                    if param_count > 5:  # 参数过多阈值
                        issues.append(CodeIssue(
                            type="long_parameter_list",
                            severity="warning",
                            message=f"方法 '{method_name}' 参数过多 ({param_count} 个参数)",
                            line_number=i + 1,
                            line_content=line.strip(),
                            suggestion=f"使用参数对象重构 {method_name}，或考虑是否违反了单一职责原则",
                            code_snippet=[line.strip()]
                        ))
        
        return issues
    
    def _find_naming_issues(self, lines: List[str]) -> List[CodeIssue]:
        """查找命名约定问题"""
        issues = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 检查类名
            class_match = re.search(r'class\s+(\w+)', stripped, re.IGNORECASE)
            if class_match:
                class_name = class_match.group(1)
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', class_name):
                    suggested_name = self._to_pascal_case(class_name)
                    issues.append(CodeIssue(
                        type="naming_violation",
                        severity="info",
                        message=f"类名违反PSR-1规范: '{class_name}'",
                        line_number=i + 1,
                        line_content=stripped,
                        suggestion=f"类名应使用PascalCase命名:\n修改前: class {class_name}\n修改后: class {suggested_name}",
                        code_snippet=[stripped]
                    ))
            
            # 检查方法名
            method_match = re.search(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)', stripped, re.IGNORECASE)
            if method_match:
                method_name = method_match.group(1)
                if not method_name.startswith('__') and not re.match(r'^[a-z][a-zA-Z0-9]*$', method_name):
                    suggested_name = self._to_camel_case(method_name)
                    issues.append(CodeIssue(
                        type="naming_violation", 
                        severity="info",
                        message=f"方法名违反PSR-1规范: '{method_name}'",
                        line_number=i + 1,
                        line_content=stripped,
                        suggestion=f"方法名应使用camelCase命名:\n修改前: function {method_name}(...)\n修改后: function {suggested_name}(...)",
                        code_snippet=[stripped]
                    ))
            
            # 检查变量名
            var_matches = re.findall(r'\$([A-Z_][A-Z0-9_]*)', line)
            for var_name in var_matches:
                if var_name not in ['GLOBALS', 'POST', 'GET', 'SESSION', 'COOKIE', 'SERVER', 'FILES', 'ENV']:  # 排除超全局变量
                    suggested_name = self._to_camel_case(var_name)
                    issues.append(CodeIssue(
                        type="naming_violation",
                        severity="info", 
                        message=f"变量名违反约定: '\${var_name}'",
                        line_number=i + 1,
                        line_content=stripped,
                        suggestion=f"变量名应使用camelCase:\n修改前: \${var_name}\n修改后: \${suggested_name}",
                        code_snippet=[stripped]
                    ))
        
        return issues
    
    def _find_uncommented_methods(self, lines: List[str]) -> List[CodeIssue]:
        """查找缺少注释的方法"""
        issues = []
        
        for i, line in enumerate(lines):
            method_match = re.search(r'(public|private|protected)\s+function\s+(\w+)', line, re.IGNORECASE)
            if method_match:
                method_name = method_match.group(2)
                
                # 检查前面几行是否有注释
                has_comment = False
                for j in range(max(0, i - 3), i):
                    if '//' in lines[j] or '/*' in lines[j] or '*' in lines[j]:
                        has_comment = True
                        break
                
                if not has_comment:
                    issues.append(CodeIssue(
                        type="missing_documentation",
                        severity="info",
                        message=f"方法 '{method_name}' 缺少文档注释",
                        line_number=i + 1,
                        line_content=line.strip(),
                        suggestion=f"为 {method_name} 方法添加PHPDoc注释，说明功能、参数和返回值",
                        code_snippet=[line.strip()]
                    ))
        
        return issues
    
    def _find_sql_injection_risks(self, lines: List[str]) -> List[CodeIssue]:
        """查找SQL注入风险"""
        issues = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 检测直接字符串拼接的SQL - 更全面的模式
            sql_patterns = [
                r'(SELECT|INSERT|UPDATE|DELETE).*\$\w+',  # 直接变量拼接
                r'(SELECT|INSERT|UPDATE|DELETE).*\.\s*\$',  # . $var拼接
                r'(SELECT|INSERT|UPDATE|DELETE).*".*\$.*"',  # 双引号内变量拼接
                r'(SELECT|INSERT|UPDATE|DELETE).*\'.*\$.*\'',  # 单引号内变量拼接
            ]
            
            for pattern in sql_patterns:
                if re.search(pattern, stripped, re.IGNORECASE):
                    # 排除已经使用预处理语句的情况
                    if not re.search(r'(prepare|PDO::PARAM|bindParam|bindValue|\?)', stripped, re.IGNORECASE):
                        # 获取上下文
                        context_start = max(0, i - 2)
                        context_end = min(len(lines), i + 3)
                        context = [lines[j].rstrip() for j in range(context_start, context_end)]
                        
                        issues.append(CodeIssue(
                            type="sql_injection_risk",
                            severity="error",
                            message=f"第{i+1}行发现SQL注入风险: 直接拼接变量到SQL语句",
                            line_number=i + 1,
                            line_content=stripped,
                            suggestion="修复建议:\n1. 使用PDO预处理语句: $stmt = $pdo->prepare('SELECT * FROM users WHERE id = ?');\n2. 绑定参数: $stmt->execute([$userId]);\n3. 或使用命名参数: WHERE id = :id",
                            code_snippet=context
                        ))
                        break  # 避免重复检测同一行
        
        return issues
    
    def _find_security_issues(self, lines: List[str]) -> List[CodeIssue]:
        """查找安全问题"""
        issues = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 1. 检测直接使用$_GET/$_POST/$_REQUEST
            if re.search(r'\$_(GET|POST|REQUEST|COOKIE)\[', stripped):
                if not re.search(r'(filter_|htmlspecialchars|strip_tags|mysqli_real_escape_string)', stripped):
                    issues.append(CodeIssue(
                        type="xss_risk",
                        severity="error", 
                        message=f"第{i+1}行XSS风险: 直接使用用户输入",
                        line_number=i + 1,
                        line_content=stripped,
                        suggestion="修复建议:\n1. 使用filter_input()验证输入\n2. 使用htmlspecialchars()防止XSS\n3. 验证数据类型和格式",
                        code_snippet=[stripped]
                    ))
            
            # 2. 检测明文密码存储
            if re.search(r'\$.*password.*=.*\$.*password', stripped, re.IGNORECASE):
                if not re.search(r'(password_hash|hash|crypt|bcrypt)', stripped, re.IGNORECASE):
                    issues.append(CodeIssue(
                        type="password_security",
                        severity="error",
                        message=f"第{i+1}行密码安全: 密码可能以明文存储",
                        line_number=i + 1,
                        line_content=stripped,
                        suggestion="修复建议:\n1. 使用password_hash()加密密码\n2. 使用password_verify()验证密码\n3. 永远不要存储明文密码",
                        code_snippet=[stripped]
                    ))
            
            # 3. 检测硬编码的数据库连接
            if re.search(r'new\s+PDO\(.*localhost.*root.*[\'"][0-9]+[\'"]', stripped):
                issues.append(CodeIssue(
                    type="hardcoded_credentials",
                    severity="warning",
                    message=f"第{i+1}行安全风险: 硬编码的数据库连接信息",
                    line_number=i + 1,
                    line_content=stripped,
                    suggestion="修复建议:\n1. 使用环境变量存储敏感信息\n2. 使用配置文件(不提交到版本控制)\n3. 使用依赖注入管理数据库连接",
                    code_snippet=[stripped]
                ))
            
            # 4. 检测缺少错误处理
            if re.search(r'(->query\(|->exec\(|mail\()', stripped):
                # 检查后续几行是否有错误处理
                has_error_handling = False
                for j in range(i, min(i + 3, len(lines))):
                    if re.search(r'(try|catch|if.*false|error)', lines[j], re.IGNORECASE):
                        has_error_handling = True
                        break
                
                if not has_error_handling:
                    issues.append(CodeIssue(
                        type="missing_error_handling",
                        severity="warning",
                        message=f"第{i+1}行缺少错误处理",
                        line_number=i + 1,
                        line_content=stripped,
                        suggestion="修复建议:\n1. 使用try-catch处理异常\n2. 检查函数返回值\n3. 记录错误日志\n4. 向用户显示友好的错误信息",
                        code_snippet=[stripped]
                    ))
        
        return issues
    
    def _find_code_quality_issues(self, lines: List[str]) -> List[CodeIssue]:
        """查找代码质量问题"""
        issues = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 1. 检测缺少类注释
            if re.search(r'^class\s+\w+', stripped):
                # 检查前面几行是否有注释
                has_comment = False
                for j in range(max(0, i - 3), i):
                    if re.search(r'(/\*|\*|//)', lines[j]):
                        has_comment = True
                        break
                
                if not has_comment:
                    issues.append(CodeIssue(
                        type="missing_class_comment",
                        severity="info",
                        message=f"第{i+1}行缺少类注释",
                        line_number=i + 1,
                        line_content=stripped,
                        suggestion="添加类注释说明:\n1. 类的用途和职责\n2. 主要功能说明\n3. 使用示例\n4. @author, @since等标签",
                        code_snippet=[stripped]
                    ))
            
            # 2. 检测public属性
            if re.search(r'public\s+\$\w+', stripped):
                issues.append(CodeIssue(
                    type="public_property",
                    severity="warning",
                    message=f"第{i+1}行违反封装原则: public属性",
                    line_number=i + 1,
                    line_content=stripped,
                    suggestion="修复建议:\n1. 将属性改为private或protected\n2. 提供getter/setter方法\n3. 使用readonly属性(PHP 8.1+)",
                    code_snippet=[stripped]
                ))
            
            # 3. 检测缺少类型声明
            if re.search(r'function\s+\w+\([^)]*\$\w+[^)]*\)', stripped):
                if not re.search(r'(int|string|bool|array|object|\w+\s+\$)', stripped):
                    issues.append(CodeIssue(
                        type="missing_type_declaration",
                        severity="info",
                        message=f"第{i+1}行缺少参数类型声明",
                        line_number=i + 1,
                        line_content=stripped,
                        suggestion="添加类型声明:\n1. function getUserById(int $userId, bool $includeProfile = null)\n2. 使用返回类型: function getName(): string\n3. 使用nullable类型: ?string",
                        code_snippet=[stripped]
                    ))
            
            # 4. 检测缺少访问修饰符
            if re.search(r'^\s*function\s+\w+', stripped) and not re.search(r'(public|private|protected)', stripped):
                issues.append(CodeIssue(
                    type="missing_access_modifier",
                    severity="warning",
                    message=f"第{i+1}行缺少访问修饰符",
                    line_number=i + 1,
                    line_content=stripped,
                    suggestion="添加访问修饰符:\n1. public function - 公开方法\n2. private function - 私有方法\n3. protected function - 受保护方法",
                    code_snippet=[stripped]
                ))
            
            # 5. 检测全局变量
            if re.search(r'^\$\w+\s*=', stripped):
                issues.append(CodeIssue(
                    type="global_variable",
                    severity="warning",
                    message=f"第{i+1}行使用全局变量",
                    line_number=i + 1,
                    line_content=stripped,
                    suggestion="避免全局变量:\n1. 使用类属性\n2. 使用依赖注入\n3. 使用配置类\n4. 使用单例模式(谨慎使用)",
                    code_snippet=[stripped]
                ))
        
        return issues
    
    def _find_logic_errors(self, lines: List[str]) -> List[CodeIssue]:
        """查找逻辑错误和危险模式"""
        issues = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 1. 检测潜在的死循环
            if re.search(r'while\s*\(\s*(true|1|TRUE)\s*\)', stripped):
                # 检查循环体内是否有break语句
                has_break = False
                brace_count = 0
                found_opening_brace = False
                
                for j in range(i, min(i + 50, len(lines))):  # 检查后续50行
                    loop_line = lines[j].strip()
                    
                    if '{' in loop_line:
                        found_opening_brace = True
                        brace_count += loop_line.count('{')
                        brace_count -= loop_line.count('}')
                    elif found_opening_brace:
                        brace_count += loop_line.count('{')
                        brace_count -= loop_line.count('}')
                    
                    if 'break' in loop_line or 'return' in loop_line or 'exit' in loop_line:
                        has_break = True
                    
                    if found_opening_brace and brace_count == 0:
                        break
                
                if not has_break:
                    issues.append(CodeIssue(
                        type="infinite_loop_risk",
                        severity="error",
                        message=f"第{i+1}行发现潜在的死循环: while(true)无exit条件",
                        line_number=i + 1,
                        line_content=stripped,
                        suggestion="修复建议:\n1. 添加break或return语句\n2. 使用有条件的循环: while($condition)\n3. 添加计数器防止无限循环\n4. 使用for循环替代",
                        code_snippet=[stripped]
                    ))
            
            # 2. 检测for循环中的死循环模式
            if re.search(r'for\s*\(\s*[^;]*;\s*[^;]*;\s*[^)]*\)', stripped):
                # 检测i++但条件为i < 某个不变值的情况
                if re.search(r'for\s*\(\s*\$\w+\s*=\s*\d+\s*;\s*\$\w+\s*[<>]=?\s*\d+\s*;\s*\)', stripped):
                    issues.append(CodeIssue(
                        type="infinite_loop_risk",
                        severity="error",
                        message=f"第{i+1}行for循环缺少递增/递减语句",
                        line_number=i + 1,
                        line_content=stripped,
                        suggestion="修复建议:\n1. 添加$i++或$i--\n2. 确保循环变量会改变\n3. 检查循环终止条件",
                        code_snippet=[stripped]
                    ))
            
            # 3. 检测可能的无限递归
            if re.search(r'function\s+(\w+)', stripped):
                function_name = re.search(r'function\s+(\w+)', stripped).group(1)
                # 检查函数体内是否直接调用自己且没有终止条件
                brace_count = 0
                found_opening_brace = False
                has_termination = False
                has_self_call = False
                
                for j in range(i, min(i + 100, len(lines))):
                    func_line = lines[j].strip()
                    
                    if '{' in func_line:
                        found_opening_brace = True
                        brace_count += func_line.count('{')
                        brace_count -= func_line.count('}')
                    elif found_opening_brace:
                        brace_count += func_line.count('{')
                        brace_count -= func_line.count('}')
                    
                    if found_opening_brace and f'{function_name}(' in func_line:
                        has_self_call = True
                    
                    if re.search(r'(if|return|break|\$\w+\s*[<>]=?)', func_line):
                        has_termination = True
                    
                    if found_opening_brace and brace_count == 0:
                        break
                
                if has_self_call and not has_termination:
                    issues.append(CodeIssue(
                        type="infinite_recursion_risk",
                        severity="error",
                        message=f"第{i+1}行函数'{function_name}'可能存在无限递归",
                        line_number=i + 1,
                        line_content=stripped,
                        suggestion="修复建议:\n1. 添加递归终止条件\n2. 确保参数在递归中会改变\n3. 添加递归深度限制\n4. 考虑使用迭代替代递归",
                        code_snippet=[stripped]
                    ))
            
            # 4. 检测空的catch块
            if re.search(r'catch\s*\([^)]*\)\s*\{?\s*\}?', stripped):
                # 检查catch块是否为空
                if i + 1 < len(lines) and lines[i + 1].strip() == '}':
                    issues.append(CodeIssue(
                        type="empty_catch_block",
                        severity="error",
                        message=f"第{i+1}行空的catch块: 忽略异常是危险的",
                        line_number=i + 1,
                        line_content=stripped,
                        suggestion="修复建议:\n1. 记录错误日志\n2. 显示用户友好的错误信息\n3. 重新抛出异常\n4. 执行清理操作",
                        code_snippet=[stripped]
                    ))
            
            # 5. 检测可能的内存泄漏
            if re.search(r'while\s*\([^)]*\)', stripped):
                # 检查循环内是否有大对象创建但没有释放
                for j in range(i + 1, min(i + 20, len(lines))):
                    if 'new ' in lines[j] and 'unset' not in lines[j]:
                        issues.append(CodeIssue(
                            type="memory_leak_risk",
                            severity="warning",
                            message=f"第{j+1}行循环内创建对象可能导致内存泄漏",
                            line_number=j + 1,
                            line_content=lines[j].strip(),
                            suggestion="修复建议:\n1. 在循环外创建对象\n2. 使用unset()释放大对象\n3. 避免在循环内创建不必要的对象\n4. 考虑使用对象池模式",
                            code_snippet=[lines[j].strip()]
                        ))
                        break
            
            # 6. 检测除零错误
            if re.search(r'/\s*\$\w+', stripped) and 'if' not in stripped:
                issues.append(CodeIssue(
                    type="division_by_zero_risk",
                    severity="warning",
                    message=f"第{i+1}行可能的除零错误",
                    line_number=i + 1,
                    line_content=stripped,
                    suggestion="修复建议:\n1. 在除法前检查除数不为零\n2. 使用条件语句: if($divisor != 0)\n3. 抛出适当的异常",
                    code_snippet=[stripped]
                ))
            
            # 7. 检测数组越界风险
            if re.search(r'\$\w+\[\$\w+\]', stripped) and 'isset' not in stripped and 'array_key_exists' not in stripped:
                issues.append(CodeIssue(
                    type="array_bounds_risk",
                    severity="warning",
                    message=f"第{i+1}行可能的数组越界访问",
                    line_number=i + 1,
                    line_content=stripped,
                    suggestion="修复建议:\n1. 使用isset()检查键是否存在\n2. 使用array_key_exists()检查\n3. 使用null合并运算符: $arr[$key] ?? $default",
                    code_snippet=[stripped]
                ))
            
            # 8. 检测文件操作缺少检查
            if re.search(r'(fopen|file_get_contents|include|require)\(', stripped):
                if not re.search(r'(file_exists|is_readable|@)', stripped):
                    issues.append(CodeIssue(
                        type="file_operation_risk",
                        severity="warning",
                        message=f"第{i+1}行文件操作缺少存在性检查",
                        line_number=i + 1,
                        line_content=stripped,
                        suggestion="修复建议:\n1. 使用file_exists()检查文件是否存在\n2. 使用is_readable()检查权限\n3. 使用try-catch处理文件异常\n4. 检查函数返回值",
                        code_snippet=[stripped]
                    ))
        
        return issues
    
    def _find_performance_issues(self, lines: List[str]) -> List[CodeIssue]:
        """查找性能问题"""
        issues = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 1. 检测循环内的数据库查询
            if re.search(r'(for|while|foreach)\s*\(', stripped):
                for j in range(i + 1, min(i + 30, len(lines))):
                    if re.search(r'(->query\(|->prepare\(|mysql_|mysqli_)', lines[j]):
                        issues.append(CodeIssue(
                            type="query_in_loop",
                            severity="error",
                            message=f"第{j+1}行在循环内执行数据库查询 (N+1问题)",
                            line_number=j + 1,
                            line_content=lines[j].strip(),
                            suggestion="修复建议:\n1. 将查询移到循环外\n2. 使用JOIN合并查询\n3. 使用IN子句批量查询\n4. 考虑使用ORM的eager loading",
                            code_snippet=[lines[j].strip()]
                        ))
                        break
            
            # 2. 检测大文件读取
            if re.search(r'file_get_contents\(', stripped):
                issues.append(CodeIssue(
                    type="large_file_read_risk",
                    severity="warning",
                    message=f"第{i+1}行使用file_get_contents可能导致内存问题",
                    line_number=i + 1,
                    line_content=stripped,
                    suggestion="修复建议:\n1. 对大文件使用fopen/fread分块读取\n2. 使用SplFileObject逐行读取\n3. 设置内存限制检查\n4. 考虑流式处理",
                    code_snippet=[stripped]
                ))
            
            # 3. 检测字符串连接在循环中
            if re.search(r'(for|while|foreach)\s*\(', stripped):
                for j in range(i + 1, min(i + 20, len(lines))):
                    if re.search(r'\$\w+\s*\.=', lines[j]):
                        issues.append(CodeIssue(
                            type="string_concat_in_loop",
                            severity="warning",
                            message=f"第{j+1}行循环内字符串连接影响性能",
                            line_number=j + 1,
                            line_content=lines[j].strip(),
                            suggestion="修复建议:\n1. 使用数组收集字符串，最后implode()\n2. 使用StringBuilder模式\n3. 预先估算字符串长度",
                            code_snippet=[lines[j].strip()]
                        ))
                        break
            
            # 4. 检测正则表达式在循环中编译
            if re.search(r'(for|while|foreach)\s*\(', stripped):
                for j in range(i + 1, min(i + 20, len(lines))):
                    if re.search(r'preg_(match|replace)\(', lines[j]):
                        issues.append(CodeIssue(
                            type="regex_compile_in_loop",
                            severity="info",
                            message=f"第{j+1}行循环内编译正则表达式",
                            line_number=j + 1,
                            line_content=lines[j].strip(),
                            suggestion="性能优化:\n1. 将正则表达式移到循环外预编译\n2. 使用preg_match_all批量处理\n3. 考虑使用更快的字符串函数",
                            code_snippet=[lines[j].strip()]
                        ))
                        break
            
            # 5. 检测冗余的函数调用
            if re.search(r'count\(\$\w+\)', stripped) and 'for' in stripped:
                issues.append(CodeIssue(
                    type="redundant_function_call",
                    severity="info",
                    message=f"第{i+1}行循环条件中调用count()影响性能",
                    line_number=i + 1,
                    line_content=stripped,
                    suggestion="性能优化:\n1. 将count()结果缓存到变量\n2. 使用foreach替代for循环\n3. 或改为: for($i = 0, $len = count($arr); $i < $len; $i++)",
                    code_snippet=[stripped]
                ))
        
        return issues
    
    def _to_pascal_case(self, name: str) -> str:
        """转换为PascalCase"""
        parts = re.split(r'[_\-\s]+', name.lower())
        return ''.join(word.capitalize() for word in parts if word)
    
    def _to_camel_case(self, name: str) -> str:
        """转换为camelCase"""
        parts = re.split(r'[_\-\s]+', name.lower())
        if not parts:
            return name
        return parts[0] + ''.join(word.capitalize() for word in parts[1:] if word)
    
    def detect_batch(self, file_paths: List[str]) -> List[SmellDetectionResult]:
        """批量检测代码异味"""
        results = []
        
        print(f"开始批量检测 {len(file_paths)} 个文件...")
        
        for i, file_path in enumerate(file_paths):
            try:
                result = self.detect_smells(file_path)
                results.append(result)
                
                if (i + 1) % 10 == 0:
                    print(f"已检测 {i + 1}/{len(file_paths)} 个文件")
                    
            except Exception as e:
                print(f"检测文件 {file_path} 时出错: {e}")
                continue
        
        print(f"批量检测完成，成功检测 {len(results)} 个文件")
        return results
    
    def generate_report(self, results: List[SmellDetectionResult], output_path: str):
        """生成检测报告"""
        # 统计信息
        total_files = len(results)
        smell_counts = {}
        severity_counts = {'error': 0, 'warning': 0, 'info': 0}
        
        for result in results:
            smell_type = result.smell_type
            smell_counts[smell_type] = smell_counts.get(smell_type, 0) + 1
            
            for issue in result.issues:
                severity = issue.get('severity', 'info')
                severity_counts[severity] += 1
        
        # 生成HTML报告
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>代码异味检测报告</title>
         <style>
         body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
         .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
         .summary {{ display: flex; justify-content: space-around; margin: 20px 0; }}
         .summary-item {{ text-align: center; padding: 15px; background-color: #e9ecef; border-radius: 5px; }}
         .file-result {{ margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
         .clean {{ background-color: #d4edda; }}
         .warning {{ background-color: #fff3cd; }}
         .error {{ background-color: #f8d7da; }}
         .issue {{ margin: 15px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #007bff; border-radius: 4px; }}
         .issue.warning {{ border-left-color: #ffc107; }}
         .issue.error {{ border-left-color: #dc3545; }}
         .issue.info {{ border-left-color: #17a2b8; }}
         .issue-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
         .line-number {{ background-color: #6c757d; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px; }}
         .code-location {{ margin: 10px 0; }}
         .code-snippet {{ background-color: #f1f3f4; padding: 10px; border-radius: 4px; border: 1px solid #dee2e6; font-family: 'Courier New', monospace; font-size: 14px; overflow-x: auto; }}
         .code-block {{ background-color: #f8f9fa; padding: 15px; border-radius: 4px; border: 1px solid #dee2e6; font-family: 'Courier New', monospace; font-size: 13px; overflow-x: auto; line-height: 1.4; }}
         .suggestion-detail {{ margin-top: 10px; padding: 8px; background-color: #e7f3ff; border-radius: 4px; white-space: pre-line; }}
         .code-context {{ margin-top: 10px; }}
         .code-context summary {{ cursor: pointer; color: #007bff; font-weight: bold; }}
         .code-context summary:hover {{ text-decoration: underline; }}
         .suggestions {{ margin-top: 15px; padding: 10px; background-color: #f0f8ff; border-radius: 4px; }}
         .suggestions ul {{ margin: 5px 0; }}
         pre {{ margin: 0; white-space: pre-wrap; word-wrap: break-word; }}
     </style>
</head>
<body>
    <div class="header">
        <h1>代码异味检测报告</h1>
        <p>检测时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <div class="summary-item">
            <h3>{total_files}</h3>
            <p>检测文件数</p>
        </div>
        <div class="summary-item">
            <h3>{severity_counts['error']}</h3>
            <p>错误</p>
        </div>
        <div class="summary-item">
            <h3>{severity_counts['warning']}</h3>
            <p>警告</p>
        </div>
        <div class="summary-item">
            <h3>{severity_counts['info']}</h3>
            <p>提示</p>
        </div>
    </div>
    
    <h2>异味类型分布</h2>
    <ul>
"""
        
        for smell_type, count in smell_counts.items():
            html_content += f"<li>{smell_type}: {count} 个文件</li>\n"
        
        html_content += """
    </ul>
    
    <h2>详细结果</h2>
"""
        
        for result in results:
            css_class = 'clean' if result.smell_type == 'clean' else 'warning'
            if any(issue.get('severity') == 'error' for issue in result.issues):
                css_class = 'error'
            
            html_content += f"""
    <div class="file-result {css_class}">
        <h3>{os.path.basename(result.file_path)}</h3>
        <p><strong>文件路径:</strong> {result.file_path}</p>
        <p><strong>主要异味:</strong> {self.get_smell_description(result.smell_type)} ({result.smell_type}) (置信度: {result.confidence:.2%})</p>
        
        <h4>检测到的问题:</h4>
"""
            
            # 显示详细问题（新增）
            if hasattr(result, 'detailed_issues') and result.detailed_issues:
                for issue in result.detailed_issues:
                    severity_icon = {'error': '🚨', 'warning': '⚠️', 'info': 'ℹ️'}.get(issue.severity, 'ℹ️')
                    html_content += f"""
        <div class="issue {issue.severity}">
            <div class="issue-header">
                <strong>{severity_icon} {issue.message}</strong>
                <span class="line-number">第 {issue.line_number} 行</span>
            </div>
            <div class="code-location">
                <strong>问题代码:</strong>
                <pre class="code-snippet">{issue.line_content}</pre>
            </div>
            <div class="suggestion-detail">
                <strong>💡 改进建议:</strong> {issue.suggestion}
            </div>
"""
                    if len(issue.code_snippet) > 1:
                        html_content += """
            <details class="code-context">
                <summary>查看代码上下文</summary>
                <pre class="code-block">"""
                        for j, line in enumerate(issue.code_snippet):
                            line_num = issue.line_number + j - 1
                            html_content += f"{line_num:3d}: {line}\n"
                        html_content += """</pre>
            </details>"""
                    
                    html_content += "        </div>\n"
            
            elif result.issues:
                for issue in result.issues:
                    html_content += f"""
        <div class="issue {issue.get('severity', 'info')}">
            <strong>{issue['message']}</strong><br>
            {issue['details']}
        </div>
"""
            else:
                html_content += "<p>未发现明显问题</p>"
            
            if result.suggestions:
                html_content += """
        <div class="suggestions">
            <h4>通用改进建议:</h4>
            <ul>
"""
                for suggestion in result.suggestions:
                    html_content += f"<li>{suggestion}</li>\n"
                
                html_content += """
            </ul>
        </div>
"""
            
            html_content += "    </div>\n"
        
        html_content += """
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"检测报告已保存到: {output_path}")

def main():
    """演示代码异味检测器"""
    import tempfile
    
    detector = CodeSmellDetector()
    
    # 创建测试文件
    test_files = []
    
    # 1. 清洁代码示例
    clean_code = '''<?php
class UserService {
    private $repository;
    
    public function __construct(UserRepository $repository) {
        $this->repository = $repository;
    }
    
    public function createUser($email, $name) {
        if (!$this->isValidEmail($email)) {
            throw new InvalidArgumentException('Invalid email');
        }
        
        $user = new User($email, $name);
        return $this->repository->save($user);
    }
    
    private function isValidEmail($email) {
        return filter_var($email, FILTER_VALIDATE_EMAIL) !== false;
    }
}
?>'''
    
    # 2. 有问题的代码示例
    bad_code = '''<?php
class bad_user_manager {
    public function VERY_COMPLEX_USER_PROCESSING_METHOD($user_data, $validation_rules, $processing_options, $email_settings, $logging_config, $cache_settings, $security_options) {
        $result = [];
        
        if ($user_data && is_array($user_data) && count($user_data) > 0) {
            for ($i = 0; $i < count($user_data); $i++) {
                if (isset($user_data[$i]['email']) && !empty($user_data[$i]['email'])) {
                    if (filter_var($user_data[$i]['email'], FILTER_VALIDATE_EMAIL)) {
                        if (isset($validation_rules['email_domain_check']) && $validation_rules['email_domain_check']) {
                            $domain = substr(strrchr($user_data[$i]['email'], "@"), 1);
                            if (in_array($domain, $validation_rules['allowed_domains'])) {
                                if (isset($user_data[$i]['name']) && strlen($user_data[$i]['name']) > 2) {
                                    if (isset($processing_options['name_validation']) && $processing_options['name_validation']) {
                                        if (preg_match('/^[a-zA-Z\s]+$/', $user_data[$i]['name'])) {
                                            if (isset($user_data[$i]['age']) && is_numeric($user_data[$i]['age'])) {
                                                if ($user_data[$i]['age'] >= 18 && $user_data[$i]['age'] <= 120) {
                                                    $processed_user = [];
                                                    $processed_user['email'] = strtolower(trim($user_data[$i]['email']));
                                                    $processed_user['name'] = ucwords(strtolower(trim($user_data[$i]['name'])));
                                                    $processed_user['age'] = intval($user_data[$i]['age']);
                                                    
                                                    if (isset($email_settings['send_welcome_email']) && $email_settings['send_welcome_email']) {
                                                        // 非常复杂的邮件发送逻辑
                                                        $email_template = $email_settings['template'];
                                                        $email_subject = str_replace('{name}', $processed_user['name'], $email_template['subject']);
                                                        $email_body = str_replace('{name}', $processed_user['name'], $email_template['body']);
                                                        // ... 更多邮件处理逻辑
                                                    }
                                                    
                                                    $result[] = $processed_user;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        return $result;
    }
}
?>'''
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='_clean.php', delete=False) as f:
        f.write(clean_code)
        test_files.append(f.name)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_bad.php', delete=False) as f:
        f.write(bad_code)
        test_files.append(f.name)
    
    try:
        # 批量检测
        results = detector.detect_batch(test_files)
        
        # 显示结果
        for result in results:
            print(f"\n文件: {os.path.basename(result.file_path)}")
            print(f"异味类型: {detector.get_smell_description(result.smell_type)} ({result.smell_type}) (置信度: {result.confidence:.2%})")
            print(f"代码行数: {result.features.lines_of_code}")
            print(f"圈复杂度: {result.features.cyclomatic_complexity}")
            
            if result.issues:
                print("问题:")
                for issue in result.issues:
                    print(f"  - {issue['message']}: {issue['details']}")
            
            if result.suggestions:
                print("建议:")
                for suggestion in result.suggestions:
                    print(f"  - {suggestion}")
        
        # 生成报告
        detector.generate_report(results, 'code_smell_report.html')
        
    finally:
        # 清理临时文件
        for file_path in test_files:
            if os.path.exists(file_path):
                os.unlink(file_path)

if __name__ == '__main__':
    main() 