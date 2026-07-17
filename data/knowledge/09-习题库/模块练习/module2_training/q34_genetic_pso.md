# 保证种群大小

> 来源模块: module2_training
> 原始文件: q34_genetic_pso.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】元启发式优化：遗传算法与粒子群优化
【模块】模型训练与评估
【难度】8
【知识点】遗传算法、粒子群优化、适应度函数、交叉变异、群体智能、函数优化
【描述】
手动实现遗传算法（GA）和粒子群优化（PSO）算法，用于求解连续函数优化问题。
对比两种算法的收敛性能和全局搜索能力。

【要求】
1. 实现遗传算法：选择（锦标赛选择）、交叉（算术交叉）、变异（高斯变异）
2. 实现粒子群优化：速度更新、位置更新、个体最优和全局最优维护
3. 在多个标准测试函数上评估（Rastrigin、Ackley、Rosenbrock）
4. 对比两种算法的收敛曲线
5. 支持多维优化问题
6. 输出最优解和收敛过程

【提示】
- Rastrigin函数: f(x) = 10n + sum(xi^2 - 10*cos(2*pi*xi))
- PSO速度更新: v = w*v + c1*r1*(pbest-x) + c2*r2*(gbest-x)
- 锦标赛选择：从种群中随机选k个个体，选最优的
- 算术交叉：child = alpha * parent1 + (1-alpha) * parent2
=============================
"""

# ========== 参考答案 ==========

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
from typing import Callable


# ======================== 测试函数 ========================

def rastrigin(x):
    """Rastrigin函数，全局最小值在原点，值为0"""
    n = len(x)
    return 10 * n + np.sum(x ** 2 - 10 * np.cos(2 * np.pi * x))


def ackley(x):
    """Ackley函数，全局最小值在原点，值为0"""
    n = len(x)
    sum1 = np.sum(x ** 2)
    sum2 = np.sum(np.cos(2 * np.pi * x))
    return -20 * np.exp(-0.2 * np.sqrt(sum1 / n)) - np.exp(sum2 / n) + 20 + np.e


def rosenbrock(x):
    """Rosenbrock函数，全局最小值在(1,1,...,1)，值为0"""
    return np.sum(100 * (x[1:] - x[:-1] ** 2) ** 2 + (1 - x[:-1]) ** 2)


def sphere(x):
    """Sphere函数，全局最小值在原点，值为0"""
    return np.sum(x ** 2)


# ======================== 遗传算法 ========================

class GeneticAlgorithm:
    """遗传算法"""

    def __init__(
        self,
        objective_func: Callable,
        dim: int = 2,
        pop_size: int = 50,
        bounds: tuple = (-5.12, 5.12),
        crossover_rate: float = 0.8,
        mutation_rate: float = 0.1,
        mutation_std: float = 0.3,
        tournament_size: int = 3,
        elite_size: int = 2,
    ):
        self.objective_func = objective_func
        self.dim = dim
        self.pop_size = pop_size
        self.bounds = bounds
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.mutation_std = mutation_std
        self.tournament_size = tournament_size
        self.elite_size = elite_size

    def _init_population(self):
        """初始化种群"""
        return np.random.uniform(
            self.bounds[0], self.bounds[1], (self.pop_size, self.dim)
        )

    def _evaluate(self, population):
        """评估种群适应度"""
        return np.array([self.objective_func(ind) for ind in population])

    def _tournament_selection(self, fitness):
        """锦标赛选择"""
        selected = []
        for _ in range(self.pop_size - self.elite_size):
            candidates = np.random.choice(self.pop_size, self.tournament_size, replace=False)
            best = candidates[np.argmin(fitness[candidates])]
            selected.append(best)
        return selected

    def _arithmetic_crossover(self, parent1, parent2):
        """算术交叉"""
        alpha = np.random.random()
        child1 = alpha * parent1 + (1 - alpha) * parent2
        child2 = (1 - alpha) * parent1 + alpha * parent2
        return child1, child2

    def _gaussian_mutation(self, individual):
        """高斯变异"""
        mutant = individual.copy()
        for i in range(self.dim):
            if np.random.random() < self.mutation_rate:
                mutant[i] += np.random.normal(0, self.mutation_std)
                mutant[i] = np.clip(mutant[i], self.bounds[0], self.bounds[1])
        return mutant

    def optimize(self, num_generations=200, verbose=True):
        """运行遗传算法优化"""
        population = self._init_population()
        fitness = self._evaluate(population)

        best_fitness_history = []
        avg_fitness_history = []

        best_idx = np.argmin(fitness)
        best_solution = population[best_idx].copy()
        best_fitness = fitness[best_idx]

        for gen in range(num_generations):
            # 精英保留
            elite_indices = np.argsort(fitness)[:self.elite_size]
            new_population = [population[i].copy() for i in elite_indices]

            # 选择
            selected = self._tournament_selection(fitness)

            # 交叉和变异
            for i in range(0, len(selected), 2):
                if i + 1 < len(selected):
                    p1, p2 = population[selected[i]], population[selected[i + 1]]
                    if np.random.random() < self.crossover_rate:
                        c1, c2 = self._arithmetic_crossover(p1, p2)
                    else:
                        c1, c2 = p1.copy(), p2.copy()

                    c1 = self._gaussian_mutation(c1)
                    c2 = self._gaussian_mutation(c2)
                    new_population.extend([c1, c2])
                else:
                    c = self._gaussian_mutation(population[selected[i]].copy())
                    new_population.append(c)

            # 保证种群大小
            new_population = new_population[: self.pop_size]
            population = np.array(new_population)
            fitness = self._evaluate(population)

            # 更新最优
            gen_best_idx = np.argmin(fitness)
            if fitness[gen_best_idx] < best_fitness:
                best_fitness = fitness[gen_best_idx]
                best_solution = population[gen_best_idx].copy()

            best_fitness_history.append(best_fitness)
            avg_fitness_history.append(np.mean(fitness))

            if verbose and (gen + 1) % 50 == 0:
                print(f"  GA Gen {gen + 1:4d} | Best: {best_fitness:.6f} | Avg: {np.mean(fitness):.6f}")

        return best_solution, best_fitness, best_fitness_history, avg_fitness_history


# ======================== 粒子群优化 ========================

class ParticleSwarmOptimization:
    """粒子群优化算法"""

    def __init__(
        self,
        objective_func: Callable,
        dim: int = 2,
        pop_size: int = 50,
        bounds: tuple = (-5.12, 5.12),
        w: float = 0.7,      # 惯性权重
        c1: float = 1.5,     # 认知系数
        c2: float = 1.5,     # 社会系数
        v_max: float = 1.0,  # 最大速度
    ):
        self.objective_func = objective_func
        self.dim = dim
        self.pop_size = pop_size
        self.bounds = bounds
        self.w = w
        self.c1 = c1
        self.c2 = c2
        self.v_max = v_max

    def optimize(self, num_iterations=200, verbose=True):
        """运行PSO优化"""
        # 初始化粒子位置和速度
        positions = np.random.uniform(
            self.bounds[0], self.bounds[1], (self.pop_size, self.dim)
        )
        velocities = np.random.uniform(
            -self.v_max, self.v_max, (self.pop_size, self.dim)
        )

        # 评估适应度
        fitness = np.array([self.objective_func(p) for p in positions])

        # 个体最优
        pbest_positions = positions.copy()
        pbest_fitness = fitness.copy()

        # 全局最优
        gbest_idx = np.argmin(fitness)
        gbest_position = positions[gbest_idx].copy()
        gbest_fitness = fitness[gbest_idx]

        best_fitness_history = []
        avg_fitness_history = []

        for it in range(num_iterations):
            for i in range(self.pop_size):
                # 更新速度
                r1 = np.random.random(self.dim)
                r2 = np.random.random(self.dim)

                velocities[i] = (
                    self.w * velocities[i]
                    + self.c1 * r1 * (pbest_positions[i] - positions[i])
                    + self.c2 * r2 * (gbest_position - positions[i])
                )

                # 限制速度
                velocities[i] = np.clip(velocities[i], -self.v_max, self.v_max)

                # 更新位置
                positions[i] += velocities[i]
                positions[i] = np.clip(
                    positions[i], self.bounds[0], self.bounds[1]
                )

                # 评估适应度
                current_fitness = self.objective_func(positions[i])

                # 更新个体最优
                if current_fitness < pbest_fitness[i]:
                    pbest_fitness[i] = current_fitness
                    pbest_positions[i] = positions[i].copy()

                    # 更新全局最优
                    if current_fitness < gbest_fitness:
                        gbest_fitness = current_fitness
                        gbest_position = positions[i].copy()

            best_fitness_history.append(gbest_fitness)
            current_fitness_all = np.array([self.objective_func(p) for p in positions])
            avg_fitness_history.append(np.mean(current_fitness_all))

            if verbose and (it + 1) % 50 == 0:
                print(f"  PSO Iter {it + 1:4d} | Best: {gbest_fitness:.6f} | Avg: {np.mean(current_fitness_all):.6f}")

        return gbest_position, gbest_fitness, best_fitness_history, avg_fitness_history


# ======================== 可视化 ========================

def plot_convergence_comparison(
    ga_history, pso_history, func_name, dim, save_path=None
):
    """绘制收敛对比图"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # 最优适应度对比
    ax1.plot(ga_history[0], label="GA (Best)", color="blue")
    ax1.plot(pso_history[0], label="PSO (Best)", color="red")
    ax1.set_xlabel("Generation/Iteration")
    ax1.set_ylabel("Best Fitness")
    ax1.set_title(f"{func_name} (dim={dim}) - Best Fitness")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale("log")

    # 平均适应度对比
    ax2.plot(ga_history[1], label="GA (Avg)", color="blue", alpha=0.7)
    ax2.plot(pso_history[1], label="PSO (Avg)", color="red", alpha=0.7)
    ax2.set_xlabel("Generation/Iteration")
    ax2.set_ylabel("Average Fitness")
    ax2.set_title(f"{func_name} (dim={dim}) - Average Fitness")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=100, bbox_inches="tight")
    plt.close()


