"""
🧠 REDIS SHORT-TERM MEMORY
Lưu tối đa 10 prompt cũ của user theo machine_id (request-id của máy).
"""

import json
import os
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

MEMORY_LIMIT = 10
KEY_PREFIX = "vinuni:agent:memory:"


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_or_create_machine_id() -> str:
    """ID ổn định của máy (dùng làm Redis key). Tạo một lần, ghi vào .machine_id."""
    path = os.path.join(_project_root(), ".machine_id")
    if os.path.exists(path):
        value = open(path, "r", encoding="utf-8").read().strip()
        if value:
            return value
    value = str(uuid.uuid4())
    with open(path, "w", encoding="utf-8") as f:
        f.write(value)
    return value


def new_request_id() -> str:
    return str(uuid.uuid4())


class ConversationMemory:
    """Lưu / đọc 10 prompt user gần nhất. Ưu tiên Redis; fallback RAM nếu Redis tắt."""

    def __init__(self, redis_url: Optional[str] = None, limit: int = MEMORY_LIMIT):
        self.machine_id = load_or_create_machine_id()
        self.limit = max(1, int(os.getenv("MEMORY_LIMIT", limit)))
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_key = f"{KEY_PREFIX}{self.machine_id}"
        self._local: deque = deque(maxlen=self.limit)
        self._redis = None
        self.backend = "memory"

        try:
            import redis
            client = redis.Redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            client.ping()
            self._redis = client
            self.backend = "redis"
            print(
                f"✅ [MEMORY] Redis kết nối {self.redis_url} | "
                f"machine_id={self.machine_id} | key={self.redis_key}"
            )
        except Exception as exc:
            print(
                f"⚠️ [MEMORY] Redis không dùng được ({exc}). "
                f"Fallback RAM theo machine_id={self.machine_id} (mất khi tắt app)."
            )

    def get_recent(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Trả về prompt cũ, cũ → mới, tối đa `limit` (mặc định 10)."""
        cap = limit or self.limit
        records: List[Dict[str, Any]] = []

        if self._redis is not None:
            try:
                raw_items = self._redis.lrange(self.redis_key, 0, cap - 1)
                for raw in reversed(raw_items):
                    try:
                        records.append(json.loads(raw))
                    except json.JSONDecodeError:
                        records.append({
                            "request_id": "",
                            "prompt": raw,
                            "role": "user"
                        })
                return records
            except Exception as exc:
                print(f"⚠️ [MEMORY] Đọc Redis lỗi ({exc}), dùng RAM.")

        return list(self._local)[-cap:]

    def append_user_prompt(self, prompt: str, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Đẩy prompt hiện tại lên Redis (LPUSH + LTRIM 0..9). Không gồm câu hỏi đang hỏi vào lần lấy trước đó."""
        record = {
            "request_id": request_id or new_request_id(),
            "machine_id": self.machine_id,
            "role": "user",
            "prompt": prompt,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        payload = json.dumps(record, ensure_ascii=False)
        self._local.append(record)

        if self._redis is not None:
            try:
                pipe = self._redis.pipeline()
                pipe.lpush(self.redis_key, payload)
                pipe.ltrim(self.redis_key, 0, self.limit - 1)
                pipe.execute()
            except Exception as exc:
                print(f"⚠️ [MEMORY] Ghi Redis lỗi ({exc}). Đã lưu RAM.")

        return record
