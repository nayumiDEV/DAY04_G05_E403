---
name: summarize
track: core
kind: process
requires_env: []
inputs: [text, max_points]
outputs: [key_points, keywords, input_length, point_count]
side_effect: false
---
# summarize

Extract key points and keywords from a long text.
Use when the user asks to "summarize", "tóm tắt", "extract key points", or needs a quick overview of a long article.
Do NOT use when the user already has a clear short answer or when the text is already short.
The tool returns top N scored sentences and extracted keywords.
