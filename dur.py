import requests
import re
from urllib.parse import unquote  # ✅ [추가] 키 디코딩 도구

# ==========================================
# 설정 및 API 키
# ==========================================
SERVICE_KEY = '5WH0LHB3CqNWF/SNt1NnxsTOxNIsAoqvl22JTUQS3EN/N3D+yXGcLCgfwFKX9qGLRgDJMTTKMUbHVokec8WxKA=='
URL_SEARCH = 'http://apis.data.go.kr/1471000/MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03'
URL_DUR = 'https://apis.data.go.kr/1471000/DURIrdntInfoService03/getUsjntTabooInfoList02'

NUTRIENT_DB = {
    # 1. 만성질환
    '메트포르민': {
        'depletion': ['비타민 B12', '엽산(B9)', '코엔자임Q10'],
        'avoid': ['과도한 음주 (젖산 산증 위험)'],
        'foods': ['조개', '굴', '계란', '소고기', '시금치']
    },
    '글리메피리드': {
        'depletion': ['코엔자임Q10'],
        'avoid': ['음주 (저혈당 쇼크 위험)'],
        'foods': ['고등어', '정어리', '땅콩', '브로콜리']
    },
    '글리클라지드': {
        'depletion': ['코엔자임Q10'],
        'avoid': ['음주'],
        'foods': ['고등어', '정어리', '땅콩']
    },
    '아토르바스타틴': {
        'depletion': ['코엔자임Q10'],
        'avoid': ['자몽 주스 (약물 농도 증가 독성 위험)'],
        'foods': ['소고기', '닭고기', '고등어', '두부']
    },
    '심바스타틴': {
        'depletion': ['코엔자임Q10'],
        'avoid': ['자몽 주스 (절대 금기)'],
        'foods': ['소고기', '닭고기', '고등어', '두부']
    },
    '로수바스타틴': {
        'depletion': ['코엔자임Q10'],
        'avoid': ['자몽 주스 (주의)'],
        'foods': ['소고기', '닭고기', '고등어']
    },
    '로바스타틴': {
        'depletion': ['코엔자임Q10'],
        'avoid': ['자몽 주스'],
        'foods': ['소고기', '등푸른 생선']
    },
    '프라바스타틴': {
        'depletion': ['코엔자임Q10'],
        'avoid': ['자몽 주스'],
        'foods': ['소고기', '등푸른 생선']
    },
    '아테놀롤': {
        'depletion': ['코엔자임Q10', '멜라토닌'],
        'avoid': [],
        'foods': ['체리(멜라토닌)', '호두', '소고기']
    },
    '비소프롤롤': {
        'depletion': ['코엔자임Q10', '멜라토닌'],
        'avoid': [],
        'foods': ['체리', '토마토', '등푸른 생선']
    },
    '프로프라놀롤': {
        'depletion': ['코엔자임Q10', '멜라토닌'],
        'avoid': [],
        'foods': ['체리', '바나나', '소고기']
    },
    '암로디핀': {
        'depletion': ['칼륨', '칼슘', '비타민 D'],
        'avoid': ['자몽 주스 (약효 과다 발현 위험)'],
        'foods': ['우유', '버섯', '바나나', '고구마']
    },
    '니페디핀': {
        'depletion': ['칼슘', '비타민 D'],
        'avoid': ['자몽 주스'],
        'foods': ['멸치', '치즈', '연어']
    },
    '푸로세미드': {
        'depletion': ['마그네슘', '칼륨', '아연', '비타민 B1(티아민)', '비타민 B6'],
        'avoid': ['과도한 나트륨(소금)'],
        'foods': ['바나나', '토마토', '감자', '돼지고기(B1)', '굴']
    },
    '히드로클로로티아지드': {
        'depletion': ['마그네슘', '칼륨', '아연', '코엔자임Q10'],
        'avoid': ['음주 (혈압 급강하 위험)'],
        'foods': ['바나나', '시금치', '아몬드']
    },

    # 2. 통증 및 염증
    '이부프로펜': {
        'depletion': ['엽산(B9)', '비타민 C', '철분'],
        'avoid': ['공복 복용 (위장 출혈 위험)', '음주'],
        'foods': ['키위', '브로콜리', '붉은 살코기', '깻잎']
    },
    '덱시부프로펜': {
        'depletion': ['엽산', '비타민 C', '철분'],
        'avoid': ['공복 복용', '음주'],
        'foods': ['키위', '오렌지', '소고기']
    },
    '나프록센': {
        'depletion': ['엽산', '비타민 C', '철분'],
        'avoid': ['공복 복용', '음주'],
        'foods': ['딸기', '시금치', '선지']
    },
    '세레콕시브': {
        'depletion': ['엽산', '비타민 C', '철분'],
        'avoid': [],
        'foods': ['녹색 잎채소', '감귤류']
    },
    '아스피린': {
        'depletion': ['비타민 C', '칼슘', '철분', '엽산', '칼륨'],
        'avoid': ['음주 (위장 출혈 위험 증가)'],
        'foods': ['피망', '우유', '멸치', '바나나']
    },
    '아세트아미노펜': {
        'depletion': ['글루타치온 (간 해독 효소)'],
        'avoid': ['음주 (심각한 간 손상/독성 유발)', '과다 복용'],
        'foods': ['마늘', '양파', '아스파라거스', '아보카도', '브로콜리']
    },
    '프레드니솔론': {
        'depletion': ['칼슘', '비타민 D', '마그네슘', '아연', '칼륨', '비타민 C'],
        'avoid': ['나트륨 (부종 악화)'],
        'foods': ['우유', '연어', '아몬드', '바나나', '굴']
    },
    '덱사메타손': {
        'depletion': ['칼슘', '비타민 D', '마그네슘', '칼륨'],
        'avoid': ['짠 음식'],
        'foods': ['치즈', '고구마', '견과류']
    },
    '콜키신': {
        'depletion': ['비타민 B12', '마그네슘', '베타카로틴'],
        'avoid': ['자몽 주스', '음주'],
        'foods': ['조개', '다시마', '당근', '호박']
    },

    # 3. 소화기계
    '오메프라졸': {
        'depletion': ['비타민 B12', '마그네슘', '칼슘', '철분'],
        'avoid': [],
        'foods': ['조개', '김', '아몬드', '멸치', '소고기']
    },
    '에스오메프라졸': {
        'depletion': ['비타민 B12', '마그네슘', '칼슘', '철분'],
        'avoid': [],
        'foods': ['조개', '시금치', '두부']
    },
    '라베프라졸': {
        'depletion': ['비타민 B12', '마그네슘', '칼슘'],
        'avoid': [],
        'foods': ['해조류', '견과류', '유제품']
    },
    '파모티딘': {
        'depletion': ['비타민 B12', '비타민 D', '엽산'],
        'avoid': [],
        'foods': ['생선', '계란', '버섯']
    },

    # 4. 정신신경계 및 뇌전증
    '에스시탈로프람': {
        'depletion': ['멜라토닌', '비타민 B2', '비타민 B6', '비타민 B12', '엽산'],
        'avoid': ['음주 (약효 증폭 및 부작용)'],
        'foods': ['체리', '돼지고기', '닭고기', '바나나']
    },
    '플루니트라제팜': {
        'depletion': ['멜라토닌', '비타민 D', '엽산'],
        'avoid': ['음주 (호흡 억제 위험)', '자몽 주스'],
        'foods': ['체리', '연어', '시금치']
    },
    '트리아졸람': {
        'depletion': ['멜라토닌', '비타민 B군'],
        'avoid': ['자몽 주스', '음주'],
        'foods': ['우유', '현미', '콩']
    },
    '발프로산': {
        'depletion': ['비오틴(B7)', '비타민 D', '칼슘', '엽산', '카르니틴'],
        'avoid': ['임의 중단 금지'],
        'foods': ['계란 노른자(비오틴)', '버섯', '우유', '소고기']
    },
    '카바마제핀': {
        'depletion': ['비오틴', '비타민 D', '칼슘', '엽산'],
        'avoid': ['자몽 주스'],
        'foods': ['콩', '연어', '치즈', '녹색 채소']
    },
    '가바펜틴': {
        'depletion': ['비타민 B12', '비타민 D', '엽산'],
        'avoid': ['제산제 (동시 복용 시 흡수 저해, 2시간 간격 필요)'],
        'foods': ['조개', '계란', '브로콜리']
    },

    # 5. 기타
    '에티닐에스트라디올': {
        'depletion': ['비타민 B2', '비타민 B6', '비타민 B12', '엽산', '마그네슘', '아연', '셀레늄'],
        'avoid': ['흡연 (혈전 위험 급증)'],
        'foods': ['바나나', '참치', '굴', '견과류', '통곡물']
    },
    '미노사이클린': {
        'depletion': ['유산균(프로바이오틱스)', '비타민 K', '비타민 B군', '아연', '마그네슘', '칼슘'],
        'avoid': ['우유/유제품 (약 흡수 방해, 2시간 간격 섭취)', '제산제'],
        'foods': ['김치/요거트(약 복용 후 섭취)', '녹색 채소(비타민K)', '굴']
    },
    '아목시실린': {
        'depletion': ['유산균', '비타민 K'],
        'avoid': [],
        'foods': ['발효 식품', '브로콜리']
    },
    '이소트레티노인': {
        'depletion': ['비타민 B12', '엽산', '비타민 D'],
        'avoid': ['비타민 A 보충제 (비타민 A 독성 중복 위험)', '임신(기형 유발)'],
        'foods': ['조개', '버섯', '계란']
    },
    '알렌드로네이트': {
        'depletion': ['칼슘', '마그네슘', '인'],
        'avoid': ['커피/카페인 (칼슘 배출)', '복용 직후 눕기(식도염 위험)'],
        'foods': ['우유', '치즈', '멸치', '두부', '아몬드']
    },
    '와파린': {
        'depletion': [],
        'avoid': ['비타민 K 과다 섭취 주의(녹즙, 청국장, 콩물 등 - 약효 감소)', '크랜베리 주스'],
        'foods': ['(일정한 식단 유지 중요)']
    }
}

