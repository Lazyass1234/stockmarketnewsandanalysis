import yfinance as yf # https://github.com/ranaroussi/yfinance # 0.29v
import json
import psycopg2

import time

conn = psycopg2.connect(host="localhost", dbname="postgres", user="postgres", password="220602", port=5432)
cur = conn.cursor()

try:
    save_json = open("save.json", "r")
    load_save = json.load(save_json)
except:
    save_json = open("save.json", "w", encoding ='utf-8')
    load_save = []
    load_save.append({"Market" : "NYSE", "Finished" : 0, "StartFrom" : 0})
    load_save.append({"Market" : "NASDAQ", "Finished" : 0, "StartFrom" : 0})
    load_save.append({"Market" : "KOSPI", "Finished" : 0, "StartFrom" : 0})
    load_save.append({"Market" : "TSE", "Finished" : 0, "StartFrom" : 0})
    json.dump(load_save, save_json, ensure_ascii=False)
save_json.close()

def get_ibc(symbol, market):
    if market == 'KOSPI':
        symbol += ".KS"
    if market == 'TSE':
        symbol += ".T"
    t = yf.Ticker(symbol)
    for atmpt in range(10):
        try:
            ist = t.income_stmt
        except:
            print("couldn't get the income statement of", symbol)
            time.sleep(1)
            continue
        else:
            if ist.empty:
                print("income statement of", symbol, "is empty")
                continue
            else:
                break
    for atmpt in range(10):
        try:
            bls = t.balance_sheet
        except:
            print("couldn't get the balance sheet of", symbol)
            time.sleep(1)
            continue
        else:
            if bls.empty:
                print("balance sheet of", symbol, "is empty")
                continue
            else:
                break
    for attempt in range(10):
        try:
            cfl =t.cash_flow
        except:
            print("couldn't get the cash flow of", symbol)
            time.sleep(1)
            continue
        else:
            if cfl.empty:
                print("cash flow of", symbol, "is empty")
                continue
            else:
                break
    try:
        dvd = t.dividends[-1]
    except:
        dvd = None
    return ist, bls, cfl, dvd

def safe_save(cur, m, stocks, load_save):
    cur.execute("SELECT COUNT(*) FROM \"AIS\".stck_mtdt_"+m.lower())
    lastidx = cur.fetchone()[0]
    stcklen = len(stocks)
    for l in load_save:
        if l['Market'] == m:
            l['StartFrom'] = lastidx
            if stcklen == lastidx:
                l['Finished'] = 1
    json_file = open("save.json", "w", encoding = "utf-8")
    json_file.truncate()
    json.dump(load_save, json_file, ensure_ascii=False)
    json_file.close()

def commiting(stocks, m, strt):
    for i in range(strt, len(stocks)):
        s = stocks[i]['Symbol']
        n = stocks[i]['Name']
        print(m, '\t', s, '\t', n)
        ist, bls, cfl, dvd = get_ibc(s, m)
        
        if ist.empty:
            netcom, diEPS = None, None
        else:
            try:
                netcom, diEPS = ist.loc[['Net Income', 'Diluted EPS']][ist.columns[0]].to_list()
            except:
                netcom, diEPS = None, None
        if bls.empty:
            toteqt, totcap = None, None
        else:
            try:
                toteqt, totcap = bls.loc[['Total Equity Gross Minority Interest', 'Total Capitalization']][bls.columns[0]].to_list()
            except:
                toteqt, totcap = None, None
        if cfl.empty:
            ocf, icf, fcf = None, None, None
        else:
            try:
                ocf, icf, fcf = cfl.loc[['Operating Cash Flow', 'Investing Cash Flow', 'Financing Cash Flow']][cfl.columns[0]].to_list()
            except:
                ocf, icf, fcf = None, None, None
        try:
            roe = netcom / toteqt
        except:
            print('Ticker', s, 'had an error at getting ROE')
            roe = None
        try:
            per = totcap / netcom
        except:
            print('Ticker', s, 'had an error at getting PER')
            per = None
        try:
            pbr = per * roe
        except:
            print('Ticker', s, 'had an error at getting PBR')
            pbr = None
        try:
            std_dt = ist.columns[0]
        except:
            print('Ticker', s, 'had an error at getting standard date')
            std_dt = None
        cur.execute("INSERT INTO \"AIS\".stck_mtdt_"+m.lower()+"(stck_ticker, stck_nm, stck_mrkt, net_income, roe, eps, per, pbr, ocf, icf, fcf, equity, cap, std_dt, dividends) values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (s, n, m, netcom, roe, diEPS, per, pbr, ocf, icf, fcf, toteqt, totcap, std_dt, dvd))
        conn.commit()

for i in load_save:
    if i['Finished'] == 0:
        strt = i['StartFrom']
        m = i['Market']
        stocks = json.load(open("stcklist/"+m+".json", "r"))
        try:
            commiting(stocks, m, strt)
        except KeyboardInterrupt:
            safe_save(cur, m, stocks, load_save)
            break
        safe_save(cur, m, stocks, load_save)
    else:
        continue