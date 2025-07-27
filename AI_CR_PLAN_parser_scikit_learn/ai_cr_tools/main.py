#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI代码异味检测主程序
基于php-parser + scikit-learn的代码异味检测系统
"""

import os
import sys
import argparse
import glob
import json
from typing import List
import warnings
warnings.filterwarnings('ignore')

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from code_smell_detector import CodeSmellDetector
from model_trainer import ModelTrainer
from feature_extractor import FeatureExtractor
from php_parser import PHPParser

def find_php_files(directory: str, recursive: bool = True) -> List[str]:
    """
    查找目录中的PHP文件
    
    Args:
        directory: 搜索目录
        recursive: 是否递归搜索
        
    Returns:
        PHP文件路径列表
    """
    php_files = []
    
    if recursive:
        pattern = os.path.join(directory, "**", "*.php")
        php_files = glob.glob(pattern, recursive=True)
    else:
        pattern = os.path.join(directory, "*.php")
        php_files = glob.glob(pattern)
    
    return php_files

def detect_command(args):
    """检测命令处理"""
    print("🔍 开始代码异味检测...")
    
    # 初始化检测器
    detector = CodeSmellDetector(models_dir=args.models_dir)
    
    # 确定要检测的文件
    php_files = []
    
    if args.file:
        # 检测单个文件
        if not os.path.exists(args.file):
            print(f"❌ 错误: 文件不存在 {args.file}")
            return
        php_files = [args.file]
    elif args.directory:
        # 检测目录中的文件
        if not os.path.exists(args.directory):
            print(f"❌ 错误: 目录不存在 {args.directory}")
            return
        php_files = find_php_files(args.directory, args.recursive)
    else:
        print("❌ 错误: 请指定要检测的文件或目录")
        return
    
    if not php_files:
        print("❌ 没有找到PHP文件")
        return
    
    print(f"📁 找到 {len(php_files)} 个PHP文件")
    
    # 批量检测
    results = detector.detect_batch(php_files)
    
    if not results:
        print("❌ 检测失败")
        return
    
    # 显示结果摘要
    print(f"\n📊 检测完成，共检测 {len(results)} 个文件")
    
    # 统计异味类型
    smell_counts = {}
    issue_counts = {'error': 0, 'warning': 0, 'info': 0}
    
    for result in results:
        smell_type = result.smell_type
        smell_counts[smell_type] = smell_counts.get(smell_type, 0) + 1
        
        for issue in result.issues:
            severity = issue.get('severity', 'info')
            issue_counts[severity] += 1
    
    print("\n🏷️  异味类型分布:")
    for smell_type, count in smell_counts.items():
        print(f"   {detector.get_smell_description(smell_type)} ({smell_type}): {count} 个文件")
    
    print(f"\n⚠️  问题统计:")
    print(f"   错误: {issue_counts['error']} 个")
    print(f"   警告: {issue_counts['warning']} 个")  
    print(f"   提示: {issue_counts['info']} 个")
    
    # 显示详细结果（如果启用详细模式）
    if args.verbose:
        print("\n📄 详细结果:")
        for result in results:
            print(f"\n📁 {os.path.basename(result.file_path)}")
            print(f"   异味类型: {detector.get_smell_description(result.smell_type)} ({result.smell_type}) (置信度: {result.confidence:.2%})")
            
            if result.issues:
                print("   问题:")
                for issue in result.issues:
                    severity_icon = {'error': '🚨', 'warning': '⚠️', 'info': 'ℹ️'}.get(issue['severity'], 'ℹ️')
                    print(f"   {severity_icon} {issue['message']}: {issue['details']}")
            
            if result.suggestions and args.suggestions:
                print("   建议:")
                for suggestion in result.suggestions:
                    print(f"   💡 {suggestion}")
    
    # 生成报告
    if args.output:
        detector.generate_report(results, args.output)
        print(f"\n📋 检测报告已保存到: {args.output}")

def train_command(args):
    """训练命令处理"""
    print("🚀 开始训练机器学习模型...")
    
    # 初始化训练器
    trainer = ModelTrainer(models_dir=args.models_dir)
    
    # 准备训练数据
    if args.synthetic:
        print("🎲 生成合成训练数据...")
        files, labels = trainer.generate_synthetic_data(args.samples)
    else:
        # 从指定目录收集真实数据（需要标注）
        if not args.data_dir:
            print("❌ 错误: 请指定训练数据目录或使用 --synthetic 生成合成数据")
            return
        
        # 这里应该实现从标注数据加载的逻辑
        print(f"📂 从 {args.data_dir} 加载训练数据...")
        # TODO: 实现真实数据加载逻辑
        files, labels = trainer.generate_synthetic_data(args.samples)
        print("⚠️  当前使用合成数据进行演示")
    
    try:
        # 准备训练数据
        X, y = trainer.prepare_training_data(files, labels)
        
        # 训练模型
        print("🔧 开始训练模型...")
        results = trainer.train_models(X, y, use_grid_search=args.grid_search)
        
        # 保存最佳模型
        best_model = trainer.save_best_model(results)
        
        # 显示结果
        print(f"\n✅ 训练完成！最佳模型: {best_model}")
        print("\n📈 模型性能:")
        for model_name, result in results.items():
            print(f"   {model_name}:")
            print(f"     准确率: {result['accuracy']:.4f}")
            print(f"     交叉验证: {result['cv_mean']:.4f} (±{result['cv_std']*2:.4f})")
        
        # 生成可视化报告
        if args.plot:
            plot_path = os.path.join(args.models_dir, 'training_results.png')
            trainer.plot_results(results, plot_path)
            print(f"📊 训练结果图表已保存到: {plot_path}")
        
    finally:
        # 清理临时文件
        if args.synthetic:
            import shutil
            temp_dir = os.path.dirname(files[0]) if files else None
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"🧹 已清理临时目录: {temp_dir}")

def analyze_command(args):
    """分析命令处理"""
    print("📊 开始代码分析...")
    
    # 初始化特征提取器
    extractor = FeatureExtractor()
    
    # 确定要分析的文件
    if args.file:
        if not os.path.exists(args.file):
            print(f"❌ 错误: 文件不存在 {args.file}")
            return
        php_files = [args.file]
    elif args.directory:
        if not os.path.exists(args.directory):
            print(f"❌ 错误: 目录不存在 {args.directory}")
            return
        php_files = find_php_files(args.directory, args.recursive)
    else:
        print("❌ 错误: 请指定要分析的文件或目录")
        return
    
    if not php_files:
        print("❌ 没有找到PHP文件")
        return
    
    print(f"📁 找到 {len(php_files)} 个PHP文件")
    
    # 分析文件
    all_features = []
    for i, file_path in enumerate(php_files):
        try:
            features = extractor.extract_features(file_path)
            all_features.append((file_path, features))
            
            if args.verbose:
                print(f"\n📄 {os.path.basename(file_path)}:")
                print(f"   代码行数: {features.lines_of_code}")
                print(f"   圈复杂度: {features.cyclomatic_complexity}")
                print(f"   类数量: {features.number_of_classes}")
                print(f"   方法数量: {features.number_of_methods}")
                print(f"   平均方法复杂度: {features.avg_method_complexity:.2f}")
                print(f"   命名约定违规: {features.naming_convention_violations}")
                print(f"   注释密度: {features.comment_ratio:.2%}")
            
            if (i + 1) % 10 == 0:
                print(f"已分析 {i + 1}/{len(php_files)} 个文件")
                
        except Exception as e:
            print(f"分析文件 {file_path} 时出错: {e}")
            continue
    
    # 生成统计报告
    if all_features:
        print(f"\n📈 统计摘要 (基于 {len(all_features)} 个文件):")
        
        # 计算统计信息
        lines = [f.lines_of_code for _, f in all_features]
        complexities = [f.cyclomatic_complexity for _, f in all_features]
        classes = [f.number_of_classes for _, f in all_features]
        methods = [f.number_of_methods for _, f in all_features]
        
        print(f"   平均代码行数: {sum(lines)/len(lines):.1f}")
        print(f"   平均圈复杂度: {sum(complexities)/len(complexities):.1f}")
        print(f"   平均类数量: {sum(classes)/len(classes):.1f}")
        print(f"   平均方法数量: {sum(methods)/len(methods):.1f}")
        
        # 找出问题文件
        problematic_files = []
        for file_path, features in all_features:
            issues = []
            if features.lines_of_code > 1000:
                issues.append("文件过大")
            if features.cyclomatic_complexity > 20:
                issues.append("复杂度过高")
            if features.long_method_count > 0:
                issues.append("存在长方法")
            if features.naming_convention_violations > 5:
                issues.append("命名约定违规")
            
            if issues:
                problematic_files.append((file_path, issues))
        
        if problematic_files:
            print(f"\n⚠️  发现 {len(problematic_files)} 个问题文件:")
            for file_path, issues in problematic_files[:5]:  # 只显示前5个
                print(f"   📁 {os.path.basename(file_path)}: {', '.join(issues)}")
            
            if len(problematic_files) > 5:
                print(f"   ... 还有 {len(problematic_files) - 5} 个文件")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AI代码异味检测工具 - 基于php-parser + scikit-learn",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 检测单个文件
  python main.py detect -f path/to/file.php
  
  # 检测整个目录
  python main.py detect -d /path/to/project --recursive
  
  # 生成详细报告
  python main.py detect -d /path/to/project -o report.html --verbose
  
  # 训练模型
  python main.py train --synthetic --samples 500 --grid-search
  
  # 分析代码统计信息
  python main.py analyze -d /path/to/project --verbose
        """
    )
    
    # 全局参数
    parser.add_argument('--models-dir', default='models', 
                       help='模型文件目录 (默认: models)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 检测命令
    detect_parser = subparsers.add_parser('detect', help='检测代码异味')
    detect_group = detect_parser.add_mutually_exclusive_group(required=True)
    detect_group.add_argument('-f', '--file', help='要检测的PHP文件')
    detect_group.add_argument('-d', '--directory', help='要检测的目录')
    detect_parser.add_argument('-r', '--recursive', action='store_true',
                              help='递归搜索目录')
    detect_parser.add_argument('-o', '--output', default='code_smell_report.html',
                              help='输出报告文件 (默认: code_smell_report.html)')
    detect_parser.add_argument('--suggestions', action='store_true',
                              help='显示改进建议')
    
    # 训练命令
    train_parser = subparsers.add_parser('train', help='训练机器学习模型')
    train_parser.add_argument('--synthetic', action='store_true',
                             help='使用合成数据进行训练')
    train_parser.add_argument('--data-dir', help='训练数据目录')
    train_parser.add_argument('--samples', type=int, default=500,
                             help='合成数据样本数量 (默认: 500)')
    train_parser.add_argument('--grid-search', action='store_true',
                             help='使用网格搜索优化参数')
    train_parser.add_argument('--plot', action='store_true',
                             help='生成训练结果图表')
    
    # 分析命令
    analyze_parser = subparsers.add_parser('analyze', help='分析代码统计信息')
    analyze_group = analyze_parser.add_mutually_exclusive_group(required=True)
    analyze_group.add_argument('-f', '--file', help='要分析的PHP文件')
    analyze_group.add_argument('-d', '--directory', help='要分析的目录')
    analyze_parser.add_argument('-r', '--recursive', action='store_true',
                               help='递归搜索目录')
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 创建模型目录
    os.makedirs(args.models_dir, exist_ok=True)
    
    # 执行对应命令
    try:
        if args.command == 'detect':
            detect_command(args)
        elif args.command == 'train':
            train_command(args)
        elif args.command == 'analyze':
            analyze_command(args)
    except KeyboardInterrupt:
        print("\n❌ 操作被用户中断")
    except Exception as e:
        print(f"❌ 执行过程中出现错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main() 