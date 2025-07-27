#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHP代码解析器
使用PHP内置的token_get_all函数来解析PHP代码
"""

import subprocess
import json
import re
import tempfile
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class PHPMethod:
    """PHP方法信息"""
    name: str
    lines: int
    complexity: int
    parameters: int
    visibility: str
    is_static: bool
    has_return_type: bool

@dataclass
class PHPClass:
    """PHP类信息"""
    name: str
    lines: int
    methods: List[PHPMethod]
    properties: int
    extends: Optional[str]
    implements: List[str]

@dataclass
class PHPFunction:
    """PHP函数信息"""
    name: str
    lines: int
    complexity: int
    parameters: int
    has_return_type: bool

class PHPParser:
    def __init__(self):
        self.php_tokenizer_script = self._create_tokenizer_script()
    
    def _create_tokenizer_script(self) -> str:
        """创建PHP tokenizer脚本"""
        script_content = '''<?php
// PHP代码解析脚本
function analyze_php_code($code) {
    $tokens = token_get_all($code);
    $analysis = [
        'classes' => [],
        'functions' => [],
        'complexity' => 0,
        'lines' => substr_count($code, "\n") + 1,
        'tokens_count' => count($tokens),
        'methods' => [],
        'variables' => [],
        'includes' => []
    ];
    
    $current_class = null;
    $current_function = null;
    $brace_level = 0;
    $complexity = 1; // 基础复杂度
    
    for ($i = 0; $i < count($tokens); $i++) {
        $token = $tokens[$i];
        
        if (is_array($token)) {
            $token_name = token_name($token[0]);
            $token_value = $token[1];
            
            switch ($token[0]) {
                case T_CLASS:
                    // 查找类名
                    for ($j = $i + 1; $j < count($tokens); $j++) {
                        if (is_array($tokens[$j]) && $tokens[$j][0] == T_STRING) {
                            $current_class = [
                                'name' => $tokens[$j][1],
                                'line' => $token[2],
                                'methods' => [],
                                'properties' => 0,
                                'extends' => null,
                                'implements' => []
                            ];
                            $analysis['classes'][] = $current_class;
                            break;
                        }
                    }
                    break;
                    
                case T_FUNCTION:
                    // 查找函数名
                    for ($j = $i + 1; $j < count($tokens); $j++) {
                        if (is_array($tokens[$j]) && $tokens[$j][0] == T_STRING) {
                            $func_info = [
                                'name' => $tokens[$j][1],
                                'line' => $token[2],
                                'parameters' => 0,
                                'complexity' => 1,
                                'visibility' => 'public'
                            ];
                            
                            // 计算参数个数
                            $param_start = false;
                            for ($k = $j; $k < count($tokens); $k++) {
                                if ($tokens[$k] == '(') {
                                    $param_start = true;
                                } elseif ($tokens[$k] == ')') {
                                    break;
                                } elseif ($param_start && $tokens[$k] == ',') {
                                    $func_info['parameters']++;
                                } elseif ($param_start && is_array($tokens[$k]) && $tokens[$k][0] == T_VARIABLE) {
                                    if ($func_info['parameters'] == 0) $func_info['parameters'] = 1;
                                }
                            }
                            
                            if ($current_class !== null) {
                                $analysis['classes'][count($analysis['classes'])-1]['methods'][] = $func_info;
                            } else {
                                $analysis['functions'][] = $func_info;
                            }
                            break;
                        }
                    }
                    break;
                    
                case T_IF:
                case T_ELSEIF:
                case T_WHILE:
                case T_FOR:
                case T_FOREACH:
                case T_SWITCH:
                    $complexity++;
                    break;
                    
                case T_VARIABLE:
                    if (!in_array($token_value, $analysis['variables'])) {
                        $analysis['variables'][] = $token_value;
                    }
                    break;
                    
                case T_INCLUDE:
                case T_INCLUDE_ONCE:
                case T_REQUIRE:
                case T_REQUIRE_ONCE:
                    $analysis['includes'][] = $token_value;
                    break;
            }
        } else {
            // 单字符token
            if ($token == '{') {
                $brace_level++;
            } elseif ($token == '}') {
                $brace_level--;
            }
        }
    }
    
    $analysis['complexity'] = $complexity;
    return $analysis;
}

if ($argc != 2) {
    echo json_encode(['error' => 'Usage: php script.php <file_path>']);
    exit(1);
}

$file_path = $argv[1];
if (!file_exists($file_path)) {
    echo json_encode(['error' => 'File not found: ' . $file_path]);
    exit(1);
}

$code = file_get_contents($file_path);
$result = analyze_php_code($code);
echo json_encode($result, JSON_PRETTY_PRINT);
?>'''
        
        # 保存PHP脚本到临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False) as f:
            f.write(script_content)
            return f.name
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """解析PHP文件"""
        try:
            # 使用PHP脚本解析文件
            result = subprocess.run([
                'php', self.php_tokenizer_script, file_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                # 如果PHP不可用，使用简单的正则表达式解析
                return self._simple_parse(file_path)
            
            return json.loads(result.stdout)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
            # PHP不可用时的备用解析方法
            return self._simple_parse(file_path)
    
    def _simple_parse(self, file_path: str) -> Dict[str, Any]:
        """简单的PHP代码解析（当PHP不可用时使用）"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 基本的代码分析
        lines = content.count('\n') + 1
        
        # 查找类
        class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?'
        classes = []
        for match in re.finditer(class_pattern, content, re.IGNORECASE):
            classes.append({
                'name': match.group(1),
                'extends': match.group(2),
                'implements': match.group(3).split(',') if match.group(3) else [],
                'methods': [],
                'properties': 0
            })
        
        # 查找函数
        function_pattern = r'function\s+(\w+)\s*\([^)]*\)'
        functions = []
        for match in re.finditer(function_pattern, content, re.IGNORECASE):
            functions.append({
                'name': match.group(1),
                'parameters': content[match.start():match.end()].count(',') + (1 if '(' in content[match.start():match.end()] and ')' in content[match.start():match.end()] else 0),
                'complexity': 1
            })
        
        # 计算复杂度
        complexity_keywords = ['if', 'elseif', 'else', 'while', 'for', 'foreach', 'switch', 'case', 'catch']
        complexity = 1
        for keyword in complexity_keywords:
            complexity += len(re.findall(r'\b' + keyword + r'\b', content, re.IGNORECASE))
        
        # 查找变量
        variables = list(set(re.findall(r'\$\w+', content)))
        
        return {
            'classes': classes,
            'functions': functions,
            'complexity': complexity,
            'lines': lines,
            'tokens_count': len(content.split()),
            'variables': variables,
            'includes': []
        }
    
    def __del__(self):
        """清理临时文件"""
        if hasattr(self, 'php_tokenizer_script') and os.path.exists(self.php_tokenizer_script):
            os.unlink(self.php_tokenizer_script)

def main():
    """测试函数"""
    parser = PHPParser()
    
    # 创建测试PHP文件
    test_php = '''<?php
class TestClass extends BaseClass implements TestInterface {
    private $property1;
    protected $property2;
    
    public function __construct($param1, $param2) {
        $this->property1 = $param1;
        $this->property2 = $param2;
    }
    
    public function complexMethod($data) {
        if ($data > 10) {
            for ($i = 0; $i < $data; $i++) {
                if ($i % 2 == 0) {
                    echo $i;
                } else {
                    continue;
                }
            }
        } elseif ($data < 0) {
            while ($data < 0) {
                $data++;
            }
        }
        return $data;
    }
}

function globalFunction($param) {
    switch ($param) {
        case 1:
            return "one";
        case 2:
            return "two";
        default:
            return "other";
    }
}
?>'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False) as f:
        f.write(test_php)
        test_file = f.name
    
    try:
        result = parser.parse_file(test_file)
        print("解析结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    finally:
        os.unlink(test_file)

if __name__ == '__main__':
    main() 