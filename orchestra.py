import json
import os
from datetime import datetime
from typing import Dict, List
from config import load_config, validate_config, print_config
from agent_1 import process_card_scan, save_cards_data
from agent_2 import enrich_all_cards
from agent_3 import grade_all_cards

#orchestrate full pipeline from scan to final output
def process_full_pipeline(image_path: str, 
                         sheet_metadata: Dict,
                         enable_enrichment: bool = True,
                         enable_grading: bool = True) -> Dict:
    
    print("="*60)
    print("baseball card processing pipeline")
    print("="*60)
    
    #load config
    config = load_config()
    print_config(config)
    validate_config(config, require_api_keys=enable_grading)
    
    #check if image exists
    if not os.path.exists(image_path):
        print(f"error: image not found at {image_path}")
        return None
    
    #agent 1: ocr extraction
    cards_data = process_card_scan(image_path, sheet_metadata, config)
    
    #save intermediate results
    sheet_id = sheet_metadata.get('sheet_id', 'sheet_001')
    agent1_output = f"{config['data_dir']}/{sheet_id}_agent1_ocr.json"
    save_cards_data(cards_data, agent1_output)
    
    #agent 2: web enrichment (optional)
    if enable_enrichment:
        cards_data = enrich_all_cards(cards_data, config)
        agent2_output = f"{config['data_dir']}/{sheet_id}_agent2_enriched.json"
        save_cards_data(cards_data, agent2_output)
    else:
        print("\nagent 2: skipped (enrichment disabled)")
    
    #agent 3: grading and descriptions (optional)
    if enable_grading:
        cards_data = grade_all_cards(cards_data, config)
        agent3_output = f"{config['data_dir']}/{sheet_id}_agent3_graded.json"
        save_cards_data(cards_data, agent3_output)
    else:
        print("\nagent 3: skipped (grading disabled)")
    
    #create final output
    final_output = {
        'pipeline_timestamp': datetime.now().isoformat(),
        'sheet_metadata': sheet_metadata,
        'processing_config': {
            'enrichment_enabled': enable_enrichment,
            'grading_enabled': enable_grading
        },
        'cards': cards_data,
        'summary': {
            'total_cards': len(cards_data),
            'cards_with_prices': sum(1 for c in cards_data if 'market_value' in c),
            'cards_with_stats': sum(1 for c in cards_data if 'player_stats' in c),
            'cards_with_grades': sum(1 for c in cards_data if 'condition_estimate' in c)
        }
    }
    
    #save final output
    final_path = f"{config['outputs_dir']}/{sheet_id}_final.json"
    with open(final_path, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=4, ensure_ascii=False)
    
    print("\n" + "="*60)
    print(f"pipeline complete")
    print(f"processed {len(cards_data)} cards")
    print(f"final output: {final_path}")
    print("="*60)
    
    return final_output

#batch process multiple scans
def process_batch(scan_configs: List[Dict],
                 enable_enrichment: bool = True,
                 enable_grading: bool = True) -> List[Dict]:
    
    results = []
    
    for i, scan_config in enumerate(scan_configs):
        print(f"\n\nprocessing scan {i+1}/{len(scan_configs)}")
        
        image_path = scan_config['image_path']
        sheet_metadata = scan_config.get('sheet_metadata', {
            'sheet_id': f'sheet_{i+1:03d}',
            'scan_date': datetime.now().strftime('%Y-%m-%d')
        })
        
        result = process_full_pipeline(
            image_path,
            sheet_metadata,
            enable_enrichment,
            enable_grading
        )
        
        if result:
            results.append(result)
    
    return results

#generate collection summary from all processed cards
def generate_collection_summary(output_files: List[str]) -> Dict:
    all_cards = []
    
    for file_path in output_files:
        with open(file_path, 'r') as f:
            data = json.load(f)
            all_cards.extend(data.get('cards', []))
    
    #calculate collection stats
    total_value = 0
    player_counts = {}
    team_counts = {}
    year_counts = {}
    
    for card in all_cards:
        #value
        if 'market_value' in card:
            total_value += card['market_value'].get('avg_sold_price', 0)
        
        #player frequency
        player = card.get('player_name', 'unknown')
        player_counts[player] = player_counts.get(player, 0) + 1
        
        #team frequency
        team = card.get('team', 'unknown')
        team_counts[team] = team_counts.get(team, 0) + 1
        
        #year frequency
        year = card.get('year', 'unknown')
        year_counts[year] = year_counts.get(year, 0) + 1
    
    summary = {
        'total_cards': len(all_cards),
        'total_estimated_value': round(total_value, 2),
        'average_card_value': round(total_value / len(all_cards), 2) if all_cards else 0,
        'top_players': sorted(player_counts.items(), key=lambda x: x[1], reverse=True)[:10],
        'teams': dict(sorted(team_counts.items(), key=lambda x: x[1], reverse=True)),
        'years': dict(sorted(year_counts.items()))
    }
    
    return summary
