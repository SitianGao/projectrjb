# Flask模型部署

> 来源模块: module3_deployment
> 原始文件: q46_flask_deploy.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】Flask模型部署应用
【模块】模块3 - 模型部署
【难度】5
【知识点】Flask应用路由、模型单例加载、懒加载、批量请求处理、
          RESTful API设计、JSON请求响应、错误处理
【描述】
本题要求设计一个基于Flask的模型部署应用，包含模型加载、推理接口、
批量处理等功能。

注意：本题不实际启动Flask服务器，而是展示完整的应用代码结构
并提供测试代码验证路由逻辑。

需要实现的功能：
1. 模型单例加载（全局只加载一次）
2. 模型懒加载（首次请求时加载）
3. 单条预测接口 POST /predict
4. 批量预测接口 POST /predict_batch
5. 健康检查接口 GET /health
6. 模型信息接口 GET /model_info
7. 统一的错误处理
8. 请求参数验证

【输入输出】
- 输入：模拟的HTTP请求（通过Flask测试客户端）
- 输出：打印各接口的请求/响应结果

【要求】
1. 使用Flask的应用工厂模式
2. 模型单例模式确保全局只加载一次
3. 懒加载模式在首次推理时才加载模型
4. /predict 接口接受单条数据，返回预测结果和概率
5. /predict_batch 接口接受批量数据（最多100条）
6. 所有响应使用统一JSON格式 {"code": 200, "data": ..., "message": "ok"}
7. 实现请求参数验证（特征数量、数据类型）
8. 使用Flask的test_client进行测试（不启动服务器）

【提示】
- 使用 flask.Flask 的 test_client() 进行测试
- 模型加载可以用 threading.Lock 保证线程安全
- 使用 @app.errorhandler 统一处理异常
- 使用 @app.before_first_request（Flask <2.3）或手动标志实现懒加载
=============================
"""

# ========== 参考答案 ==========

import threading
import numpy as np
import torch
import torch.nn as nn

from flask import Flask, request, jsonify


# ==================== 模型定义 ====================

class SimpleClassifier(nn.Module):
    """简单分类模型"""

    def __init__(self, input_dim=10, num_classes=3):
        super(SimpleClassifier, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, num_classes),
        )

    def forward(self, x):
        return self.net(x)


# ==================== 模型管理器（单例模式） ====================

class ModelManager:
    """模型管理器 - 单例模式

    确保模型在整个应用生命周期内只加载一次。
    使用线程锁保证多线程安全。
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_path=None, input_dim=10, num_classes=3):
        if self._initialized:
            return
        self._model = None
        self._model_path = model_path
        self._input_dim = input_dim
        self._num_classes = num_classes
        self._device = "cpu"
        self._loaded = False
        self._load_lock = threading.Lock()
        self._initialized = True

    def load_model(self):
        """加载模型"""
        if self._loaded:
            return

        with self._load_lock:
            if self._loaded:
                return

            # 创建并初始化模型（实际场景中从文件加载）
            self._model = SimpleClassifier(
                input_dim=self._input_dim,
                num_classes=self._num_classes,
            ).to(self._device)

            if self._model_path:
                # 从文件加载权重
                state_dict = torch.load(
                    self._model_path, map_location=self._device
                )
                self._model.load_state_dict(state_dict)

            self._model.eval()
            self._loaded = True

    def predict(self, features):
        """单条预测

        Args:
            features: list, 特征值列表

        Returns:
            dict: 预测结果
        """
        self.load_model()  # 懒加载

        x = torch.FloatTensor([features]).to(self._device)
        with torch.no_grad():
            logits = self._model(x)
            probs = torch.softmax(logits, dim=1)
            pred_class = torch.argmax(probs, dim=1).item()
            pred_prob = probs[0][pred_class].item()

        return {
            "predicted_class": pred_class,
            "confidence": round(pred_prob, 4),
            "probabilities": {
                str(i): round(probs[0][i].item(), 4)
                for i in range(self._num_classes)
            },
        }

    def predict_batch(self, features_list):
        """批量预测

        Args:
            features_list: list of list, 批量特征值

        Returns:
            list[dict]: 批量预测结果
        """
        self.load_model()

        x = torch.FloatTensor(features_list).to(self._device)
        with torch.no_grad():
            logits = self._model(x)
            probs = torch.softmax(logits, dim=1)
            pred_classes = torch.argmax(probs, dim=1).tolist()

        results = []
        for i, pred_class in enumerate(pred_classes):
            results.append({
                "predicted_class": pred_class,
                "confidence": round(probs[i][pred_class].item(), 4),
            })
        return results

    @property
    def is_loaded(self):
        return self._loaded

    @property
    def model_info(self):
        return {
            "input_dim": self._input_dim,
            "num_classes": self._num_classes,
            "device": self._device,
            "loaded": self._loaded,
            "model_type": "SimpleClassifier",
        }


