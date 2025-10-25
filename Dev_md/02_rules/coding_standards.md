# Nong-View 코딩 표준

## 1. Python 코딩 규칙

### 1.1 기본 규칙
- **PEP 8** 준수
- **Python 3.10+** 기능 활용
- **Type Hints** 필수

### 1.2 네이밍 컨벤션

#### 파일명
```python
# snake_case 사용
data_registry.py  # ✅ Good
DataRegistry.py   # ❌ Bad
```

#### 클래스
```python
# PascalCase 사용
class DataRegistry:  # ✅ Good
    pass

class data_registry:  # ❌ Bad
    pass
```

#### 함수 및 메서드
```python
# snake_case 사용
def process_image():  # ✅ Good
    pass

def ProcessImage():  # ❌ Bad
    pass
```

#### 상수
```python
# UPPER_SNAKE_CASE 사용
MAX_TILE_SIZE = 640  # ✅ Good
DEFAULT_OVERLAP = 0.2  # ✅ Good

max_tile_size = 640  # ❌ Bad
```

#### Private 속성
```python
# 언더스코어 prefix 사용
class MyClass:
    def __init__(self):
        self._private_attr = 10  # ✅ Good
        self.__very_private = 20  # 특별한 경우만
```

### 1.3 Type Hints

#### 기본 타입
```python
def add_numbers(a: int, b: int) -> int:
    return a + b

def process_text(text: str) -> str:
    return text.upper()

def check_valid(value: float) -> bool:
    return value > 0
```

#### 컬렉션 타입
```python
from typing import List, Dict, Set, Tuple, Optional

def get_items() -> List[str]:
    return ["item1", "item2"]

def get_mapping() -> Dict[str, int]:
    return {"key": 1}

def get_coordinates() -> Tuple[float, float]:
    return (10.0, 20.0)

def find_item(id: int) -> Optional[str]:
    return None  # or some string
```

#### 복잡한 타입
```python
from typing import Union, Any, Callable, TypeVar

T = TypeVar('T')

def process(
    data: Union[str, bytes],
    callback: Callable[[str], None],
    metadata: Dict[str, Any]
) -> List[T]:
    pass
```

### 1.4 Docstring

#### 함수 Docstring
```python
def complex_function(
    param1: str,
    param2: int,
    optional: bool = False
) -> Dict[str, Any]:
    """
    Brief description of the function.
    
    Detailed explanation of what the function does,
    including any important algorithms or business logic.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        optional: Whether to enable optional feature
        
    Returns:
        Dictionary containing:
        - 'result': The main result
        - 'status': Operation status
        
    Raises:
        ValueError: If param1 is empty
        TypeError: If param2 is not integer
        
    Example:
        >>> result = complex_function("test", 123)
        >>> print(result['status'])
        'success'
    """
    pass
```

#### 클래스 Docstring
```python
class DataProcessor:
    """
    Process various types of data.
    
    This class handles data validation, transformation,
    and storage for the application.
    
    Attributes:
        config: Configuration dictionary
        logger: Logger instance
        
    Example:
        >>> processor = DataProcessor(config={'debug': True})
        >>> processor.process("data")
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize processor with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
```

### 1.5 Import 규칙

#### Import 순서
```python
# 1. 표준 라이브러리
import os
import sys
from pathlib import Path

# 2. 서드파티 라이브러리
import numpy as np
import pandas as pd
from fastapi import FastAPI

# 3. 로컬 모듈
from src.common import config
from src.pod1_data_ingestion import DataRegistry
```

#### Import 스타일
```python
# 절대 import 선호
from src.pod1_data_ingestion.registry import DataRegistry  # ✅

# 상대 import는 패키지 내부에서만
from .schemas import ImageMetadata  # ✅ (같은 패키지 내)

# 와일드카드 import 금지
from module import *  # ❌ Bad
```

## 2. 에러 처리

### 2.1 Exception 계층
```python
# 기본 Exception 클래스
class NongViewException(Exception):
    """Base exception for Nong-View"""
    pass

# 도메인별 Exception
class DataValidationError(NongViewException):
    """Data validation failed"""
    pass

class ProcessingError(NongViewException):
    """Processing failed"""
    pass
```

### 2.2 에러 처리 패턴
```python
# 구체적인 예외 처리
try:
    result = process_data(data)
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    raise DataValidationError(f"Input file missing: {e}")
except ValueError as e:
    logger.warning(f"Invalid value: {e}")
    return default_value
except Exception as e:
    logger.critical(f"Unexpected error: {e}")
    raise ProcessingError(f"Processing failed: {e}")
finally:
    cleanup_resources()
```

## 3. 로깅

