# Day 04 Lab v2 Report — Research Agent

> **PHẦN A — Giới thiệu agent**: dùng để demo, xong trước 16:30.
>
> **PHẦN B — Chi tiết / Bằng chứng**: dựa trên log thật, hoàn thiện sau debate để nộp bài.

## Team

- Team: K4-Team
- Members: [Tên thành viên]
- Provider/model: openrouter / auto

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent đa năng: tìm tweet theo tài khoản (timeline), tìm tweet theo chủ đề (social_search), tra tin tức web (lookup), đọc nội dung URL (fetch), hỏi lại khi thiếu thông tin (clarify), xác nhận trước khi gửi (send), so sánh bài viết (compare), tóm tắt văn bản dài (summarize), tạo newsletter (newsletter), và tra thời tiết (weather).

**Link dùng thử:**

> URL: `http://localhost:8501` (chạy `streamlit run app.py`)
>
> Hoặc deploy với Cloudflare Tunnel: `cloudflared tunnel --url http://localhost:8501`

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu thông tin | không |
| timeline | Lấy tweet của một người dùng cụ thể | không |
| social_search | Tìm tweet theo chủ đề/từ khóa | không |
| lookup | Tra cứu tin tức web | không |
| fetch | Đọc nội dung URL | không |
| format | Trình bày items thành markdown digest | không |
| summarize | Trích xuất key points từ văn bản dài | **CÓ** |
| newsletter | Tạo bản tin markdown từ items | **CÓ** |
| compare | So sánh 2+ items cạnh nhau | **CÓ** |
| weather | Tra thời tiết thành phố bất kỳ | **CÓ** |
| send | Gửi text lên Telegram (cần xác nhận) | optional |
| policy | Tra company policy nội bộ | optional |
| papers | Tìm paper arXiv | optional |
| paper_text | Đọc nội dung PDF arXiv | optional |

## A3. Câu hỏi mẫu để thử

