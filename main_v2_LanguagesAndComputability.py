import time
import json
import os
import logging
from pathlib import Path
from tqdm import tqdm
from retrying import retry
from DrissionPage import ChromiumPage, ChromiumOptions

# Configure logging
logging.basicConfig(
   level=logging.INFO,
   format='%(asctime)s - %(levelname)s - %(message)s',
   handlers=[
       logging.FileHandler('download.log', encoding='utf-8'),
       logging.StreamHandler()
   ]
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG_FILE = 'config.json'
DEFAULT_CONFIG = {
   'download_path': 'downloads',
   'timeout': 10,
   'retry_times': 3,
       'selectors': {
        'username': '#user_id',
        'password': '#password', 
        'login_button': '#entry-login',
        'lectures_button': "#folder-title-_4389218_1",
        'week_buttons': "button[id^='folder-title-'][aria-controls^='folder-contents-']",
        # 修改这个选择器
        'content_links': "div[id^='folder-contents-'] a[href*='/ultra/courses/']",
        'download_button': "button[data-ally-invoke='alternativeformats']",
        'original_file': "span:contains('Download original file')"
    }
}

def load_config():
   """Load configuration file"""
   if os.path.exists(CONFIG_FILE):
       with open(CONFIG_FILE, 'r') as f:
           config = json.load(f)
           return {**DEFAULT_CONFIG, **config}
   return DEFAULT_CONFIG

def save_config(config):
   """Save configuration to file"""
   with open(CONFIG_FILE, 'w') as f:
       json.dump(config, f, indent=4)

def get_credentials():
   """Get user credentials"""
   config = load_config()
   if 'username' in config and 'password' in config:
       return config['username'], config['password']
   else:
       username = input("Enter your username: ")
       password = input("Enter your password: ") 
       config['username'] = username
       config['password'] = password
       save_config(config)
       return username, password

def create_week_folder(week_text):
   """Create and return week folder path"""
   config = load_config()
   base_path = Path(config['download_path'])
   week_num = ''.join(filter(str.isdigit, week_text.split('-')[0]))
   folder_path = base_path / f"Week_{week_num}"
   folder_path.mkdir(parents=True, exist_ok=True)
   return str(folder_path)

def scroll_to_bottom(page):
   """Scroll to bottom of page"""
   last_height = page.run_js("return document.documentElement.scrollHeight")
   while True:
       page.run_js("window.scrollTo(0, document.documentElement.scrollHeight);")
       time.sleep(1)
       new_height = page.run_js("return document.documentElement.scrollHeight")
       if new_height == last_height:
           break
       last_height = new_height

@retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000)
def wait_and_click(page, selector, timeout=10, download=False):
   """Wait for and click element"""
   start_time = time.time()
   while time.time() - start_time < timeout:
       try:
           ele = page.ele(selector, timeout=0.5)
           if ele:
               if download:
                   ele.click.to_download()
               else:
                   ele.click()
               return True
       except Exception as e:
           logger.debug(f"Click wait failed: {e}")
           time.sleep(0.5)
   raise TimeoutError(f"Button '{selector}' not found or clickable within {timeout} seconds")

def get_week_content(page, week_button):
    """Get content links for each week"""
    try:
        week_text = week_button.text
        logger.info(f"\n{'='*50}\nProcessing {week_text}\n{'='*50}")
        
        # 1. 获取content_id
        content_id = week_button.attr('aria-controls')
        logger.debug(f"Content ID: {content_id}")
        
        # 2. 如果文件夹未展开，则展开它
        if week_button.attr('aria-expanded') == 'false':
            week_button.click()
            time.sleep(2)  # 给内容加载一点时间
        
        # 3. 直接使用有效的XPath选择器
        selector = f"xpath://div[@id='{content_id}']//a[contains(@class, 'MuiTypography')]"
        links = page.eles(selector, timeout=5)
        
        if links:
            valid_links = []
            for link in links:
                href = link.attr('href')
                text = link.text
                if href and text and '/ultra/courses/' in href:
                    valid_links.append((href, text, week_text))
                    logger.info(f"Link found - href: {href}, text: {text}")
            
            if valid_links:
                logger.info(f"Successfully found {len(valid_links)} valid links")
                return valid_links
        
        logger.warning(f"No valid links found in {week_text}")
        return []

    except Exception as e:
        logger.error(f"Failed to get week content: {e}")
        return []

