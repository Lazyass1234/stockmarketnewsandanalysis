import datetime

import psycopg2
import yfinance as yf  # 업데이트 안하면 못쓰게 됨
# https://apiportal.koreainvestment.com/apiservice/apiservice-domestic-stock-current#L_0e9fb2ba-bbac-4735-925a-a35e08c9a790

conn = psycopg2.connect(host="localhost", dbname="postgres",
                        user="postgres", password="220602", port=5432)
cur = conn.cursor()

mrkt = ['nyse', 'nasdaq', 'kospi', 'tse']
query1 = 'select stck_ticker, stck_nm from \"AIS\".view_'
query2 = '_stck_mtdt where ocfrt + icfrt + fcfrt >= 0 and icfrt <= -0.3 and roe > 0.15 and per <= 10 and pbr >= 1 and pbr < 5 order by roe desc'
for m in mrkt:
    query = query1+m+query2
    cur.execute(query)
    # list[tuple] 여기에 튜플 형식으로 위의 조건을 만족하는 주식들의 티커 심볼들이 모일 것.
    selected = cur.fetchall()
    for s in selected:
        t = yf.Ticker(s[0])
        # t = yf.Ticker('lad')

        schema = '\"SDB\"'
        tbnm = '\"'+'daily_'+m+'_'+s[0].lower()+'\"'
        # tbnm = '\"'+'daily_'+m+'_'+'lad'.lower()+'\"'
        values = '(dt date NULL,open numeric(8,2) NULL,close numeric(8,2) NULL,high numeric(8,2) NULL,low numeric(8,2) NULL,volume int8 NULL,dividends numeric(8,2) NULL,stocksplits numeric(8,2) NULL)'
        # cur.execute('select dt from '+schema+'.'+tbnm + ' order by dt desc limit 1')
        try:  # 우선 기존 DB에 이 주식의 데이터가 있는지부터 확인
            cur.execute('select dt from '+schema+'.' +
                        tbnm + ' order by dt desc limit 1')
        except:  # 데이터가 없을 시, create table. 이후 전부 읽어서 인서트.
            conn.rollback()
            cur.execute('create table '+schema+'.'+tbnm+' '+values)
            cur.execute('insert into \"AIS\".slctd_stcks (stck_ticker, stck_nm, stck_mrkt, slctd_dt) values (%s,%s,%s,%s)',
                        (s[0], s[1], m, datetime.date.today()))
            conn.commit()
            # Open, High, Low, Close, Volume, Dividends, Stock Splits
            t_hist = t.history(period='max')
            # ['2018-01-16 00:00:00-05:00'......] 의 리스트가 나옴. Date로 갖다 넣어야지.
            t_date = t_hist.axes[0]
            for dt, open, high, low, close, volume, dividends, stocksplits in zip(t_date, t_hist['Open'], t_hist['Close'], t_hist['High'], t_hist['Low'], t_hist['Volume'], t_hist['Dividends'], t_hist['Stock Splits']):
                cur.execute('insert into '+schema+'.'+tbnm+' (dt, open, close, high, low, volume, dividends, stocksplits) values (%s,%s,%s,%s,%s,%s,%s,%s)',
                            (dt, open, high, low, close, volume, dividends, stocksplits))
            conn.commit()
        else:  # 테이블이 있을 시, 제일 최근에 등록된 로우의 날짜를 읽어 그 이후부터 다시 읽어서 인서트 하기
            lastdate = cur.fetchone()[0]  # 2023-02-08
            # 2023-02-09 이거는 프로그램이 돌아가는 당시의 시간을 의미하기는 함.
            today = datetime.date.today()
            if lastdate == None:  # 테이블만 있고 안에 값은 없을 때
                t_hist = t.history(period='max')
                t_date = t_hist.axes[0]
                for dt, open, high, low, close, volume, dividends, stocksplits in zip(t_date, t_hist['Open'], t_hist['Close'], t_hist['High'], t_hist['Low'], t_hist['Volume'], t_hist['Dividends'], t_hist['Stock Splits']):
                    cur.execute('insert into '+schema+'.'+tbnm+' (dt, open, close, high, low, volume, dividends, stocksplits) values (%s,%s,%s,%s,%s,%s,%s,%s)',
                                (dt, open, high, low, close, volume, dividends, stocksplits))
            elif lastdate == today:  # 오늘 날짜가 테이블 마지막 날짜와 동일할 때
                pass
            else:  # 값은 있는데 테이블 마지막 날짜와 오늘 날짜가 다를 때
                startdate = lastdate+datetime.timedelta(days=1)
                t_hist = t.history(start=startdate)
                t_date = t_hist.axes
                for dt, open, high, low, close, volume, dividends, stocksplits in zip(t_date, t_hist['Open'], t_hist['Close'], t_hist['High'], t_hist['Low'], t_hist['Volume'], t_hist['Dividends'], t_hist['Stock Splits']):
                    cur.execute('insert into '+schema+'.'+tbnm+' (dt, open, close, high, low, volume, dividends, stocksplits) values (%s,%s,%s,%s,%s,%s,%s,%s)',
                                (dt[0], open, high, low, close, volume, dividends, stocksplits))
            conn.commit()
        # 아무래도 시간대도 설정해서 그 차이만큼 감안해서 읽어올 날짜 범위 정하는게 맞을 듯 함.
