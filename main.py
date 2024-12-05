import time
from DrissionPage import ChromiumPage
import json
import os
CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None

def save_config(username, password):
    config = {'username': username, 'password': password}
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def get_credentials():
    config = load_config()
    if config:
        return config['username'], config['password']
    else:
        username = input("请输入您的用户名: ")
        password = input("请输入您的密码: ")
        save_config(username, password)
        return username, password

def scroll_to_bottom(page):
    last_height = page.run_js("return document.documentElement.scrollHeight")
    while True:
        page.run_js("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(2)
        new_height = page.run_js("return document.documentElement.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
def wait_and_click(page, selector, timeout=10, download=False):
    if not download:
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                page.wait.eles_loaded(selector)
                button = page.ele(selector, timeout=0.5)
                button.click()
                return True
            except:
                pass
        raise TimeoutError(f"按钮 '{selector}' 在 {timeout} 秒内未出现或无法点击")
    else:
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                page.wait.eles_loaded(selector)
                button = page.ele(selector, timeout=0.5)
                button.click.to_download()
                return True
            except:
                pass
        raise TimeoutError(f"按钮 '{selector}' 在 {timeout} 秒内未出现或无法点击")
# from DrissionPage import  Chromium, ChromiumOptions
#
# co = ChromiumOptions()
# co.incognito()  # 匿名模式
# page = Chromium(co)
page = ChromiumPage()


def scroll_to_bottom(page):
    last_height = page.run_js("return document.body.scrollHeight")
    while True:
        page.run_js("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # 给页面加载时间
        new_height = page.run_js("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

try:
    # 获取用户输入的账号和密码
    username, password = get_credentials()

    # 登录
    website = input("请输入您要访问的网站: ") # 输入网址
    page.get(website)
    page.wait.eles_loaded("#user_id")
    page.ele("#user_id").input(username)
    page.ele("#password").input(password)
    page.ele("#entry-login").click()

    # 等待页面加载完成
    page.wait.eles_loaded("xpath://button[matches(@id, 'folder-title-_.*_1') and contains(text(), 'Lectures')]", timeout=10)
    print("Lectureschuxinale")
    # 点击 "Lectures" 按钮
    lecture_id = input("请输入您要访问的讲座的ID: ")
    if not wait_and_click(page, lecture_id):
        print("无法点击 Lectures 按钮")
    # 点击所有 "Week" 按钮
    page.wait.eles_loaded("xpath://button[contains(@id, 'folder-title-') and starts-with(normalize-space(.), 'Week')]",
                          timeout=10)
    week_buttons = page.eles(
        "xpath://button[contains(@id, 'folder-title-') and starts-with(normalize-space(.), 'Week')]")
    for button in week_buttons:
        print(button.text)
        try:
            button.click()
            print(f"成功点击 {button.text} 按钮")
            time.sleep(2.5)
            scroll_to_bottom(page)

        except Exception as e:
            print(e)
            print(f"点击 {button.text} 按钮后，未找到预期元素")
    # 获取所有讲座链接
    print("所有Week按钮已被点击")
    page.wait.eles_loaded("xpath://a[contains(text(), 'Lecture') and contains(@href, 'blackboard.com')]", timeout=10)
    lecture_links = page.eles("xpath://a[contains(text(), 'lecture') and contains(@href, 'blackboard.com')]")
    lecture_urls = [link.attr('href') for link in lecture_links]
    print(f"找到 {len(lecture_urls)} 个讲座链接")
    a = int(input("请输入您要开始下载的讲座的序号: "))
    # 下载部分
    for link_url in lecture_urls[a:]:
        page.get(link_url)

        # 等待页面加载
        page.wait.ele_displayed('xpath://svg[contains(@class, "MuiSvgIcon") and contains(@class, "ms-Button-icon")]',
                                timeout=10)
        # 检查是否存在直接下载按钮
        direct_download_button = page.ele('xpath://button[@aria-label="Download" and @title="Download"]', timeout=5)
        print("检测到加载")
        if direct_download_button:
            # 如果存在直接下载按钮，点击它
            direct_download_button.click.to_download()
            print(f"直接下载: {link_url}")
        else:
            # 如果不存在直接下载按钮，执行原来的逻辑
            try:
                # 等待第一个按钮出现并点击
                wait_and_click(page, "css=div.ms-Button-flexContainer svg.MuiSvgIconroot-0-2-27")
                print("展开下载选项")

                # 尝试点击 "Download original file" 按钮
                wait_and_click(page, "xpath://span[text()='Download original file']", timeout=3, download=True)
                print(f"点击下载原始文件: {link_url}")
            except Exception as e:
                print(f"无法完成下载操作: {link_url}")
                print(f"错误信息: {str(e)}")
        # 等待下载完成
        time.sleep(3)
        print("完成")
        page.refresh()
except Exception as e:
    print(f"发生错误: {str(e)}")

finally:
    page.quit()