def get_all_buttons_info(page):
    """获取页面上所有按钮的详细信息"""
    try:
        # 使用多种方式查找按钮
        selectors = [
            'button',  # 所有按钮
            '[role="button"]',  # 具有button角色的元素
            '.MuiButtonBase-root',  # Material UI按钮
            '[aria-label*="Download"]',  # 包含Download的label
            '[title*="Download"]'  # 包含Download的title
        ]
        
        for selector in selectors:
            elements = page.eles(selector)
            logger.debug(f"\nFound {len(elements)} elements with selector '{selector}':")
            for idx, element in enumerate(elements):
                logger.debug(f"\nElement {idx + 1}:")
                logger.debug(f"HTML: {element.html}")
                logger.debug(f"Text: {element.text if element.text else 'No text'}")
                logger.debug(f"Class: {element.attr('class')}")
                logger.debug(f"Role: {element.attr('role')}")
                logger.debug(f"Aria-label: {element.attr('aria-label')}")
                logger.debug(f"Title: {element.attr('title')}")
                
    except Exception as e:
        logger.error(f"Error in get_all_buttons_info: {e}")

def click_download_button(page):
    """Locate and click the download button"""
    try:
        # 首先获取页面上所有按钮的信息
        logger.debug("\n=== Scanning page for buttons ===")
        get_all_buttons_info(page)
        
        # 更新的选择器列表
        selectors = [
            # Material UI按钮
            "[class*='MuiButtonBase'][class*='root']",
            
            # 通过aria属性
            "[aria-label*='download' i]",  # i表示不区分大小写
            
            # 通过title属性
            "[title*='download' i]",
            
            # 具有下载图标的按钮
            "xpath://button[.//svg]",
            
            # 更宽松的SVG路径匹配
            "xpath://button[.//svg[.//path]]",
            
            # 任何可能是下载按钮的元素
            "[role='button']",
            
            # 尝试定位父容器
            "div[class*='makeStyles'] button"
        ]
        
        for selector in selectors:
            try:
                logger.debug(f"\nTrying to find download button with selector: {selector}")
                
                elements = page.eles(selector)
                logger.debug(f"Found {len(elements)} matching elements")
                
                for element in elements:
                    logger.debug(f"Element HTML: {element.html}")
                    logger.debug(f"Element text: {element.text}")
                    
                    # 尝试点击每个可能的按钮
                    element.click()
                    time.sleep(1)
                    
                    # 检查点击后是否出现下载选项
                    download_options = page.eles("span:contains('Download original file')")
                    if download_options:
                        logger.info("Found download option after click")
                        return True
                        
            except Exception as e:
                logger.debug(f"Failed with selector {selector}: {str(e)}")
                continue
                
        logger.warning("Could not find download button with any selector")
        return False
        
    except Exception as e:
        logger.error(f"Error in click_download_button: {e}")
        return False
