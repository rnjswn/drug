from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import itertools
import dur
import ai

app = FastAPI()

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
    results = []

    if len(drugs) >= 2:
        pairs = list(itertools.combinations(drugs, 2))
        for a, b in pairs:
            res = dur.check_interaction_pair(a, b)
            results.append(res)

    return {
        "count": len(results),
        "results": results
    }

# 2. [단일 약물] 영양소/음식 분석 API 
@app.post("/check/nutrient")
def api_check_nutrient(request: SingleDrugRequest):
    result = dur.check_nutrient_data(request.drug_name)

    return result

@app.get("/search/drug")
def api_search_drug(query: str):
    return {
        "query": query,
        "results": dur.search_drug_names(query)
    }

# 3. AI 요약 API 추가
@app.post("/check/ai-summary")
def api_check_ai_summary(request: MultiDrugRequest):
    summary_text = ai.get_ai_summary(request.drug_names)
    
    return {
        "status": "SUCCESS",
        "ai_message": summary_text
    }
