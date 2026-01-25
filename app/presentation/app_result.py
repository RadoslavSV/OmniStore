from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Dict


@dataclass
class AppErrorInfo:
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class AppResult:
    ok: bool
    data: Optional[Any] = None
    error: Optional[AppErrorInfo] = None

    @staticmethod
    def success(data: Any = None) -> "AppResult":
        return AppResult(ok=True, data=data)

    @staticmethod
    def fail(code: str, message: str, details: Optional[Dict[str, Any]] = None) -> "AppResult":
        return AppResult(ok=False, error=AppErrorInfo(code=code, message=message, details=details))
