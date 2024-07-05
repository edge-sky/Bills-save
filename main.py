import time
from datetime import datetime, timedelta


from mail import get_mails, server_login
from notion import sync_bills
from data_handler import alipay_data, wechat_data


server = server_login()

print("尝试获取邮件")
waiting_time = datetime.now()  # 接收邮件计时器
re_login_time = datetime.now()  # 重新登录计时器
receive_time = datetime.now()  # 收件时间
while True:
    try:
        # 每12小时自动重新登录
        if datetime.now() - re_login_time > timedelta(hours=12):
            server = server_login()
            print("重新登录")
            re_login_time = datetime.now()
        # 尝试获取邮件
        result = get_mails(receive_time, server)
        if result == -1:
            if datetime.now() - waiting_time > timedelta(hours=1):
                print("过去一小时未收到邮件 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                waiting_time = datetime.now()
            # 重置收件时间
            receive_time = datetime.now()
            time.sleep(20)
            continue
        elif result == -2:
            server = server_login()
            print("重新登录")
            re_login_time = datetime.now()
            continue
        elif result == -3:
            # 重置收件时间
            receive_time = datetime.now()
            continue

        platform = result[0]
        path = result[1]
        receive_time = datetime.now()
        if path is not None:
            is_successes = -1
            print("尝试同步" + platform)
            if platform == "支付宝":
                is_successes = sync_bills(server, platform, alipay_data(path))
            elif platform == "微信":
                is_successes = sync_bills(server, platform, wechat_data(path))

            if is_successes == 0:
                print("同步完成")
            elif is_successes == -1:
                print("同步异常，终止程序")
                break
    except TypeError as e:
        print(e)
        server = server_login()
        print("重新登录")
        re_login_time = datetime.now()
        continue
