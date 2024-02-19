from bs4 import BeautifulSoup
from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument("disable-gpu")
driver = webdriver.Chrome('chromedriver', chrome_options=options)

urlsise = 'https://finance.naver.com/sise/'
driver.get(urlsise)
htmltxtsise = driver.page_source
bskospi = BeautifulSoup(htmltxtsise, 'html.parser')
tag = bskospi.select("#KOSPI_now.num")
tag1 = bskospi.find('span', {'id' : 'KOSPI_now', 'class' : 'num'})
kospi_idx = tag1.text.replace(',', '')

urlworld = 'https://finance.naver.com/world/'
driver.get(urlworld)
htmltxtworld = driver.page_source
bsworld = BeautifulSoup(htmltxtworld, 'html.parser')
nasdaq_idx = bsworld.find('dt', {'class' : 'dt2'}).parent.find('dd', {'class' : 'point_status'}).find('strong').text
nasdaq_idx = nasdaq_idx.replace(',','')
nikkei_idx = bsworld.find('dt', {'class' : 'dt4'}).parent.find('dd', {'class' : 'point_status'}).find('strong').text
nikkei_idx = nikkei_idx.replace(',','')

mrktidx = [kospi_idx, nasdaq_idx, nikkei_idx]
mrktnm = ['KOSPI', 'NASDAQ', 'NIKKEI']

import psycopg2
conn = psycopg2.connect(host="localhost", dbname="postgres", user="postgres", password="220602", port=5432)
cur = conn.cursor()

for i in range(3):
    query = 'update "AIS".stck_mrkt_mtdt set stck_mrkt_now_idx = '
    query += mrktidx[i]
    query += ' where stck_mrkt_nm = '
    query += '\''+mrktnm[i]+'\''
    query += '::varchar'
    print(mrktidx[i])
    print(query)
    cur.execute(query)
conn.commit()