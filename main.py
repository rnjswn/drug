from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import itertools
import dur 

app = FastAPI()

# ✅ [추가됨] 접속 테스트용 대문 (브라우저 접속 시 404 방지)
@app.get("/")
def read_root():
    return {"status": "ONLINE", "message": "DUR 분석 서버가 정상 작동 중입니다."}

# == 요청 모델 정의 ==
class MultiDrugRequest(BaseModel):
    drug_names: List[str]  # 예: ["타이레놀", "이소티논"]

class SingleDrugRequest(BaseModel):
    drug_name: str         # 예: "메트포르민"

# 1. [다중 약물] 상호작용 검사 API
@app.post("/check/interaction")
def api_check_interaction(request: MultiDrugRequest):
    drugs = request.drug_names
    warnings = []
    
    # 약이 2개 이상일 때만 조합 검사
    if len(drugs) >= 2:
        pairs = list(itertools.combinations(drugs, 2))
        for a, b in pairs:
            res = dur.check_interaction_pair(a, b)
            if res.get("status") == "DANGER":
                warnings.append(res)

    #'warnings' 리스트가 비어있으면 안전, 있으면 위험으로 처리
    return {
        "count": len(warnings),
        "results": warnings
    }

# 2. [단일 약물] 영양소/음식 분석 API 
@app.post("/check/nutrient")
def api_check_nutrient(request: SingleDrugRequest):
    result = dur.check_nutrient_data(request.drug_name)

    return result
