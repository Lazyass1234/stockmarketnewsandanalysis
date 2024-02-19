from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
import datetime
import psycopg2
import os
conn = psycopg2.connect(host="localhost", dbname="postgres",
                        user="postgres", password="220602", port=5432)
cur = conn.cursor()

# set1 = (883978,'KO','/news/stock-market-news/article-883978', '인포스탁데일리')
# set2 = (884519,'KO','/news/stock-market-news/article-884519', '인포스탁데일리')
# set3 = (884554,'KO','/news/stock-market-news/article-884554', '인포스탁데일리')
# set4 = (885085,'KO','/news/stock-market-news/article-885085', '인포스탁데일리')

# cur.execute('insert into "AIS".news (id, lang, href, source) values (%s,%s,%s,%s)', set1)
# cur.execute('insert into "AIS".news (id, lang, href, source) values (%s,%s,%s,%s)', set2)
# cur.execute('insert into "AIS".news (id, lang, href, source) values (%s,%s,%s,%s)', set3)
# cur.execute('insert into "AIS".news (id, lang, href, source) values (%s,%s,%s,%s)', set4)

# conn.commit()

addrdict = {'EN': 'https://www.investing.com',
            'KO': 'https://kr.investing.com', 'JA': 'https://jp.investing.com'}

options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument("disable-gpu")
options.add_argument('--blink-settings=imagesEnabled=false')
options.add_argument("--log-level=3")
driver = webdriver.Chrome('chromedriver', options=options)


