# AstrBot Xiaolincoding Pusher Design

## Goal

Build a new AstrBot-native learning pusher plugin in the plugin root without modifying the existing `java-pusher/` folder. The plugin will push learning cards through AstrBot conversations, crawl xiaolincoding content for local private use, and keep generated full-content data out of GitHub.

## Scope

- Create a standalone AstrBot plugin structure in this directory.
- Keep `java-pusher/` unchanged and ignored by the new plugin repository.
- Do not use WxPusher.
- Crawl xiaolincoding content into a local data file managed by the plugin.
- Commit plugin code, metadata, configuration schema, tests, documentation, and small sample data only.
- Exclude generated full-content crawl data and runtime state from version control.

## Architecture

The plugin is split into small modules:

- `main.py`: AstrBot entrypoint, commands, lifecycle, scheduling task.
- `crawler.py`: xiaolincoding discovery, article fetch, article-to-card conversion.
- `store.py`: JSON-backed local card storage and review state.
- `scheduler.py`: time matching, daily due-card selection, message formatting.
- `models.py`: typed data structures for cards and schedule state.

Runtime files are stored under the plugin data directory when available, falling back to a local `data/` folder for tests and standalone use. The crawler writes a private full-card database locally; Git tracks only code and a small fixture.

## Commands

- `/xlin status`: show card count, configured push target, push time, and today's due count.
- `/xlin next`: push the next due card immediately to the current conversation.
- `/xlin set <HH:MM>`: enable daily push for the current conversation.
- `/xlin cancel`: disable daily push.
- `/xlin import`: crawl xiaolincoding and refresh the local card database.
- `/xlin topic <keyword>`: send a card matching a category, title, section, tag, or question keyword.

## Crawl Strategy

The crawler starts from `https://www.xiaolincoding.com/`, discovers same-site article links, filters non-content links, fetches markdown through `r.jina.ai`, and converts headings into learning cards. It stores source attribution on every card using `source_url`, `title`, `section`, and `category`.

The crawler is polite and deterministic:

- Same-domain URLs only.
- Configurable maximum page count.
- Deduplicate by canonical URL and card identity.
- Skip empty, navigation-only, or advertisement-heavy content.
- Preserve image URLs as references rather than downloading all images by default.

## Data Format

Each card has:

- `id`: stable slug based on category, URL, and section.
- `source_url`: original xiaolincoding URL.
- `category`: inferred topic group.
- `title`: page title.
- `section`: section heading.
- `prompt`: question-like heading or generated review prompt.
- `content`: concise card body extracted from the article section.
- `images`: remote image URLs.
- `tags`: normalized topic tags.
- `status`, `next_review`, `review_count`, `interval_days`: review scheduling state.

## Scheduling

Daily scheduling is handled inside the plugin with an async background task. It checks once per minute, sends only once per local date, and writes schedule state after successful push. Manual `/xlin next` uses the same selection logic.

Selection order:

1. Cards whose `next_review` is empty or due today.
2. Matching topic cards for `/xlin topic`.
3. Stable fallback to the first available card when no due cards exist.

## GitHub And Version Control

This directory becomes an independent Git repository. The repository commits plugin source and tests frequently. It ignores:

- `java-pusher/`
- generated full crawl data
- runtime schedule/review state
- caches and virtual environments

Creating the remote GitHub repository is a separate final step because it needs GitHub credentials, network access, and a visibility choice. Default remote name should be `astrbot_plugin_javalearnpusher`.

## Testing

Tests cover:

- crawler parsing and filtering using local markdown fixtures
- card storage load/save and due-card selection
- schedule time validation and once-per-day behavior
- message formatting for AstrBot push output

Verification commands:

- `ruff format .`
- `ruff check .`
- `python -m pytest`

