# Tasks: Windows Error Analyzer

**Input**: Design documents from `/specs/001-windows-error-analyzer/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

All paths are relative to repository root using single project structure:
- **Source**: `src/`
- **Tests**: `tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure per plan.md (src/, tests/, tests/fixtures/, tests/unit/, tests/integration/)
- [ ] T002 Initialize Python project with pyproject.toml and configure poetry/setuptools for Python 3.11+
- [ ] T003 [P] Create requirements.txt with dependencies: python-evtx, minidump, openai, click, rich, pytest
- [ ] T004 [P] Create requirements-dev.txt with dev dependencies: black, ruff, mypy, pytest-cov
- [ ] T005 [P] Create .env.example file with OPENAI_API_KEY placeholder
- [ ] T006 [P] Create .gitignore for Python project (venv/, __pycache__/, .env, *.pyc, .pytest_cache/)
- [ ] T007 [P] Create README.md with installation and usage instructions from quickstart.md
- [ ] T008 [P] Configure black formatter in pyproject.toml (line-length: 100)
- [ ] T009 [P] Configure ruff linter in pyproject.toml
- [ ] T010 [P] Configure mypy type checker in pyproject.toml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T011 Create src/__init__.py to make src a package
- [ ] T012 [P] Create all module __init__.py files (src/parsers/, src/models/, src/analyzers/, src/reporters/, src/utils/)
- [ ] T013 [P] Create tests/__init__.py and test module __init__.py files
- [ ] T014 Create src/utils/config.py for configuration and API key management (environment variables, config file loading)
- [ ] T015 [P] Create src/utils/progress.py with Rich progress bar utilities (wrappers for common progress patterns)
- [ ] T016 [P] Create src/utils/filters.py with event log filtering utilities (filter by level, time range)
- [ ] T017 Create data model enums in src/models/__init__.py (EventLevel, SessionStatus, ConfidenceLevel per data-model.md)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract and Display Dump File Contents (Priority: P1) 🎯 MVP CORE

**Goal**: Parse .dmp files and display crash information in human-readable format with progress feedback

**Independent Test**: Load a .dmp file and verify crash information (error codes, stack traces, module information) is extracted and displayed

### Implementation for User Story 1

- [ ] T018 [P] [US1] Create src/models/dump_analysis.py with DumpFileAnalysis dataclass per data-model.md (all fields, validation, __post_init__)
- [ ] T019 [US1] Create src/parsers/dump_parser.py with DumpParser class (parse() method using minidump library)
- [ ] T020 [US1] Implement dump file validation and error handling in dump_parser.py (file exists, valid format, corrupted file detection)
- [ ] T021 [US1] Implement dump content extraction in dump_parser.py (crash type, error code, faulting module, process info, OS version, architecture)
- [ ] T022 [US1] Implement stack trace extraction in dump_parser.py (top 20 frames, format as strings)
- [ ] T023 [US1] Implement loaded modules extraction in dump_parser.py (module list from dump)
- [ ] T024 [US1] Add progress feedback integration in dump_parser.py using utils/progress.py (file size-based progress bar)
- [ ] T025 [US1] Create src/reporters/console_reporter.py for Rich-formatted console output (display DumpFileAnalysis with tables and syntax highlighting)
- [ ] T026 [US1] Implement dump information display formatter in console_reporter.py (crash summary, stack trace, system info sections)
- [ ] T027 [US1] Add CLI stub in src/cli.py using Click framework (analyze command skeleton, --dmp option, basic argument validation)

**Checkpoint**: At this point, dump file parsing should work end-to-end: load .dmp → parse → display formatted output

---

## Phase 4: User Story 2 - Extract and Display Event Log Contents (Priority: P1) 🎯 MVP CORE

**Goal**: Parse .evtx files and display events chronologically with filtering by severity, source, and time range

**Independent Test**: Load a .evtx file and verify events are extracted with timestamps, event IDs, sources, and messages in filterable format

### Implementation for User Story 2

