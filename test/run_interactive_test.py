"""
交互测试脚本 —— 使用 profile_cases.py 中的三个案例
运行 ProfileAgent → PlannerAgent 完整交互链，生成 HTML 可视化报告
"""
import sys, os, json, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, os.path.dirname(__file__))

from profile_cases import (
    MultiTurnMockLLM, CASE_1_NAME, CASE_1_DIALOGUES, CASE_1_EXPECTED_FINAL,
    CASE_2_NAME, CASE_2_DIALOGUES, CASE_2_EXPECTED_FINAL,
    CASE_3_NAME, CASE_3_DIALOGUES, CASE_3_EXPECTED_FINAL,
)
from agents.profile_agent import ProfileAgent
from agents.planner_agent import PlannerAgent


async def run_case(case_name, dialogues, case_id):
    """运行一个完整案例：ProfileAgent 多轮 → PlannerAgent 生成路径"""
    print(f"\n{'='*60}")
    print(f"  {case_name}")
    print(f"{'='*60}")

    # Step 1: ProfileAgent 多轮对话
    llm = MultiTurnMockLLM([d["llm_profile"] for d in dialogues])
    profile_agent = ProfileAgent(llm)
    planner_agent = PlannerAgent(llm)

    history = []
    current_profile = None
    rounds = []

    for i, turn in enumerate(dialogues):
        result = await profile_agent.build_profile(
            student_id=case_id,
            message=turn["message"],
            history=list(history),
            current_profile=current_profile,
        )
        history.append(turn["message"])
        current_profile = result

        p = result.get("profile", {})
        rounds.append({
            "round": i + 1,
            "message": turn["message"][:80] + "...",
            "completeness": result.get("completeness", 0),
            "confidence": result.get("confidence", 0),
            "profile_snapshot": {
                "knowledge_level": p.get("knowledge_level", ""),
                "learning_goal": p.get("learning_goal", ""),
                "cognitive_style": p.get("cognitive_style", ""),
                "weakness": p.get("weakness", []),
                "interest": p.get("interest", []),
                "pace_preference": p.get("pace_preference", ""),
            },
            "next_questions": result.get("next_questions", []),
        })
        print(f"  Round {i+1}: completeness={result['completeness']}, confidence={result['confidence']}")

    final_profile = current_profile

    # Step 2: PlannerAgent 生成路径（规则降级，基于画像关键字）
    path = planner_agent._rule_fallback(
        student_id=case_id,
        profile=final_profile.get("profile", {}),
        goal=final_profile.get("profile", {}).get("learning_goal", ""),
    )

    stages = path.get("stages", [])
    print(f"  Path: {len(stages)} stages, {path.get('total_estimated_days')} days")
    for s in stages:
        print(f"    Stage {s['stage_id']}: {s['title']} ({s['difficulty']}, {s['estimated_days']}d)")

    return {
        "case_name": case_name,
        "case_id": case_id,
        "profile": final_profile,
        "rounds": rounds,
        "path": path,
    }


async def main():
    results = []

    # Case 1: 小张
    r1 = await run_case(CASE_1_NAME, CASE_1_DIALOGUES, "case_001")
    results.append(r1)

    # Case 2: 小李
    r2 = await run_case(CASE_2_NAME, CASE_2_DIALOGUES, "case_002")
    results.append(r2)

    # Case 3: 小王
    r3 = await run_case(CASE_3_NAME, CASE_3_DIALOGUES, "case_003")
    results.append(r3)

    # 输出 JSON 汇总
    output = {
        "test_time": "2026-06-11",
        "cases": []
    }
    for r in results:
        output["cases"].append({
            "case_name": r["case_name"],
            "profile": {k: v for k, v in r["profile"].items() if k != "learning_history"},
            "stages": [{
                "stage_id": s["stage_id"],
                "title": s["title"],
                "difficulty": s["difficulty"],
                "estimated_days": s["estimated_days"],
                "topics": s["topics"],
                "objectives": s["objectives"],
                "tasks": s["tasks"],
            } for s in r["path"].get("stages", [])],
            "total_estimated_days": r["path"].get("total_estimated_days"),
            "difficulty_level": r["path"].get("difficulty_level"),
            "adaptation_notes": r["path"].get("adaptation_notes", ""),
        })

    # 保存 JSON
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "screenshots"), exist_ok=True)
    json_path = os.path.join(os.path.dirname(__file__), "..", "screenshots", "test_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nJSON results saved to: {json_path}")

    # 生成 HTML 报告
    html = generate_html_report(results)
    html_path = os.path.join(os.path.dirname(__file__), "..", "screenshots", "test_report.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML report saved to: {html_path}")

    return html_path


