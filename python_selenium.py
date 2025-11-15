import re
import time
import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def extract_table_from_url(url: str, table_id: str, image: bool = False) -> tuple[pd.DataFrame, str | None]:
    """
    Open web page with Selenium, extract HTML table with table id, and also can
    be collect url image player

    Parameters
    ----------
    url : str
        Fbref URL.
    table_id : str
        Table id.
    image : bool, optionnel
        True to collect URL image player.

    Return
    --------
    tuple[pd.DataFrame, str | None]
        Table in DataFrame format and URL image (or None if image=False)
    """
    
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        driver.get(url)
        time.sleep(1)
        
        html = driver.page_source
        html = re.sub(r'<!--', '', html)
        html = re.sub(r'-->', '', html)
        
        soup = BeautifulSoup(html, "html.parser")
        
        table = soup.find("table", id=table_id)
        if table is None:
            raise ValueError(f"No table with '{table_id}' on {url}")
        
        df = pd.read_html(StringIO(str(table)))[0]
        
        img_url = None
        if image:
            # default img
            default_img_url = "https://assets-fr.imgfoot.com/mbappe-chute.jpg"
            
            media_item = soup.select_one(".media-item img")
            
            if media_item and media_item.get('src'):
                img_url = media_item['src']
            else:
                img = soup.find("img", alt=lambda x: x and "headshot" in x.lower())
                
                if img and img.get('src'):
                    img_url = img['src']
                else:
                    img_url = default_img_url
            
            if img_url and img_url != default_img_url and img_url.startswith('/'):
                from urllib.parse import urljoin
                img_url = urljoin(url, img_url)
        
        return df, img_url
        
    finally:
        driver.quit()
