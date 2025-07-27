# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 PHP 和 Composer
sudo apt install -y php8.1 php8.1-cli composer
php -m | grep json


# 安装 Python 和 pip
sudo apt install python3 python3-pip python3-venv

# 安装机器学习依赖
sudo apt install libopenblas-dev  # 加速矩阵运算


#  项目初始化

## 创建项目目录：
mkdir php-ai-review && cd php-ai-review



# 初始化 PHP 和 Python 环境：
# PHP 依赖
composer require nikic/php-parser

# Python 虚拟环境
python3 -m venv venv
source venv/bin/activate

# Python 虚拟环境【步骤二】
# 创建虚拟环境（如果之前失败，换用 --copies）
python3 -m venv --copies ~/venv
# 激活虚拟环境
source ~/venv/bin/activate
# 现在可以安全安装
pip install scikit-learn pandas numpy joblib
pip install joblib scikit-learn pandas numpy

python3 install joblib