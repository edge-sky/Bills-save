import csv
from conf import configs

debug = configs['debug']
if type(debug) is not bool:
    debug = False


def alipay_data(filepath):
    data = []
    with open(filepath, "r", encoding="gbk") as f:
        reader = csv.reader(f)
        is_start = False
        jump_line = True
        if debug:
            print(reader)
        for row in reader:
            # 对商户名中出现英文逗号的情况进行处理
            while len(row) > 13:
                row[2] += row[3]
                row.pop(3)
            if not is_start:
                # 支付宝可能存在空行，防止越界
                for item in row:
                    if "电子客户回单" in item:
                        is_start = True
                        break
                continue
            # 跳过说明行
            if jump_line:
                jump_line = False
                continue
            data.append(row)
    return data


# 微信导出字段：交易时间,交易类型,交易对方,商品,金额(元),支付方式,当前状态,备注
def wechat_data(filepath):
    data = []
    with open(filepath, "r", encoding="utf-8") as f:
        # 使用 csv.reader 来处理带引号和逗号的复杂字段
        reader = csv.reader(f)
        is_start = False
        jump_line = True
        if debug:
            print(reader)
        for row in reader:
            # 对商户名中出现英文逗号的情况进行处理
            while len(row) > 11:
                row[2] += row[3]
                row.pop(3)
            if not is_start:
                # 与支付宝统一格式
                for item in row:
                    if "微信支付账单明细列表" in item:
                        is_start = True
                        break
                continue
            if jump_line:
                jump_line = False
                continue
            data.append(row)
    return data
