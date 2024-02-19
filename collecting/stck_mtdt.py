from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
import json
import psycopg2
import time
conn = psycopg2.connect(host="localhost", dbname="postgres",
                        user="postgres", password="220602", port=5432)
cur = conn.cursor()

options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument("disable-gpu")
options.add_argument('--blink-settings=imagesEnabled=false')
options.add_argument("--log-level=3")
driver = webdriver.Chrome('chromedriver', options=options)


def to_txt(pgelem):
    return pgelem.text

def getdata(symbol, market, json_list, sidx):
    if market == 'KOSPI':
        symbol += ".KS"
    if market == 'TSE':
        symbol += ".T"
    rtyhfin = "https://finance.yahoo.com/"  # root yahoo financial
    query = "quote/" + symbol
    ist_param = "/financials?p="
    bls_param = "/balance-sheet?p="
    cfl_param = "/cash-flow?p="

    # dividend -- no worry till the data-test's value is changed
    driver.get(rtyhfin+query)
    htmltxtidx = driver.page_source
    bs = BeautifulSoup(htmltxtidx, 'html.parser')

    headtitle = bs.find('head').find('title').text
    try:
        if headtitle == "Symbol Lookup from Yahoo Finance":
            raise Exception('Not a valid ticker')
    except Exception:
        print('유효하지 않은 ticker')
        json_list[sidx]['Status'] = -1
        with open("stcklist/"+market+".json", "w", encoding='utf-8') as json_file:
            json.dump(json_list, json_file, ensure_ascii=False)
        return

    dvd = bs.select(
        '[data-test="DIVIDEND_AND_YIELD-value"]')[0].text.split(' ')[1][1:-1]
    dvd = dvd.split('%')[0]
    if dvd == '-' or dvd == 'N/A':
        dvd = None
    else:
        dvd = float(dvd)
    del (htmltxtidx, bs)

    # income statement
    driver.get(rtyhfin+query+ist_param+symbol)
    time.sleep(1)
    try:
        driver.find_element(By.CSS_SELECTOR, '.lightbox-wrapper').find_elements(
            By.TAG_NAME, 'button')[0].click()  # for disabling modal
    except:
        pass
    driver.implicitly_wait(1)
    driver.find_element(
        By.CSS_SELECTOR, '[aria-label="Net Income Common Stockholders"]').click()

    htmltxtidx = driver.page_source
    bs = BeautifulSoup(htmltxtidx, 'html.parser')
    cols = list(map(to_txt, bs.find('div', ['D(tbhg)']).find(
        'div', ['D(tbr)']).contents))
    rows = list(
        map(to_txt, bs.find('div', ['D(tbrg)']).find_all('span', ['Va(m)'])))

    if 'ttm' in cols:
        tmpyy = cols[2].split('/')
        rcntyycol = 2
    else:
        tmpyy = cols[1].split('/')
        rcntyycol = 1
    fiscaldt = tmpyy[-1] + '-' + (tmpyy[0] if len(tmpyy[0])
                                  == 2 else '0'+tmpyy[0]) + '-' + tmpyy[1]
    del (tmpyy)
    netcom = int("".join(bs.find('div', ['D(tbrg)']).find('div', attrs={
                 'title': 'Net Income'}).findParent().findParent().contents[rcntyycol].text.split(',')))
    diEPS = bs.find('div', ['D(tbrg)']).find('div', attrs={
        'title': 'Diluted EPS'}).findParent().findParent().contents[rcntyycol].text
    if diEPS == '-':
        diEPS = None
    else:
        diEPS = diEPS.replace('k', '')
    del (htmltxtidx, bs, cols)

    driver.find_element(By.CSS_SELECTOR, '[data-test="qsp-financial"]').find_elements(
        By.TAG_NAME, 'span')[6].click()  # quarter
    time.sleep(1)
    htmltxtidx = driver.page_source
    bs = BeautifulSoup(htmltxtidx, 'html.parser')
    del (htmltxtidx)
    cols = list(map(to_txt, bs.find('div', ['D(tbhg)']).find(
        'div', ['D(tbr)']).contents))

    qtr = bs.find('div', ['D(tbrg)']).find(
        'div', attrs={'title': 'Net Income'}).findParent().findParent().contents[2:6]
    qtr = list(map(to_txt, qtr))
    qtr = list(map(lambda q: int("".join(q.split(','))), qtr))

    qdl = list(map(lambda c: c.split('/'), cols[2:6]))
    qdl = list(map(
        lambda cl: cl[-1]+'-'+(cl[0] if len(cl[0]) == 2 else '0'+cl[0]) + '-'+cl[1], qdl))
    del (ist_param, bs, rows, cols)

    # balance sheet
    driver.get(rtyhfin+query+bls_param+symbol)
    htmltxtidx = driver.page_source
    bs = BeautifulSoup(htmltxtidx, 'html.parser')

    cols = list(map(to_txt, bs.find('div', ['D(tbhg)']).find(
        'div', ['D(tbr)']).contents))
    if 'ttm' in cols:
        rcntyycol = 2
    else:
        rcntyycol = 1
    rows = list(
        map(to_txt, bs.find('div', ['D(tbrg)']).find_all('span', ['Va(m)'])))
    toteqtidx = rows.index('Total Equity Gross Minority Interest')
    totcapidx = rows.index('Total Capitalization')

    finrows = bs.find('div', ['D(tbrg)']).find_all('div', recursive=False)
    toteqt = finrows[toteqtidx].find(
        'div', ['D(tbr)']).contents[rcntyycol].text
    totcap = finrows[totcapidx].find(
        'div', ['D(tbr)']).contents[rcntyycol].text
    if toteqt == '-':
        toteqt = None
    else:
        toteqt = int("".join(toteqt.split(',')))
    if totcap == '-':
        totcap = None
    else:
        totcap = int("".join(totcap.split(',')))
    del (bls_param, htmltxtidx, bs, finrows, rows, cols)

    # cash flow
    driver.get(rtyhfin+query+cfl_param+symbol)
    htmltxtidx = driver.page_source
    bs = BeautifulSoup(htmltxtidx, 'html.parser')
    cols = list(map(to_txt, bs.find('div', ['D(tbhg)']).find(
        'div', ['D(tbr)']).contents))
    if 'ttm' in cols:
        rcntyycol = 2
    else:
        rcntyycol = 1
    rows = list(
        map(to_txt, bs.find('div', ['D(tbrg)']).find_all('span', ['Va(m)'])))
    ocfidx = rows.index('Operating Cash Flow')
    icfidx = rows.index('Investing Cash Flow')
    fcfidx = rows.index('Financing Cash Flow')
    finrows = bs.find('div', ['D(tbrg)']).find_all('div', recursive=False)
    ocf = int("".join(finrows[ocfidx].find(
        'div', ['D(tbr)']).contents[rcntyycol].text.split(',')))
    icf = int("".join(finrows[icfidx].find(
        'div', ['D(tbr)']).contents[rcntyycol].text.split(',')))
    fcf = int("".join(finrows[fcfidx].find(
        'div', ['D(tbr)']).contents[rcntyycol].text.split(',')))
    if ocf == '-':
        ocf = None
    if icf == '-':
        icf = None
    if fcf == '-':
        fcf = None
    return dvd, fiscaldt, netcom, diEPS, qtr, qdl, toteqt, totcap, ocf, icf, fcf

