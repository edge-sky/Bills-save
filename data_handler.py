import csv

def alipay_data(filepath):
    data = []
    with open(filepath, "r", encoding="gbk") as f:
        reader = csv.reader(f)
        is_start = False
        jump_line = True
        for row in reader:
            if not is_start:
                if "电子客户回单" in row[0]:
                    is_start = True
                continue
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
        for row in reader:
            if not is_start:
                if "微信支付账单明细列表" in row[0]:
                    is_start = True
                continue
            if jump_line:
                jump_line = False
                continue
            data.append(row)
    return data
