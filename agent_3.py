from typing import Dict, Optional
import json

#try openai first, fallback to google
_llm_client = None
_llm_type = None

def init_llm(config: Dict):
    global _llm_client, _llm_type
    
    #try openai
    if config.get('openai_api_key'):
        try:
            from openai import OpenAI
            _llm_client = OpenAI(api_key=config['openai_api_key'])
            _llm_type = 'openai'
            print("initialized openai llm")
            return
        except Exception as e:
            print(f"openai init failed: {e}")
    
    #fallback to google
    if config.get('google_api_key'):
        try:
            import google.generativeai as genai
            genai.configure(api_key=config['google_api_key'])
            _llm_client = genai.GenerativeModel('gemini-pro')
            _llm_type = 'google'
            print("initialized google gemini llm")
            return
        except Exception as e:
            print(f"google init failed: {e}")
    
    print("warning: no llm available for agent 3")

#generate card description using llm
def generate_card_description(card: Dict) -> Optional[str]:
    if not _llm_client:
        return None
    
    player = card.get('player_name', 'unknown')
    year = card.get('year', 'unknown')
    manufacturer = card.get('manufacturer', 'unknown')
    team = card.get('team', 'unknown')
    position = card.get('position', 'unknown')
    
    #include stats if available
    stats_text = ""
    if 'player_stats' in card:
        stats = card['player_stats']
        ba = stats.get('career_batting_avg', '')
        hr = stats.get('career_home_runs', '')
        if ba or hr:
            stats_text = f"Career stats: .{ba} BA, {hr} HR. "
    
    #include market value if available
    value_text = ""
    if 'market_value' in card:
        avg_price = card['market_value'].get('avg_sold_price', 0)
        if avg_price > 0:
            value_text = f"Recent sold average: ${avg_price}. "
    
    prompt = f"""Write a concise 2-3 sentence description for this baseball card:

Player: {player}
Year: {year}
Manufacturer: {manufacturer}
Team: {team}
Position: {position}
{stats_text}{value_text}

Make it informative and appealing for a card collector. Focus on the player's significance and card value."""
    
    try:
        if _llm_type == 'openai':
            response = _llm_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        
        elif _llm_type == 'google':
            response = _llm_client.generate_content(prompt)
            return response.text.strip()
    
    except Exception as e:
        print(f"  llm description error: {e}")
        return None

#estimate card condition/grade from ocr quality and completeness
def estimate_card_grade(card: Dict) -> Dict:
    raw_text = card.get('raw_text', '')
    
    #simple heuristic based on ocr completeness
    score = 0
    max_score = 10
    
    #check if key fields were extracted
    if card.get('player_name'):
        score += 2
    if card.get('team'):
        score += 1
    if card.get('position'):
        score += 1
    if card.get('year'):
        score += 1
    if card.get('manufacturer'):
        score += 1
    
    #check text length (more text = cleaner scan)
    if len(raw_text) > 200:
        score += 2
    elif len(raw_text) > 100:
        score += 1
    
    #check for physical stats (indicates good condition)
    if card.get('height') and card.get('weight_lbs'):
        score += 1
    if card.get('bats') and card.get('throws'):
        score += 1
    
    #convert to grade scale
    if score >= 9:
        grade = "mint"
        grade_num = 9
    elif score >= 7:
        grade = "near mint"
        grade_num = 7
    elif score >= 5:
        grade = "excellent"
        grade_num = 6
    elif score >= 3:
        grade = "good"
        grade_num = 4
    else:
        grade = "poor"
        grade_num = 2
    
    return {
        'estimated_grade': grade,
        'grade_numeric': grade_num,
        'completeness_score': score,
        'max_score': max_score,
        'note': 'estimate based on ocr quality, not physical inspection'
    }

#main agent 3 pipeline
def grade_and_describe_card(card: Dict) -> Dict:
    player_name = card.get('player_name', 'unknown')
    
    print(f"  grading: {player_name}")
    
    #estimate grade
    grade_info = estimate_card_grade(card)
    card['condition_estimate'] = grade_info
    print(f"    grade: {grade_info['estimated_grade']} ({grade_info['grade_numeric']}/10)")
    
    #generate description with llm
    if _llm_client:
        description = generate_card_description(card)
        if description:
            card['ai_description'] = description
            print(f"    description: {description[:60]}...")
    
    return card

#batch process all cards
def grade_all_cards(cards_data: list, config: Dict) -> list:
    print(f"\nagent 3: grading and describing {len(cards_data)} cards")
    
    init_llm(config)
    
    graded_cards = []
    for card in cards_data:
        graded = grade_and_describe_card(card)
        graded_cards.append(graded)
    
    return graded_cards
