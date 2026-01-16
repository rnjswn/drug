import requests
import re
from urllib.parse import unquote
import json

try:
    from dur_db import MANUAL_INGR_MAP, NUTRIENT_DB
except ImportError:
    MANUAL_INGR_MAP = {}
    NUTRIENT_DB = {}

# ==========================================
# 1. 설정 및 API 키
# ==========================================
SERVICE_KEY = '5WH0LHB3CqNWF/SNt1NnxsTOxNIsAoqvl22JTUQS3EN/N3D+yXGcLCgfwFKX9qGLRgDJMTTKMUbHVokec8WxKA=='
URL_SEARCH = 'http://apis.data.go.kr/1471000/MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03'
URL_DUR = 'https://apis.data.go.kr/1471000/DURIrdntInfoService03/getUsjntTabooInfoList02'

def clean_drug_name(name: str) -> str:
    if not name:
        return ""

    name = re.sub(r'\(.*?\)', '', name)
    name = re.sub(
        r'\d+(\.\d+)?\s*(mg|㎎|mcg|μg|ug|g|그램|밀리그램|밀리그람|밀리그렘|마이크로그램|%|단위|IU|UI)?',
        '',
        name,
        flags=re.IGNORECASE
    )
    garbage_list = [
        '타르타르산염', '브롬화수소산염', '메탄설폰산염', '메실산염', '베실산염', '캄실산염',
        '아세테이트', '푸마르산염', '나파디실산염', '시트르산염', '석신산염', '숙신산염',
        '염산염', '황산염', '인산염', '질산염', '말레산염', '탄산염', '오로트산염',
        '나트륨', '칼륨', '칼슘', '마그네슘', '수화물', '무수물', '고체분산체',
        '필름코팅정', '연질캡슐', '경질캡슐', '서방정', '장용정', '구강붕해정',
        '현탁액', '현탁정', '점안액', '점이액', '스프레이', '나잘스프레이',
        '시럽', '캡슐', '패치', '좌제', '과립', '세립', '분말', '정제',
        '이알', '8시간', '엑스', '틴크', '유동', '건조',
        '주', '액', '정', '산', '전', '후'
    ]
    garbage_list.sort(key=len, reverse=True)

    for g in garbage_list:
        name = name.replace(g, '')

    name = re.sub(r'[.,]', '', name)
    name = re.sub(r'\s+', ' ', name)

    return name.strip()

def get_ingredient_api(drug_name):
    params = {
        'serviceKey': unquote(SERVICE_KEY), 
        'pageNo': '1', 
        'numOfRows': '1', 
        'type': 'json', 
        'item_name': drug_name
    }
    
    try:
        res = requests.get(URL_SEARCH, params=params, timeout=5)
        if res.status_code == 200:
            items = res.json().get('body', {}).get('items', [])
            if items:
                item = items[0]
                class_name = item.get('CLASS_NAME', '기타 약물')
                
                real_ingr = item.get('MAIN_ITEM_INGR') or item.get('INGR_NAME')
                if real_ingr:
                    first_ingr = re.split(r'[|,\+]', real_ingr)[0]
                    return {"name": first_ingr, "category": class_name}
                
                match = re.search(r'\((.*?)\)', item.get('ITEM_NAME', ''))
                if match:
                    return {"name": match.group(1), "category": class_name}
    except Exception as e:
        print(f"API Error: {e}")

    if drug_name in MANUAL_INGR_MAP:
        return {"name": MANUAL_INGR_MAP[drug_name], "category": "일반의약품(수동)"}
    
    clean_input = clean_drug_name(drug_name)
    if clean_input in MANUAL_INGR_MAP:
         return {"name": MANUAL_INGR_MAP[clean_input], "category": "일반의약품(수동)"}

    return {"name": clean_drug_name(drug_name), "category": "알 수 없음"}

def check_interaction_pair(drug_A, drug_B):
    try:
        info_A = get_ingredient_api(drug_A)
        info_B = get_ingredient_api(drug_B)

        clean_A = clean_drug_name(info_A['name'])
        clean_B = clean_drug_name(info_B['name'])

        params = {
            'serviceKey': unquote(SERVICE_KEY),
            'pageNo': '1',
            'numOfRows': '100',
            'type': 'json',
            'ingrKorName': clean_A
        }

        res = requests.get(URL_DUR, params=params, timeout=10)
        items = res.json().get('body', {}).get('items', [])

        if items:
            for item in items:
                real = item.get('item', item)
                taboo = clean_drug_name(real.get('MIXTURE_INGR_KOR_NAME', ''))

                if taboo and (clean_B in taboo or taboo in clean_B):
                    return {
                        "status": "DANGER",
                        "pair": [drug_A, drug_B],
                        "cause": f"{real.get('INGR_KOR_NAME')} + {real.get('MIXTURE_INGR_KOR_NAME')}",
                        "content": real.get('PROHBT_CONTENT')
                    }

        return {"status": "SAFE"}

    except Exception as e:
        return {"status": "ERROR", "msg": str(e)}

def check_nutrient_data(drug_name):
    api_result = get_ingredient_api(drug_name)
    raw_ingr = api_result['name']
    category_name = api_result['category']
    cleaned_ingr = clean_drug_name(raw_ingr)
    

    target_info = None
    final_ingr_name = raw_ingr 

    if cleaned_ingr in NUTRIENT_DB:
        target_info = NUTRIENT_DB[cleaned_ingr]
        final_ingr_name = cleaned_ingr
    
    elif raw_ingr in NUTRIENT_DB:
        target_info = NUTRIENT_DB[raw_ingr]
        final_ingr_name = raw_ingr
        
    elif raw_ingr.replace(" ", "") in NUTRIENT_DB:
        target_info = NUTRIENT_DB[raw_ingr.replace(" ", "")]
        final_ingr_name = raw_ingr.replace(" ", "")

    if target_info:
        return {
            "found": True,
            "ingredient": final_ingr_name,           
            "category": target_info.get('category', category_name),
            "depletion": target_info.get('depletion', []),
            "avoid": target_info.get('avoid', []),
            "foods": target_info.get('foods', [])
        }
    else:
        return {
            "found": False,
            "ingredient": raw_ingr,                   
            "category": category_name
        }
