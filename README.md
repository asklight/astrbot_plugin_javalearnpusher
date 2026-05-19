# AstrBot Xiaolincoding Learning Pusher

AstrBot plugin that crawls xiaolincoding content into a local private learning-card database and pushes cards through AstrBot conversations.

The existing `java-pusher/` folder is intentionally left untouched and ignored by this plugin repository.

## Commands

- `/xlin status` - show card count and schedule status
- `/xlin import` - crawl xiaolincoding and refresh local cards
- `/xlin next` - send the next due card
- `/xlin topic <keyword>` - send a card matching a topic
- `/xlin set <HH:MM>` - enable daily push for the current conversation
- `/xlin cancel` - disable daily push
- `/xlin rate <card_id> <again|hard|good>` - update review spacing

## Data Policy

Full crawled article content is stored under AstrBot plugin data, not in Git. The repository tracks code and small tests only.

## Development

```bash
python -m pytest
ruff format .
ruff check .
```

