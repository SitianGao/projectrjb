# 构建Pipeline

> 来源模块: module3_deployment
> 原始文件: q43_sklearn_onnx.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】sklearn模型转换为ONNX并推理验证
【模块】模块3 - 模型部署
【难度】5
【知识点】skl2onnx、sklearn Pipeline、ONNX转换、onnxruntime推理、
          模型一致性验证、特征类型处理
【描述】
本题要求将sklearn的机器学习Pipeline转换为ONNX格式，
并使用onnxruntime进行推理验证。

步骤：
1. 构建sklearn Pipeline（含标准化 + 模型）
2. 使用skl2onnx将Pipeline转换为ONNX
3. 使用onnxruntime推理并验证一致性

注意：skl2onnx可能需要额外安装（pip install skl2onnx），代码中已做兼容处理。

【输入输出】
- 输入：sklearn生成的分类/回归数据集
- 输出：打印转换信息、推理结果对比

【要求】
1. 分别对分类模型（RandomForest/LogisticRegression）和回归模型（Ridge）进行转换
2. 使用Pipeline包含StandardScaler + 模型
3. 转换时正确指定初始类型（initial_type）
4. 对比sklearn预测结果与onnxruntime推理结果
5. 分类结果应完全一致（argmax后），回归结果误差<1e-4
6. 用try/except处理skl2onnx未安装的情况

