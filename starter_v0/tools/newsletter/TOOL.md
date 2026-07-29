---
name: newsletter
track: core
kind: process
requires_env: []
inputs: [items, title, date]
outputs: [title, date, markdown, item_count]
side_effect: false
---
# newsletter

Compile collected research items into a structured newsletter markdown.
Use when the user asks for a "newsletter", "bản tin", "daily brief", or "weekly summary".
Do NOT use for simple formatting of a few items — use format() instead.
Groups items by section/source automatically.
