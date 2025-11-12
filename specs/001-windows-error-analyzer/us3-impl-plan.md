# Implementation Plan — User Story 3 (LLM分析)

対象: specs/001-windows-error-analyzer/
日付: 2025-11-12
ブランチ: devin/1762938008-user-story-3-llm-analysis

## 目的
- 抽出済みのダンプ/イベント情報から、LLMを用いた原因分析・推奨対処のレポートを生成する。
- 受け入れ条件(US3-1〜3)の達成、およびLLM不通時のフォールバック(US3-4)を実装。
- レポート本文は日本語で出力（JSONキー名は英語のまま）に統一。

## 前提/依存
- US1/US2のパーサとデータモデルが利用可能であること。
- `OPENAI_API_KEY` が設定済み（環境変数または設定ファイル）。
- すべての時刻表示はJST(UTC+9)。内部処理はUTCで保持し、表示時に変換。

## アーキテクチャ
- `analyzers/correlator.py`: クラッシュ時刻±ウィンドウで関連イベントを抽出し、タイムラインを生成。
- `analyzers/llm_analyzer.py`: 入力要約→プロンプト生成→OpenAI呼び出し→レスポンス解析→`AnalysisReport`作成。
- `reporters/console_reporter.py`: 分析結果(要約/詳細/タイムライン/対処)の整形表示を拡張。
- `cli.py`: `--analyze/--no-analyze`、`--model`、`--time-window`、APIキー検証。

## 主要インターフェース(予定)
- `src/analyzers/correlator.py`
  - `def correlate_events(dump: DumpFileAnalysis|None, events: list[EventLogEntry], start: datetime|None, end: datetime|None, time_window_seconds: int = 3600) -> list[EventLogEntry]`
  - `def generate_timeline(events: list[EventLogEntry]) -> list[str]`  # `"HH:MM:SS | Level | Source | EventID | Message"` (JST)
- `src/analyzers/llm_analyzer.py`
  - `class LLMAnalyzer:`
    - `__init__(model: str = "gpt-4", timeout_s: int = 60, temperature: float = 0.3, max_tokens: int = 2000)`
    - `summarize_inputs(dump: DumpFileAnalysis|None, events: list[EventLogEntry]) -> dict`  # 文字数/トークン制御
    - `build_prompts(summary: dict) -> tuple[str, str]`  # (system, user)
    - `analyze(summary: dict) -> tuple[AnalysisReport, dict]`  # (report, {token_usage, latency})

## プロンプト設計(要旨)
- system: 日本語での回答を必須化。根拠（該当イベントやスタック）明示、誤認時は不確実性も明示。出力はJSONのみ（キーは英語）。
- user: ダンプ要約(エラーコード/モジュール/上位スタック)＋相関イベント(最大N件)＋環境(OS/arch)。
- 出力フォーマット: JSON(キー: root_cause_summary, detailed_analysis, remediation_steps[], event_timeline[], confidence)。

## トークン制御
- スタック: 先頭20フレームに制限(既仕様)。
- イベント: 重要度優先(Error/Critical)→新しい順に最大200件→タイムライン整形で要約。
- 長文メッセージは先頭512文字にトリム、改行と連続空白を正規化。

## エラーハンドリング/リトライ
- APIキー未設定: CLIで即時エラー(ヘルプ表示)。
- 通信/レート制限/5xx: 指数バックオフ(1s, 2s, 4s, 8s; 最大4回)。
- タイムアウト: `timeout_s` 超過でメッセージ表示し再試行案内。
- LLM不通時: 抽出結果のみのレポート雛形を提示(US3-4)。

## CLI拡張
- 追加フラグ: `--analyze/--no-analyze`(既定: analyze), `--model [gpt-4|gpt-3.5-turbo]`, `--time-window INT`。
- APIキー検証: 実行開始時に`utils/config.py`で検証し、未設定ならExit 2。

## 表示/出力
- Console: 既存レポーターに「AI Analysis」セクションを追加。
- JSON/Markdown: `AnalysisReport.to_markdown()`は`markdown_reporter.py`で実装、CLIの`--json`時はシリアライズ。

## テスト計画
- 単体
  - correlator: 窓内/外、境界、ソート順、フィルタ(レベル/ソース/期間)。
  - llm_analyzer: 要約のトークン上限制御、プロンプト生成、エラーパス(キー欠如/タイムアウト/429)。OpenAIクライアントはモック。
  - models: `AnalysisReport`の検証・`to_markdown()`の基本整形。
- 結合
  - CLI `--no-analyze`でパース→相関→出力まで。
  - `--analyze`でモックLLM→レポート生成→表示。
- 受け入れ
  - US3-1/2/3/4のシナリオをfixturesで再現。

## タスク分解(対応: specs/tasks.md T044–T060)
- T044: `models/analysis_report.py` 作成
- T045–T048: `analyzers/correlator.py` 相関/タイムライン
- T049–T056: `analyzers/llm_analyzer.py` (初期化→要約→プロンプト→API→解析→スピナー)
- T057–T059: `src/cli.py` フラグ追加・APIキー検証
- T060: `reporters/console_reporter.py` AI出力表示
- 付随: `utils/progress.py` スピナーAPI追加、`tests/` 追加

## 品質ゲート/DoD
- 受け入れ条件4項すべて満たすこと。
- 主要モジュール単体テストカバレッジ ≥ 80%。
- 2GBダンプ/10万件イベントで動作(モック/制限下で性能確認)。
- エラーメッセージは実用的かつ再試行案内を含む。

## 実装シーケンス
1) モデル(T044)→相関(T045–T048)
2) LLM要約/プロンプト/API(モック先行)(T049–T055)
3) 進捗表示(T056)→CLI拡張(T057–T059)→レポーター(T060)
4) 結合/受け入れテスト整備→調整

