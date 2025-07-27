# PR-Agent 本地实施指南

## 🏠 环境准备

### 1. 安装 Python 环境
```bash
# 检查 Python 版本（需要 3.8+）
python --version

# 如果没有 Python，下载安装：
# Windows: https://www.python.org/downloads/
# 或使用 Anaconda: https://www.anaconda.com/
```

### 2. 克隆 PR-Agent 项目
```bash
# 克隆官方仓库
git clone https://github.com/Codium-ai/pr-agent.git
cd pr-agent

# 或者 Fork 后克隆自己的仓库（推荐）
git clone https://github.com/你的用户名/pr-agent.git
cd pr-agent
```

### 3. 创建虚拟环境
```bash
# 创建虚拟环境
python -m venv pr_agent_env

# 激活虚拟环境
# Windows:
source pr_agent_env/Scripts/activate

# Linux/Mac:
source pr_agent_env/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 🔑 GitHub Token 配置

### 1. 创建 GitHub Personal Access Token
1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 选择权限范围：
   - ✅ `repo` (完整仓库访问)
   - ✅ `read:org` (读取组织信息)
   - ✅ `workflow` (访问 GitHub Actions)
4. 复制生成的 token [ghp_your_token_here]

### 2. 配置环境变量
```bash
# Windows PowerShell:
$env:GITHUB_TOKEN="ghp_your_token_here"
$env:OPENAI_KEY="sk-your_openai_key_here"  # 可选，用于更好的AI分析

# 在Git Bash中
export GITHUB_TOKEN="ghp_your_token_here"
# Linux/Mac/git bash:
export GITHUB_TOKEN="ghp_your_token_here"
export OPENAI_KEY="sk-your_openai_key_here"
```

## ⚙️ 本地配置文件

### 1. 创建配置文件
```bash
# 在项目根目录创建配置文件
cat > .pr_agent.toml << EOF
[config]
model = "gpt-4o-mini"  # 或使用免费的本地模型
max_description_tokens = 500
max_commits_tokens = 500

[github]
user_token = "ghp_your_token_here"
try_fix_invalid_tokens = true

[pr_reviewer]
# PR审查配置
require_tests_review = true
require_security_review = true
require_focused_review = true
num_code_suggestions = 3
inline_code_comments = true

# PHP特定配置
extra_instructions = """
重点关注以下PHP代码问题：
1. 魔数检测 - 硬编码的数字和字符串
2. 长方法 - 超过20行的方法
3. 重复代码 - 相似的代码块
4. 安全问题 - SQL注入、XSS风险
5. 性能问题 - N+1查询、内存泄漏
"""

[pr_description]
use_bullet_points = true
add_original_user_description = true
keep_original_user_title = true
generate_ai_title = false

[pr_questions]
enable_pr_questions = true

[pr_code_suggestions]
num_code_suggestions = 3
commitable_code_suggestions = false
EOF
```

## 🚀 本地使用方法

### 方法一：分析现有PR
```bash
# 分析GitHub上的PR
python3 -m pr_agent.cli --pr_url="https://github.com/AIRsummer/AI_CR_PLAN_CodeRabbit/pull/3" review
python3 -m pr_agent.cli --pr_url "https://github.com/AIRsummer/AI_CR_PLAN_CodeRabbit/pull/3" review
# 生成PR描述
python -m pr_agent.cli \
  --pr_url="https://github.com/你的用户名/你的仓库/pull/1" \
  describe

# 生成代码建议
python -m pr_agent.cli \
  --pr_url="https://github.com/你的用户名/你的仓库/pull/1" \
  improve
```

### 方法二：分析本地代码差异
```bash
# 创建一个测试脚本
cat > local_analyze.py << 'EOF'
#!/usr/bin/env python3
import os
import subprocess
from pr_agent.cli import main

def analyze_local_changes():
    """分析本地Git变更"""
    
    # 1. 获取当前分支的变更
    try:
        # 获取与main分支的差异
        diff_output = subprocess.check_output(
            ['git', 'diff', 'main...HEAD'], 
            text=True
        )
        
        if not diff_output.strip():
            print("❌ 没有发现代码变更")
            return
            
        print("📊 发现代码变更，开始AI分析...")
        
        # 2. 创建临时文件保存diff
        with open('temp_diff.patch', 'w') as f:
            f.write(diff_output)
        
        # 3. 简单的PHP代码异味检测
        analyze_php_code_smells(diff_output)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git命令执行失败: {e}")
    except Exception as e:
        print(f"❌ 分析失败: {e}")