- [ ] T028 [P] [US2] Create src/models/event_log.py with EventLogEntry dataclass per data-model.md (all fields, is_error_or_critical(), within_time_range() methods)
- [ ] T029 [P] [US2] Create src/models/analysis_session.py with AnalysisSession dataclass per data-model.md (session management, create_new() classmethod, helper methods)
- [ ] T030 [US2] Create src/parsers/evtx_parser.py with EvtxParser class (parse() method using python-evtx library with streaming)
- [ ] T031 [US2] Implement evtx file validation and error handling in evtx_parser.py (file exists, valid format, corrupted record handling)
- [ ] T032 [US2] Implement event record parsing in evtx_parser.py (timestamp, event ID, source, level, message extraction from XML)
- [ ] T033 [US2] Implement streaming iterator in evtx_parser.py (yield events one at a time for memory efficiency)
- [ ] T034 [US2] Implement corrupted record recovery in evtx_parser.py (try-except per record, log warnings, continue parsing)
- [ ] T035 [US2] Add progress feedback for event parsing in evtx_parser.py (record count-based progress)
- [ ] T036 [US2] Implement event filtering by severity level in utils/filters.py (filter_by_level function using EventLevel enum)
- [ ] T037 [US2] Implement event filtering by time range in utils/filters.py (filter_by_time_range function)
- [ ] T038 [US2] Implement event filtering by source in utils/filters.py (filter_by_source function)
- [ ] T039 [US2] Implement chronological merging for multiple .evtx files in evtx_parser.py (merge_events function, sort by timestamp)
- [ ] T040 [US2] Add event log display formatter in console_reporter.py (table format with timestamp, level, source, event ID, message)
- [ ] T041 [US2] Implement event level color coding in console_reporter.py (Critical=red, Error=red, Warning=yellow, Info=blue using Rich)
- [ ] T042 [US2] Update CLI in src/cli.py to add --evtx option (support multiple files, integrate with analyze command)
- [ ] T043 [US2] Add filter CLI options in src/cli.py (--filter-level, --time-window options per contracts/cli-interface.md)

**Checkpoint**: At this point, event log parsing should work end-to-end: load .evtx → parse → filter → display formatted output. Both US1 and US2 can work independently (dump-only or events-only mode).

---

## Phase 5: User Story 3 - Generate LLM-Powered Analysis Report (Priority: P2)

**Goal**: Send extracted crash and event data to OpenAI API and generate analysis report with root cause, timeline, and remediation steps

**Independent Test**: Load dump and event files, verify LLM generates report with root cause analysis and remediation steps

### Implementation for User Story 3

- [ ] T044 [P] [US3] Create src/models/analysis_report.py with AnalysisReport dataclass per data-model.md (all fields, __post_init__, to_markdown() stub)
- [ ] T045 [US3] Create src/analyzers/correlator.py for timestamp correlation between dumps and events
- [ ] T046 [US3] Implement crash timestamp extraction in correlator.py (get crash time from DumpFileAnalysis)
- [ ] T047 [US3] Implement relevant event filtering in correlator.py (events within ±time_window of crash, default 1 hour)
- [ ] T048 [US3] Implement event timeline generation in correlator.py (chronological list of relevant events with formatting)
- [ ] T049 [US3] Create src/analyzers/llm_analyzer.py with LLMAnalyzer class (OpenAI client initialization from config)
- [ ] T050 [US3] Implement data summarization in llm_analyzer.py (extract key info from dump/events for prompt, stay under token limit)
- [ ] T051 [US3] Implement prompt engineering in llm_analyzer.py (system prompt: Windows diagnostic expert, user prompt: structured crash summary + events)
- [ ] T052 [US3] Implement OpenAI API call in llm_analyzer.py (chat.completions.create with gpt-4, temperature=0.3, max_tokens=2000)
- [ ] T053 [US3] Add OpenAI API error handling in llm_analyzer.py (auth errors, rate limits, network errors, timeouts with exponential backoff)
- [ ] T054 [US3] Implement response parsing in llm_analyzer.py (extract root cause, detailed analysis, remediation steps from LLM output)
- [ ] T055 [US3] Create AnalysisReport from LLM response in llm_analyzer.py (populate all fields, track token usage and processing time)
- [ ] T056 [US3] Add progress spinner for LLM analysis in llm_analyzer.py using utils/progress.py (indeterminate spinner: "Analyzing crash with AI...")
- [ ] T057 [US3] Update CLI in src/cli.py to add --analyze/--no-analyze flag (default: enabled)
- [ ] T058 [US3] Update CLI in src/cli.py to add --model option (gpt-4, gpt-3.5-turbo per contracts/cli-interface.md)
- [ ] T059 [US3] Implement API key validation in CLI (check OPENAI_API_KEY env var, show helpful error message if missing)
- [ ] T060 [US3] Add analysis report display in console_reporter.py (formatted sections: root cause, detailed analysis, timeline, remediation steps)