def getdatetime(lc, lang):
    monlist = ['Jan', 'Feb', 'Mar', 'Apr', 'May',
               'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    if lang == 'EN':
        try:
            month, dd, yy, tt, tz = lc.select('.contentSectionDetails')[0].find(
                'span').text.split('(')[1][:-1].split(' ')
        except:
            month, dd, yy, tt, tz = lc.select('.contentSectionDetails')[
                0].find('span').text.split(' ')
        mm = monlist.index(month)+1
        if 'PM' in tt:
            hh, m = tt[:-2].split(':')
            hh = int(hh)+12
        elif 'AM' in tt and tt[:2] == '12':
            hh = '00'
            m = tt[:-2].split(':')[1]
        else:
            hh, m = tt[:-2].split(':')
        # dt = yy+'-'+mm+'-'+dd[:-1]+' '+hh+':'+m
        if tz == 'ET':
            dt = datetime.datetime(year=int(yy), month=mm, day=int(
                dd[:-1]), hour=int(hh), minute=int(m))
            dt = dt+datetime.timedelta(hours=14)
    elif lang == 'KO':
        try:
            yy, mm, dd, tt = lc.select('.contentSectionDetails')[0].find(
                'span').text.split('(')[1][:-1].split(' ')
        except:
            yy, mm, dd, tt = lc.select('.contentSectionDetails')[
                0].find('span').text.split(' ')
        dt = yy[:-1]+'-'+mm[:-1]+'-'+dd[:-1]+' '+tt+':00'
    else:
        try:
            ymd, tt = lc.select('.contentSectionDetails')[0].find(
                'span').text.split('(')[1][:-1].split(' ')
        except:
            ymd, tt = lc.select('.contentSectionDetails')[
                0].find('span').text.split(' ')
        dt = ymd[0:4]+'-'+ymd[5:7]+'-'+ymd[8:10]+' '+tt+':00'
    return dt


def getscndrid(cur):
    cur.execute('select id from "AIS".news order by id')
    scndrid = cur.fetchone()[0]
    return 0 if scndrid > 0 else scndrid


for addr in addrdict.values():
    driver.get(addr+'/news/latest-news')
    htmltxtidx = driver.page_source
    bs = BeautifulSoup(htmltxtidx, 'html.parser')
    lang = bs.select('html')[0].attrs['lang'].upper()
    titles = bs.select('.largeTitle')[0].contents
    for t in titles:
        try:
            id = t.attrs['data-id']
            href = t.contents[3].contents[1].attrs['href']
            if 'cryptocurrency' in href:  # 암호화폐 안함
                continue
            # if 'general' in href:         # 종합지 일단 할지 안할지 고민중
            #     continue
            source = t.contents[3].contents[3].contents[0].text[3:]
            if lang == 'JA':              # 왜 앞에 빈칸? 빈칸 지우는 용
                source = source[1:]
            # source와 Ban List 비교해 보고 일치하지 않으면 그때 execute 하도록
            if source == 'Economic Review' or source == 'The Stock':
                continue
            cur.execute(
                'insert into "AIS".news (id, lang, href, source) values (%s,%s,%s,%s)', (id, lang, href, source))
        except:
            pass
    conn.commit()

cur.execute('select id, lang, href, source from "AIS".news where title is NULL')
#cur.execute('select id, lang, href, source from "AIS".news where title is NULL and lang = \'JA\' and source = \'Fisco\'')
proyet = cur.fetchall()
for p in proyet:
    id, lang, href, source = p
    addr = addrdict[lang]
    driver.get(addr + href)
    htmltxtidx = driver.page_source
    bs = BeautifulSoup(htmltxtidx, 'html.parser')
    lc = bs.select('#leftColumn')[0]
    title = lc.select('.articleHeader')[0].text
    if '특징주' in title or '안재광의 대기만성' in title or '主食이 주식' in title:                  # 장투 목적이니 특징주 기사 컷, 긴 칼럼도
        cur.execute('delete from "AIS".news where id = %s', [id])
        conn.commit()
        continue
    dt = getdatetime(lc, lang)
    rawpglist = lc.select('[class = "WYSIWYG articlePage"]')[0]
    pglist = rawpglist.findChildren('p', recursive=False)
    pglist = list(map(lambda pg: pg.text, pglist))
    if lang == 'EN':
        ### 영어 공통 ###
        if 'By' in pglist[0]:
            pglist = pglist[1:]
        for i in range(len(pglist)):
            if '--' in pglist[i]:
                pglist[i] = pglist[i].replace('--', '- ')
            if u'\xa0' in pglist[i]:
                pglist[i] = pglist[i].replace(u'\xa0', ' ')
            if '  ' in pglist[i]:
                pglist[i] = pglist[i].replace('  ', ' ')
            if '    ' in pglist[i]:
                pglist[i] = pglist[i].replace('    ', ' ')
            try:
                if pglist[i][0] == ' ':
                    pglist[i] = pglist[i][1:]
            except:
                pass
            ### 영어 공통 ###
        if source == 'Reuters':  # 로이터
            delist = []
            for i in range(len(pglist)):
                # p 태그 중 없거나 빈칸이거나 \t이거나 마지막거일 경우
                if pglist[i] == '' or pglist[i] == ' ' or pglist[i] == '    ' or 'has been refiled' in pglist[i]:
                    delist.append(i)
            delist.reverse()
            for dl in delist:
                del pglist[dl]
            if 'Reuters' in pglist[0]:
                try:
                    pglist[0] = pglist[0].split('Reuters) - ')[1]
                except:
                    pglist[0] = pglist[0].split('Reuters) -')[1]
            if 'Marketmind' in title or 'Market Mind' in title:  # 특집: 'Marketmind'
                nolist = []
                for i in range(len(pglist)):
                    if 'look at the day ahead' in pglist[i] or 'https://' in pglist[i] or 'http://' in pglist[i]:
                        nolist.append(i)
                    elif 'ey development' in pglist[i]:
                        nolist.append(i)
                        break
                pglist = pglist[nolist.pop(0)+1:nolist.pop(-1)]
                if len(nolist) != 0:
                    for n in nolist:
                        del pglist[n]
        elif source == 'Investing.com':  # 인베스팅닷컴
            if 'Investing.com' in pglist[0]:
                pglist[0] = pglist[0].replace('–','-')
                try:
                    pglist[0] = pglist[0].split('-  ')[1]
                except:
                    pglist[0] = pglist[0].split('- ')[1]
        cntnt = '***'.join(pglist)
        cur.execute(
            'update "AIS".news set title = %s, bfr = %s, datetime = %s where id = %s', (title, cntnt, dt, id))
    elif lang == 'KO':
        if source == 'Hankyung':
            for i in range(len(pglist)):
                if '@hankyung.com' in pglist[i]:
                    pglist = pglist[:i]
                    break
                elif '\n' in pglist[i]:
                    pglist[i] = pglist[i].replace('\n', ' ')
                if '--' in pglist[i]:
                    pglist[i] = pglist[i].replace('--', '- ')
                if u'\xa0' in pglist[i]:
                    pglist[i] = pglist[i].replace(u'\xa0', ' ')
                if '  ' in pglist[i]:
                    pglist[i] = pglist[i].replace('  ', ' ')
                if '    ' in pglist[i]:
                    pglist[i] = pglist[i].replace('    ', ' ')
                try:
                    if pglist[i][0] == ' ':
                        pglist[i] = pglist[i][1:]
                except:
                    pass
            wordlist = pglist[0].split(' ')
            for w in wordlist:
                if '사진=' in w:
                    wordlist.pop(wordlist.index(w))
            pglist[0] = ' '.join(wordlist)
            cntnt = '***'.join(pglist)
            cur.execute(
                'update "AIS".news set title = %s, bfr = %s, datetime = %s where id = %s', (title, cntnt, dt, id))
        elif source == 'MoneyS':
            for i in range(len(rawpglist.contents)):
                if rawpglist.contents[i].text == pglist[0]:
                    start = i
                elif '머니S에서 읽기' in rawpglist.contents[i].text:
                    end = i
                    break
                elif rawpglist.contents[i].text == pglist[-1]:
                    end = i
                    break
            rawpglist = rawpglist.contents[start:end]
            pglist = list(map(lambda t: t.text, rawpglist))
            for i in range(len(pglist)):
                if '\n' in pglist[i]:
                    pglist[i] = pglist[i].replace('\n', ' ')
                if '--' in pglist[i]:
                    pglist[i] = pglist[i].replace('--', '- ')
                if u'\xa0' in pglist[i]:
                    pglist[i] = pglist[i].replace(u'\xa0', ' ')
                if '  ' in pglist[i]:
                    pglist[i] = pglist[i].replace('  ', ' ')
                if '    ' in pglist[i]:
                    pglist[i] = pglist[i].replace('    ', ' ')
                try:
                    if pglist[i][0] == ' ':
                        pglist[i] = pglist[i][1:]
                except:
                    pass
            if pglist[0] == ' ':
                pglist = pglist[1:]
            pglist = list(filter(lambda pg: pg != '', pglist))
            cntnt = '***'.join(pglist)
            cur.execute(
                'update "AIS".news set title = %s, bfr = %s, datetime = %s where id = %s', (title, cntnt, dt, id))
        elif source == 'Investing.com':
            if pglist == []: #886537
                continue
            if 'By' in pglist[0]:
                pglist = pglist[1:]
            if 'Investing.com' in pglist[0]:
                pglist[0] = pglist[0].replace('–', '-')  # 하이푼 대시 차이인가?
                try:
                    pglist[0] = pglist[0].split('-  ')[1]
                except:
                    pglist[0] = pglist[0].split('- ')[1]
            if '이번 주 주목해야 할 주요 이슈 5가지' == title:  # 특집. 이거는 2차 기사로 생성해야 할 것 같음.
                cur.execute('delete from "AIS".news where id = %s', [id])
                cur.execute(
                    'select distinct href from "AIS".news where id < 0')
                if href in cur.fetchall():
                    continue
                pglist = pglist[2:-2]
                headlist = []
                for pg in pglist:
                    if pg[:2] in ['1.', '2.', '3.', '4.', '5.']:
                        headlist.append(pglist.index(pg))
                headlist.append(len(pglist))
                for hd in headlist[:-1]:
                    tmpttl = pglist[hd][3:]
                    tmpcntnt = '***'.join(pglist[hd +
                                          1:headlist[headlist.index(hd)+1]])
                    scndrid = getscndrid(cur)
                    cur.execute('insert into "AIS".news (id, lang, title, bfr, datetime, href, source) values(%s,%s,%s,%s,%s,%s,%s)',
                                (scndrid-1, lang, tmpttl, tmpcntnt, dt, href, source))
            else:
                cntnt = '***'.join(pglist)
                cur.execute(
                    'update "AIS".news set title = %s, bfr = %s, datetime = %s where id = %s', (title, cntnt, dt, id))
        elif source == '인포스탁데일리':
            if '언론사별' in title or '주요뉴스' in title:       # 합친 뉴스다?
                cur.execute('delete from "AIS".news where id = %s', [id])
                cur.execute('select distinct href from "AIS".news where id < 0')
                if href in cur.fetchall():
                    continue
                for i in range(2, len(pglist)-3, 2):                             # 두칸씩 해서 삼각형을 기준으로
                    # 삼각형 다음걸 제목
                    tmpttl = pglist[i][1:]
                    # 삼각형 아래를 본문으로 해서
                    tmpcntnt = pglist[i+1]
                    scndrid = getscndrid(cur)
                    cur.execute('insert into "AIS".news (id, lang, title, bfr, datetime, href, source) values(%s,%s,%s,%s,%s,%s,%s)',
                                (scndrid-1, lang, tmpttl, tmpcntnt, dt, href, source))

            elif '개장체크' in title:       # 개장체크다?
                cur.execute('delete from "AIS".news where id = %s', [id])
                cur.execute('select distinct href from "AIS".news where id < 0')
                if href in cur.fetchall():
                    continue
                for i in range(len(pglist)):
                    if 'infostock.co.kr' in pglist[i]:
                        pglist = pglist[0:i]
                        break
                headlist = []
                for i in range(len(pglist)):
                    if '■' in pglist[i]:
                        headlist.append(i)
                headlist.append(len(pglist))
                for hls in headlist[:-1]:
                    hle = headlist[1:][headlist.index(hls)]
                    tmpttl = pglist[hls][1:]
                    if tmpttl[0] == ' ':
                        tmpttl = tmpttl[1:]
                    if '주요 일정' in tmpttl or '주요일정' in tmpttl:
                        continue
                    tmpcntnt = '***'.join(pglist[hls+1:hle])
                    tmpcntnt = tmpcntnt.replace('● ','')
                    tmpcntnt = tmpcntnt.replace('●','')
                    scndrid = getscndrid(cur)
                    cur.execute('insert into "AIS".news (id, lang, title, bfr, datetime, href, source) values(%s,%s,%s,%s,%s,%s,%s)',
                                (scndrid-1, lang, tmpttl, tmpcntnt, dt, href, source))
            elif '시황레이더' in title:     # 시황 레이더
                cur.execute('delete from "AIS".news where id = %s', [id])
                cur.execute('select distinct href from "AIS".news where id < 0')
                if href in cur.fetchall():
                    continue
                headlist = list(map(lambda rpg: rpg.text, rawpglist.findChildren('strong')))
                delist = [] # 지울 것
                for pg in pglist:
                    if '기자]' in pg or '사진=' in pg:
                        delist.append(pglist.index(pg))
                    elif 'infostock.co.kr' in pg:
                        pglist = pglist[:pglist.index(pg)]
                        break
                delist.reverse()
                for dl in delist:
                    del pglist[dl]
                hidx = list(map(lambda hl: pglist.index(hl),headlist))
                hidx.append(len(pglist))
                for hid in hidx[:-1]:
                    tmpttl = pglist[hid]
                    tmppglist = pglist[hid+1:hidx[hidx.index(hid)+1]]
                    tmpcntnt = '***'.join(tmppglist)
                    scndrid = getscndrid(cur)
                    cur.execute('insert into "AIS".news (id, lang, title, bfr, datetime, href, source) values(%s,%s,%s,%s,%s,%s,%s)',
                                (scndrid-1, lang, tmpttl, tmpcntnt, dt, href, source))
            else:
                delist = []
                for i in range(len(pglist)):
                    if '사진=' in pglist[i] or '자료=' in pglist[i] or '사진 =' in pglist[i] or '자료 =' in pglist[i]:
                        delist.append(i)
                    elif '기자]' in pglist[i]:
                        if pglist[i][-1] == ']':
                            delist.append(i)
                        else:
                            pglist[i] = pglist[i].split('기자]')[1]
                    elif '@infostock.co.kr' in pglist[i] or '@naver.com' in pglist[i]:
                        pglist=pglist[:i]
                        break
                    if pglist[i][0] == ' ':
                        pglist[i] = pglist[i][1:]
                    
                delist.reverse()
                for dl in delist:
                    del pglist[dl]
                if '공시분석' in title:
                    pglist = pglist[1:-1]
                if '스몰캡+' in title:
                    pglist = pglist[1:]
                cntnt = '***'.join(pglist)
                cntnt = cntnt.replace('\n', '')
                cur.execute('update "AIS".news set title = %s, bfr = %s, datetime = %s where id = %s', (title, cntnt, dt, id))
    else:
        if source == "Reuters":
            delist = []
            for i in range(len(pglist)):
                if pglist[i] == '' or pglist[i] == ' ' or pglist[i] == ' ':
                    delist.append(i)
            delist.reverse()
            for dl in delist:
                del pglist[dl]
            delist = []
            for i in range(len(pglist)):
                if '\u3000' in pglist[i]:
                    pglist[i] = pglist[i].replace('\u3000', ' ')
                if 'ロイター］' in pglist[i]:
                    pglist[i] = pglist[i].split('- ')[1]
                elif 'ロイター] ' in pglist[i]:
                    pglist[i] = pglist[i].split(' - ')[1]
                try:
                    if pglist[i][0] == ' ':
                        pglist[i] = pglist[i][1:]
                except IndexError:
                    delist.append(i)
            delist.reverse()
            for dl in delist:
                del pglist[dl]
            cntnt = '***'.join(pglist)
            cur.execute('update "AIS".news set title = %s, bfr = %s, datetime = %s where id = %s', (title, cntnt, dt, id))
        elif source == "Fisco":
            link = addr + href
            pglist = rawpglist.contents
            dividx = rawpglist.findChildren('div', recursive=False)
            try:
                scridx = pglist.index(
                    rawpglist.findChild('script', recursive=False))
            except:
                scridx = 0
            try:
                start = pglist.index(dividx[0]) if len(dividx) == 2 else pglist.index(dividx[1])
            except IndexError:
                continue
            start = scridx if scridx > start else start
            last = pglist.index(dividx[-1])
            pglist = list(map(lambda pg: pg.text, pglist[start+1:last]))
            try:
                pglist[0] = pglist[0].split('JST')[1]
            except:
                pass
            if pglist[0][0] == ' ':
                pglist[0] = pglist[0][1:]
            clslist = []
            for i in range(len(pglist)):
                pglist[i] = pglist[i].replace('\n', '')
                try:
                    if pglist[i][0] == ')':
                        clslist.append(i)
                except:
                    pass
            clslist.reverse()
            for cls in clslist:
                pglist[cls-2] = ''.join(pglist[cls-2:cls+1])
                pglist[cls-1] = ''
                pglist[cls] = ''
            for i in range(len(pglist)-1,-1,-1):
                if pglist[i] == '':
                    del pglist[i]
            cntnt = '***'.join(pglist)
            cur.execute(
                'update "AIS".news set title = %s, bfr = %s, datetime = %s where id = %s', (title, cntnt, dt, id))
    conn.commit()

# google key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'dark-runway-374500-7b076182f12f.json'

# Google API 부 # 파파고 만글자, 구글 50만자.
def translate_text_with_model(target, text, model="nmt"):
    """Translates text into the target language.

    Make sure your project is allowlisted.

    Target must be an ISO 639-1 language code.
    See https://g.co/cloud/translate/v2/translate-reference#supported_languages
    """
    from google.cloud import translate_v2 as translate

    translate_client = translate.Client()

    if isinstance(text, bytes):
        text = text.decode("utf-8")

    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    result = translate_client.translate(
        text, target_language=target, model=model)

    # print(u"Text: {}".format(result["input"]))
    # print(u"Translation: {}".format(result["translatedText"]))
    # print(u"Detected source language: {}".format(result["detectedSourceLanguage"]))
    return result["translatedText"]

cur.execute('select id, lang, bfr from "AIS".news where trnsltd is null and bfr is not null')
proyet = cur.fetchall()
for p in proyet:
    id, lang, bfr = p
    print('id : ', id)
    bfrlist = bfr.split('***')
    if lang == 'KO':
        print('번역중...')
        bfrlist = list(map(lambda b: translate_text_with_model('ja', b), bfrlist))
        bfrlist = list(map(lambda b: translate_text_with_model('en', b), bfrlist))
        trnsltd = '***'.join(bfrlist)
    elif lang == 'JA':
        print('번역중...')
        bfrlist = list(map(lambda b: translate_text_with_model('en', b), bfrlist))
        trnsltd = '***'.join(bfrlist)
    else:
        trnsltd = bfr
    trnsltd = '\''.join(trnsltd.split('&#39;'))
    trnsltd = '\"'.join(trnsltd.split('&quot;'))
    trnsltd = '&'.join(trnsltd.split('&amp;'))
    trnsltd = '>'.join(trnsltd.split('&gt;'))
    trnsltd = '<'.join(trnsltd.split('&lt;'))
    cur.execute('update "AIS".news set trnsltd = %s where id = %s',[trnsltd,id])
    conn.commit()