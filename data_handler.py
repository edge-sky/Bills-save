def alipay_data(filepath):
    data = []
    with open(filepath, "r", encoding="gbk") as f:
        lines = f.readlines()
        is_start = False
        jump_line = True
        for line in lines:
            if not is_start:
                if "电子客户回单" in line:
                    is_start = True
                continue
            if jump_line:
                jump_line = False
                continue
            data_line = line.strip().split(",")
            data.append(data_line)
    return data


# 微信导出字段：交易时间,交易类型,交易对方,商品,金额(元),支付方式,当前状态,备注
def wechat_data(filepath):
    data = []
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        is_start = False
        jump_line = True
        for line in lines:
            if not is_start:
                if "微信支付账单明细列表" in line:
                    is_start = True
                continue
            if jump_line:
                jump_line = False
                continue
            data_line = line.strip().split(",")
            data.append(data_line)
    return data
