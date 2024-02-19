import yfinance as yf # https://github.com/ranaroussi/yfinance
import FinanceDataReader as fdr # https://github.com/FinanceData/FinanceDataReader
import psycopg2
stocks = fdr.StockListing('NASDAQ')
stocklist = []
invact = []
finact = []
opeact = []
acts = ['Total Cashflows From Investing Activities',
 'Total Cash From Financing Activities',
 'Total Cash From Operating Activities']

for i in stocks.Symbol:
    stocklist.append(i) # for column tickersymbol
    print(i)
    tmp = yf.Ticker(i).cashflow.T[acts].sum()
    invact.append(tmp[acts[0]])
    finact.append(tmp[acts[1]])
    opeact.append(tmp[acts[2]])
    
namelist = []
for i in stocks.Name:
    namelist.append(i) # for column tickername

# 현금흐름표
#^Total.*Investing Activities$ -
#^Total.*Financing Activities$ -
#^Total.*Operating Activities$ + 위에 두 값과 이 값을 더해서 양수면 우량기업, 아니면 불안함. 근데 마소나 애플도 이 기준으론 불안함.

conn = psycopg2.connect(host="localhost", dbname="postgres", user="postgres", password="220602", port=5432)
cur = conn.cursor()

for i in range(stocklist.len()):
    cur.execute("INSERT INTO nsdq.tickers(tickersymbol, tickername, dividends, investingactivities, financingactivities, operatingactivities) values (%s,%s,%s,%s,%s,%s)",
                (stocklist[i], namelist[i], yf.Ticker(stocklist[i]).dividends, invact[i], finact[i], opeact[i])
                )
    
    """찾을 건 많음. 심볼, 이름, 배당률, 저 세 개.
    우선 쟤네들만 해서 DB 만들고,
    이후 시간 칼럼, 나스닥 칼럼, 이후 모든 종목들 티커 심볼들을 칼럼,으로 해서 지수와 종가를 모두 담기.
    이후 뉴스 채집 프로그램 만들고 뉴스 원문과 뉴스 키워드(아니면 제목)으로만 해서 긍정 부정 점수 부여. 뉴스도 경제지만 하지 말고 가능한 많은 것을 담기.
    """
    