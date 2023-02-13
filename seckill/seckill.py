import json
from datetime import datetime
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

import seckill.utils as utils

logger = utils.build_logger("taobao-seckill")


class ChromeDrive:

    def __init__(self,
                 config_path="./seckill/config.yml",
                 chrome_options=utils.build_chrome_options()
                 ):
        config = utils.read_yaml(config_path)
        self.taobao_config = config["taobao"]
        self.seckill_config = config["seckill"]
        # 秒杀开始时间
        self.seckill_time = self.seckill_config["time"]
        # find_chrome_driver
        self.chrome_path = utils.get_chrome_path(config["chrome-driver-dir"])
        self.driver = webdriver.Chrome(executable_path=self.chrome_path, chrome_options=chrome_options)
        self.driver_wait = WebDriverWait(self.driver, 10)
        # 支付密码
        self.password = self.taobao_config["pay"]["password"]

    def login(self):
        homepage = self.taobao_config["homepage"]
        login_locator = (By.LINK_TEXT, self.taobao_config["login"]["button"])
        login_success_flag = self.taobao_config["login"]["success-xpath"]
        while True:
            self.driver.get(homepage)
            login_button = self.driver.find_element(*login_locator)
            login_button.click()
            logger.info("没登录，现在点击登录按钮。")
            logger.warn("请在30s内扫码登陆！！！")
            WebDriverWait(self.driver, 30).until(
                expected_conditions.visibility_of_element_located((By.LINK_TEXT, "让小丑飞")))
            try:
                self.driver.find_element_by_xpath(login_success_flag)
                logger.info("登陆成功！")
                break
            except NoSuchElementException:
                logger.error("登陆失败, 将刷新重试, 请尽快登陆!!!")
                continue

    def wait_in_cart(self):
        cart_url = self.taobao_config["cart"]["url"]
        logger.info("跳转购物车界面，进入抢购等待状态...")
        self.driver.get(cart_url)
        while True:
            now = datetime.now()
            if now < self.seckill_time and (self.seckill_time - now).seconds > 180:
                logger.info("每分钟刷新一次界面，防止登录超时...")
                self.driver.refresh()
                sleep(60)
            else:
                self.saveCookie()
                logger.info("抢购时间将至，停止自动刷新，准备进入抢购阶段...")
                # self.driver_wait.until(expected_conditions.title_is("淘宝网 - 我的购物车"))
                self.driver.implicitly_wait(10)
                break

    def do_sec_kill(self):
        select_all_locator = (By.ID, self.taobao_config["cart"]["select-all-dom"])
        settle_button_locator = (By.ID, self.taobao_config["cart"]["settle"])
        submit_button = self.taobao_config["cart"]["submit"]
        max_retry_count = self.seckill_config["max-retry"]
        retry_count = 0
        seckill_flag = False
        while retry_count <= max_retry_count:
            now = datetime.now()
            if now >= self.seckill_time:
                retry_count += 1
                logger.info(f"开始第{retry_count}次抢购")
                self.driver_wait.until(expected_conditions.element_to_be_clickable(select_all_locator))
                select_all_button = self.driver.find_element(*select_all_locator)
                select_all_button.click()
                selected_dom = self.driver.find_element_by_id("J_SelectAllCbx1")
                self.driver_wait.until(expected_conditions.element_to_be_selected(selected_dom))
                logger.info("已选中购物车中全部商品！！！")
                self.driver.find_element(*settle_button_locator).click()
                logger.info("已点击结算按钮...")
                self.driver_wait.until(expected_conditions.title_contains("确认订单"))
                # 点击结算按钮后跳转到提交订单页面需要一定时间，因此通过轮循来处理这段时间消耗
                query_times = 30
                for i in range(query_times):
                    try:
                        self.driver.find_element_by_link_text(submit_button).click()
                        logger.info(f"第{i + 1}次尝试提交订单：已点击提交订单按钮！")
                        seckill_flag = True
                        break
                    except NoSuchElementException as e:
                        logger.error(f"第{i + 1}次尝试提交订单：未发现“{submit_button}”按钮, 页面未加载, 重试...")
                if seckill_flag:
                    break
                else:
                    self.driver.back()
                    self.driver.implicitly_wait(10)
                    logger.error("提交订单失败，回退到购物车页面...")
        return seckill_flag

    def pay(self):
        element = self.driver_wait.until(
            expected_conditions.presence_of_element_located((By.CLASS_NAME, 'sixDigitPassword')))
        element.send_keys(self.password)
        self.driver_wait.until(expected_conditions.presence_of_element_located((By.ID, 'J_authSubmit'))).click()
        utils.notify_user(msg="付款成功")

    def saveCookie(self):
        cookies = self.driver.get_cookies()
        cookie_json = json.dumps(cookies)
        with open('./cookies.txt', 'w', encoding='utf-8') as f:
            f.write(cookie_json)

    def sec_kill(self):
        try:
            self.login()
            self.wait_in_cart()
            flag = self.do_sec_kill()
            if flag:
                if self.password:
                    self.pay()
            else:
                logger.error("抢购失败！！！")
        except Exception as e:
            logger.error(e)
            raise
        finally:
            self.driver.quit()
