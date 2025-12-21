"""
Performance Profiling Utilities for Mall Chatbot

This module provides timing decorators and utilities to measure
performance bottlenecks in the query processing pipeline.
"""

import time
import functools
import asyncio
from typing import Callable, Any, Dict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PerformanceTimer:
    """Context manager for timing code blocks."""
    
    def __init__(self, name: str, logger_func=None):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.logger_func = logger_func or logger.info
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.duration = (self.end_time - self.start_time) * 1000  # Convert to ms
        self.logger_func(f"⏱️  {self.name}: {self.duration:.2f}ms")
        return False
    
    def get_duration_ms(self) -> float:
        """Get duration in milliseconds."""
        return self.duration if self.duration is not None else 0.0


def time_function(func: Callable) -> Callable:
    """
    Decorator to time synchronous functions.
    
    Usage:
        @time_function
        def my_function():
            pass
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = (end_time - start_time) * 1000
        logger.info(f"⏱️  {func.__name__}: {duration:.2f}ms")
        return result
    return wrapper


def time_async_function(func: Callable) -> Callable:
    """
    Decorator to time asynchronous functions.
    
    Usage:
        @time_async_function
        async def my_async_function():
            pass
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = (end_time - start_time) * 1000
        logger.info(f"⏱️  {func.__name__}: {duration:.2f}ms")
        return result
    return wrapper


class QueryProfiler:
    """
    Comprehensive query profiler for tracking multiple timing stages.
    
    Usage:
        profiler = QueryProfiler()
        profiler.start("retrieval")
        # ... do retrieval work ...
        profiler.end("retrieval")
        profiler.start("llm")
        # ... do LLM work ...
        profiler.end("llm")
        profiler.log_summary()
    """
    
    def __init__(self, query_id: str = None):
        self.query_id = query_id or f"query_{int(time.time() * 1000)}"
        self.timings: Dict[str, Dict[str, float]] = {}
        self.total_start = time.perf_counter()
    
    def start(self, stage_name: str):
        """Start timing a stage."""
        if stage_name not in self.timings:
            self.timings[stage_name] = {}
        self.timings[stage_name]["start"] = time.perf_counter()
    
    def end(self, stage_name: str):
        """End timing a stage."""
        if stage_name not in self.timings or "start" not in self.timings[stage_name]:
            logger.warning(f"Stage '{stage_name}' was not started")
            return
        
        end_time = time.perf_counter()
        start_time = self.timings[stage_name]["start"]
        duration = (end_time - start_time) * 1000  # Convert to ms
        self.timings[stage_name]["duration"] = duration
        self.timings[stage_name]["end"] = end_time
    
    def get_duration(self, stage_name: str) -> float:
        """Get duration of a stage in milliseconds."""
        if stage_name in self.timings and "duration" in self.timings[stage_name]:
            return self.timings[stage_name]["duration"]
        return 0.0
    
    def get_total_duration(self) -> float:
        """Get total duration from profiler creation in milliseconds."""
        return (time.perf_counter() - self.total_start) * 1000
    
    def log_summary(self):
        """Log a formatted summary of all timings."""
        total = self.get_total_duration()
        
        logger.info("=" * 70)
        logger.info(f"📊 QUERY PROFILING SUMMARY - {self.query_id}")
        logger.info("=" * 70)
        
        if not self.timings:
            logger.info("No timing data collected")
            logger.info("=" * 70)
            return
        
        # Sort by duration (descending)
        sorted_timings = sorted(
            [(name, data.get("duration", 0)) for name, data in self.timings.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        for stage_name, duration in sorted_timings:
            percentage = (duration / total * 100) if total > 0 else 0
            bar_length = int(percentage / 2)  # Scale to 50 chars max
            bar = "█" * bar_length
            logger.info(f"{stage_name:.<30} {duration:>8.2f}ms ({percentage:>5.1f}%) {bar}")
        
        logger.info("-" * 70)
        logger.info(f"{'TOTAL':.<30} {total:>8.2f}ms (100.0%)")
        logger.info("=" * 70)
    
    def get_summary_dict(self) -> Dict[str, Any]:
        """Get summary as a dictionary for API responses."""
        return {
            "query_id": self.query_id,
            "total_duration_ms": round(self.get_total_duration(), 2),
            "stages": {
                name: {
                    "duration_ms": round(data.get("duration", 0), 2),
                    "percentage": round((data.get("duration", 0) / self.get_total_duration() * 100), 1)
                }
                for name, data in self.timings.items()
                if "duration" in data
            }
        }


# Global profiler for request-level tracking
_current_profiler = None


def get_current_profiler() -> QueryProfiler:
    """Get the current thread-local profiler."""
    global _current_profiler
    if _current_profiler is None:
        _current_profiler = QueryProfiler()
    return _current_profiler


def set_current_profiler(profiler: QueryProfiler):
    """Set the current thread-local profiler."""
    global _current_profiler
    _current_profiler = profiler


def clear_current_profiler():
    """Clear the current thread-local profiler."""
    global _current_profiler
    _current_profiler = None


if __name__ == "__main__":
    # Test the profiling utilities
    print("Testing profiling utilities...\n")
    
    # Test PerformanceTimer
    with PerformanceTimer("Test operation"):
        time.sleep(0.1)
    
    # Test QueryProfiler
    profiler = QueryProfiler("test_query")
    
    profiler.start("stage1")
    time.sleep(0.05)
    profiler.end("stage1")
    
    profiler.start("stage2")
    time.sleep(0.15)
    profiler.end("stage2")
    
    profiler.start("stage3")
    time.sleep(0.03)
    profiler.end("stage3")
    
    profiler.log_summary()
    print("\nSummary dict:")
    print(profiler.get_summary_dict())