1. "Tweet mới nhất của Sam Altman là gì?"
2. "Tin tức AI hôm nay có gì nổi bật?"
3. "So sánh thời tiết Hà Nội và TP HCM giúp mình"
4. "Tóm tắt bài này: https://openai.com/blog/gpt-5"
5. "Làm bản tin AI trong tuần này"

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| Tweet của Sam Altman | timeline(screenname="sama") | v0 gọi sai tool; v1+v2 thêm mapping | runs/*.json |
| Thiếu URL → clarify | clarify → fetch | v0 đoán bừa; v1 thêm policy clarify | runs/*.json |
| Gửi Telegram cần xác nhận | clarify(yes_no) → send | v0 gửi luôn; v1 thêm confirm boundary | runs/*.json |
| So sánh 2 bài báo | lookup×2 → compare | v3 dùng tool mới compare | transcripts/*.json |
| Weather chuyển đơn vị | weather(°C) → weather(°F) | v2 thêm weather tool; v3 multi-turn carry | transcripts/*.json |

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version evidence

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---|---|---|
| v0 | baseline (starter) | — | case_accuracy | — | — | runs/*v0*.json |
| v1 | fix system_prompt.md: clarify, refuse, confirm, multi-turn | Prompt sai "đừng hỏi" gây fail R10,R11,R12 | case_accuracy | v0 | v1 | runs/*v1*.json |
| v2 | fix tools.yaml: descriptions, routing rules, add 4 new tools | Tool descriptions vague → sai routing | case_accuracy | v1 | v2 | runs/*v2*.json |
| v3 | polish both + team eval | Fine-tune remaining edge cases | case_accuracy | v2 | v3 | runs/*v3*.json |

## B2. Failure analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R10 | missing_info | timeline(sama) | v0 agent đoán handle thay vì clarify | v1: thêm clarify policy |
| R11 | missing_info | fetch(example.com) | v0 agent đoán URL thay vì clarify | v1: thêm clarify policy |
| R12 | wrong_boundary | send(text) | v0 agent gửi luôn không confirm | v1: thêm confirm boundary |
| R08 | out_of_scope | send() | v0 agent gọi tool thay vì refuse | v1: thêm out-of-scope rule |
| R13 | wrong_tool | 1 tool instead of 2 | v0 prompt "pick one tool" | v1: thêm parallel rule |

## B3. Team eval cases

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|---|
| G01 | Weather query for a city | weather(city="Hanoi") | ✅ PASS |
| G02 | Summarize long text | summarize(text=...) | ✅ PASS |
| G03 | Weather with non-default units | weather(city="London", units="fahrenheit") | ✅ PASS |
| G04 | Weather without specifying units (default celsius) | weather(city="Tokyo") | ✅ PASS |
| G05 | Summarize routing: user provides text and asks for summary | summarize(text=...) | ✅ PASS |
| G06 | Multi-turn: carry city context, override to Seoul, switch units to fahrenheit | weather(city="Seoul", units="fahrenheit") | ✅ PASS |
| G07 | Multi-turn: switch from social_search to weather on latest turn | weather(city="Da Nang") | ✅ PASS |
| G08 | Multi-turn: first turn out-of-scope (refuse), second turn corrects to legit request | lookup(query="AI", topic="news", timeframe="day") | ✅ PASS |
| G09 | Multi-turn: carry city context, switch to Hue, change units to fahrenheit | weather(city="Hue", units="fahrenheit") | ✅ PASS |
| G10 | Multi-turn: first turn asks multiple cities, second narrows to London, third adds fahrenheit | weather(city="London", units="fahrenheit") | ✅ PASS |

## B4. Live chat evidence

| Scenario/Turn | Version | Tool Calls + Args | Transcript File | Outcome |
|---|---|---|---|---|
| Research bình thường | v3 | → lookup("AI", news, day) → format | transcripts/v3_*.transcript.json | ✅ PASS (from run JSON) |
| Thiếu info rồi bổ sung | v3 | → clarify → fetch(url) | transcripts/v3_*.transcript.json | ✅ PASS (from run JSON) |
| Hành động nhạy cảm (xác nhận trước khi gửi) | v3 | → clarify(yes_no) → send(confirmed=true) | transcripts/v3_*.transcript.json | ✅ PASS (from run JSON) |

## B5. Tool capability evidence

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên | tools/summarize/ | Trích key points + keywords từ text | Chỉ dùng với text đủ dài |
| Must-have: tool mới thứ 2 | tools/newsletter/ | Compile items thành newsletter | Cần items đã collect sẵn |
| Must-have: tool mới thứ 3 | tools/compare/ | So sánh 2+ items | Cần ≥2 items |
| Bonus: tool mới thứ 4+ | tools/weather/ | Weather real-time free API | wttr.in reliability |
| Optional built-in | tools/send/ | Telegram send | Cần credentials; luôn confirm trước |
| Optional built-in | tools/policy/ | Company policy search | Chỉ search trong policy có sẵn |
| Optional built-in | tools/papers/ | arXiv search | Rate limit 1 req/3s |
| Optional built-in | tools/paper_text/ | arXiv PDF text extraction | pypdf dependency |

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?**
  Clarify policy, out-of-scope handling, meta-question handling, confirmation boundary, multi-turn rules, parallel call support, tool routing table. Những cái này là behavior instruction, không phải tool interface.

- **Which fixes belonged in `tools.yaml`?**
  Tool descriptions with when-to-use/when-not-to-use, name→handle mapping conventions, arg default conventions (timeframe mapping, limit, search_type). Đây là tool interface với model.

- **Which failure needed manual review instead of automatic grading?**
  Multi-turn cases M01-M06 cần review carryover logic vì eval chỉ chấm latest turn nhưng context từ các turn trước có thể bị mất. Tool execution errors (API key thiếu, network timeout) cần manual review để phân biệt với routing errors.

- **What would you improve next?**
  Thêm rate limiting cho Twitter API, thêm caching layer cho weather/lookup results, thêm unit tests cho tool functions, và mở rộng team eval cases để cover nhiều edge case hơn.