# [주의] 위 NUTRIENT_DB에 님 원본 데이터가 다 들어가 있어야 합니다!

# ==========================================
# 도구 함수
# ==========================================
def clean_drug_name(name):
    if not name: return ""
    name = re.sub(r'\(.*?\)', '', name)
    garbage_list = ['고체분산체', '염산염', '장용정', '서방정', '캡슐', '정', '연질', '수화물', '타르타르산염']
    for garbage in garbage_list:
        name = name.replace(garbage, '')
    return name.strip()

def get_ingredient_api(drug_name):
    # ✅ [수정] unquote 적용 및 timeout 추가
    params = {
        'serviceKey': unquote(SERVICE_KEY), 
        'pageNo': '1', 
        'numOfRows': '1', 
        'type': 'json', 
        'item_name': drug_name
    }
    try:
        # 5초 안에 응답 없으면 끊기
        res = requests.get(URL_SEARCH, params=params, timeout=5)
        items = res.json().get('body', {}).get('items', [])
        if items:
            full_name = items[0].get('ITEM_NAME', '')
            match = re.search(r'\((.*?)\)', full_name)
            if match: return match.group(1)
            else: return clean_drug_name(full_name)
        return clean_drug_name(drug_name)
    except Exception as e:
        print(f"API Error ({drug_name}): {e}") # 로그 출력
        return drug_name