【提示】
- skl2onnx的convert_sklearn函数需要initial_type参数
- initial_type格式: [("input", FloatTensorType([None, n_features]))]
- DoubleTensorType用于回归任务可能更精确
- onnxruntime输入需要numpy float32数组
=============================
"""

# ========== 参考答案 ==========

import numpy as np
from sklearn.datasets import make_classification, make_regression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, mean_squared_error


def convert_classification_pipeline():
    """分类Pipeline: StandardScaler + LogisticRegression -> ONNX"""
    print("=" * 60)
    print("[分类任务] Pipeline转换验证")
    print("=" * 60)

    # 准备数据
    X, y = make_classification(
        n_samples=1000, n_features=10, n_informative=5,
        n_classes=3, random_state=42
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 构建Pipeline
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=200, random_state=42)),
    ])
    pipeline.fit(X_train, y_train)

    # sklearn预测
    sklearn_pred = pipeline.predict(X_test)
    sklearn_proba = pipeline.predict_proba(X_test)
    sklearn_acc = accuracy_score(y_test, sklearn_pred)
    print(f"  sklearn准确率: {sklearn_acc:.4f}")

    # 尝试转换为ONNX
    try:
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType

        # 定义初始类型
        n_features = X_train.shape[1]
        initial_type = [("float_input", FloatTensorType([None, n_features]))]

        # 转换
        onnx_model = convert_sklearn(
            pipeline,
            initial_types=initial_type,
            target_opset=12,
        )

        # 保存ONNX模型
        onnx_path = "/tmp/sklearn_classification_pipeline.onnx"
        with open(onnx_path, "wb") as f:
            f.write(onnx_model.SerializeToString())
        print(f"  ONNX模型已保存: {onnx_path}")

        # onnxruntime推理
        import onnxruntime as ort

        sess = ort.InferenceSession(onnx_path)
        input_name = sess.get_inputs()[0].name

        X_test_f32 = X_test.astype(np.float32)
        onnx_outputs = sess.run(None, {input_name: X_test_f32})

        onnx_pred = onnx_outputs[0]   # 预测标签
        onnx_proba = onnx_outputs[1]  # 预测概率

        # 对比结果
        pred_agreement = np.mean(sklearn_pred == onnx_pred)
        proba_diff = np.max(np.abs(sklearn_proba - onnx_proba))

        print(f"  预测一致率: {pred_agreement:.4f}")
        print(f"  概率最大误差: {proba_diff:.2e}")
        print(f"  ONNX准确率: {accuracy_score(y_test, onnx_pred):.4f}")
        print(f"  验证: {'通过' if pred_agreement == 1.0 else '未通过'}")

    except ImportError as e:
        print(f"  [跳过] skl2onnx未安装: {e}")
        print("  安装方法: pip install skl2onnx")
    except Exception as e:
        print(f"  [错误] 转换失败: {e}")


def convert_regression_pipeline():
    """回归Pipeline: StandardScaler + Ridge -> ONNX"""
    print("\n" + "=" * 60)
    print("[回归任务] Pipeline转换验证")
    print("=" * 60)

    # 准备数据
    X, y = make_regression(
        n_samples=1000, n_features=10, n_informative=5,
        noise=10, random_state=42
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 构建Pipeline
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("reg", Ridge(alpha=1.0)),
    ])
    pipeline.fit(X_train, y_train)

    # sklearn预测
    sklearn_pred = pipeline.predict(X_test)
    sklearn_mse = mean_squared_error(y_test, sklearn_pred)
    print(f"  sklearn MSE: {sklearn_mse:.4f}")

    # 转换为ONNX
    try:
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType

        n_features = X_train.shape[1]
        initial_type = [("float_input", FloatTensorType([None, n_features]))]

        onnx_model = convert_sklearn(
            pipeline,
            initial_types=initial_type,
            target_opset=12,
        )

        onnx_path = "/tmp/sklearn_regression_pipeline.onnx"
        with open(onnx_path, "wb") as f:
            f.write(onnx_model.SerializeToString())
        print(f"  ONNX模型已保存: {onnx_path}")

        # onnxruntime推理
        import onnxruntime as ort

        sess = ort.InferenceSession(onnx_path)
        input_name = sess.get_inputs()[0].name

        X_test_f32 = X_test.astype(np.float32)
        onnx_pred = sess.run(None, {input_name: X_test_f32})[0].flatten()

        # 对比结果
        pred_diff = np.max(np.abs(sklearn_pred - onnx_pred))
        pred_mean_diff = np.mean(np.abs(sklearn_pred - onnx_pred))
        onnx_mse = mean_squared_error(y_test, onnx_pred)

        print(f"  预测最大误差: {pred_diff:.2e}")
        print(f"  预测平均误差: {pred_mean_diff:.2e}")
        print(f"  ONNX MSE: {onnx_mse:.4f}")
        print(f"  验证: {'通过' if pred_diff < 1e-3 else '未通过'}")

    except ImportError as e:
        print(f"  [跳过] skl2onnx未安装: {e}")
        print("  安装方法: pip install skl2onnx")
    except Exception as e:
        print(f"  [错误] 转换失败: {e}")


def convert_random_forest_pipeline():
    """RandomForest分类Pipeline -> ONNX"""
    print("\n" + "=" * 60)
    print("[RandomForest分类] Pipeline转换验证")
    print("=" * 60)

    X, y = make_classification(
        n_samples=1000, n_features=10, n_informative=5,
        n_classes=2, random_state=42
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=50, random_state=42)),
    ])
    pipeline.fit(X_train, y_train)

    sklearn_pred = pipeline.predict(X_test)
    sklearn_proba = pipeline.predict_proba(X_test)
    sklearn_acc = accuracy_score(y_test, sklearn_pred)
    print(f"  sklearn准确率: {sklearn_acc:.4f}")

    try:
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType

        n_features = X_train.shape[1]
        initial_type = [("float_input", FloatTensorType([None, n_features]))]

        onnx_model = convert_sklearn(
            pipeline,
            initial_types=initial_type,
            target_opset=12,
        )

        onnx_path = "/tmp/sklearn_rf_pipeline.onnx"
        with open(onnx_path, "wb") as f:
            f.write(onnx_model.SerializeToString())
        print(f"  ONNX模型已保存: {onnx_path}")

        import onnxruntime as ort

        sess = ort.InferenceSession(onnx_path)
        input_name = sess.get_inputs()[0].name

        X_test_f32 = X_test.astype(np.float32)
        onnx_outputs = sess.run(None, {input_name: X_test_f32})

        onnx_pred = onnx_outputs[0]
        onnx_proba = onnx_outputs[1]

        pred_agreement = np.mean(sklearn_pred == onnx_pred)
        proba_diff = np.max(np.abs(sklearn_proba - onnx_proba))

        print(f"  预测一致率: {pred_agreement:.4f}")
        print(f"  概率最大误差: {proba_diff:.2e}")
        print(f"  ONNX准确率: {accuracy_score(y_test, onnx_pred):.4f}")
        print(f"  验证: {'通过' if pred_agreement >= 0.99 else '未通过'}")

    except ImportError as e:
        print(f"  [跳过] skl2onnx未安装: {e}")
    except Exception as e:
        print(f"  [错误] 转换失败: {e}")


def solve():
    print("=" * 60)
    print("【sklearn Pipeline -> ONNX 转换验证】")
    print("=" * 60)
    print()

    convert_classification_pipeline()
    convert_regression_pipeline()
    convert_random_forest_pipeline()

    print("\n" + "=" * 60)
    print("sklearn -> ONNX 转换验证完成！")
    print("=" * 60)


if __name__ == "__main__":
    solve()

```
