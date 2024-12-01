import time
import json
import os
import logging
from pathlib import Path
from tqdm import tqdm
from retrying import retry
from DrissionPage import ChromiumPage, ChromiumOptions

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 配置
CONFIG_FILE = 'config.json'
DEFAULT_CONFIG = {
    'download_path': 'downloads',
    'timeout': 10,
    'retry_times': 3,
    'selectors': {
        'username': '#user_id',
        'password': '#password',
        'login_button': '#entry-login',
        'lectures_button': '#folder-title-_4390020_1',
        'week_buttons': "xpath://button[contains(@id, 'folder-title-') and starts-with(normalize-space(.), 'Week')]",
        'lecture_links': "xpath://a[contains(text(), 'lecture') and contains(@href, 'blackboard.com')]",
        'download_button': 'xpath://button[@aria-label="Download" and @title="Download"]',
        'download_options': "css=div.ms-Button-flexContainer svg.MuiSvgIconroot-0-2-27",
        'original_file': "xpath://span[text()='Download original file']"
    }
}

def load_config():
    """加载配置文件，如果不存在则创建默认配置"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # 合并默认配置和用户配置
            return {**DEFAULT_CONFIG, **config}
    return DEFAULT_CONFIG

def save_config(config):
    """保存配置到文件"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def get_credentials():
    """获取用户凭证"""
    config = load_config()
    if 'username' in config and 'password' in config:
        return config['username'], config['password']
    else:
        username = input("请输入您的用户名: ")
        password = input("请输入您的密码: ")
        config['username'] = username
        config['password'] = password
        save_config(config)
        return username, password

def create_week_folder(week_num):
    """创建并返回周文件夹路径"""
    config = load_config()
    base_path = Path(config['download_path'])
    folder_path = base_path / f"Week_{week_num}"
    folder_path.mkdir(parents=True, exist_ok=True)
    return str(folder_path)

def scroll_to_bottom(page):
    """滚动到页面底部"""
    last_height = page.run_js("return document.documentElement.scrollHeight")
    while True:
        page.run_js("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(1)  # 减少等待时间
        new_height = page.run_js("return document.documentElement.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

@retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000)
def wait_and_click(page, selector, timeout=10, download=False):
    """等待并点击元素，支持重试"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            page.wait.eles_loaded(selector)
            button = page.ele(selector, timeout=0.5)
            if download:
                button.click.to_download()
            else:
                button.click()
            return True
        except Exception as e:
            logger.debug(f"等待点击失败: {e}")
            time.sleep(0.5)
    raise TimeoutError(f"按钮 '{selector}' 在 {timeout} 秒内未出现或无法点击")

def main():
    config = load_config()
    # 创建下载目录
    Path(config['download_path']).mkdir(parents=True, exist_ok=True)
    
    # 浏览器配置
    co = ChromiumOptions()
    co.auto_port()  # 自动设置端口
    co.timeout_base = config['timeout']  # 设置基本超时时间
    page = ChromiumPage(co)

    try:
        # 登录
        username, password = get_credentials()
        course_url = "https://abdn.blackboard.com/ultra/courses/_66721_1/outline"
        logger.info("正在访问课程页面...")
        
        page.get(course_url)
        page.wait.eles_loaded(config['selectors']['username'])
        page.ele(config['selectors']['username']).input(username)
        page.ele(config['selectors']['password']).input(password)
        page.ele(config['selectors']['login_button']).click()

        # 等待并点击 Lectures 按钮
        logger.info("正在加载课程内容...")
        if not wait_and_click(page, config['selectors']['lectures_button']):
            logger.error("无法点击 Lectures 按钮")
            return

        # 展开所有周内容
        logger.info("正在展开所有周内容...")
        week_buttons = page.eles(config['selectors']['week_buttons'])
        for button in week_buttons:
            try:
                week_num = ''.join(filter(str.isdigit, button.text))
                logger.info(f"展开第 {week_num} 周内容")
                button.click()
                time.sleep(1)
                scroll_to_bottom(page)
            except Exception as e:
                logger.error(f"展开第 {week_num} 周内容失败: {e}")

        # 获取所有讲座链接
        logger.info("收集讲座链接...")
        lecture_links = page.eles(config['selectors']['lecture_links'])
        lecture_urls = [link.attr('href') for link in lecture_links]
        logger.info(f"找到 {len(lecture_urls)} 个讲座链接")

        # 选择开始下载的讲座
        start_index = int(input(f"请输入要开始下载的讲座序号 (0-{len(lecture_urls)-1}): "))

        # 下载讲座
        for i, link_url in enumerate(tqdm(lecture_urls[start_index:], desc="下载进度")):
            week_num = i // 2 + 1  # 假设每周有2个讲座
            download_folder = create_week_folder(week_num)
            
            try:
                page.get(link_url)
                page.wait.ele_displayed('xpath://svg[contains(@class, "MuiSvgIcon")]', timeout=10)
                
                # 检查是否存在直接下载按钮
                direct_download_button = page.ele(config['selectors']['download_button'], timeout=5)
                
                if direct_download_button:
                    logger.info(f"直接下载: {link_url}")
                    direct_download_button.click.to_download()
                else:
                    # 展开下载选项并下载
                    wait_and_click(page, config['selectors']['download_options'])
                    wait_and_click(page, config['selectors']['original_file'], download=True)
                
                # 等待下载完成
                time.sleep(2)
                logger.info(f"成功下载讲座到 {download_folder}")
                
            except Exception as e:
                logger.error(f"下载失败 {link_url}: {e}")
                continue

    except Exception as e:
        logger.error(f"发生错误: {e}")

    finally:
        page.quit()

if __name__ == "__main__":
    main()