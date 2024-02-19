# 매 불러올 때 마다 DB에 현재 코스피 나스닥 닛케이 지수 업데이트
import collecting.intl_indices

# 매 불러올 때 마다 DB에 글로벌 지수들 인서트
import collecting.global_indices

# 매 불러올 때 마다 제목이 다른 새로운 뉴스 인서트
import collecting.news

# 매 불러올 때 마다 뉴스를 평가
import collecting.score

# 매 불러올 때 마다 티커 리스트 생성 or 업데이트
import collecting.get_tickers

# 매 불러올 때 마다 새로 인서트 ( 시간 제일 오래 걸림 16000 개를 읽어야 한다고 치면 최소 80시간 )
# 근데 회사마다 fiscal year가 정해져 있으니깐 최초로 한 번 다 읽고, 그 다음에는 fiscal year가 겹치는게 많을 때 그 때마다 그 회사들만 모아서 하면 될듯?
# 거의다 월말이라서 그냥 매 월초에 읽도록 배치하면 될듯?
import collecting.stck_mtdt

# 조건에 해당하는 주식들의 히스토리 전부
import collecting.selector