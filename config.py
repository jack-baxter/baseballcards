import os
from dotenv import load_dotenv

#load config from env file
def load_config() -> dict:
    load_dotenv()
    
    config = {
        'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
        'google_api_key': os.getenv('GOOGLE_API_KEY', ''),
        'user_agent': os.getenv('USER_AGENT', 'Mozilla/5.0'),
        'scrape_delay': int(os.getenv('SCRAPE_DELAY', 2)),
        'tesseract_path': os.getenv('TESSERACT_PATH', '/usr/bin/tesseract'),
        'ocr_language': os.getenv('OCR_LANGUAGE', 'eng'),
        'card_grid_size': int(os.getenv('CARD_GRID_SIZE', 3)),
        'image_enhance_threshold': int(os.getenv('IMAGE_ENHANCE_THRESHOLD', 140)),
        'cardscans_dir': os.getenv('CARDSCANS_DIR', './cardscans'),
        'data_dir': os.getenv('DATA_DIR', './data'),
        'outputs_dir': os.getenv('OUTPUTS_DIR', './outputs'),
        'logs_dir': os.getenv('LOGS_DIR', './logs')
    }
    
    #set api keys in environment
    if config['openai_api_key']:
        os.environ['OPENAI_API_KEY'] = config['openai_api_key']
    if config['google_api_key']:
        os.environ['GOOGLE_API_KEY'] = config['google_api_key']
    
    return config

#validate required settings
def validate_config(config: dict, require_api_keys: bool = False) -> bool:
    required_dirs = ['cardscans_dir', 'data_dir', 'outputs_dir']
    
    for key in required_dirs:
        path = config.get(key)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            print(f"created directory: {path}")
    
    if require_api_keys:
        if not config.get('openai_api_key') and not config.get('google_api_key'):
            print("warning: no api keys configured for llm agents")
            return False
    
    return True

#print config for debugging
def print_config(config: dict):
    print("current configuration:")
    print("-" * 50)
    for key, value in config.items():
        if 'key' in key.lower():
            display = f"{value[:8]}..." if value else "(not set)"
        else:
            display = value
        print(f"{key}: {display}")
    print("-" * 50)