def download_content(page, url, title, week_folder):
    """Download content from the page"""
    try:
        page.get(url)
        time.sleep(2)
        
        # 等待页面加载 - 等待更多选项SVG图标出现
        try:
            svg_icon = page.wait.ele_displayed(
                'xpath://svg[contains(@class, "MuiSvgIcon") and contains(@class, "ms-Button-icon")]',
                timeout=10
            )
            logger.debug("Page loaded, SVG icon found")
        except:
            logger.warning(f"Page load timeout for: {title}")
            return False

        # 首先尝试直接下载按钮
        try:
            direct_button = page.ele('button[title="Download"]', timeout=3)
            if direct_button:
                direct_button.click.to_download()
                logger.info(f"Successfully downloaded (direct): {title}")
                time.sleep(2)
                return True
        except Exception as e:
            logger.debug(f"Direct download button not found: {str(e)}")

        # 如果没有直接下载按钮，尝试通过更多选项下载
        try:
            # 点击更多选项按钮
            more_options = page.ele("css=div.ms-Button-flexContainer svg.MuiSvgIcon", timeout=3)
            if more_options:
                more_options.click()
                time.sleep(1)
                
                # 点击"Download original file"选项
                download_original = page.ele('xpath://span[text()="Download original file"]', timeout=3)
                if download_original:
                    download_original.click.to_download()
                    logger.info(f"Successfully downloaded (menu): {title}")
                    time.sleep(2)
                    return True
                else:
                    logger.warning("Download original file option not found")
        except Exception as e:
            logger.debug(f"Menu download failed: {str(e)}")

        logger.warning(f"Failed to download: {title}")
        return False
        
    except Exception as e:
        logger.error(f"Download failed {title}: {e}")
        return False
def debug_page_structure(page):
    """Debug helper to analyze page structure"""
    try:
        logger.debug("\n=== Page Structure Analysis ===")
        # 打印所有按钮
        buttons = page.eles('button')
        logger.debug(f"Found {len(buttons)} buttons:")
        for btn in buttons:
            logger.debug(f"Button HTML: {btn.html}")
            
        # 打印所有带有data-ally属性的元素
        ally_elements = page.eles('[data-ally-invoke]')
        logger.debug(f"\nFound {len(ally_elements)} ally elements:")
        for elem in ally_elements:
            logger.debug(f"Ally element HTML: {elem.html}")
            
    except Exception as e:
        logger.error(f"Debug failed: {e}")


def main():
   config = load_config()
   Path(config['download_path']).mkdir(parents=True, exist_ok=True)
   
   co = ChromiumOptions()
   co.auto_port()
   co.timeout_base = config['timeout']
   page = ChromiumPage(co)

   try:
       username, password = get_credentials()
       course_url = "https://abdn.blackboard.com/ultra/courses/_66721_1/outline"
       logger.info("Accessing course page...")
       
       page.get(course_url)
       page.wait.eles_loaded(config['selectors']['username'])
       page.ele(config['selectors']['username']).input(username)
       page.ele(config['selectors']['password']).input(password)
       page.ele(config['selectors']['login_button']).click()

       logger.info("Waiting for Lectures & Practical Sessions button...") 
       time.sleep(5)
       
       lectures_button = page.ele(config['selectors']['lectures_button'])
       
       if not lectures_button:
           logger.error("Lectures button not found by ID, trying alternative method...")
           lectures_button = page.ele("xpath://button[contains(text(), 'Lectures & Practical Sessions')]")
       
       if not lectures_button:
           logger.error("Cannot find Lectures button")
           return
           
       logger.info("Found Lectures button, clicking...")
       if lectures_button.attr('aria-expanded') == 'false':
           lectures_button.click()
           time.sleep(2)
           scroll_to_bottom(page)
       
       logger.info("Lectures section expanded")

       week_buttons = page.eles(config['selectors']['week_buttons'])
       logger.info(f"Found {len(week_buttons)} week folders")

       all_content = []
       for week_button in week_buttons:
           content = get_week_content(page, week_button)
           all_content.extend(content)
           scroll_to_bottom(page)
           time.sleep(1)

       logger.info(f"Found {len(all_content)} content items")
       print("\nFound content:")
       for i, (url, title, week) in enumerate(all_content):
           print(f"{i}: [{week}] {title}")

       if not all_content:
           logger.error("No content found")
           return

       start_index = int(input(f"\nEnter the starting index (0-{len(all_content)-1}): "))

       for url, title, week in tqdm(all_content[start_index:], desc="Download progress"):
           week_folder = create_week_folder(week)
           download_content(page, url, title, week_folder)
           

   except Exception as e:
       logger.error(f"Error occurred: {e}")

   finally:
       page.quit()

if __name__ == "__main__":
   main()