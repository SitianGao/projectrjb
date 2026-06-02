# backend/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="EduAgent Backend",
    description="基于大模型的个性化学习多智能体系统后端",
    version="0.1.0"
)

# 允许跨域访问（前端 React 5173端口可访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境可改成具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 根路径测试
@app.get("/")
def root():
    return {"msg": "EduAgent Backend Running"}

# MVP聊天接口：返回结构化学生画像
@app.post("/chat")
def chat(data: dict):
    """
    前端发送 JSON 格式：
    { "message": "我是计算机二年级学生" }
    返回结构化学生画像
    """
    message = data.get("message", "")

    # 模拟生成6维学生画像
    profile = {
        "knowledge_level": "中等",           # 知识水平
        "learning_goal": "考研",             # 学习目标
        "weak_points": ["概率论", "数据结构"], # 学生薄弱点
        "interest": ["人工智能", "前端开发"], # 兴趣方向
        "study_style": "视觉型",             # 学习风格
        "preferred_resources": ["文档", "视频"], # 偏好资源
        "analysis": f"已分析输入：{message}"   # 简单分析输入
    }

    return {"reply": profile}

# 可选：未来可扩展多智能体资源生成接口
@app.post("/generate_resource")
def generate_resource(data: dict):
    """
    输入：
    {
        "profile": {...学生画像...},
        "course": "人工智能入门"
    }
    返回个性化学习资源（文档、视频、题库）
    """
    return {"reply": "资源生成功能待实现"}