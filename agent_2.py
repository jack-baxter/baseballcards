import requests
from bs4 import BeautifulSoup
import time
import re
from typing import Dict, Optional

#search ebay sold listings for card value
#uses ebay advanced search to find completed sales
def search_ebay_price(player_name: str, year: str, manufacturer: str, config: Dict) -> Optional[Dict]:
    try:
        #build search query
        query = f"{year} {manufacturer} {player_name} baseball card"
        query_encoded = query.replace(' ', '+')
        
        #ebay sold listings url
        url = f"https://www.ebay.com/sch/i.html?_nkw={query_encoded}&LH_Complete=1&LH_Sold=1"
        
        headers = {'User-Agent': config['user_agent']}
        
        time.sleep(config['scrape_delay'])
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"  ebay request failed: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        #find sold price listings
        prices = []
        items = soup.find_all('div', class_='s-item__info')
        
        for item in items[:10]:  #look at top 10 results
            price_elem = item.find('span', class_='s-item__price')
            if price_elem:
                price_text = price_elem.text.strip()
                #extract numeric value
                price_match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                if price_match:
                    price_val = float(price_match.group(1).replace(',', ''))
                    prices.append(price_val)
        
        if not prices:
            return None
        
        #calculate stats
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        return {
            'avg_sold_price': round(avg_price, 2),
            'min_sold_price': round(min_price, 2),
            'max_sold_price': round(max_price, 2),
            'num_sales_found': len(prices),
            'source': 'ebay_sold_listings'
        }
    
    except Exception as e:
        print(f"  ebay scrape error: {e}")
        return None

#search baseball reference for player stats
def search_baseball_reference(player_name: str) -> Optional[Dict]:
    try:
        #search url
        query = player_name.replace(' ', '+')
        search_url = f"https://www.baseball-reference.com/search/search.fcgi?search={query}"
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        #try to find player link in search results
        search_item = soup.find('div', class_='search-item')
        if not search_item:
            return None
        
        link = search_item.find('a')
        if not link or 'href' not in link.attrs:
            return None
        
        player_url = f"https://www.baseball-reference.com{link['href']}"
        
        #get player page
        time.sleep(2)
        player_response = requests.get(player_url, headers=headers, timeout=10)
        player_soup = BeautifulSoup(player_response.content, 'html.parser')
        
        #extract basic stats
        stats = {
            'bbref_url': player_url,
            'source': 'baseball_reference'
        }
        
        #try to get career stats
        stats_table = player_soup.find('tfoot')
        if stats_table:
            #batting average
            avg_elem = stats_table.find('td', {'data-stat': 'batting_avg'})
            if avg_elem:
                stats['career_batting_avg'] = avg_elem.text.strip()
            
            #home runs
            hr_elem = stats_table.find('td', {'data-stat': 'HR'})
            if hr_elem:
                stats['career_home_runs'] = hr_elem.text.strip()
            
            #rbi
            rbi_elem = stats_table.find('td', {'data-stat': 'RBI'})
            if rbi_elem:
                stats['career_rbi'] = rbi_elem.text.strip()
        
        return stats
    
    except Exception as e:
        print(f"  baseball reference error: {e}")
        return None

#main agent 2 pipeline
def enrich_card_data(card: Dict, config: Dict) -> Dict:
    player_name = card.get('player_name', '')
    year = card.get('year', '')
    manufacturer = card.get('manufacturer', '')
    
    if not player_name:
        print(f"  skipping enrichment for card with no player name")
        return card
    
    print(f"  enriching: {player_name} ({year} {manufacturer})")
    
    #search ebay for pricing
    price_data = search_ebay_price(player_name, year, manufacturer, config)
    if price_data:
        card['market_value'] = price_data
        print(f"    avg price: ${price_data['avg_sold_price']}")
    else:
        print(f"    no price data found")
    
    #search baseball reference for stats
    stats_data = search_baseball_reference(player_name)
    if stats_data:
        card['player_stats'] = stats_data
        ba = stats_data.get('career_batting_avg', 'n/a')
        print(f"    career avg: {ba}")
    else:
        print(f"    no stats found")
    
    return card

#batch enrich all cards
def enrich_all_cards(cards_data: list, config: Dict) -> list:
    print(f"\nagent 2: enriching {len(cards_data)} cards")
    
    enriched_cards = []
    for i, card in enumerate(cards_data):
        enriched = enrich_card_data(card, config)
        enriched_cards.append(enriched)
    
    return enriched_cards
