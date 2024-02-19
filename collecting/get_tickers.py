import FinanceDataReader as fdr  # https://github.com/FinanceData/FinanceDataReader
import json

markets = ['NYSE', 'NASDAQ', 'KOSPI', 'TSE']  # 뉴욕증권거래소, 나스닥, 코스피, 도쿄증권거래소
for m in markets:
    try:
        # dictionary data. Loading previous json file.
        with open("stcklist/"+m+".json", "r", encoding='utf-8') as json_file:
            json_list = json.load(json_file)
        symbol = []
        name = []
        status = []
        njl = []
        for l in json_list: #기존
            symbol.append(l["Symbol"])
            name.append(l["Name"])
            status.append(l["Status"])
        stocks = fdr.StockListing(m)
        sblist = list(map(lambda x : '-'.join(x.split('.')), list(stocks.get('Symbol'))))
        for s in symbol:
            if s not in sblist:   # 방금 찾은 심볼들과 매치하지 않을 경우, 사라지거나 상장폐지된 티커.
                status[symbol.index(s)] = -1    # 문제있는 티커
        for s in sblist:
            if s in symbol:       # 기존에 있는 티커?
                pass
            elif s not in symbol: # 그렇지 않다는 건 새로운 티커라는 것.
                symbol.append(s)
                name.append(stocks.get('Name')[symbol.index(s)])
                status.append(0)
        for sb, nm, st in zip(symbol, name, status):
            njl.append({"Symbol": sb, "Name": nm, "Status": st})
        with open("stcklist/"+m+".json", "w", encoding='utf-8') as json_file:
            json.dump(njl, json_file, ensure_ascii=False)
    except FileNotFoundError:
        # only when there is no previous json file. Loading new fresh list.
        stocks = fdr.StockListing(m)
        symbol = stocks.get('Symbol')
        name = stocks.get('Name')
        json_list = []
        for s, n in zip(symbol, name):
            s = s.replace('.','-')
            json_list.append({"Symbol": s, "Name": n, "Status": 0})
        with open("stcklist/"+m+".json", "w", encoding='utf-8') as json_file:
            json.dump(json_list, json_file, ensure_ascii=False)
    json_file.close()