def commiting(stocks, m, json_list):
    lens = len(stocks)
    for i in range(lens):
        if json_list[i]['Status'] == 0:        # status가 0인 애들 모두
            s = json_list[i]['Symbol']
            n = json_list[i]['Name']
            print(m, '\t', s, '\t', n)
            try:
                dvd, fiscaldt, netcom, diEPS, qtr, qdl, toteqt, totcap, ocf, icf, fcf = getdata(
                s, m, json_list, i)
            except Exception:
                continue
            qtr0 = None
            qtr1 = None
            qtr2 = None
            qtr3 = None
            if len(qtr) == 0:
                pass
            elif len(qtr) == 1:
                qtr0 = qtr[0]
            elif len(qtr) == 2:
                qtr0 = qtr[0]
                qtr1 = qtr[1]
            elif len(qtr) == 3:
                qtr0 = qtr[0]
                qtr1 = qtr[1]
                qtr2 = qtr[2]
            else:
                qtr0 = qtr[0]
                qtr1 = qtr[1]
                qtr2 = qtr[2]
                qtr3 = qtr[3]
            qdl0 = None
            qdl1 = None
            qdl2 = None
            qdl3 = None
            if len(qdl) == 0:
                pass
            elif len(qdl) == 1:
                qdl0 = qdl[0]
            elif len(qdl) == 2:
                qdl0 = qdl[0]
                qdl1 = qdl[1]
            elif len(qdl) == 3:
                qdl0 = qdl[0]
                qdl1 = qdl[1]
                qdl2 = qdl[2]
            else:
                qdl0 = qdl[0]
                qdl1 = qdl[1]
                qdl2 = qdl[2]
                qdl3 = qdl[3]
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
                std_dt = fiscaldt
            except:
                print('Ticker', s, 'had an error at getting standard date')
                std_dt = None
            cur.execute("INSERT INTO \"AIS\".stck_mtdt_"+m.lower()+"(stck_ticker, stck_nm, stck_mrkt, net_income, roe, eps, per, pbr, ocf, icf, fcf, equity, cap, std_dt, dividends,fstrcntqtdt,fstrcntqtnc,scndrcntqtdt,scndrcntqtnc,trdrcntqtdt,trdrcntqtnc,fthrcntqtdt,fthrcntqtnc) values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (s, n, m, netcom, roe, diEPS, per, pbr, ocf, icf, fcf, toteqt, totcap, std_dt, dvd, qdl0, qtr0, qdl1, qtr1, qdl2, qtr2, qdl3, qtr3))
            conn.commit()
            cur.execute("SELECT stck_ticker from \"AIS\".stck_mtdt_"+m.lower()+" order by stck_id desc")
            lastone = cur.fetchone()[0]
            if s == lastone:
                json_list[stocks.index(s)]['Status'] = 1
                with open("stcklist/"+m+".json", "w", encoding='utf-8') as json_file:
                    json.dump(json_list, json_file, ensure_ascii=False)
                    
        cur.execute('select stck_ticker from \"AIS\".stck_mtdt_' + m + ' where stck_ticker = \'' + json_list[i]['Symbol'] +'\'')
        try:
            tmp = cur.fetchone()[0]
        except TypeError:
            tmp = cur.fetchone()
            
        if json_list[i]['Status'] < 0 and tmp == json_list[i]['Symbol']:       # 기존 DB의 더 이상 유용하지 않은 데이터 삭제
            cur.execute('delete from \"AIS\".stck_mtdt_' + m.lower() + ' where stck_ticker = ' + json_list[i]['Symbol'])
            conn.commit()

markets = ['NYSE', 'NASDAQ', 'KOSPI', 'TSE']
for m in markets:
    with open("stcklist/"+m+".json", "r", encoding='utf-8') as json_file:
        json_list = json.load(json_file)
    stocks = list(map(lambda x : x['Symbol'], json_list))
    commiting(stocks, m, json_list)