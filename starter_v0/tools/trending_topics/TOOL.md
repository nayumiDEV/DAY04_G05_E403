---
name: trending_topics
track: core
kind: live_api
provider: Twitter API45 via RapidAPI
requires_env: [RAPIDAPI_KEY]
inputs: [woeid, country, limit]
outputs: [woeid, country, items]
side_effect: false
---
# trending_topics

Lấy danh sách chủ đề đang trending trên X/Twitter theo khu vực. Trả về tối đa `limit` topic với tên, volume tweet ước tính, và URL search tương ứng.

## Khi nào dùng / không dùng

Dùng khi user hỏi về "trending", "đang hot", "hôm nay có gì trending", "chủ đề nổi bật trên Twitter/X". KHÔNG dùng cho news thế giới (dùng `lookup` topic=news) hoặc tìm kiếm bài đăng theo từ khóa cụ thể (dùng `social_search`).

## Convention

- Mặc định `woeid=1` (Worldwide) nếu không nói khu vực.
- Nếu user nói "tại Việt Nam" → `woeid=23424984` (hoặc `country="Vietnam"`); "tại Mỹ" → `woeid=23424977`.
- `limit` mặc định 10, tối đa 50.

## Output

Mỗi item có: `name`, `query` (chuỗi search), `tweet_volume`, `url`.