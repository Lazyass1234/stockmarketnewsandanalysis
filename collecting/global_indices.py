from bs4 import BeautifulSoup
from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument("disable-gpu")
driver = webdriver.Chrome('chromedriver', chrome_options=options)

# 천원당 환율
exchangeindices = 'https://finance.naver.com/marketindex/exchangeList.naver'
driver.get(exchangeindices)
htmltxtidx = driver.page_source
bs = BeautifulSoup(htmltxtidx, 'html.parser')

usd = bs.find('a', {'href' : "/marketindex/exchangeDetail.naver?marketindexCd=FX_USDKRW"}).find_parent().find_next_sibling().text
usd = usd.replace(',','')
eur = bs.find('a', {'href' : "/marketindex/exchangeDetail.naver?marketindexCd=FX_EURKRW"}).find_parent().find_next_sibling().text
eur = eur.replace(',','')
jpy = bs.find('a', {'href' : "/marketindex/exchangeDetail.naver?marketindexCd=FX_JPYKRW"}).find_parent().find_next_sibling().text
jpy = jpy.replace(',','')
gbp = bs.find('a', {'href' : "/marketindex/exchangeDetail.naver?marketindexCd=FX_GBPKRW"}).find_parent().find_next_sibling().text
gbp = gbp.replace(',','')

# 각국 중앙은행 금리
interestrates = 'https://tradingeconomics.com/country-list/interest-rate'
driver.get(interestrates)
htmltxtitrst = driver.page_source
bs = BeautifulSoup(htmltxtitrst, 'html.parser')
usi = bs.find('a', {'href' : "/united-states/interest-rate"}).find_parent().find_next_sibling().text
eui = bs.find('a', {'href' : '/euro-area/interest-rate'}).find_parent().find_next_sibling().text
jpi = bs.find('a', {'href' : '/japan/interest-rate'}).find_parent().find_next_sibling().text
gbi = bs.find('a', {'href' : '/united-kingdom/interest-rate'}).find_parent().find_next_sibling().text
kri = bs.find('a', {'href' : '/south-korea/interest-rate'}).find_parent().find_next_sibling().text

# 원유 금 은
oilandgold = 'https://finance.naver.com/marketindex/?tabSel=gold#tab_section'
driver.get(oilandgold)
htmltxtoag = driver.page_source
bs = BeautifulSoup(htmltxtoag, 'html.parser')
brent = bs.find('a', {'href' : "/marketindex/worldOilDetail.naver?marketindexCd=OIL_BRT&fdtc=2"}).find_parent().find_next_siblings()[1].text
brent = brent.replace(',','')
wti = bs.find('a', {'href' : "/marketindex/worldOilDetail.naver?marketindexCd=OIL_CL&fdtc=2"}).find('span', {'class' : "value"}).text
wti = wti.replace(',','')
dubai = bs.find('a', {'href' : "/marketindex/worldOilDetail.naver?marketindexCd=OIL_DU&fdtc=2"}).find_parent().find_next_siblings()[1].text
dubai = dubai.replace(',','')
gold = bs.find('a', {'href' : "/marketindex/worldGoldDetail.naver?marketindexCd=CMDT_GC&fdtc=2"}).find('span', {'class' : "value"}).text
gold = gold.replace(',','')
silver = bs.find('a', {'href' : "/marketindex/worldGoldDetail.naver?marketindexCd=CMDT_SI&fdtc=2"}).find_parent().find_next_siblings()[1].text
silver = silver.replace(',','')

# 쌀 밀
riceandwheat = 'https://finance.naver.com/marketindex/?tabSel=materials#tab_section'
driver.get(riceandwheat)
htmltxtraw = driver.page_source
bs = BeautifulSoup(htmltxtraw, 'html.parser')
rice = bs.find('a', {'href' : "/marketindex/materialDetail.naver?marketindexCd=CMDT_RR"}).find_parent().find_parent().find('td', {'class' : "num"}).text
rice = rice.replace(',','')
wheat = bs.find('a', {'href' : "/marketindex/materialDetail.naver?marketindexCd=CMDT_W"}).find_parent().find_parent().find('td', {'class' : "num"}).text
wheat = wheat.replace(',','')

import psycopg2
conn = psycopg2.connect(host="localhost", dbname="postgres", user="postgres", password="220602", port=5432)
cur = conn.cursor()

query = 'insert into "AIS".global_indices(dollar, euro, yen, pound, us_interest, europe_interest, japan_interest, england_interest, korea_interest, brent, wti, dubai, gold, silver, rice, wheat) values '
query += '(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
print([usd, eur, jpy, gbp, usi, eui, jpi, gbi, kri, brent, wti, dubai, gold, silver, rice, wheat])
cur.execute(query, [usd, eur, jpy, gbp, usi, eui, jpi, gbi, kri, brent, wti, dubai, gold, silver, rice, wheat])
conn.commit()