# ======================== 主函数 ========================

def solve():
    """元启发式优化完整演示"""
    print("=" * 60)
    print("元启发式优化: 遗传算法 (GA) vs 粒子群优化 (PSO)")
    print("=" * 60)

    output_dir = os.path.dirname(__file__) or "."

    # ---- 测试配置 ----
    test_functions = [
        ("Rastrigin", rastrigin, (-5.12, 5.12)),
        ("Ackley", ackley, (-5.0, 5.0)),
        ("Rosenbrock", rosenbrock, (-5.0, 5.0)),
        ("Sphere", sphere, (-5.0, 5.0)),
    ]

    dim = 5
    pop_size = 50
    num_generations = 200

    results = {}

    for func_name, func, bounds in test_functions:
        print(f"\n{'=' * 40}")
        print(f"测试函数: {func_name} (dim={dim}, bounds={bounds})")
        print(f"{'=' * 40}")

        # ---- 遗传算法 ----
        print(f"\n遗传算法 (GA):")
        ga = GeneticAlgorithm(
            objective_func=func,
            dim=dim,
            pop_size=pop_size,
            bounds=bounds,
            crossover_rate=0.8,
            mutation_rate=0.15,
            mutation_std=0.3,
            tournament_size=3,
            elite_size=2,
        )
        ga_best_sol, ga_best_fit, ga_best_hist, ga_avg_hist = ga.optimize(
            num_generations=num_generations, verbose=True
        )
        print(f"  GA 最优解: {ga_best_sol}")
        print(f"  GA 最优值: {ga_best_fit:.8f}")

        # ---- 粒子群优化 ----
        print(f"\n粒子群优化 (PSO):")
        pso = ParticleSwarmOptimization(
            objective_func=func,
            dim=dim,
            pop_size=pop_size,
            bounds=bounds,
            w=0.7,
            c1=1.5,
            c2=1.5,
            v_max=1.0,
        )
        pso_best_sol, pso_best_fit, pso_best_hist, pso_avg_hist = pso.optimize(
            num_iterations=num_generations, verbose=True
        )
        print(f"  PSO 最优解: {pso_best_sol}")
        print(f"  PSO 最优值: {pso_best_fit:.8f}")

        # 记录结果
        results[func_name] = {
            "ga_best": ga_best_fit,
            "pso_best": pso_best_fit,
        }

        # 绘制收敛对比图
        plot_convergence_comparison(
            (ga_best_hist, ga_avg_hist),
            (pso_best_hist, pso_avg_hist),
            func_name, dim,
            save_path=os.path.join(output_dir, f"optimization_{func_name.lower()}.png"),
        )
        print(f"  收敛图已保存: optimization_{func_name.lower()}.png")

    # ---- 结果汇总 ----
    print("\n" + "=" * 60)
    print("结果汇总:")
    print("-" * 60)
    print(f"{'函数':<15} {'GA最优值':<20} {'PSO最优值':<20} {'更优算法':<10}")
    print("-" * 60)

    for func_name, res in results.items():
        ga_val = res["ga_best"]
        pso_val = res["pso_best"]
        winner = "GA" if ga_val < pso_val else "PSO" if pso_val < ga_val else "平局"
        print(f"{func_name:<15} {ga_val:<20.8f} {pso_val:<20.8f} {winner:<10}")

    print("-" * 60)

    # ---- 2D等高线可视化 (以Rastrigin为例) ----
    print("\n生成2D Rastrigin等高线图...")
    x = np.linspace(-5.12, 5.12, 200)
    y = np.linspace(-5.12, 5.12, 200)
    X, Y = np.meshgrid(x, y)
    Z = np.array([[rastrigin(np.array([xi, yi])) for xi in x] for yi in y])

    fig, ax = plt.subplots(1, 1, figsize=(8, 6))
    contour = ax.contourf(X, Y, Z, levels=50, cmap="viridis")
    plt.colorbar(contour, label="f(x, y)")
    ax.set_xlabel("x1")
    ax.set_ylabel("x2")
    ax.set_title("Rastrigin函数等高线图")
    ax.scatter([0], [0], c="red", marker="*", s=200, label="全局最优(0,0)")
    ax.legend()
    plt.savefig(os.path.join(output_dir, "rastrigin_contour.png"), dpi=100, bbox_inches="tight")
    plt.close()
    print(f"等高线图已保存: {os.path.join(output_dir, 'rastrigin_contour.png')}")

    print("\n元启发式优化演示完成。")


if __name__ == "__main__":
    solve()

```
