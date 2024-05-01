import datetime
import json
from mail import archive_bill, send_email
from conf import configs

import requests

token = configs['notion']['token']
parent_type = configs['notion']['type']
type_id = configs['notion']['type_id']

body = {
    "parent": {
        "type": parent_type,
        "database_id": type_id,
    },
    "properties": {
        "日期": {
            "date": {
                "start": "",
            }
        },
        "星期": {
            "select": {
                "name": "",  # 可选：周一、周二...周日
            },
        },
        "账单信息": {
            "title": [
                {
                    "type": "text",
                    "text": {"content": ""},
                }
            ]
        },
        "金额": {
            "number": 0.0,
        },
        "交易平台": {
            "select": {
                "name": "",  # 可选：支付宝、微信
            },
        },
        "交易类型": {
            "select": {
                "name": "",  # 可选：收入、支出
            },
        },
        "交易方式": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": ""},
                }
            ]
        },
        "平台交易单号": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": ""},
                }
            ]
        }
    }
}


# 对比已有数据
# data 得到的数据字段形如：{'object': '', 'id': '', 'created_time': '',
#       'last_edited_time': '',
#       'created_by': {'object': '', 'id': ''},
#       'last_edited_by': {'object': '', 'id': ''}, 'cover': , 'icon': ,
#       'parent': {'type': '', 'database_id': ''}, 'archived': ,
#       'in_trash': , 'properties': {'': {'id': '', 'type': 'select', 'select': {'id': '', 'name': '', 'color': ''}}, },
#       'url': '', 'public_url': }
def check_contrast(platform):
    # 第一次获取数据
    get_data = requests.request(
        'POST',
        'https://api.notion.com/v1/databases/67d863ff0de448288ad21235576d2ec1/query',
        headers={'Authorization': 'Bearer ' + token, 'Notion-Version': '2021-05-13'},
    )
    datas = json.loads(get_data.text)
    temp_list = []
    temp_list.extend(datas['results'])

    # 如果一页不能加载完所有数据，继续获取，防止添加重复数据（折磨了作者三天才发现
    while datas['has_more']:
        print("数据量过大，正在获取更多数据")
        get_data = requests.request(
            'POST',
            'https://api.notion.com/v1/databases/67d863ff0de448288ad21235576d2ec1/query',
            headers={'Authorization': 'Bearer ' + token, 'Notion-Version': '2021-05-13'},
            json={'start_cursor': datas['next_cursor']}
        )
        datas = json.loads(get_data.text)
        temp_list.extend(datas['results'])

    bill_list = []
    for data in temp_list:
        # 根据平台筛选数据
        if data['properties']['交易平台']['select']['name'] == platform:
            try:
                bill_list.append(data['properties']['平台交易单号']['rich_text'][0]['text']['content'])
            except IndexError:
                print("该记录未填写订单号 " + str(data))
    return bill_list


def sync_bills(server, platform, update_data):
    nums = 0
    same_nums = 0
    bill_list = check_contrast(platform)
    week_list = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    if platform == '微信':
        for bill in update_data:
            # 去除奇奇怪怪恼人的空格和占位符
            if bill[8].replace('\t', '').replace(' ', '') not in bill_list:
                body['properties']['日期']['date']['start'] = bill[0] + '+08:00'
                body['properties']['星期']['select']['name'] = week_list[
                    datetime.datetime.strptime(bill[0], "%Y-%m-%d %H:%M:%S").weekday()]
                body['properties']['金额']['number'] = float(bill[5].replace('¥', ''))
                body['properties']['交易平台']['select']['name'] = platform
                body['properties']['交易类型']['select']['name'] = bill[4]
                body['properties']['平台交易单号']['rich_text'][0]['text']['content'] = bill[8].replace('\t',
                                                                                                        '').replace(' ',
                                                                                                                    '')
                if bill[4] == '支出':
                    body['properties']['交易方式']['rich_text'][0]['text']['content'] = bill[6]
                    if bill[3] == '"/"':
                        body['properties']['账单信息']['title'][0]['text']['content'] = bill[1]
                    else:
                        body['properties']['账单信息']['title'][0]['text']['content'] = bill[3]
                else:
                    body['properties']['交易方式']['rich_text'][0]['text']['content'] = bill[7]
                    body['properties']['账单信息']['title'][0]['text']['content'] = bill[1]

                try:
                    send_data = requests.request(
                        'POST',
                        'https://api.notion.com/v1/pages',
                        json=body,
                        headers={'Authorization': 'Bearer ' + token, 'Notion-Version': '2021-05-13'},
                    )
                    if configs['output_data']:
                        print(send_data.text)
                    nums += 1
                except requests.exceptions.ConnectionError:
                    print("订单号：" + bill[9] + "发送失败")
                    continue
            else:
                same_nums += 1
    else:
        for bill in update_data:
            if bill[9].replace('\t', '').replace(' ', '') not in bill_list:
                body['properties']['日期']['date']['start'] = bill[0] + '+08:00'
                body['properties']['星期']['select']['name'] = week_list[
                    datetime.datetime.strptime(bill[0], "%Y-%m-%d %H:%M:%S").weekday()]
                body['properties']['账单信息']['title'][0]['text']['content'] = bill[4]
                body['properties']['金额']['number'] = float(bill[6].replace('¥', ''))
                body['properties']['交易平台']['select']['name'] = platform
                body['properties']['交易类型']['select']['name'] = bill[5]
                body['properties']['平台交易单号']['rich_text'][0]['text']['content'] = bill[9].replace('\t',
                                                                                                        '').replace(' ',
                                                                                                                    '')
                if bill[5] == '支出':
                    body['properties']['交易方式']['rich_text'][0]['text']['content'] = bill[7]
                else:
                    body['properties']['交易方式']['rich_text'][0]['text']['content'] = bill[8]

                try:
                    send_data = requests.request(
                        'POST',
                        'https://api.notion.com/v1/pages',
                        json=body,
                        headers={'Authorization': 'Bearer ' + token, 'Notion-Version': '2021-05-13'},
                    )
                    if configs['output_data']:
                        print(send_data.text)
                    nums += 1
                except requests.exceptions.ConnectionError:
                    print("订单号：" + bill[9] + "发送失败")
                    continue

            else:
                same_nums += 1
    send_email(server=server, subject="同步完成", content=platform + "同步完成\n本次同步了" + str(nums) + "条数据")
    print("成功同步" + str(nums) + "条数据")
    print("重复数据" + str(same_nums) + "条")
    archive_bill(platform)
