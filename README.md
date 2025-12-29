Baseball Card Cataloging System

multi-agent pipeline for scanning, extracting, enriching, and grading baseball card collections. uses ocr, web scraping, and llm agents to automatically catalog and value cards from sheet scans.

## what it does

takes 3x3 grid scans of baseball cards and:
1. **agent 1 (ocr)**: extracts player names, stats, teams, positions from card backs using pytesseract
2. **agent 2 (enrichment)**: scrapes ebay for sold prices and baseball-reference for career stats
3. **agent 3 (grading)**: estimates card condition and generates ai descriptions

outputs comprehensive json with market values, player stats, condition grades, and collector descriptions.

## project structure

```
baseball_cards/
├── cardscans/              # input: 3x3 card grid scans
├── data/                   # intermediate: agent outputs
├── outputs/                # final: complete cataloged data
├── logs/                   # processing logs
├── config.py              # configuration loader
├── utils.py               # helper functions
├── agent_1.py             # ocr extraction pipeline
├── agent_2.py             # web scraping for prices/stats
├── agent_3.py             # llm grading and descriptions
├── orchestra.py           # pipeline orchestration
├── main.py                # execution script
└── requirements.txt
```

## setup

1. install dependencies
```bash
pip install -r requirements.txt
```

2. install tesseract ocr
```bash
# ubuntu/debian
sudo apt-get install tesseract-ocr

# mac
brew install tesseract

# windows
# download from https://github.com/UB-Mannheim/tesseract/wiki
```

3. configure api keys (optional, for agent 3)
```bash
cp .env.example .env
# add your openai or google api key
```

4. add card scans to `cardscans/` directory

5. run pipeline
```bash
python main.py
```

## usage

**single scan:**
```python
from orchestra import process_full_pipeline

result = process_full_pipeline(
    image_path="cardscans/baseball2.png",
    sheet_metadata={
        "sheet_id": "sheet_001",
        "collection_name": "my collection",
        "binder_page": "page 1"
    },
    enable_enrichment=True,  # web scraping
    enable_grading=True      # llm descriptions
)
```

**batch processing:**
```python
from orchestra import process_batch

scan_configs = [
    {'image_path': 'cardscans/scan1.png', 'sheet_metadata': {'sheet_id': 'sheet_001'}},
    {'image_path': 'cardscans/scan2.png', 'sheet_metadata': {'sheet_id': 'sheet_002'}}
]

results = process_batch(scan_configs, enable_enrichment=True, enable_grading=True)
```

## pipeline stages

### agent 1: ocr extraction
- splits 3x3 grid into individual cards
- enhances images for better ocr (grayscale, invert, threshold)
- extracts text with pytesseract
- parses metadata:
  - player name (first/last)
  - team and position
  - physical stats (height, weight)
  - batting/throwing hand
  - birth date and hometown
  - year, manufacturer, card code

### agent 2: web enrichment
**ebay sold listings:**
- searches completed sales for matching cards
- calculates avg/min/max sold prices
- tracks number of recent sales

**baseball reference:**
- finds player career stats
- extracts batting average, home runs, rbi
- provides reference url

### agent 3: grading & descriptions
**condition estimation:**
- analyzes ocr quality and completeness
- assigns grade: mint, near mint, excellent, good, poor
- numeric score 0-10

**ai descriptions:**
- uses openai (gpt-3.5) or google (gemini)
- generates 2-3 sentence collector descriptions
- incorporates stats, team history, market value

## output format

final json includes:
```json
{
  "pipeline_timestamp": "2025-12-29T10:00:00",
  "sheet_metadata": {...},
  "cards": [
    {
      "card_position": "card 1",
      "player_name": "Derek Jeter",
      "first_name": "Derek",
      "last_name": "Jeter",
      "team": "Yankees",
      "position": "Shortstop",
      "year": "2012",
      "manufacturer": "Topps",
      "height": "6'3\"",
      "weight_lbs": 195,
      "bats": "Right",
      "throws": "Right",
      "market_value": {
        "avg_sold_price": 24.99,
        "min_sold_price": 15.00,
        "max_sold_price": 45.00,
        "num_sales_found": 8
      },
      "player_stats": {
        "career_batting_avg": ".310",
        "career_home_runs": "260",
        "career_rbi": "1311"
      },
      "condition_estimate": {
        "estimated_grade": "near mint",
        "grade_numeric": 7,
        "completeness_score": 8
      },
      "ai_description": "2012 Topps Derek Jeter card..."
    }
  ],
  "summary": {
    "total_cards": 9,
    "cards_with_prices": 7,
    "cards_with_stats": 6,
    "cards_with_grades": 9
  }
}
```

## notes and gotchas

- **ocr quality**: card backs work best. fronts have photos that confuse tesseract
- **scan alignment**: cards must be in perfect 3x3 grid. misalignment causes crop issues
- **text enhancement**: threshold=140 works for most topps cards. adjust for other manufacturers
- **rate limiting**: agent 2 has 2-second delays between requests. ebay/bbref may block aggressive scraping
- **api costs**: agent 3 uses llm apis. ~$0.001 per card with gpt-3.5-turbo
- **price accuracy**: ebay prices vary widely. use avg as rough estimate, not definitive value
- **player matching**: common names may match wrong players on baseball-reference
- **condition grading**: estimates based on ocr quality, not physical card inspection

## agent behaviors

**agent 1** (always runs):
- input: card scan image
- output: extracted metadata json
- no external dependencies

**agent 2** (optional):
- input: agent 1 output
- output: enriched with prices/stats
- requires internet connection
- can be slow (2s delay per card)

**agent 3** (optional):
- input: agent 2 output (or agent 1 if 2 skipped)
- output: graded with ai descriptions
- requires api key (openai or google)
- costs money per card (~$0.001)

## future improvements

things to add:
- front-side ocr for card numbers and special editions
- psa/bgs grade prediction from image analysis
- automatic upload to collection tracking sites
- barcode/qr code support for modern cards
- multi-page pdf scanning
- database integration (sqlite/postgres)
- web ui for upload and viewing
- mobile app for on-the-go scanning
- price trend analysis over time
- collection portfolio valuation

## troubleshooting

**ocr not finding text:**
- check tesseract installation: `tesseract --version`
- adjust `IMAGE_ENHANCE_THRESHOLD` in .env
- ensure card backs (not fronts) are scanned

**web scraping fails:**
- check internet connection
- increase `SCRAPE_DELAY` in .env
- ebay/bbref may be blocking requests (use vpn)

**llm not working:**
- verify api key in .env
- check quota/billing on openai/google
- fallback will use whichever key is available

**prices seem wrong:**
- ebay results vary based on condition, seller, etc
- use as rough estimate only
- manually verify high-value cards

## legal disclaimer

this tool is for personal collection management only. respect rate limits and terms of service for all scraped websites. card values are estimates and should be verified before buying/selling. ai-generated descriptions are not professional appraisals.

## license

personal use only - not for commercial card grading services
