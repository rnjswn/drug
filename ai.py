import os
from openai import OpenAI
import dur  # dur.py에서 데이터 조회

api_key = os.environ.get("GROQ_API_KEY")
client = OpenAI(api_key=api_key)

def get_ai_summary(drug_names: list[str]):
    context_lines = []
    
    # 1. [엄격] DB에 있는 영양소 정보만 수집
    for drug in drug_names:
        nutri = dur.check_nutrient_data(drug)
        if nutri['found']:
            # DB에 있는 내용만 그대로 텍스트로 변환
            depletion = ", ".join(nutri['depletion'])
            avoid = ", ".join(nutri['avoid'])
            foods = ", ".join(nutri['foods'])
            
            # 정보가 비어있지 않은 경우에만 기록
            info_parts = []
            if depletion: info_parts.append(f"결핍 영양소: {depletion}")
            if avoid: info_parts.append(f"피해야 할 것: {avoid}")
            if foods: info_parts.append(f"추천 음식: {foods}")
            
            if info_parts:
                context_lines.append(f"- {drug}: {', '.join(info_parts)}")
        
        # else: DB에 없으면 아예 언급하지 않음 (사용자 요청 사항 반영)

    # 2. [엄격] DB에 있는 상호작용 정보만 수집
    import itertools
    if len(drug_names) >= 2:
        for a, b in itertools.combinations(drug_names, 2):
            inter = dur.check_interaction_pair(a, b)
            if inter['status'] == 'DANGER':
                context_lines.append(f"- [주의] {a}와 {b} 병용 시: {inter['content']}")

    # 수집된 데이터가 하나도 없는 경우 처리
    if not context_lines:
        return "선택하신 약물에 대한 분석 데이터가 데이터베이스에 없습니다."

    context_text = "\n".join(context_lines)

    # 3. 프롬프트: "DB 내용만 예쁘게 말해줘"
    system_prompt = """
    당신은 데이터베이스의 정보를 사용자에게 전달하는 'AI 약사'입니다.
    
    [절대 규칙]
    1. **오직 제공된 [분석 데이터]에 있는 사실만 말하세요.** 2. 데이터에 없는 내용은 절대 지어내거나 외부 상식을 덧붙이지 마세요.
    3. 말투는 "~해요", "~예요"체를 사용하여 부드럽게 요약해 주세요.
    4. 출력 형식은 아래 두 가지로 분류해 주세요.
       
        AI 요약
       - (가장 필요한 영양소가 있다면 추천)
       - (음식 섭취 가이드 요약)
       
        주의할 점
       - (피해야 할 음식이나 행동, 병용 금기 사항이 있다면 작성)
    """
    
    user_prompt = f"""
    [분석 데이터]
    {context_text}
    
    위 데이터를 기반으로 사용자 리포트를 작성해줘.
    """

    try:
        response = client.chat.completions.create(
            # [수정됨] 모델명을 Groq에서 무료로 제공하는 고성능 모델(Llama-3)로 변경
            model="llama3-8b-8192", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5 # 창의성을 낮춰서(0.5) 팩트 위주로 말하게 설정
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 분석 실패: {str(e)}"
