#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机器学习模型训练器
使用scikit-learn训练代码异味检测模型
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.pipeline import Pipeline
import matplotlib.pyplot as plt
import seaborn as sns
from feature_extractor import FeatureExtractor, CodeFeatures

class ModelTrainer:
    def __init__(self, models_dir: str = "models"):
        """
        初始化模型训练器
        
        Args:
            models_dir: 模型保存目录
        """
        self.models_dir = models_dir
        self.feature_extractor = FeatureExtractor()
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        # 确保模型目录存在
        os.makedirs(models_dir, exist_ok=True)
        
        # 定义可用的模型
        self.models = {
            'random_forest': RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=100,
                random_state=42
            ),
            'svm': SVC(
                kernel='rbf',
                random_state=42,
                probability=True
            ),
            'logistic_regression': LogisticRegression(
                random_state=42,
                max_iter=1000
            )
        }
        
        # 代码异味类型定义
        self.code_smell_types = [
            'clean',                    # 清洁代码
            'long_method',              # 长方法
            'large_class',              # 大类
            'long_parameter_list',      # 长参数列表
            'complex_method',           # 复杂方法
            'naming_issues',            # 命名问题
            'low_cohesion',             # 低内聚
            'high_coupling',            # 高耦合
            'duplicate_code',           # 重复代码
            'security_issues',          # 安全问题
            'logic_errors',             # 逻辑错误
            'error_handling_issues',    # 错误处理问题
            'performance_issues',       # 性能问题
            'critical_issues',          # 严重问题
            'code_quality_issues'       # 代码质量问题
        ]
    
    def prepare_training_data(self, php_files: List[str], labels: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        """
        准备训练数据
        
        Args:
            php_files: PHP文件路径列表
            labels: 对应的标签列表
            
        Returns:
            特征矩阵和标签数组
        """
        features_list = []
        valid_labels = []
        
        print(f"正在处理 {len(php_files)} 个PHP文件...")
        
        for i, (file_path, label) in enumerate(zip(php_files, labels)):
            try:
                if not os.path.exists(file_path):
                    print(f"警告: 文件不存在 {file_path}")
                    continue
                
                features = self.feature_extractor.extract_features(file_path)
                features_list.append(features.to_vector())
                valid_labels.append(label)
                
                if (i + 1) % 10 == 0:
                    print(f"已处理 {i + 1}/{len(php_files)} 个文件")
                    
            except Exception as e:
                print(f"处理文件 {file_path} 时出错: {e}")
                continue
        
        if not features_list:
            raise ValueError("没有成功处理任何文件")
        
        X = np.array(features_list)
        y = np.array(valid_labels)
        
        print(f"成功处理 {len(features_list)} 个文件")
        print(f"特征维度: {X.shape}")
        print(f"标签分布: {dict(zip(*np.unique(y, return_counts=True)))}")
        
        return X, y
    
    def train_models(self, X: np.ndarray, y: np.ndarray, 
                    test_size: float = 0.2, 
                    use_grid_search: bool = True) -> Dict[str, Any]:
        """
        训练多个模型
        
        Args:
            X: 特征矩阵
            y: 标签数组
            test_size: 测试集比例
            use_grid_search: 是否使用网格搜索优化参数
            
        Returns:
            训练结果字典
        """
        # 分割数据
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # 标准化特征
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 编码标签
        y_train_encoded = self.label_encoder.fit_transform(y_train)
        y_test_encoded = self.label_encoder.transform(y_test)
        
        results = {}
        
        print("开始训练模型...")
        
        for model_name, model in self.models.items():
            print(f"\n训练 {model_name}...")
            
            try:
                if use_grid_search:
                    # 使用网格搜索优化参数
                    param_grid = self._get_param_grid(model_name)
                    if param_grid:
                        grid_search = GridSearchCV(
                            model, param_grid, 
                            cv=5, scoring='accuracy', 
                            n_jobs=-1, verbose=1
                        )
                        grid_search.fit(X_train_scaled, y_train_encoded)
                        best_model = grid_search.best_estimator_
                        print(f"最佳参数: {grid_search.best_params_}")
                    else:
                        best_model = model
                        best_model.fit(X_train_scaled, y_train_encoded)
                else:
                    best_model = model
                    best_model.fit(X_train_scaled, y_train_encoded)
                
                # 预测
                y_pred = best_model.predict(X_test_scaled)
                y_pred_proba = best_model.predict_proba(X_test_scaled) if hasattr(best_model, 'predict_proba') else None
                
                # 计算指标
                accuracy = accuracy_score(y_test_encoded, y_pred)
                cv_scores = cross_val_score(best_model, X_train_scaled, y_train_encoded, cv=5)
                
                # 分类报告
                target_names = self.label_encoder.classes_
                class_report = classification_report(
                    y_test_encoded, y_pred, 
                    target_names=target_names,
                    output_dict=True
                )
                
                results[model_name] = {
                    'model': best_model,
                    'accuracy': accuracy,
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std(),
                    'classification_report': class_report,
                    'predictions': y_pred,
                    'probabilities': y_pred_proba,
                    'test_labels': y_test_encoded
                }
                
                print(f"{model_name} - 准确率: {accuracy:.4f}")
                print(f"{model_name} - 交叉验证: {cv_scores.mean():.4f} (±{cv_scores.std()*2:.4f})")
                
            except Exception as e:
                print(f"训练 {model_name} 时出错: {e}")
                continue
        
        # 保存预处理器
        self._save_preprocessors()
        
        return results
    
    def _get_param_grid(self, model_name: str) -> Dict[str, List]:
        """获取模型的参数网格"""
        param_grids = {
            'random_forest': {
                'n_estimators': [50, 100, 200],
                'max_depth': [None, 10, 20],
                'min_samples_split': [2, 5, 10]
            },
            'gradient_boosting': {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7]
            },
            'svm': {
                'C': [0.1, 1, 10],
                'gamma': ['scale', 'auto']
            },
            'logistic_regression': {
                'C': [0.1, 1, 10],
                'penalty': ['l1', 'l2'],
                'solver': ['liblinear', 'lbfgs']
            }
        }
        
        return param_grids.get(model_name, {})
    
    def save_best_model(self, results: Dict[str, Any], metric: str = 'accuracy') -> str:
        """
        保存最佳模型
        
        Args:
            results: 训练结果
            metric: 评估指标
            
        Returns:
            最佳模型名称
        """
        # 找到最佳模型
        best_model_name = max(results.keys(), key=lambda k: results[k][metric])
        best_model = results[best_model_name]['model']
        
        # 保存模型
        model_path = os.path.join(self.models_dir, f'best_model_{best_model_name}.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump(best_model, f)
        
        # 保存模型信息
        model_info = {
            'model_name': best_model_name,
            'accuracy': results[best_model_name]['accuracy'],
            'cv_mean': results[best_model_name]['cv_mean'],
            'cv_std': results[best_model_name]['cv_std'],
            'feature_names': CodeFeatures.get_feature_names(),
            'label_classes': self.label_encoder.classes_.tolist()
        }
        
        info_path = os.path.join(self.models_dir, 'model_info.json')
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(model_info, f, indent=2, ensure_ascii=False)
        
        print(f"最佳模型 ({best_model_name}) 已保存到 {model_path}")
        print(f"模型信息已保存到 {info_path}")
        
        return best_model_name
    
    def _save_preprocessors(self):
        """保存预处理器"""
        scaler_path = os.path.join(self.models_dir, 'scaler.pkl')
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        encoder_path = os.path.join(self.models_dir, 'label_encoder.pkl')
        with open(encoder_path, 'wb') as f:
            pickle.dump(self.label_encoder, f)
    
    def plot_results(self, results: Dict[str, Any], save_path: str = None):
        """
        绘制训练结果
        
        Args:
            results: 训练结果
            save_path: 保存路径
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. 模型准确率比较
        model_names = list(results.keys())
        accuracies = [results[name]['accuracy'] for name in model_names]
        cv_means = [results[name]['cv_mean'] for name in model_names]
        
        axes[0, 0].bar(model_names, accuracies, alpha=0.7, label='测试集准确率')
        axes[0, 0].bar(model_names, cv_means, alpha=0.7, label='交叉验证准确率')
        axes[0, 0].set_title('模型准确率比较')
        axes[0, 0].set_ylabel('准确率')
        axes[0, 0].legend()
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 2. 最佳模型的混淆矩阵
        best_model_name = max(results.keys(), key=lambda k: results[k]['accuracy'])
        best_result = results[best_model_name]
        
        cm = confusion_matrix(best_result['test_labels'], best_result['predictions'])
        sns.heatmap(cm, annot=True, fmt='d', ax=axes[0, 1], 
                   xticklabels=self.label_encoder.classes_,
                   yticklabels=self.label_encoder.classes_)
        axes[0, 1].set_title(f'{best_model_name} 混淆矩阵')
        axes[0, 1].set_xlabel('预测标签')
        axes[0, 1].set_ylabel('真实标签')
        
        # 3. 特征重要性（如果模型支持）
        if hasattr(best_result['model'], 'feature_importances_'):
            feature_names = CodeFeatures.get_feature_names()
            importances = best_result['model'].feature_importances_
            
            # 选择前10个最重要的特征
            indices = np.argsort(importances)[-10:]
            
            axes[1, 0].barh(range(len(indices)), importances[indices])
            axes[1, 0].set_yticks(range(len(indices)))
            axes[1, 0].set_yticklabels([feature_names[i] for i in indices])
            axes[1, 0].set_title('特征重要性 (Top 10)')
            axes[1, 0].set_xlabel('重要性')
        
        # 4. 类别分布
        if len(results) > 0:
            first_result = list(results.values())[0]
            unique, counts = np.unique(first_result['test_labels'], return_counts=True)
            class_names = [self.label_encoder.classes_[i] for i in unique]
            
            axes[1, 1].pie(counts, labels=class_names, autopct='%1.1f%%')
            axes[1, 1].set_title('测试集类别分布')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"结果图表已保存到 {save_path}")
        
        plt.show()
    
    def generate_synthetic_data(self, num_samples: int = 1000) -> Tuple[List[str], List[str]]:
        """
        生成合成训练数据（用于演示）
        
        Args:
            num_samples: 生成样本数量
            
        Returns:
            文件路径列表和标签列表
        """
        import tempfile
        
        synthetic_files = []
        synthetic_labels = []
        
        # 定义不同类型的代码模板
        templates = {
            'clean': '''<?php
class CleanExample {
    private $data;
    
    public function __construct($data) {
        $this->data = $data;
    }
    
    public function process() {
        return $this->data * 2;
    }
    
    public function validate($input) {
        return is_numeric($input) && $input > 0;
    }
}
?>''',
            
            'long_method': '''<?php
class LongMethodExample {
    public function veryLongMethod($data) {
        $result = 0;
        for ($i = 0; $i < 100; $i++) {
            if ($i % 2 == 0) {
                if ($i % 4 == 0) {
                    if ($i % 8 == 0) {
                        $result += $i * 2;
                        if ($result > 1000) {
                            $result = $result / 2;
                            for ($j = 0; $j < 10; $j++) {
                                $result += $j;
                                if ($j % 3 == 0) {
                                    $result *= 1.1;
                                }
                            }
                        }
                    } else {
                        $result += $i;
                    }
                } else {
                    $result -= $i;
                }
            } else {
                $result += $i / 2;
            }
        }
        return $result;
    }
}
?>''',
            
            'long_parameter_list': '''<?php
class LongParameterExample {
    public function methodWithManyParams($param1, $param2, $param3, $param4, $param5, $param6, $param7, $param8) {
        return $param1 + $param2 + $param3 + $param4 + $param5 + $param6 + $param7 + $param8;
    }
}
?>''',
            
            'naming_issues': '''<?php
class bad_class_name {
    private $VeryBadVariableName;
    
    public function BADMETHODNAME($ugly_param) {
        $another_BAD_var = $ugly_param;
        return $another_BAD_var;
    }
}
?>''',
            
            'complex_method': '''<?php
class ComplexExample {
    public function complexMethod($data) {
        if ($data > 100) {
            for ($i = 0; $i < $data; $i++) {
                if ($i % 2 == 0) {
                    if ($i % 4 == 0) {
                        if ($i % 8 == 0) {
                            switch ($i % 16) {
                                case 0:
                                    while ($i < 50) {
                                        $i++;
                                        if ($i % 3 == 0) {
                                            continue;
                                        }
                                    }
                                    break;
                                case 8:
                                    foreach (range(1, 10) as $j) {
                                        if ($j > 5) {
                                            break;
                                        }
                                    }
                                    break;
                            }
                        }
                    }
                }
            }
        }
        return $data;
    }
}
?>'''
        }
        
        temp_dir = tempfile.mkdtemp()
        
        for i in range(num_samples):
            # 随机选择代码异味类型
            smell_type = np.random.choice(list(templates.keys()))
            
            # 生成临时文件
            temp_file = os.path.join(temp_dir, f'sample_{i}_{smell_type}.php')
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(templates[smell_type])
            
            synthetic_files.append(temp_file)
            synthetic_labels.append(smell_type)
        
        print(f"生成了 {num_samples} 个合成样本到 {temp_dir}")
        return synthetic_files, synthetic_labels

def main():
    """演示模型训练流程"""
    trainer = ModelTrainer()
    
    # 生成合成数据进行演示
    print("生成合成训练数据...")
    files, labels = trainer.generate_synthetic_data(100)
    
    try:
        # 准备训练数据
        X, y = trainer.prepare_training_data(files, labels)
        
        # 训练模型
        results = trainer.train_models(X, y, use_grid_search=False)  # 为了快速演示，不使用网格搜索
        
        # 保存最佳模型
        best_model = trainer.save_best_model(results)
        
        # 绘制结果
        trainer.plot_results(results, 'training_results.png')
        
        print(f"\n训练完成！最佳模型: {best_model}")
        
        # 显示详细结果
        print("\n详细结果:")
        for model_name, result in results.items():
            print(f"\n{model_name}:")
            print(f"  准确率: {result['accuracy']:.4f}")
            print(f"  交叉验证: {result['cv_mean']:.4f} (±{result['cv_std']*2:.4f})")
        
    finally:
        # 清理临时文件
        import shutil
        temp_dir = os.path.dirname(files[0]) if files else None
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"已清理临时目录: {temp_dir}")

if __name__ == '__main__':
    main() 