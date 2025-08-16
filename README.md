# KR/JP IT·부동산·경제 뉴스 메일러

- 대상: **한국/일본 주요 언론사**의 RSS
- 섹션: **IT/테크**, **부동산 개발**, **경제**
- 수집 창: **어제 08:00 ~ 오늘 07:59 (Asia/Seoul)**

## 실행
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
export $(grep -v '^#' .env | xargs)

python summarize_and_email.py
```

## 커스터마이징
- `config.yaml`
  - `feeds`: 언론사 RSS를 추가/교체
  - `include_sections`: 정규식 키워드로 섹션 필터(IT/부동산/경제)
  - `summarization.mode`: `none` 또는 `llm`

## 스케줄(크론)
```
0 7 * * * cd /path/to/project && /path/to/.venv/bin/python summarize_and_email.py >> cron.log 2>&1
```