def generate_html_report(results):
    """生成可视化 HTML 报告"""

    def profile_card(case):
        p = case["profile"]["profile"]
        rounds = case["rounds"]

        # 画像各维度
        dims_html = f"""
        <div class="profile-dims">
            <div class="dim"><span class="dim-label">知识水平</span><span class="dim-value">{p.get('knowledge_level','')}</span></div>
            <div class="dim"><span class="dim-label">学习目标</span><span class="dim-value">{p.get('learning_goal','')}</span></div>
            <div class="dim"><span class="dim-label">认知风格</span><span class="dim-value">{p.get('cognitive_style','')}</span></div>
            <div class="dim"><span class="dim-label">学习节奏</span><span class="dim-value">{p.get('pace_preference','')}</span></div>
            <div class="dim"><span class="dim-label">薄弱点</span><span class="dim-value">{', '.join(p.get('weakness',[])) or '无'}</span></div>
            <div class="dim"><span class="dim-label">兴趣方向</span><span class="dim-value">{', '.join(p.get('interest',[])) or '未明确'}</span></div>
        </div>"""

        # 多轮对话收敛
        conv_rows = ""
        for r in rounds:
            conv_rows += f"""
            <tr>
                <td>第{r['round']}轮</td>
                <td class="msg-cell">{r['message']}</td>
                <td>{r['completeness']:.0%}</td>
                <td>{r['confidence']:.0%}</td>
            </tr>"""

        conv_html = f"""
        <table class="conv-table">
            <thead><tr><th>轮次</th><th>学生消息</th><th>完整度</th><th>置信度</th></tr></thead>
            <tbody>{conv_rows}</tbody>
        </table>"""

        return dims_html, conv_html

    def path_table(path):
        stages = path.get("stages", [])
        rows = ""
        for s in stages:
            tasks_html = ""
            for t in s.get("tasks", []):
                tasks_html += f'<div class="task-item">[{t["type"]}] {t["description"]} ({t["estimated_minutes"]}min)</div>'

            rows += f"""
            <tr>
                <td class="stage-num">Stage {s['stage_id']}</td>
                <td><strong>{s['title']}</strong><br><span class="desc">{s.get('description','')}</span></td>
                <td><span class="badge badge-{s.get('difficulty','初级')}">{s.get('difficulty','')}</span></td>
                <td>{s.get('estimated_days','')}天</td>
                <td>{', '.join(s.get('topics',[]))}</td>
                <td class="tasks-cell">{tasks_html}</td>
            </tr>"""

        return f"""
        <div class="path-summary">
            <span>总目标: <strong>{path.get('goal','')}</strong></span>
            <span style="margin-left:24px">总天数: <strong>{path.get('total_estimated_days','')}天</strong></span>
            <span style="margin-left:24px">难度: <strong>{path.get('difficulty_level','')}</strong></span>
        </div>
        <table class="path-table">
            <thead><tr><th>#</th><th>阶段</th><th>难度</th><th>天数</th><th>知识点</th><th>任务</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
        <div class="adaptation">📝 {path.get('adaptation_notes','')}</div>
        """

    # 组装每个案例的卡片
    cases_html = ""
    colors = ["#4A90D9", "#5CB85C", "#F0AD4E"]  # 蓝、绿、橙
    for i, case in enumerate(results):
        dims_html, conv_html = profile_card(case)
        c = colors[i]

        cases_html += f"""
        <div class="case-section" style="border-left: 4px solid {c}">
            <h2 style="color: {c}">案例 {i+1}：{case['case_name']}</h2>

            <div class="two-col">
                <div class="col">
                    <h3>📋 最终画像（6维）</h3>
                    {dims_html}
                    <div class="metrics">
                        <span>完整度: <strong>{case['profile']['completeness']:.0%}</strong></span>
                        <span style="margin-left:16px">置信度: <strong>{case['profile']['confidence']:.0%}</strong></span>
                    </div>
                </div>
                <div class="col">
                    <h3>📈 多轮对话收敛过程</h3>
                    {conv_html}
                </div>
            </div>

            <h3>🗺️ 个性化学习路径</h3>
            {path_table(case['path'])}
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EduAgent 交互测试报告 — ProfileAgent + PlannerAgent</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif; background: #f5f7fa; color: #333; line-height: 1.6; }}
.header {{ background: linear-gradient(135deg, #1a237e, #283593); color: white; padding: 32px 48px; }}
.header h1 {{ font-size: 24px; margin-bottom: 8px; }}
.header p {{ opacity: 0.85; font-size: 14px; }}
.container {{ max-width: 1200px; margin: 0 auto; padding: 24px 48px; }}
.case-section {{ background: white; border-radius: 8px; padding: 28px; margin-bottom: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
.case-section h2 {{ font-size: 20px; margin-bottom: 20px; }}
.case-section h3 {{ font-size: 16px; margin: 20px 0 12px; color: #555; }}
.two-col {{ display: flex; gap: 24px; margin-bottom: 16px; }}
.col {{ flex: 1; min-width: 0; }}
.profile-dims {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
.dim {{ background: #f8f9fa; border-radius: 4px; padding: 8px 12px; }}
.dim-label {{ font-size: 12px; color: #888; display: block; }}
.dim-value {{ font-size: 13px; color: #333; font-weight: 500; }}
.metrics {{ margin-top: 12px; font-size: 14px; color: #666; }}
.conv-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
.conv-table th {{ background: #f0f2f5; padding: 8px 10px; text-align: left; font-weight: 500; }}
.conv-table td {{ padding: 8px 10px; border-bottom: 1px solid #f0f0f0; }}
.msg-cell {{ max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.path-summary {{ background: #f0f5ff; padding: 12px 16px; border-radius: 4px; margin-bottom: 12px; font-size: 14px; }}
.path-table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 12px; }}
.path-table th {{ background: #f0f2f5; padding: 10px 12px; text-align: left; font-weight: 500; }}
.path-table td {{ padding: 10px 12px; border-bottom: 1px solid #f0f0f0; vertical-align: top; }}
.stage-num {{ font-weight: 700; color: #1a237e; white-space: nowrap; }}
.desc {{ font-size: 12px; color: #999; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 500; }}
.badge-初级 {{ background: #e8f5e9; color: #2e7d32; }}
.badge-中级 {{ background: #fff3e0; color: #e65100; }}
.badge-高级 {{ background: #fce4ec; color: #c62828; }}
.task-item {{ font-size: 12px; color: #666; padding: 2px 0; }}
.tasks-cell {{ max-width: 300px; }}
.adaptation {{ font-size: 13px; color: #888; font-style: italic; }}
.footer {{ text-align: center; padding: 32px; color: #999; font-size: 12px; }}
</style>
</head>
<body>
<div class="header">
    <h1>EduAgent 交互测试报告</h1>
    <p>ProfileAgent（多轮对话画像构建）→ PlannerAgent（个性化学习路径生成）| 2026-06-11 | 测试环境：Mock LLM + 规则降级</p>
</div>
<div class="container">
    {cases_html}
</div>
<div class="footer">
    EduAgent — 基于大模型的个性化学习资源生成与学习多智能体系统 | 第15届软件杯 A3
</div>
</body>
</html>"""


if __name__ == "__main__":
    html_path = asyncio.run(main())
    print(f"\nOpen in browser: file:///{html_path}")
