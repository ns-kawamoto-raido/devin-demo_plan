from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict
from typing import Dict, List, Optional, Tuple

from openai import OpenAI
from openai import APIError, APIConnectionError, RateLimitError, AuthenticationError, BadRequestError, Timeout

from src.models.analysis_report import AnalysisReport, ConfidenceLevel
from src.models.dump_analysis import DumpFileAnalysis
from src.models.event_log import EventLogEntry
from src.analyzers.correlator import generate_timeline
from src.utils.config import get_openai_api_key
from src.utils.progress import spinner


class LLMAnalyzer:
    def __init__(
        self,
        model: str = "gpt-4",
        timeout_s: int = 60,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> None:
        self.model = model
        self.timeout_s = timeout_s
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client: Optional[OpenAI] = None

    def _client_or_init(self) -> OpenAI:
        if self._client is None:
            key = get_openai_api_key()
            if not key:
                raise RuntimeError("OPENAI_API_KEY is not set.")
            self._client = OpenAI(api_key=key)
        return self._client

    def summarize_inputs(
        self,
        dump: Optional[DumpFileAnalysis],
        events: List[EventLogEntry],
        event_limit: int = 200,
    ) -> Dict:
        stack = []
        if dump and getattr(dump, "stack_trace", None):
            stack = [str(f) for f in (dump.stack_trace or [])][:20]

        # Prioritize errors/critical first, then fill up to event_limit
        crit_err = [e for e in events if e.is_error_or_critical()]
        others = [e for e in events if not e.is_error_or_critical()]
        ordered = (crit_err + others)[:event_limit]

        timeline = generate_timeline(ordered)

        dump_summary = None
        if dump:
            dump_summary = {
                "file_path": dump.file_path,
                "crash_timestamp": dump.crash_timestamp.isoformat(),
                "error_code": dump.error_code,
                "faulting_module": dump.faulting_module,
                "process_name": dump.process_name,
                "os_version": dump.os_version,
                "architecture": dump.architecture,
                "stack_trace": stack,
            }

        limitations: List[str] = []
        if not dump:
            limitations.append("ダンプが未提供のため、根因特定の精度が限定されます。")
        if not events:
            limitations.append("イベントログが未提供のため、時系列相関の精度が限定されます。")

        return {
            "dump": dump_summary,
            "timeline": timeline,
            "limitations": limitations,
        }

    def build_prompts(self, summary: Dict) -> Tuple[str, str]:
        system = (
            "あなたはWindows障害解析の上級エンジニアです。クラッシュダンプとWindowsイベントログを分析し、"
            "根本原因と具体的な対処手順を提示してください。回答は必ず日本語で、簡潔かつ根拠（提示データの項目や時刻）に言及してください。"
            "出力形式は厳密にJSONのみとし、キーは次の通り（英語のまま）: "
            "root_cause_summary, detailed_analysis, remediation_steps, event_timeline, confidence。"
            "推測は避け、不確実な点はその旨を明示してください。Markdownや追加テキストは含めないでください。"
        )

        user = json.dumps(summary, ensure_ascii=False)
        return system, user

    def analyze(self, summary: Dict) -> Tuple[AnalysisReport, Dict]:
        client = self._client_or_init()
        system, user = self.build_prompts(summary)

        start = time.perf_counter()
        # Exponential backoff: 1s, 2s, 4s, 8s (max 4 attempts)
        last_err: Exception | None = None
        with spinner("Analyzing crash with AI..."):
            for attempt in range(4):
                try:
                    resp = client.chat.completions.create(
                        model=self.model,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                        timeout=self.timeout_s,
                    )
                    break
                except (RateLimitError, APIConnectionError, Timeout) as e:
                    last_err = e
                    delay = 2 ** attempt
                    time.sleep(delay)
                except (AuthenticationError, BadRequestError, APIError) as e:
                    # Non-retryable or likely client-side issues
                    last_err = e
                    raise
            else:
                # Exhausted retries
                if last_err:
                    raise last_err
        elapsed = time.perf_counter() - start

        content = resp.choices[0].message.content if resp.choices else "{}"
        try:
            data = json.loads(content)
        except Exception:
            # Fallback to wrapping as plain text
            data = {
                "root_cause_summary": content[:512],
                "detailed_analysis": content,
                "remediation_steps": [],
                "event_timeline": summary.get("timeline", []),
                "confidence": "Medium",
            }

        def _as_list_str(value) -> List[str]:
            if value is None:
                return []
            if isinstance(value, list):
                return [str(v).strip() for v in value if str(v).strip()]
            if isinstance(value, str):
                parts = [p.strip(" \t\r\n-•") for p in value.splitlines()]
                return [p for p in parts if p]
            # Fallback: wrap single value
            s = str(value).strip()
            return [s] if s else []

        session_id = str(uuid.uuid4())
        confidence = (data.get("confidence") or "Medium").capitalize()
        conf_enum = ConfidenceLevel[confidence.upper()] if confidence.upper() in ConfidenceLevel.__members__ else None

        event_timeline_norm = _as_list_str(data.get("event_timeline")) or summary.get("timeline", [])
        remediation_steps_norm = _as_list_str(data.get("remediation_steps"))

        report = AnalysisReport(
            session_id=session_id,
            generated_at=
            __import__("datetime").datetime.utcnow(),
            model_used=self.model,
            root_cause_summary=data.get("root_cause_summary", ""),
            detailed_analysis=data.get("detailed_analysis", ""),
            event_timeline=event_timeline_norm,
            remediation_steps=remediation_steps_norm,
            processing_time_seconds=elapsed,
            confidence_level=conf_enum,
            token_usage=getattr(resp, "usage", None).total_tokens if getattr(resp, "usage", None) else None,
            limitations=(
                _as_list_str(data.get("limitations")) + summary.get("limitations", [])
            ),
        )

        meta = {
            "token_usage": report.token_usage,
            "latency_seconds": elapsed,
        }
        return report, meta