def analyze_php_code_smells(diff_content):
    """PHP代码异味检测"""
    issues = []
    lines = diff_content.split('\n')
    
    for i, line in enumerate(lines):
        if not line.startswith('+'):  # 只检查新增的代码
            continue
            
        line_content = line[1:].strip()  # 去掉+号
        
        # 检测魔数
        import re
        magic_numbers = re.findall(r'\b(\d{2,})\b', line_content)
        for num in magic_numbers:
            if num not in ['100', '200', '404', '500']:  # 排除常见HTTP状态码
                issues.append(f"🔢 行 {i+1}: 发现魔数 '{num}'，建议定义为常量")
        
        # 检测长字符串
        long_strings = re.findall(r'"([^"]{50,})"', line_content)
        for string in long_strings:
            issues.append(f"📝 行 {i+1}: 长字符串建议提取为配置: '{string[:30]}...'")
        
        # 检测重复的VIP折扣逻辑
        if 'vip' in line_content.lower() and any(x in line_content for x in ['0.9', '0.8', '0.7']):
            issues.append(f"💎 行 {i+1}: VIP折扣逻辑建议统一管理")
        
        # 检测可能的安全问题
        if '$_GET' in line_content or '$_POST' in line_content:
            if 'htmlspecialchars' not in line_content and 'filter_' not in line_content:
                issues.append(f"🔒 行 {i+1}: 用户输入未过滤，存在XSS风险")
    
    # 输出结果
    if issues:
        print("⚠️  发现以下代码问题：")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("✅ 未发现明显的代码问题")

if __name__ == '__main__':
    analyze_local_changes()
EOF

# 运行本地分析
python local_analyze.py
```

### 方法三：集成到Git Hook
```bash
# 创建预提交钩子
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "🤖 运行AI代码检测..."

# 运行PHP代码异味检测
python local_analyze.py

# 如果有问题，询问是否继续
if [ $? -ne 0 ]; then
    echo "⚠️  发现代码问题，是否继续提交？(y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        echo "❌ 提交已取消"
        exit 1
    fi
fi

echo "✅ 代码检测通过"
EOF

# 设置执行权限
chmod +x .git/hooks/pre-commit
```

## 🎯 PHP项目集成示例

### 在你的PHP项目中使用
```bash
# 1. 进入你的PHP项目目录
cd /path/to/your/php/project

# 2. 创建分支并修改代码
git checkout -b feature/ai-code-review

# 3. 修改一些PHP代码（故意加入一些问题）
cat > test_code.php << 'EOF'
<?php
class PriceCalculator {
    public function calculateVipPrice($originalPrice, $userLevel) {
        // 魔数问题
        if ($userLevel == 1) {
            return $originalPrice * 0.9;  // VIP折扣
        } elseif ($userLevel == 2) {
            return $originalPrice * 0.8;  // 超级VIP
        }
        return $originalPrice;
    }
    
    // 长方法问题
    public function processOrder($orderData) {
        // 安全问题：未过滤用户输入
        $userName = $_POST['user_name'];
        
        // ... 20+ 行代码
        for ($i = 0; $i < 25; $i++) {
            echo "Processing step " . $i . "\n";
        }
        
        return "Order processed";
    }
}
?>
EOF

# 4. 提交代码
git add test_code.php
git commit -m "Add price calculator with some issues"

# 5. 推送到GitHub
git push origin feature/ai-code-review

# 6. 在GitHub上创建PR
# 7. 运行PR-Agent分析
python -m pr_agent.cli \
  --pr_url="https://github.com/你的用户名/你的仓库/pull/新PR号码" \
  review
```

## 🔧 故障排除

### 常见问题解决

1. **Token权限不足**
```bash
# 重新生成token，确保包含所有必要权限
# repo, read:org, workflow
```

2. **依赖安装失败**
```bash
# 升级pip
pip install --upgrade pip

# 单独安装可能有问题的依赖
pip install --upgrade openai requests
```

3. **网络连接问题**
```bash
# 配置代理（如果需要）
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port
```

4. **本地Git配置**
```bash
# 确保Git配置正确
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## 📊 效果展示

运行成功后，你会看到类似这样的输出：
```
🤖 PR-Agent Analysis Results:

📋 PR Description:
- 添加了价格计算器类
- 实现了VIP用户折扣逻辑
- 包含订单处理功能

⚠️ Code Issues Found:
1. 🔢 Magic numbers detected: 0.9, 0.8 (建议定义为常量)
2. 🔒 Security risk: Unfiltered user input in $_POST['user_name']
3. 📏 Long method: processOrder() has 25+ lines
4. 🔄 Code duplication: Similar VIP discount logic

💡 Suggestions:
1. 创建 VipDiscountConstants 类
2. 使用 filter_input() 或 htmlspecialchars() 过滤输入
3. 将 processOrder() 方法拆分为更小的方法
4. 考虑使用策略模式处理不同VIP等级
```

这样就完成了PR-Agent的本地实施！你可以根据实际需求调整配置和检测规则。 