# ==========================================
# [기능 1] 상호작용 체크
# ==========================================
def check_interaction_pair(drug_A, drug_B):
    clean_A = clean_drug_name(get_ingredient_api(drug_A))
    clean_B = clean_drug_name(get_ingredient_api(drug_B))
    
    # ✅ [수정] unquote 적용 및 timeout 추가
    params = {
        'serviceKey': unquote(SERVICE_KEY), 
        'pageNo': '1', 
        'numOfRows': '100', 
        'type': 'json', 
        'ingrKorName': clean_A
    }
    
    try:
        # DUR 서버는 느릴 수 있으니 10초 대기
        res = requests.get(URL_DUR, params=params, timeout=10)
        items = res.json().get('body', {}).get('items', [])
        
        if items:
            for item in items:
                real_data = item.get('item') if 'item' in item else item
                taboo_name = real_data.get('MIXTURE_INGR_KOR_NAME', '')
                taboo_clean = clean_drug_name(taboo_name)
                
                if taboo_clean and (clean_B in taboo_clean or taboo_clean in clean_B):
                    return {
                        "status": "DANGER",
                        "pair": [drug_A, drug_B],
                        "cause": f"{real_data.get('INGR_KOR_NAME')} + {taboo_name}", 
                        "content": real_data.get('PROHBT_CONTENT')
                    }
        return {"status": "SAFE"}
    except Exception as e:
        print(f"DUR API Error: {e}") # 로그 출력
        return {"status": "ERROR", "msg": str(e)}

# ==========================================
# [기능 2] 영양소 체크
# ==========================================
def check_nutrient_data(drug_name):
    # 여기에도 API 호출이 있으니 간접적으로 영향 받음 (get_ingredient_api 사용)
    ingr = clean_drug_name(get_ingredient_api(drug_name))
    info = NUTRIENT_DB.get(ingr)
    
    if info:
        return {
            "found": True,
            "ingredient": ingr,
            "depletion": info['depletion'],
            "avoid": info['avoid'],
            "foods": info['foods']
        }
    else:
        return {
            "found": False,
            "ingredient": ingr
        }