**Checkpoint**: At this point, full analysis workflow should work: load files → parse → correlate → analyze with LLM → display report. Tool provides intelligent insights, not just raw data.

---

## Phase 6: User Story 4 - Save and Export Analysis Results (Priority: P3)

**Goal**: Export analysis reports and extracted data to Markdown files for documentation and sharing

**Independent Test**: Generate analysis report and verify it can be saved as Markdown file with all sections intact

### Implementation for User Story 4

- [ ] T061 [P] [US4] Create src/reporters/markdown_reporter.py with MarkdownReporter class
- [ ] T062 [US4] Implement AnalysisReport.to_markdown() method in models/analysis_report.py (generate markdown with sections per contracts/cli-interface.md output format)
- [ ] T063 [US4] Implement dump info markdown formatting in markdown_reporter.py (crash information section with details)
- [ ] T064 [US4] Implement event log markdown formatting in markdown_reporter.py (timeline table with timestamp, level, source, event ID, message)
- [ ] T065 [US4] Implement LLM analysis markdown formatting in markdown_reporter.py (AI Analysis section with root cause, detailed analysis, recommendations)
- [ ] T066 [US4] Implement metadata section in markdown_reporter.py (session ID, timestamps, model used, confidence, processing time, tokens)
- [ ] T067 [US4] Add file writing functionality in markdown_reporter.py (save_to_file method, handle file permissions, overwrite protection)
- [ ] T068 [US4] Update CLI to implement --output option in src/cli.py (required PATH argument per contracts/cli-interface.md)
- [ ] T069 [US4] Integrate markdown export into analyze command workflow in src/cli.py (call markdown_reporter after analysis complete)
- [ ] T070 [US4] Add success message in CLI (display report location using Rich: "✓ Analysis complete! Report saved to: {path}")
- [ ] T071 [US4] Update AnalysisSession to track output_file_path in models/analysis_session.py (store path when report saved)

**Checkpoint**: At this point, complete workflow is functional: load → parse → analyze → export to Markdown file. All four user stories delivered.

---

## Phase 7: CLI Commands & Exit Codes

**Purpose**: Complete CLI implementation with all commands, options, and proper exit codes

