import os
import random
import shutil
import string
import time
import requests
import zmail
import re
from datetime import datetime, timedelta
import zipfile

from conf import configs

# 登录邮箱(邮箱名, 密码)
user_email = configs['email']['user_address']
# 存放文件地址
save_path = os.getcwd()

temp_path = save_path + '/bill_save/temp'
archives_path = save_path + '/bill_save/archives'
interval = configs['email']['server']['interval']
debug = configs['debug']
if type(debug) is not bool:
    debug = False


# return -1 未能获取目标邮件
# return -2 连接断开，需要重新登录
# return -3 未能获取解压密码


def server_login():
    try:
        s = zmail.server(username=configs['email']['server']['address'],
                         password=configs['email']['server']['password'])
    except Exception as e:
        print("登录服务端邮箱时出现异常 ")
        if debug:
            print(e)
        print("请检查配置文件是否填写完整")
        return -1

    if s.smtp_able():
        print("SMTP服务器连接成功")
        if s.pop_able():
            print("POP3服务器连接成功")
            return s
        else:
            print("POP3服务器连接失败")
            return -1
    else:
        print("SMTP服务器连接失败")
        return -1


def re_login():
    for delay_time in [300, 900, 1800, 2700, 3600]:
        print(str(int(delay_time / 60)) + "分钟后重试")
        time.sleep(delay_time)
        server = server_login()
        if server != -1:
            break
    while server == -1:
        print("重新登录失败，等待1小时后重试")
        time.sleep(3600)
        server = server_login()


# 解压文件
def unzip_with_password(zip_file, password, unzip_dir):
    print(f"尝试使用密码 {password}")
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_file:
            for file in zip_file.namelist():
                if file.endswith('.csv'):
                    zip_file.extract(member=file, pwd=password.encode('utf-8'), path=unzip_dir)

            # 首先检查目录下的直接文件
            for filename in os.listdir(unzip_dir):
                if filename.endswith('.csv'):
                    return unzip_dir + '/' + filename

            # 然后遍历目录及其所有子目录
            for dir_path, dir_names, filenames in os.walk(unzip_dir):
                for filename in filenames:
                    if filename.endswith('.csv'):
                        return dir_path + '/' + filename

    except FileNotFoundError:
        print(f"文件 {zip_file} 不存在.")
        return 1
    except zipfile.BadZipFile:
        print(f"文件 {zip_file} 不是一个有效的zip文件.")
        return 2
    except RuntimeError:
        print(f"解压文件 {zip_file} 时密码错误.")
        return 3


# 下载文件
def download_file(url, download_path):
    response = requests.get(url)
    with open(download_path, 'wb') as fd:
        for chunk in response.iter_content(chunk_size=1024):
            fd.write(chunk)


# 发送请求邮件
def send_email(server, subject, content):
    mail = {
        'subject': subject,
        'content_text': content
    }
    server.send_mail(user_email, mail)
    print("请求邮件已发送")


# 归档账单
def archive_bill(platform):
    if not os.path.exists(temp_path):
        print(f"源文件夹 {temp_path} 不存在")
        return

    if platform == '支付宝':
        platform = 'alipay'
    elif platform == '微信':
        platform = 'wechat'
    elif platform == 'all':
        for filename in os.listdir(temp_path):
            # 清空文件
            file_path = os.path.join(temp_path, filename)
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)
        return

    else:
        print("平台名称错误")
        return

    # 创建目标文件夹
    if not os.path.exists(archives_path):
        print(f"目标文件夹 {archives_path} 不存在，创建该文件夹")
        os.mkdir(archives_path)

    # 创建目标分类文件夹
    platform_path = os.path.join(archives_path, platform)
    if not os.path.exists(platform_path):
        print(f"目标文件夹 {platform_path} 不存在，创建该文件夹")
        os.mkdir(platform_path)

    for filename in os.listdir(temp_path):
        # 生成源文件和目标文件目录
        src_file_path = os.path.join(temp_path, filename)
        dst_file_path = os.path.join(platform_path, filename)
        # 移动文件到目标文件夹
        shutil.move(src_file_path, dst_file_path)


def init_path():
    if not os.path.exists(save_path + '/bill_save'):
        print(f"目标文件夹 {save_path} 不存在，创建该文件夹")
        os.mkdir(save_path + '/bill_save')
    if not os.path.exists(save_path + '/bill_save/temp'):
        print(f"目标文件夹 {save_path} 不存在，创建该文件夹")
        os.mkdir(save_path + '/bill_save/temp')


