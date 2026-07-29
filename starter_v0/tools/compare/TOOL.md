---
name: compare
track: core
kind: process
requires_env: []
inputs: [items, aspect]
outputs: [aspect, item_count, markdown]
side_effect: false
---
# compare

Compare two or more research items (articles, tweets, papers) side by side.
Use when the user asks to "compare", "so sánh", "contrast", or wants to see differences/similarities between items.
Requires at least 2 items. Aspect can be "overview", "differences", or "similarities".
