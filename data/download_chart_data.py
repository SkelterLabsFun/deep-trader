"""Script which is used when downloading chart data

NOTE: This script requires Windows environment.

Details: https://skelterlabs.atlassian.net/wiki/spaces/DeepTrader/pages/1956085778/API+CYBOS+Plus

"""

import win32com.client

inst_cp_cybos = win32com.client.Dispatch("CpUtil.CpCybos")
print(inst_cp_cybos.IsConnect)

inst_cp_stock_code = win32com.client.Dispatch("CpUtil.CpStockCode")
total_count = inst_cp_stock_code.getCount()

stock_codes = []
f = open('c:\\test.csv', 'w')

for i in range(total_count) :
    #print(inst_cp_stock_code.GetData(1,i))
    stock_codes.append(inst_cp_stock_code.GetData(0, i))

inst_stock_chart = win32com.client.Dispatch("CpSysDib.StockChart")
COUNT = 3000000

for stock_code in stock_codes:

    inst_stock_chart.SetInputValue(0, stock_code)
    inst_stock_chart.SetInputValue(1, ord('2'))
    inst_stock_chart.SetInputValue(4, COUNT)
    inst_stock_chart.SetInputValue(5, (0, 1, 2, 3, 4, 5, 8))
    inst_stock_chart.SetInputValue(6, ord('m'))

    sum_data = 0

    while sum_data <= COUNT:
        inst_stock_chart.BlockRequest()

        num_data = inst_stock_chart.GetHeaderValue(3)
        num_field = inst_stock_chart.GetHeaderValue(1)

        print(num_data)

        if num_data == 0 :
            break

        sum_data += num_data

        for i in range(num_data):
            f.write("%s" % (stock_code))
            for j in range(num_field):
                f.write(",%s" % (inst_stock_chart.GetDataValue(j, i)))
            f.write("\n")

f.close()