# 生产随机码用于标示邮件
def generate_code(length):
    # 获取所有字母和数字的数组
    code_chars = string.ascii_letters + string.digits
    # 随机生成 length 个随机码
    return ''.join(random.choice(code_chars) for _ in range(length))


def handle_alipay_mail(server, mail_of_alipay):
    init_path()
    archive_bill("all")
    random_code = generate_code(6)

    # 保存附件
    zmail.save_attachment(mail_of_alipay, temp_path, overwrite=True)
    # 从邮箱获取解压密码
    start_time = datetime.now()
    black_list = [mail_of_alipay['Id']]
    send_email(server=server, subject="<" + random_code + ">支付宝账单密码请求",
               content='你正在对支付宝进行记账操作，你需要对这封邮件回复6位数字解压密码，有效时间2小时，发信时间为'
                       + datetime.now().strftime("%m-%d %H:%M:%S") + '。')

    # 轮询邮箱获取密码
    time.sleep(interval)
    is_loop = True
    try_times = 3
    while is_loop and try_times > 0:
        # 时限为2小时
        if datetime.now() - start_time > timedelta(hours=2):
            break
        # 接收请求邮箱之后的回复邮箱
        try:
            mail_for_pwd = server.get_mails(subject='<' + random_code + '>支付宝账单密码请求',
                                            start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"))
        except ConnectionResetError:
            print("连接重置，即将尝试重连")
            try_times -= 1
            time.sleep(interval)
            continue
        except BrokenPipeError:
            print("连接关闭，将尝试重新登录")
            try_times -= 1
            re_login()
            continue
        except Exception as e:
            if debug:
                print("在获取支付宝文件密码时异常 " + str(e))
            print("收取邮件时遇到错误，即将重试")
            try_times -= 1
            time.sleep(interval)
            continue

        if len(mail_for_pwd) != 0:
            for i in range(0, len(mail_for_pwd)):
                # 跳过黑名单的邮件
                if mail_for_pwd[i]['Id'] in black_list:
                    continue
                # 尝试获取密码
                zip_password = re.search(r'\d{6}', mail_for_pwd[i]['Content_text'][0]).group()
                state = unzip_with_password(temp_path + '/' + mail_of_alipay['attachments'][0][0], zip_password,
                                            temp_path)
                if state == 1:
                    is_loop = False
                    break
                elif state == 2:
                    print('文件失效，该链接可能已过期')
                    os.remove(temp_path + '/' + mail_of_alipay['attachments'][0][0])
                    break
                elif state == 3:
                    black_list.append(mail_for_pwd[i]['id'])
                    send_email(server=server, subject='<' + random_code + '>支付宝账单密码请求',
                               content='密码 ' + zip_password + '错误' + '\n你正在对支付宝进行记账操作，你需要对这封邮件回复6位数字解压密码，发信时间为'
                                       + datetime.now().strftime("%m-%d %H:%M:%S") + '。')
                else:
                    os.remove(temp_path + '/' + mail_of_alipay['attachments'][0][0])
                    if debug:
                        print(f'解压成功，密码为{zip_password}')
                    else:
                        print('解压成功')
                    if configs['email']['delete_after_used']:
                        if debug:
                            print(mail_for_pwd[i]['Id'])
                        server.delete(mail_of_alipay['Id'])
                        print('邮件已删除')
                    return state
        print("未获取支付宝账单解压密码，即将重试")
        time.sleep(interval)
    if try_times == 0:
        return -4
    print("2小时内未能获取支付宝账单解压密码")
    send_email(server=server, subject="同步失败", content="未能获取解压密码")
    return -3


def handle_wechat_mail(server, mail_of_wechat):
    # 初始化环境
    init_path()
    archive_bill("all")
    random_code = generate_code(6)

    # 获取下载地址
    content = str(mail_of_wechat['content_html'])
    url = re.findall(r'https://download\.bill\.weixin\.qq\.com/[^"]*', content)
    download_path = temp_path + '/wechat_bill' + datetime.now().strftime("%Y%m%d%H%M%S") + '.zip'
    download_file(url[0], download_path)

    # 从邮箱获取解压密码
    start_time = datetime.now()
    black_list = [mail_of_wechat['Id']]
    send_email(server=server, subject="<" + random_code + ">微信账单密码请求",
               content='你正在对微信进行记账操作，你需要对这封邮件回复6位数字解压密码，有效时间2小时，发信时间为'
                       + datetime.now().strftime("%m-%d %H:%M:%S") + '。')

    # 轮询邮箱获取密码
    time.sleep(interval)
    is_loop = True
    try_times = 3
    while is_loop and try_times > 0:
        # 时限为2小时
        if datetime.now() - start_time > timedelta(hours=2):
            break
        try:
            mail_for_pwd = server.get_mails(subject='<' + random_code + '>微信账单密码请求',
                                            start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"))
        except ConnectionResetError:
            print("连接重置，即将重试")
            try_times -= 1
            time.sleep(interval)
            continue
        except BrokenPipeError:
            print("连接关闭，将尝试重新登录")
            try_times -= 1
            re_login()
            continue
        except Exception as e:
            if debug:
                print("在获取微信文件密码时异常 " + str(e))
            print("收取邮件时遇到错误，即将重试")
            try_times -= 1
            time.sleep(interval)
            continue

        if len(mail_for_pwd) != 0:
            for i in range(0, len(mail_for_pwd)):
                # 跳过黑名单的邮件
                if mail_for_pwd[i]['Id'] in black_list:
                    continue
                # 尝试获取密码
                zip_password = re.search(r'\d{6}', mail_for_pwd[i]['Content_text'][0]).group()
                state = unzip_with_password(zip_file=download_path, password=zip_password, unzip_dir=temp_path)
                if state == 1:
                    is_loop = False
                    break
                elif state == 2:
                    print('文件失效，该链接可能已过期')
                    os.remove(download_path)
                    is_loop = False
                    break
                elif state == 3:
                    black_list.append(mail_for_pwd[i]['id'])
                    send_email(server=server, subject="<" + random_code + ">微信账单密码请求",
                               content='密码 ' + zip_password + '错误' + '\n你正在对微信进行记账操作，你需要对这封邮件回复6位数字解压密码，发信时间为'
                                       + datetime.now().strftime("%m-%d %H:%M:%S") + '。')
                else:
                    os.remove(download_path)
                    print(f'解压成功，密码为{zip_password}')
                    if configs['email']['delete_after_used']:
                        server.delete(mail_of_wechat['Id'])
                        print('邮件已删除')
                    return state
        print("未获取微信账单解压密码，即将重试")
        time.sleep(interval)
    if try_times == 0:
        return -4
    print("2小时内未能获取微信账单解压密码")
    send_email(server=server, subject="同步失败", content="未能获取解压密码")
    return -3


def get_mail(receive_time, server):
    try_times = 3
    result = []
    state = None
    while try_times > 0:
        try:
            # 补偿多轮次下接收支付宝和微信邮件的时间差
            mails_of_alipay = server.get_mails(subject='支付宝交易流水明细',
                                               start_time=(receive_time - timedelta(seconds=interval)).strftime(
                                                   '%Y-%m-%d %H:%M:%S'),
                                               sender='service@mail.alipay.com')
        except ConnectionResetError:
            print("连接重置，即将重试")
            time.sleep(interval)
            try_times -= 1
            continue
        except BrokenPipeError:
            print("连接关闭，将尝试重新登录")
            re_login()
            continue
        except Exception as e:
            if debug:
                print("在获取支付宝邮件时异常 " + str(e))
            print("收取邮件时遇到错误，即将重试")
            try_times -= 1
            time.sleep(interval)
            continue

        if len(mails_of_alipay) != 0:
            state = handle_alipay_mail(server=server, mail_of_alipay=mails_of_alipay[0])
            result = "支付宝", state
        else:
            time.sleep(interval)
            try:
                mails_of_wechat = server.get_mails(subject='微信支付',
                                                   start_time=receive_time.strftime(
                                                       '%Y-%m-%d %H:%M:%S'),
                                                   sender='wechatpay@tencent.com')
            except ConnectionResetError:
                print("连接重置，即将重试")
                time.sleep(interval)
                try_times -= 1
                continue
            except BrokenPipeError:
                print("连接关闭，将尝试重新登录")
                re_login()
                continue
            except Exception as e:
                if debug:
                    print("在获取微信支付邮件时异常 " + str(e))
                print("收取邮件时遇到错误，即将重试")
                try_times -= 1
                time.sleep(interval)
                continue

            if len(mails_of_wechat) != 0:
                state = handle_wechat_mail(server=server, mail_of_wechat=mails_of_wechat[0])
                result = "微信", state

        if state == -3:
            send_email(server=server, subject="同步失败", content="未能获取解压密码")
            return -3
        elif state:
            return result
        else:
            return -1
    print("获取邮件失败次数达到上限")
    return -2