### 3.1 로깅 레벨
```python
import logging

logger = logging.getLogger(__name__)

# 로그 레벨 사용 지침
logger.debug("Detailed debugging info")  # 개발 중 디버깅
logger.info("Process started")  # 일반 정보
logger.warning("Low memory")  # 경고 (처리는 계속)
logger.error("Failed to connect")  # 에러 (복구 가능)
logger.critical("System failure")  # 심각 (시스템 중단)
```

### 3.2 로깅 포맷
```python
# 구조화된 로깅
logger.info(
    "Processing completed",
    extra={
        'image_id': image_id,
        'duration': processing_time,
        'tiles_count': len(tiles)
    }
)

# 에러 로깅
logger.error(
    f"Processing failed for {image_id}",
    exc_info=True  # 스택 트레이스 포함
)
```

## 4. 비동기 프로그래밍

### 4.1 Async/Await 패턴
```python
import asyncio
from typing import List

async def fetch_data(url: str) -> dict:
    """Fetch data asynchronously"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def process_multiple(urls: List[str]) -> List[dict]:
    """Process multiple URLs concurrently"""
    tasks = [fetch_data(url) for url in urls]
    return await asyncio.gather(*tasks)
```

### 4.2 동기/비동기 혼용
```python
# 동기 코드에서 비동기 함수 호출
def sync_wrapper():
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(async_function())
    return result

# 비동기 코드에서 동기 함수 호출
async def async_wrapper():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, sync_function)
    return result
```

## 5. 테스트

### 5.1 테스트 구조
```python
import pytest
from unittest.mock import Mock, patch

class TestDataRegistry:
    """Test DataRegistry functionality"""
    
    @pytest.fixture
    def registry(self):
        """Create test registry"""
        return DataRegistry(test_mode=True)
    
    def test_register_image(self, registry):
        """Test image registration"""
        # Arrange
        image_path = "test.tif"
        
        # Act
        result = registry.register_image(image_path)
        
        # Assert
        assert result is not None
        assert result.file_path == image_path
    
    @patch('src.external_api.call')
    def test_with_mock(self, mock_call):
        """Test with mocked external call"""
        mock_call.return_value = {'status': 'ok'}
        # Test logic here
```

### 5.2 테스트 명명
```python
# 테스트 메서드명: test_<what>_<condition>_<expected>
def test_process_image_with_invalid_path_raises_error():
    pass

def test_calculate_area_with_polygon_returns_float():
    pass
```

## 6. 성능 최적화

### 6.1 프로파일링
```python
import time
import cProfile
from functools import wraps

def timeit(func):
    """Decorator to measure execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        logger.debug(f"{func.__name__} took {end-start:.4f} seconds")
        return result
    return wrapper

@timeit
def slow_function():
    # Function implementation
    pass
```

### 6.2 메모리 관리
```python
# Generator 사용으로 메모리 절약
def process_large_file(filepath: str):
    with open(filepath, 'r') as f:
        for line in f:  # Generator, 한 줄씩 처리
            yield process_line(line)

# Context manager로 리소스 관리
from contextlib import contextmanager

@contextmanager
def managed_resource():
    resource = acquire_resource()
    try:
        yield resource
    finally:
        release_resource(resource)
```

## 7. 보안

### 7.1 입력 검증
```python
from pydantic import BaseModel, validator

class UserInput(BaseModel):
    file_path: str
    
    @validator('file_path')
    def validate_path(cls, v):
        # Path traversal 방지
        if '..' in v or v.startswith('/'):
            raise ValueError("Invalid path")
        return v
```

### 7.2 민감정보 처리
```python
import os
from dotenv import load_dotenv

# 환경변수로 관리
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
API_KEY = os.getenv("API_KEY")

# 로깅에서 제외
def log_safe(data: dict) -> dict:
    """Remove sensitive data before logging"""
    safe_data = data.copy()
    for key in ['password', 'api_key', 'token']:
        if key in safe_data:
            safe_data[key] = '***'
    return safe_data
```

## 8. Git 커밋 메시지

### 8.1 커밋 메시지 형식
```
<type>(<scope>): <subject>

<body>

<footer>
```

### 8.2 Type 종류
- **feat**: 새로운 기능
- **fix**: 버그 수정
- **docs**: 문서 수정
- **style**: 코드 포맷팅
- **refactor**: 리팩토링
- **test**: 테스트 코드
- **chore**: 빌드, 패키지 관련

### 8.3 예시
```
feat(pod1): Add image metadata extraction

Implement metadata extraction from TIF/ECW files
including capture date, CRS, and resolution.

Closes #123
```

---

*Version: 1.0.0*
*Last Updated: 2025-10-26*
*Next Review: 2025-11-26*