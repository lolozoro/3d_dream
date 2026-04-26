import logging
import sys
import time
from typing import Optional, Dict, Any


class StepTimer:
    """步骤计时上下文管理器，在 async / sync 函数中均可使用"""

    def __init__(
        self,
        logger: logging.Logger,
        step_name: str,
        extra: Optional[Dict[str, Any]] = None,
    ):
        self.logger = logger
        self.step_name = step_name
        self.extra = extra or {}
        self.start: float = 0.0

    def __enter__(self):
        self.start = time.perf_counter()
        self.logger.info(f"▶️  开始步骤: {self.step_name}", extra=self.extra)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = (time.perf_counter() - self.start) * 1000
        if exc_type:
            self.logger.error(
                f"❌ 步骤失败: {self.step_name} | 耗时: {elapsed:.2f}ms | 错误: {exc_val}",
                extra=self.extra,
            )
        else:
            self.logger.info(
                f"✅ 步骤完成: {self.step_name} | 耗时: {elapsed:.2f}ms",
                extra=self.extra,
            )


def get_logger(name: str) -> logging.Logger:
    """获取统一命名规范的 logger"""
    return logging.getLogger(name)


def setup_logging(level: int = logging.INFO) -> None:
    """配置全局日志格式与输出"""
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    # 避免重复添加 handler（如 uvicorn 已配置时保留其 handler）
    if not root.handlers:
        root.addHandler(handler)
    root.setLevel(level)