- [ ] T072 Create main CLI group in src/cli.py (@click.group() for windows-error-analyzer command)
- [ ] T073 [P] Implement config command in src/cli.py (--set-api-key, --show-config, --reset options per contracts/cli-interface.md)
- [ ] T074 [P] Implement version command in src/cli.py (display tool version, Python version, dependency versions)
- [ ] T075 Implement proper exit codes in src/cli.py (0=success, 1=invalid args, 2=file not found, 3=parsing error, 4=API error, 5=network error, 10=internal error)
- [ ] T076 Add verbose logging mode in src/cli.py (--verbose flag enables DEBUG logging)
- [ ] T077 Add quiet mode in src/cli.py (--quiet flag suppresses progress output, only shows final result/errors)
- [ ] T078 [P] Create CLI error message formatter (user-friendly error messages with actionable guidance per contracts/cli-interface.md error messages section)
- [ ] T079 Implement argument validation in analyze command (at least one of --dmp or --evtx required, output path validation)

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T080 [P] Add comprehensive docstrings to all public functions and classes (Google-style docstrings per quickstart.md)
- [ ] T081 [P] Add type hints to all function signatures (Python 3.11+ syntax with | for unions)
- [ ] T082 [P] Create test fixtures in tests/fixtures/ (sample.dmp, sample.evtx files for testing - can use minimal valid files)
- [ ] T083 [P] Create pytest configuration in pyproject.toml (test paths, coverage settings, markers)
- [ ] T084 [P] Add unit tests for dump_parser in tests/unit/test_dump_parser.py (test parsing, error handling, edge cases)
- [ ] T085 [P] Add unit tests for evtx_parser in tests/unit/test_evtx_parser.py (test parsing, streaming, filtering, error handling)
- [ ] T086 [P] Add unit tests for llm_analyzer in tests/unit/test_llm_analyzer.py (mock OpenAI client, test prompt generation, error handling)
- [ ] T087 [P] Add unit tests for correlator in tests/unit/test_correlator.py (test timestamp filtering, timeline generation)
- [ ] T088 [P] Add unit tests for reporters in tests/unit/test_reporters.py (test markdown generation, console formatting)
- [ ] T089 [P] Add unit tests for filters in tests/unit/test_filters.py (test event filtering by level, time, source)
- [ ] T090 [P] Add integration test for full workflow in tests/integration/test_full_workflow.py (load fixtures → parse → analyze → export)
- [ ] T091 [P] Add CLI integration tests in tests/integration/test_cli.py (test commands, options, exit codes per contracts/cli-interface.md test scenarios)
- [ ] T092 Run code formatter (black src/ tests/)
- [ ] T093 Run linter (ruff check src/ tests/) and fix any issues
- [ ] T094 Run type checker (mypy src/) and fix any type errors
- [ ] T095 Run test suite (pytest --cov=src --cov-report=html) and verify 80%+ coverage
- [ ] T096 Validate README.md instructions (follow installation steps, run example commands)
- [ ] T097 Create CHANGELOG.md with initial v1.0.0 release notes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) - Dump file extraction MVP
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) - Event log extraction (can run parallel to US1 if desired)
- **User Story 3 (Phase 5)**: Depends on US1 and US2 completion (needs both parsers) - LLM analysis
- **User Story 4 (Phase 6)**: Depends on US3 completion (needs AnalysisReport) - Export functionality
- **CLI Commands (Phase 7)**: Depends on all user stories - Complete CLI polish
- **Polish (Phase 8)**: Depends on all previous phases - Final quality improvements

### User Story Dependencies

- **User Story 1 (P1)**: Independent - Can start after Foundational phase
- **User Story 2 (P1)**: Independent - Can start after Foundational phase (parallel to US1)
- **User Story 3 (P2)**: Depends on US1 + US2 (needs both parsers and data models)
- **User Story 4 (P3)**: Depends on US3 (needs AnalysisReport from LLM analysis)

### Critical Path

```
Setup (Phase 1)
    ↓
Foundational (Phase 2) ← BLOCKING
    ↓
    ├─→ US1: Dump Parsing (Phase 3)
    │       ↓
    └─→ US2: Event Parsing (Phase 4)
            ↓
        US3: LLM Analysis (Phase 5)
            ↓
        US4: Export (Phase 6)
            ↓
        CLI Commands (Phase 7)
            ↓
        Polish & Tests (Phase 8)
```

### Within Each User Story

1. Models before parsers
2. Parsers before analyzers
3. Analyzers before reporters
4. Reporters before CLI integration
5. Core functionality before CLI options

### Parallel Opportunities

**Phase 1 (Setup)**: Tasks T003-T010 can all run in parallel (different files)

**Phase 2 (Foundational)**: Tasks T012-T017 can run in parallel

**Phase 3 (US1)**: T018 parallel start