# ==================== 响应格式化 ====================

def make_response(code=200, data=None, message="ok"):
    """统一响应格式"""
    return jsonify({
        "code": code,
        "data": data,
        "message": message,
    })


# ==================== 应用工厂 ====================

def create_app(input_dim=10, num_classes=3):
    """Flask应用工厂函数

    Args:
        input_dim: 输入特征维度
        num_classes: 分类类别数

    Returns:
        Flask app实例
    """
    app = Flask(__name__)

    # 初始化模型管理器（但不加载模型 - 懒加载）
    model_manager = ModelManager(input_dim=input_dim, num_classes=num_classes)

    # ---------- 路由定义 ----------

    @app.route("/health", methods=["GET"])
    def health_check():
        """健康检查接口"""
        return make_response(data={
            "status": "healthy",
            "model_loaded": model_manager.is_loaded,
        })

    @app.route("/model_info", methods=["GET"])
    def model_info():
        """模型信息接口"""
        return make_response(data=model_manager.model_info)

    @app.route("/predict", methods=["POST"])
    def predict():
        """单条预测接口

        请求体JSON格式:
        {
            "features": [1.0, 2.0, 3.0, ...]  // 长度为input_dim的列表
        }
        """
        try:
            data = request.get_json()
            if data is None:
                return make_response(400, message="请求体不是有效的JSON")

            features = data.get("features")
            if features is None:
                return make_response(400, message="缺少features字段")

            # 参数验证
            if not isinstance(features, list):
                return make_response(400, message="features必须是列表")

            if len(features) != model_manager._input_dim:
                return make_response(
                    400,
                    message=f"特征数量错误，期望{model_manager._input_dim}，"
                            f"实际{len(features)}",
                )

            # 类型验证
            try:
                features = [float(f) for f in features]
            except (TypeError, ValueError):
                return make_response(400, message="features中的值必须为数字")

            # 预测
            result = model_manager.predict(features)
            return make_response(data=result)

        except Exception as e:
            return make_response(500, message=f"服务器内部错误: {str(e)}")

    @app.route("/predict_batch", methods=["POST"])
    def predict_batch():
        """批量预测接口

        请求体JSON格式:
        {
            "features_list": [[1.0, 2.0, ...], [3.0, 4.0, ...], ...]
        }
        """
        try:
            data = request.get_json()
            if data is None:
                return make_response(400, message="请求体不是有效的JSON")

            features_list = data.get("features_list")
            if features_list is None:
                return make_response(400, message="缺少features_list字段")

            if not isinstance(features_list, list):
                return make_response(400, message="features_list必须是列表")

            # 批量大小限制
            if len(features_list) > 100:
                return make_response(400, message="批量大小不能超过100")

            if len(features_list) == 0:
                return make_response(400, message="features_list不能为空")

            # 参数验证
            for i, features in enumerate(features_list):
                if len(features) != model_manager._input_dim:
                    return make_response(
                        400,
                        message=f"第{i}条数据特征数量错误，"
                                f"期望{model_manager._input_dim}，"
                                f"实际{len(features)}",
                    )

            # 类型转换
            try:
                features_list = [
                    [float(f) for f in features]
                    for features in features_list
                ]
            except (TypeError, ValueError):
                return make_response(400, message="features中的值必须为数字")

            # 批量预测
            results = model_manager.predict_batch(features_list)
            return make_response(data={"predictions": results, "count": len(results)})

        except Exception as e:
            return make_response(500, message=f"服务器内部错误: {str(e)}")

    # ---------- 错误处理 ----------

    @app.errorhandler(404)
    def not_found(e):
        return make_response(404, message="接口不存在")

    @app.errorhandler(405)
    def method_not_allowed(e):
        return make_response(405, message="请求方法不允许")

    @app.errorhandler(500)
    def internal_error(e):
        return make_response(500, message="服务器内部错误")

    return app


