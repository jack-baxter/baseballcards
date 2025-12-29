#!/usr/bin/env python3

from orchestra import process_full_pipeline, process_batch
from datetime import datetime

def main():
    #example single scan processing
    image_path = "cardscans/baseball2.png"
    
    sheet_metadata = {
        "sheet_id": "sheet_001",
        "scan_date": datetime.now().strftime("%Y-%m-%d"),
        "scan_side": "back",
        "scanner_notes": "clean 2012 topps backs, excellent ocr",
        "collection_name": "my collection",
        "binder_page": "binder 1 - page 1"
    }
    
    #run full pipeline
    result = process_full_pipeline(
        image_path=image_path,
        sheet_metadata=sheet_metadata,
        enable_enrichment=True,  #set to false to skip web scraping
        enable_grading=True      #set to false to skip llm grading
    )
    
    if result:
        print(f"\nprocessed {result['summary']['total_cards']} cards")
        print(f"cards with prices: {result['summary']['cards_with_prices']}")
        print(f"cards with stats: {result['summary']['cards_with_stats']}")
        print(f"cards with grades: {result['summary']['cards_with_grades']}")

#example batch processing
def batch_example():
    scan_configs = [
        {
            'image_path': 'cardscans/scan1.png',
            'sheet_metadata': {'sheet_id': 'sheet_001', 'binder_page': 'page 1'}
        },
        {
            'image_path': 'cardscans/scan2.png',
            'sheet_metadata': {'sheet_id': 'sheet_002', 'binder_page': 'page 2'}
        }
    ]
    
    results = process_batch(scan_configs, enable_enrichment=True, enable_grading=True)
    print(f"\nbatch complete: processed {len(results)} scans")

if __name__ == "__main__":
    main()
