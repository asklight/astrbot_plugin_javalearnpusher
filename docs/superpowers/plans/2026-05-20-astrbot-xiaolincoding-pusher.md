# AstrBot Xiaolincoding Pusher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a new AstrBot-native plugin that crawls xiaolincoding content into a private local learning-card database and pushes cards through AstrBot conversations.

**Architecture:** Core logic lives in `xlin_pusher/` and stays testable without AstrBot. `main.py` adapts that core to AstrBot commands, lifecycle, and message sending. Generated crawl data and runtime state live under the plugin data directory and are ignored by Git.

**Tech Stack:** Python 3.11+, AstrBot plugin API, `requests`, JSON files, `pytest`, `ruff`.

---

### Task 1: Core Models And Formatting

**Files:**
- Create: `xlin_pusher/models.py`
- Create: `xlin_pusher/formatter.py`
- Test: `tests/test_formatter.py`

- [x] **Step 1: Write failing tests**

Test card serialization and push text formatting with source attribution and length trimming.

- [x] **Step 2: Implement minimal models and formatter**

Use dataclasses for `LearningCard` and `ScheduleState`. Keep formatting plain text for broad platform compatibility.

- [ ] **Step 3: Verify**

Run: `python -m pytest tests/test_formatter.py -v`

### Task 2: Store And Scheduling Logic

**Files:**
- Create: `xlin_pusher/store.py`
- Create: `xlin_pusher/scheduler.py`
- Test: `tests/test_store_scheduler.py`

- [x] **Step 1: Write failing tests**

Test JSON load/save, due-card selection, topic matching, time validation, and once-per-day gating.

- [x] **Step 2: Implement minimal storage and scheduler**

Store cards in `cards.json` and schedule state in `schedule.json`. Use `pathlib.Path` for all paths.

- [ ] **Step 3: Verify**

Run: `python -m pytest tests/test_store_scheduler.py -v`

### Task 3: Xiaolincoding Crawler

**Files:**
- Create: `xlin_pusher/crawler.py`
- Test: `tests/test_crawler.py`

- [x] **Step 1: Write failing tests**

Test same-site link discovery, markdown parsing into cards, image extraction, and deduplication.

- [x] **Step 2: Implement crawler**

Use `requests` and `r.jina.ai` markdown fetches. Keep full generated data local, not tracked.

- [ ] **Step 3: Verify**

Run: `python -m pytest tests/test_crawler.py -v`

### Task 4: AstrBot Plugin Adapter

**Files:**
- Create: `main.py`
- Create: `metadata.yaml`
- Create: `_conf_schema.json`
- Create: `requirements.txt`
- Create: `README.md`

- [x] **Step 1: Implement AstrBot entrypoint**

Register `/xlin` commands for status, next, set, cancel, import, topic, and rate.

- [x] **Step 2: Add metadata and configuration**

Expose max crawl pages, push time, daily count, and start URL.

- [ ] **Step 3: Verify imports**

Run: `python -m py_compile main.py xlin_pusher/*.py`

### Task 5: Final Verification And Commits

**Files:**
- Modify: `.gitignore`
- Use: all created files

- [ ] **Step 1: Run formatting and checks**

Run: `ruff format .`, `ruff check .`, and `python -m pytest`.

- [ ] **Step 2: Confirm ignored data**

Run: `git status --short --ignored`.

- [ ] **Step 3: Commit changes**

Commit in logical chunks using conventional commit messages.

