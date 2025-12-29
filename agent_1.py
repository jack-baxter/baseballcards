from PIL import Image, ImageOps
import cv2
import numpy as np
import pytesseract
import re
import json
from typing import List, Dict

#load and split 3x3 card grid from scan
def load_and_split_scan(image_path: str, grid_size: int = 3) -> List[np.ndarray]:
    img_cv = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    
    height, width, _ = img_rgb.shape
    card_width = width // grid_size
    card_height = height // grid_size
    
    cropped_cards = []
    for row in range(grid_size):
        for col in range(grid_size):
            x1 = col * card_width
            x2 = (col + 1) * card_width
            y1 = row * card_height
            y2 = (row + 1) * card_height
            
            card = img_rgb[y1:y2, x1:x2]
            cropped_cards.append(card)
    
    print(f"split {len(cropped_cards)} cards from scan")
    return cropped_cards

#enhance card image for better ocr
def enhance_card(card_pil: Image, threshold: int = 140) -> Image:
    grayscale = ImageOps.grayscale(card_pil)
    inverted = ImageOps.invert(grayscale)
    enhanced = inverted.point(lambda x: 0 if x < threshold else 255)
    return enhanced

#run ocr on single card
def extract_text_from_card(card_rgb: np.ndarray, enhance_threshold: int = 140) -> str:
    card_pil = Image.fromarray(card_rgb)
    card_enhanced = enhance_card(card_pil, enhance_threshold)
    text = pytesseract.image_to_string(card_enhanced)
    return text

#parse metadata from raw ocr text
def parse_card_metadata(raw_text: str, card_position: int, sheet_metadata: Dict) -> Dict:
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    
    card = sheet_metadata.copy()
    card['card_position'] = f'card {card_position + 1}'
    card['raw_text'] = raw_text
    
    #player name (first line)
    if lines:
        full_name_line = lines[0].replace('-', ' ').strip()
        full_name = full_name_line.strip().title()
        card['player_name'] = full_name
        
        #split first and last name
        name_parts = full_name.split()
        if len(name_parts) >= 2:
            card['first_name'] = name_parts[0]
            card['last_name'] = ' '.join(name_parts[1:])
        elif len(name_parts) == 1:
            card['first_name'] = name_parts[0]
            card['last_name'] = ''
        else:
            card['first_name'] = ''
            card['last_name'] = ''
    
    #team and position (second line)
    if len(lines) >= 2:
        team_pos_line = lines[1]
        if '"' in team_pos_line:
            parts = team_pos_line.split('"')
            if len(parts) >= 3:
                card['team'] = parts[0].strip().title()
                card['position'] = parts[2].strip().title()
    
    #extract various stats from remaining lines
    for line in lines:
        if re.search(r'ht:|height:', line, re.I):
            ht_match = re.search(r'(\d\'\d+\")', line)
            if ht_match:
                card['height'] = ht_match.group(1)
        
        if re.search(r'wt:|weight:', line, re.I):
            wt_match = re.search(r'Wt:\s*(\d+)', line, re.I)
            if wt_match:
                card['weight_lbs'] = int(wt_match.group(1))
        
        if re.search(r'Bats:', line, re.I):
            bats_match = re.search(r'Bats:\s*(Left|Right|Both|Switch)', line, re.I)
            if bats_match:
                card['bats'] = bats_match.group(1).title()
        
        if re.search(r'Throws:', line, re.I):
            throws_match = re.search(r'Throws:\s*(Left|Right)', line, re.I)
            if throws_match:
                card['throws'] = throws_match.group(1).title()
        
        if re.search(r'Born:', line, re.I):
            born_match = re.search(r'Born:\s*([\d-]+\s*,\d{4})', line, re.I)
            if born_match:
                card['birth_date_raw'] = born_match.group(1)
        
        if re.search(r'Home:', line, re.I):
            home_match = re.search(r'Home:\s*(.+)', line, re.I)
            if home_match:
                card['hometown'] = home_match.group(1).strip().title()
    
    #year and manufacturer from copyright
    copyright_match = re.search(r'©\s*(\d{4})\s*THE TOPPS', raw_text, re.IGNORECASE)
    if copyright_match:
        card['year'] = copyright_match.group(1)
        card['manufacturer'] = 'Topps'
    
    #card code
    code_match = re.search(r'CODE[#:]?\s*([A-Z0-9-]+)', raw_text, re.IGNORECASE)
    if code_match:
        card['card_code'] = code_match.group(1).strip()
    
    return card

#main agent 1 pipeline
def process_card_scan(image_path: str, sheet_metadata: Dict, config: Dict) -> List[Dict]:
    print(f"\nagent 1: processing scan {image_path}")
    
    #split grid
    cropped_cards = load_and_split_scan(image_path, config['card_grid_size'])
    
    #extract text and parse metadata
    cards_data = []
    for i, card_rgb in enumerate(cropped_cards):
        raw_text = extract_text_from_card(card_rgb, config['image_enhance_threshold'])
        card_metadata = parse_card_metadata(raw_text, i, sheet_metadata)
        cards_data.append(card_metadata)
        print(f"  card {i+1}: {card_metadata.get('player_name', 'unknown')}")
    
    return cards_data

#save extracted data to json
def save_cards_data(cards_data: List[Dict], output_path: str):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cards_data, f, indent=4, ensure_ascii=False)
    print(f"saved {len(cards_data)} cards to {output_path}")
