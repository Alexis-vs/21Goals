import re
import time
import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

def extract_table_from_url(urls: list[str], table_id: str, image: bool = False) -> tuple[pd.DataFrame, str | None]:
    """
    Open web page with Selenium, extract HTML table with table id, and also can
    be collect url image player

    Parameters
    ----------
    urls : list[str]
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
    options.add_argument("--lang=fr-FR")
    options.add_argument('--window-size=1920,1080')
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-features=VizDisplayCompositor")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",{
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
    })
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    results = []
    results_images = []
    wait = WebDriverWait(driver, 15)
    
    for url in urls:
        try:
            driver.get(url)
            # time.sleep(20)
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        
            html = driver.page_source
            html = re.sub(r'<!--', '', html)
            html = re.sub(r'-->', '', html)
        
            soup = BeautifulSoup(html, "html.parser")
        
            table = soup.find("table", id=table_id)
            if table is None:
                raise ValueError(f"No table with '{table_id}' on {url}")
        
            df = pd.read_html(StringIO(str(table)))[0]
            results.append(df)
            
            if image=='yes':
                default_img_url = "https://assets-fr.imgfoot.com/mbappe-chute.jpg"

                # 1. CSS selector: .media-item img
                media_item = soup.select_one(".media-item img")
                if media_item and media_item.get("src"):
                    img_url = media_item["src"]

                # 2. alt contains "headshot"
                else:
                    img_tag = soup.find("img", alt=lambda x: x and "headshot" in x.lower())
                    if img_tag and img_tag.get("src"):
                        img_url = img_tag["src"]
                    else:
                        img_url = default_img_url

                # 3. normalize relative URL
                if img_url and img_url != default_img_url and img_url.startswith("/"):
                    img_url = urljoin(url, img_url)

            results_images.append(img_url)
            
        except Exception as e:
            print(f"Error on URL {url}: {e}")
            
    driver.quit()
    return results, results_images
