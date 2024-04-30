import time
from datetime import datetime, timedelta

import zmail

from mail import get_mails, test_server
from notion import sync_bills
from data_handler import alipay_data, wechat_data
from conf import configs

server = zmail.server(username=configs['email']['server']['address'], password=configs['email']['server']['password'])


if configs['test_server']:
    test_server(server)
else:
    print("尝试获取邮件")
    temp_time = datetime.now()
    while True:
        result = get_mails(server)
        if result == -1:
            if datetime.now() - temp_time > timedelta(hours=1):
                print("过去一小时未收到邮件 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                temp_time = datetime.now()
            time.sleep(20)
            continue

        platform = result[0]
        path = result[1]
        if path is not None:
            print("尝试同步" + platform)
            if platform == "支付宝":
                sync_bills(server, platform, alipay_data(path))
            elif platform == "微信":
                sync_bills(server, platform, wechat_data(path))

            print("同步完成")
            print("尝试获取邮件")
