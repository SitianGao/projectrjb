"""幂等初始化主演示账号、课程和数据库数据。"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.init_demo_course import init_demo_course


if __name__ == "__main__":
    result = init_demo_course()
    print(
        "demo_student 初始化完成："
        f"course={result.get('course', {}).get('id')} "
        f"path={result.get('path', {}).get('id')}"
    )