# ==================== 测试代码 ====================

def run_tests():
    """使用Flask测试客户端运行测试"""
    # 重置单例（测试用）
    ModelManager._instance = None

    app = create_app(input_dim=10, num_classes=3)
    client = app.test_client()

    print("=" * 60)
    print("【Flask模型部署应用测试】")
    print("=" * 60)

    # 1. 健康检查（模型未加载）
    print("\n[测试1] 健康检查（模型未加载）")
    resp = client.get("/health")
    print(f"  GET /health -> {resp.status_code}")
    print(f"  响应: {resp.get_json()}")

    # 2. 模型信息
    print("\n[测试2] 模型信息")
    resp = client.get("/model_info")
    print(f"  GET /model_info -> {resp.status_code}")
    print(f"  响应: {resp.get_json()}")

    # 3. 单条预测
    print("\n[测试3] 单条预测（触发懒加载）")
    features = [float(x) for x in np.random.randn(10)]
    resp = client.post(
        "/predict",
        json={"features": features},
        content_type="application/json",
    )
    print(f"  POST /predict -> {resp.status_code}")
    result = resp.get_json()
    print(f"  响应: {result}")

    # 4. 验证模型已加载
    print("\n[测试4] 健康检查（模型已加载）")
    resp = client.get("/health")
    health_data = resp.get_json()
    print(f"  GET /health -> {resp.status_code}")
    print(f"  模型加载状态: {health_data['data']['model_loaded']}")

    # 5. 批量预测
    print("\n[测试5] 批量预测")
    features_list = np.random.randn(5, 10).tolist()
    resp = client.post(
        "/predict_batch",
        json={"features_list": features_list},
        content_type="application/json",
    )
    print(f"  POST /predict_batch -> {resp.status_code}")
    batch_result = resp.get_json()
    print(f"  批量预测数量: {batch_result['data']['count']}")
    for i, pred in enumerate(batch_result["data"]["predictions"]):
        print(f"    样本{i}: class={pred['predicted_class']}, "
              f"conf={pred['confidence']}")

    # 6. 错误参数测试
    print("\n[测试6] 错误参数测试")

    # 特征数量错误
    resp = client.post("/predict", json={"features": [1.0, 2.0]})
    print(f"  特征数量错误 -> {resp.status_code}: {resp.get_json()['message']}")

    # 缺少features字段
    resp = client.post("/predict", json={"data": [1.0]})
    print(f"  缺少features -> {resp.status_code}: {resp.get_json()['message']}")

    # 空的批量请求
    resp = client.post("/predict_batch", json={"features_list": []})
    print(f"  空批量请求 -> {resp.status_code}: {resp.get_json()['message']}")

    # 超量批量请求
    large_batch = np.random.randn(101, 10).tolist()
    resp = client.post("/predict_batch", json={"features_list": large_batch})
    print(f"  超量批量 -> {resp.status_code}: {resp.get_json()['message']}")

    # 7. 不存在的路由
    print("\n[测试7] 不存在的路由")
    resp = client.get("/nonexistent")
    print(f"  GET /nonexistent -> {resp.status_code}: {resp.get_json()['message']}")

    # 8. 错误的HTTP方法
    print("\n[测试8] 错误的HTTP方法")
    resp = client.get("/predict")
    print(f"  GET /predict -> {resp.status_code}: {resp.get_json()['message']}")

    # 9. 非JSON请求体
    print("\n[测试9] 非JSON请求体")
    resp = client.post("/predict", data="not json",
                       content_type="text/plain")
    print(f"  非JSON请求 -> {resp.status_code}: {resp.get_json()['message']}")

    print("\n" + "=" * 60)
    print("所有测试通过！Flask应用部署结构验证完成。")
    print("=" * 60)


def solve():
    """主函数：运行Flask应用测试"""
    run_tests()


if __name__ == "__main__":
    solve()

```