**Phase 4 (US2)**:
- T028, T029 can start in parallel (different model files)
- T036, T037, T038 can run in parallel (filter utilities)

**Phase 5 (US3)**: T044, T045 can start in parallel

**Phase 6 (US4)**: T061, T062 can start in parallel

**Phase 8 (Polish)**: Most test tasks (T080-T091) can run in parallel as they test different modules

---

## Parallel Example: Foundational Phase

```bash
# Launch all foundational tasks together:
Task: "Create all module __init__.py files"
Task: "Create src/utils/progress.py with Rich progress bar utilities"
Task: "Create src/utils/filters.py with event log filtering utilities"
```

---

## Parallel Example: User Story 1

```bash
# After foundational phase, start US1:
Task: "Create src/models/dump_analysis.py with DumpFileAnalysis dataclass"
# Then proceed sequentially through parser implementation
```

---

## Parallel Example: User Stories 1 & 2

```bash
# These two user stories can run fully in parallel if team capacity allows:
# Developer A works on Phase 3 (US1 - Dump parsing)
# Developer B works on Phase 4 (US2 - Event parsing)
# Both complete independently, then merge for US3
```

---

## Implementation Strategy

### MVP First (Minimal Viable Product)

**Recommendation**: Complete User Story 1 + User Story 2 only for initial release

1. Complete Phase 1: Setup (T001-T010)
2. Complete Phase 2: Foundational (T011-T017) ← CRITICAL BLOCKER
3. Complete Phase 3: User Story 1 - Dump Parsing (T018-T027)
4. Complete Phase 4: User Story 2 - Event Parsing (T028-T043)
5. **STOP and VALIDATE**: Test dump+event parsing independently
6. **MVP READY**: Tool can extract and display crash/event data without LLM

**Value**: Users can immediately benefit from file parsing and formatted display, even without AI analysis

### Incremental Delivery

After MVP validation:

1. **MVP** (US1 + US2): Extract and display dump + event data → Deploy
2. **v1.1** (+ US3): Add LLM-powered analysis → Deploy
3. **v1.2** (+ US4): Add Markdown export → Deploy
4. **v1.3** (+ Phase 7-8): Polish CLI, add tests, optimize → Deploy

Each increment adds value without breaking previous functionality.

### Parallel Team Strategy

With 2 developers:

1. Both complete Setup + Foundational together (Phase 1-2)
2. **Split after Foundational**:
   - Developer A: User Story 1 (Dump parsing)
   - Developer B: User Story 2 (Event parsing)
3. **Merge and continue**:
   - Developer A: User Story 3 (LLM analysis)
   - Developer B: User Story 4 (Export) + CLI polish
4. Both: Testing and polish (Phase 8)

---

## Notes

- **[P] tasks**: Different files, no dependencies - can parallelize
- **[Story] label**: Maps task to specific user story for traceability
- **Independent testing**: Each user story should be independently testable
- **File paths**: All paths are exact and implementation-ready
- **Commit frequency**: Commit after each task or logical group of related tasks
- **Checkpoints**: Stop at checkpoints to validate story independently before proceeding
- **MVP scope**: US1 + US2 = Minimum viable product (extraction + display)
- **Full feature**: US1 + US2 + US3 + US4 = Complete tool with AI analysis and export

---

## Task Statistics

- **Total Tasks**: 97
- **Setup**: 10 tasks
- **Foundational**: 7 tasks (BLOCKING)
- **User Story 1**: 10 tasks (P1 - Dump parsing)
- **User Story 2**: 16 tasks (P1 - Event parsing)
- **User Story 3**: 17 tasks (P2 - LLM analysis)
- **User Story 4**: 11 tasks (P3 - Export)
- **CLI Commands**: 8 tasks
- **Polish & Testing**: 18 tasks

**Parallelizable**: 41 tasks marked [P] (42% of total)

**MVP Scope** (US1 + US2): 43 tasks (Setup + Foundational + US1 + US2)
**Full Feature** (All US): 87 tasks (everything except final polish)
