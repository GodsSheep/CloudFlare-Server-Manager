import threading
from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RequestRecord:
    time: str
    method: str
    path: str
    status: int
    latency: int
    size: int = 0


class RequestMonitor:
    def __init__(self):
        self._records: List[RequestRecord] = []
        self._lock = threading.Lock()
        self._stats = {
            'requests': 0,
            'responses': 0,
            'errors': 0,
            'avg_latency': 0,
            'p95_latency': 0,
            'p99_latency': 0,
        }

    def record(self, record: RequestRecord):
        with self._lock:
            self._records.append(record)
            self._stats['requests'] += 1
            if 200 <= record.status < 400:
                self._stats['responses'] += 1
            else:
                self._stats['errors'] += 1
            latencies = [r.latency for r in self._records[-1000:]]
            if latencies:
                self._stats['avg_latency'] = sum(latencies) / len(latencies)
                sorted_lat = sorted(latencies)
                self._stats['p95_latency'] = sorted_lat[int(len(sorted_lat) * 0.95)]
                self._stats['p99_latency'] = sorted_lat[int(len(sorted_lat) * 0.99)]

    def get_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            return [r.__dict__ for r in self._records[-limit:]]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._stats)

    def clear(self):
        with self._lock:
            self._records.clear()
            self._stats = {
                'requests': 0, 'responses': 0, 'errors': 0,
                'avg_latency': 0, 'p95_latency': 0, 'p99_latency': 0,
            }
