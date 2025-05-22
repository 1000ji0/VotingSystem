import streamlit as st
from collections import defaultdict, Counter # Counter 추가
import pandas as pd # pandas 추가
import random # 동률 처리 시 무작위 선택을 위해 추가

# CSS 스타일 정의 (기존과 동일)
page_bg = """
<style>
body {
    background-color: #ffe0b3 !important;
}
.center-button button {
    display: block;
    margin: 4rem auto;
    font-size: 2.5rem !important;
    padding: 2rem 4rem !important;
    background-color: #ff944d !important;
    color: white !important;
    border: none !important;
    border-radius: 15px !important;
    cursor: pointer;
    font-weight: bold !important;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
}
.center-button button:hover {
    background-color: #e07b39 !important;
    transform: scale(1.1) !important;
}
h1.title {
    text-align: center;
    font-size: 4em !important;
    color: #ff6600 !important;
}
.progress-text {
    text-align: center;
    font-size: 1.2em !important;
    color: #333 !important;
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

# --- Colab 방식 투표 계산 함수들 ---

def calculate_borda_colab_style(votes, candidates):
    """
    Colab 방식 보르다 계산:
    - 각 투표자의 순위 값을 그대로 사용 (1순위=1점, 2순위=2점...).
    - 각 후보의 순위 값 합계가 가장 *작은* 후보가 승자.
    - Streamlit의 votes 구조: votes[voter]['rank'] = {후보명: 순위값}
    """
    option_ranking_sum = {c: 0 for c in candidates}

    if not votes or not candidates:
        return {}, []

    for voter_data in votes.values():
        # voter_data['rank']는 {후보: 순위} 형태
        for candidate_name, rank_value in voter_data['rank'].items():
            if candidate_name in option_ranking_sum:
                try: # rank_value가 숫자인지 확인
                    option_ranking_sum[candidate_name] += int(rank_value) # 순위 값 자체를 더함
                except (ValueError, TypeError):
                    # 숫자가 아닌 경우 오류를 로깅하거나 기본값 처리 (예: 건너뛰기)
                    # st.warning(f"경고: {voter_data}의 {candidate_name} 순위({rank_value})가 숫자가 아닙니다.")
                    pass # 또는 특정 값으로 처리


    if not option_ranking_sum:
        return {}, []

    valid_scores = [s for s in option_ranking_sum.values() if isinstance(s, (int, float))]
    if not valid_scores: # 모든 점수가 유효하지 않으면
         # 모든 후보의 점수가 0이거나 유효하지 않은 경우, 동점 처리 또는 빈 결과 반환
        if all(s == 0 for s in option_ranking_sum.values()):
            return option_ranking_sum, list(candidates) # 모든 후보를 동점자로 반환
        return {}, []


    try:
        min_sum_rank = min(valid_scores) # 유효한 점수 중에서 최소값 찾기
        winners = [c for c, s in option_ranking_sum.items() if s == min_sum_rank and isinstance(s, (int, float))]
    except ValueError: # valid_scores가 비어있을 때 발생 가능
        return {}, []

    return option_ranking_sum, winners


def calculate_bentham_colab_style(votes, candidates):
    """
    Colab 방식 벤담 계산 (Streamlit의 기존 벤담과 유사):
    - 각 투표자가 후보에게 부여한 'score' (선호도 점수)를 합산.
    - 총점이 가장 *높은* 후보가 승자.
    - Streamlit의 votes 구조: votes[voter]['score'] = {후보명: 점수값}
    """
    option_scores = {c: 0 for c in candidates}

    if not votes or not candidates:
        return {}, []

    for voter_data in votes.values():
        for candidate_name, score_value in voter_data['score'].items():
            if candidate_name in option_scores:
                try:
                    option_scores[candidate_name] += float(score_value)
                except (ValueError, TypeError):
                    # st.warning(f"경고: {voter_data}의 {candidate_name} 점수({score_value})가 숫자가 아닙니다.")
                    pass


    if not option_scores:
        return {}, []
    
    valid_scores = [s for s in option_scores.values() if isinstance(s, (int, float))]
    if not valid_scores:
        if all(s == 0 for s in option_scores.values()):
            return option_scores, list(candidates)
        return {}, []


    try:
        max_total_score = max(valid_scores)
        winners = [c for c, s in option_scores.items() if s == max_total_score and isinstance(s, (int, float))]
    except ValueError: # valid_scores가 비어있을 때
        return {}, []
        
    return option_scores, winners


def calculate_nash_colab_style(votes, candidates):
    """
    Colab 방식 내쉬 계산:
    - 각 후보에 대해, 모든 투표자가 부여한 'score'를 *곱함*.
    - 곱한 값이 가장 *높은* 후보가 승자.
    - 주의: 점수 중 0이 있으면 전체 곱이 0이 됨. Colab 코드에는 이 처리 없음.
           여기서는 0점일 경우 매우 작은 값(0.00001)으로 대체.
    """
    option_multiplication_score = {c: 1.0 for c in candidates} # 곱셈이므로 1.0으로 초기화

    if not votes or not candidates:
        return {}, []

    for voter_data in votes.values():
        for candidate_name, score_value in voter_data['score'].items():
            if candidate_name in option_multiplication_score:
                try:
                    current_score = float(score_value) # 명시적 float 변환
                    if current_score == 0:
                        option_multiplication_score[candidate_name] *= 0.00001 
                    else:
                        option_multiplication_score[candidate_name] *= current_score
                except (ValueError, TypeError):
                    # st.warning(f"경고: {voter_data}의 {candidate_name} 점수({score_value})가 숫자가 아닙니다. 곱셈에서 제외합니다.")
                    # 곱셈에 영향을 주지 않도록 1을 곱하거나, 해당 투표자의 이 후보 점수는 무시
                    pass # option_multiplication_score[candidate_name] *= 1 
    
    if not option_multiplication_score:
        return {}, []

    valid_scores = [s for s in option_multiplication_score.values() if isinstance(s, (int, float))]
    if not valid_scores:
        # 모든 후보의 점수가 1.0 (초기값)이거나 유효하지 않은 경우
        if all(abs(s - 1.0) < 1e-9 for s in option_multiplication_score.values()): # 초기값 그대로인 경우
            return option_multiplication_score, list(candidates) # 모든 후보 동점 처리
        return {}, []

    try:
        max_multiplied_score = max(valid_scores)
        winners = [c for c, s in option_multiplication_score.items() if isinstance(s, (int, float)) and abs(s - max_multiplied_score) < 1e-9]
    except ValueError:
        return {}, []

    return option_multiplication_score, winners


def calculate_condorcet_colab_style(votes, candidates):
    """
    Colab 방식 콩도르세 계산:
    - 모든 후보 쌍에 대해 (A, B) 대결.
    - 각 대결에서 투표자의 *1순위 선택*만을 기준으로 승자 결정.
      (A를 1순위로 뽑은 사람 수 vs B를 1순위로 뽑은 사람 수)
    - 각 pairwise 대결의 승자들을 모아, 가장 많이 등장한(이긴) 후보가 최종 승자.
    - Streamlit의 votes 구조: votes[voter]['rank'] = {후보명: 순위값}
    """
    if len(candidates) < 2 or not votes:
        return {c: 0 for c in candidates}, []

    pairwise_matchups = []
    for i in range(len(candidates)):
        for j in range(len(candidates)): 
            if i == j:
                continue
            pairwise_matchups.append((candidates[i], candidates[j]))

    colab_style_pairwise_winners_list = []

    for c1, c2 in pairwise_matchups: 
        c1_as_first_choice_count = 0
        c2_as_first_choice_count = 0

        for voter_name, voter_data in votes.items(): # voter_name 추가 (디버깅용)
            ranks = voter_data.get('rank', {}) 
            if not ranks: continue 

            current_voter_first_choices = []
            # rank 값이 숫자인지 확인 후 처리
            valid_ranks = {cand: r_val for cand, r_val in ranks.items() if isinstance(r_val, (int, float))}
            if not valid_ranks: continue

            min_rank_val = min(valid_ranks.values()) # 유효한 순위 중 최소값

            for candidate, rank_val in valid_ranks.items():
                if rank_val == min_rank_val and rank_val == 1 : # 1순위인 후보들
                    current_voter_first_choices.append(candidate)
            
            if len(current_voter_first_choices) == 1:
                first_choice_candidate = current_voter_first_choices[0]
                if first_choice_candidate == c1:
                    c1_as_first_choice_count += 1
                elif first_choice_candidate == c2:
                    c2_as_first_choice_count += 1
        
        if c1_as_first_choice_count > c2_as_first_choice_count:
            colab_style_pairwise_winners_list.append(c1)
        elif c2_as_first_choice_count > c1_as_first_choice_count:
            colab_style_pairwise_winners_list.append(c2)

    if not colab_style_pairwise_winners_list:
        return {c: 0 for c in candidates}, []

    winner_counts = Counter(colab_style_pairwise_winners_list)
    
    if not winner_counts: 
        return {c: 0 for c in candidates}, []

    max_wins = 0
    if winner_counts: # Counter가 비어있지 않다면
        try:
            max_wins = winner_counts.most_common(1)[0][1] 
        except IndexError: # most_common(1)이 비어있는 리스트를 반환할 경우 (이론상 발생 안 함)
            return {c:0 for c in candidates}, []


    final_winners = [cand for cand, count in winner_counts.items() if count == max_wins]
    
    display_scores = {c: winner_counts.get(c, 0) for c in candidates}
    
    return display_scores, final_winners


# --- 메인 애플리케이션 로직 ---

if 'stage' not in st.session_state:
    st.session_state.stage = "home"
    # 애플리케이션 처음 로드 시 또는 세션 초기화 시 필요한 값들 설정
    st.session_state.title = ""
    st.session_state.candidates = []
    st.session_state.voters = []
    st.session_state.votes = {}
    st.session_state.completed = {}
    st.session_state.current_voter = None
    st.session_state.method_display_name = None
    st.session_state.method_internal = None


# 홈 화면
if st.session_state.stage == "home":
    st.markdown("<h1 class='title'>💚 모두의 투표 💚</h1>", unsafe_allow_html=True)
    st.markdown("<div class='center-button'>", unsafe_allow_html=True)
    if st.button("Start", key="start_button_main", help="투표를 시작하려면 클릭하세요"):
        st.session_state.stage = "setup"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True) # 이 라인까지는 Start 버튼 관련
    
    # --- 여기부터 들여쓰기 수정 ---
    st.markdown("---") # 이 라인의 들여쓰기가 if 문과 같은 레벨이거나, div 밖으로 나와야 함.
                      # 일반적으로 if 블록 내부에 있으므로, if와 같은 레벨이거나 한 단계 안쪽.
                      # 여기서는 if 블록 내에 있으므로, if 아래 다른 요소들과 같은 들여쓰기.
    st.markdown("""
## 모두의투표: 당신의 선택, 우리의 미래

### ❓모두의투표가 뭔가요❓  
모두의투표는 여러 가지 방법으로 공정하게 투표할 수 있는 서비스입니다.<br>
동료들과 점심 메뉴 정하기, 팀장 선출, 회사 워크숍 장소 결정 등<br>
일상의 크고 작은 선택부터 중요한 의사결정까지 모두 활용할 수 있어요.<br>
단순히 "찬성, 반대"로만 결정하는 것이 아니라, 다양한 의견을 골고루 반영해서<br>
더 공평한 결과를 만들어냅니다.

#### ⚠️ **주의사항** ⚠️  
🔺 이 서비스는 다양한 투표 방식을 경험하기 위한 목적으로 제작되었습니다.<br>
🔺 이 서비스는 실제 투표 시스템이 아니며, 결과에 대한 책임을 지지 않습니다.<br>
🔺 원활한 결과 비교를 위해 **후보자와 투표자 모두 3명 이상**으로 설정해주세요.<br>
🔺 투표 결과는 방식에 따라 동률이 나올 수 있습니다.<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;동률 발생 시, 제공되는 타이브레이킹 옵션을 사용하거나<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;다른 투표 방식의 결과를 참고할 수 있습니다.

## 4가지 투표 방법을 소개할게요

#### 🏆 보르다 방식  
**"순위 숫자의 합이 가장 작은 후보가 승리!"**<br>
각 투표자가 후보들에게 매긴 순위값(1위=1점, 2위=2점...)을 모두 더합니다.<br>
이 합계가 가장 **작은** 후보가 선택됩니다.<br>
- 장점: 모든 순위가 결과에 반영됩니다.<br>
- 단점: 전통적인 보르다(높은 순위에 높은 점수)와는 반대 방식입니다.

#### ⚖️ 내쉬 방식  
**"모든 투표자의 선호도 점수를 곱해서 최대화!"**<br>
각 후보에 대해 모든 투표자가 부여한 선호도 점수(0~10점)를 곱합니다.<br>
이 곱한 값이 가장 **큰** 후보가 선택됩니다. (0점은 계산 시 0.00001로 처리)<br>
- 장점: 만장일치에 가까운 강한 선호를 가진 후보에게 유리할 수 있습니다.<br>
- 단점: 한 명이라도 0점에 가까운 점수를 주면 전체 곱이 매우 작아질 수 있습니다.

#### 🥊 콩도르세 방식  
**"1순위 대결에서 가장 많이 이긴 후보는?"**<br>
모든 후보들을 두 명씩 짝지어 가상 대결을 합니다.<br>
각 대결에서는 투표자들이 해당 후보들 중 누구를 **1순위**로 선택했는지만 비교합니다.<br>
이렇게 pairwise 대결에서 가장 많은 승리를 한 후보가 선택됩니다.<br>
- 장점: 다수결 원칙을 pairwise에 적용합니다.<br>
- 단점: 전체 순위를 고려하지 않고 1순위만 보며,<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;콩도르세 패러독스(순환) 발생 시 Colab 코드의 로직에 따릅니다.

#### 💯 벤담 방식  
**"모든 선호도 점수의 총합이 가장 큰 후보!"**<br>
각 투표자가 각 후보에게 부여한 선호도 점수(0~10점)를 모두 합산합니다.<br>
이 총합이 가장 **큰** 후보가 선택됩니다.<br>
- 장점: 선호도의 강도를 직접적으로 반영합니다.<br>
- 단점: 소수의 강한 선호가 다수의 약한 선호를 압도할 수 있습니다.

### ❓ 왜 이런 투표 시스템이 필요할까요 ❓  
일반적인 "찬성/반대" 투표만으로는 복잡한 문제를 해결하기 어려워요.<br>
모두의투표는 이런 점에서 도움이 됩니다:<br>
- 🤝 더 공정한 결정: 소수의 의견도 무시하지 않고 다양한 생각을 반영할 수 있어요.<br>
- 🗳️ 더 많은 참여: 투명하고 공정한 방식으로 모든 사람의 목소리를 들어요.<br>
- 🎯 복잡한 문제 해결: 여러 사람이 함께 결정할 때 최적의 해답을 도출할 수 있어요.<br>
- 📚 배움의 기회: 다양한 투표 방식을 체험하면서 민주주의와 선택의 본질을 고민할 수 있어요.

**💡 지금 모두의투표에서 공정하고 다양한 방식의 의사결정을 직접 경험해보세요!** <br>
#### 💬 문의 및 피드백은 [이곳](mailto:cj8442@naver.com)
""", unsafe_allow_html=True)

# 투표 설정
elif st.session_state.stage == "setup":
    st.title("🗳️ 투표 설정하기")

    # 투표 주제 입력
    st.session_state.title = st.text_input(
        "투표 주제",
        value=st.session_state.get("title", ""), 
        placeholder="예: 점심 메뉴 선택", 
        help="진행할 투표의 제목을 입력해주세요."
    )

    # 후보 목록 입력
    candidate_input_value = ",".join(st.session_state.get("candidates", []))
    candidate_input = st.text_input(
        "후보 목록 (쉼표로 구분)",
        value=candidate_input_value, 
        placeholder="예: 피자, 햄버거, 파스타",
        help="투표할 후보들을 쉼표(,)로 구분하여 입력해주세요. 최소 2명 이상이어야 합니다."
    )

    # 투표자 목록 입력
    voter_input_value = ",".join(st.session_state.get("voters", []))
    voter_input = st.text_input(
        "투표자 목록 (쉼표로 구분)",
        value=voter_input_value, 
        placeholder="예: 홍길동, 김영희, 이철수",
        help="투표에 참여할 사람들의 이름을 쉼표(,)로 구분하여 입력해주세요. 최소 1명 이상이어야 합니다."
    )

    if st.button("설정 완료하고 투표 시작", key="setup_complete_button"):
        current_title = st.session_state.title # 버튼 클릭 시점의 값 사용
        
        candidates = [x.strip() for x in candidate_input.split(",") if x.strip()]
        voters = [x.strip() for x in voter_input.split(",") if x.strip()]
        
        error_messages = []
        if not current_title.strip(): 
            error_messages.append("투표 주제를 입력하세요.")
        
        if not candidate_input.strip(): 
            error_messages.append("후보 목록을 입력하세요.")
        elif len(candidates) < 2: # Colab 방식 콩도르세 등은 최소 2명 필요
            error_messages.append("최소 2명의 후보를 입력하세요.")
        elif len(set(candidates)) != len(candidates):
            error_messages.append("후보 이름은 중복될 수 없습니다.")
        
        if not voter_input.strip(): 
            error_messages.append("투표자 목록을 입력하세요.")
        elif len(voters) < 1: # 최소 투표자 수 (필요시 2명 이상으로 조정 가능)
            error_messages.append("최소 1명의 투표자를 입력하세요.")
        elif len(set(voters)) != len(voters):
            error_messages.append("투표자 이름은 중복될 수 없습니다.")
        
        if error_messages:
            for msg in error_messages:
                st.error(msg)
        else:
            st.session_state.title = current_title # 최종 확정된 값으로 세션 상태 업데이트
            st.session_state.candidates = candidates
            st.session_state.voters = voters
            st.session_state.votes = {
                voter: {
                    'rank': {c: (idx + 1) for idx, c in enumerate(candidates)}, 
                    'score': {c: 5 for c in candidates} 
                } for voter in voters
            }
            st.session_state.completed = {voter: False for voter in voters}
            st.session_state.stage = "vote_select"
            st.rerun()
# 🔼🔼🔼 이 윗부분까지 수정합니다 🔼🔼🔼

# 투표자 선택
elif st.session_state.stage == "vote_select":
    st.title(f"🔒 {st.session_state.get('title', '비밀 투표')} / 투표자 선택")
    # title이 비어있으면 기본 제목 사용
    page_title = st.session_state.get('title',"").strip()
    if not page_title: page_title = "비밀 투표"


    completed_count = sum(1 for v_name, v_status in st.session_state.completed.items() if v_status)
    total_voters = len(st.session_state.voters)
    st.markdown(f"<p class='progress-text'>투표 진행: {completed_count}/{total_voters} 완료</p>", unsafe_allow_html=True)
    
    remaining_voters = [v for v in st.session_state.voters if not st.session_state.completed.get(v, False)]
    
    if not remaining_voters and total_voters > 0 : # 투표자가 있고, 남은 투표자가 없을 때
        st.success("모든 투표자의 입력이 완료되었습니다!")
        if st.button("결과 산출 방식 선택으로 이동", key="go_to_method_select"):
            st.session_state.stage = "method_select"
            st.rerun()
    elif total_voters == 0:
        st.warning("설정된 투표자가 없습니다. 설정 화면으로 돌아가 투표자를 추가해주세요.")
    else:
        voter = st.selectbox("투표할 사람을 선택하세요.", remaining_voters, key=f"voter_select_{st.session_state.stage}")
        if st.button(f"{voter} (으)로 투표 시작하기", key=f"start_vote_for_{voter}"):
            st.session_state.current_voter = voter
            # 현재 투표자의 rank와 score가 없으면 기본값으로 초기화 (setup에서 이미 처리)
            if voter not in st.session_state.votes:
                 st.session_state.votes[voter] = {
                    'rank': {c: (idx + 1) for idx, c in enumerate(st.session_state.candidates)}, 
                    'score': {c: 5 for c in st.session_state.candidates} 
                }
            elif 'rank' not in st.session_state.votes[voter] or not st.session_state.votes[voter]['rank']:
                st.session_state.votes[voter]['rank'] = {c: (idx + 1) for idx, c in enumerate(st.session_state.candidates)}
            elif 'score' not in st.session_state.votes[voter] or not st.session_state.votes[voter]['score']:
                 st.session_state.votes[voter]['score'] = {c: 5 for c in st.session_state.candidates}

            st.session_state.stage = "vote_input"
            st.rerun()

    if st.button("투표 설정으로 돌아가기", key="back_to_setup_from_voter_select"):
        st.session_state.stage = "setup"
        st.rerun()

# 순위 입력
elif st.session_state.stage == "vote_input":
    if not st.session_state.current_voter: # current_voter가 없으면 vote_select로 보냄
        st.warning("투표자를 먼저 선택해주세요.")
        st.session_state.stage = "vote_select"
        st.rerun() # rerun을 해야 st.warning이 제대로 표시되고 이동함
        
    voter = st.session_state.current_voter
    st.title(f"🗳️ {voter}님, 투표를 진행해주세요.")
    st.subheader(f"투표 주제: {st.session_state.get('title', '')}")

    st.markdown("#### 🔢 순위 입력 (Colab 보르다/콩도르세 방식에 사용)")
    st.markdown("각 후보에 대해 선호하는 순위를 입력해주세요 (1위가 가장 선호). **각 후보는 고유한 순위를 가져야 합니다.**")
    
    ranks_data = st.session_state.votes[voter]['rank']
    
    current_ranks_input = {}
    # 후보 목록이 변경되었을 수 있으므로 st.session_state.candidates 기준으로 루프
    for candidate_name_loop in st.session_state.candidates:
        current_ranks_input[candidate_name_loop] = st.number_input(
            f"{candidate_name_loop}의 순위", 
            min_value=1, 
            max_value=len(st.session_state.candidates), 
            value=int(ranks_data.get(candidate_name_loop, 1)), # int로 변환하여 오류 방지
            step=1, 
            key=f"rank_{candidate_name_loop}_{voter}"
        )

    if st.button("순위 입력 완료 → 점수 입력으로 이동", key="rank_to_score_button"):
        rank_values = list(current_ranks_input.values())
        if len(set(rank_values)) != len(st.session_state.candidates): # 모든 후보에 대해 순위가 매겨졌고, 중복 없는지
            st.error("각 후보는 고유한 순위를 가져야 하며, 모든 후보의 순위가 입력되어야 합니다. (1부터 후보자 수까지의 숫자가 모두 사용되어야 함)")
        elif len(rank_values) != len(st.session_state.candidates):
             st.error("모든 후보에 대한 순위를 입력해야 합니다.")
        else:
            st.session_state.votes[voter]['rank'] = current_ranks_input
            st.session_state.stage = "score_input"
            st.rerun()
    
    if st.button("이전 단계 (투표자 선택)으로 돌아가기", key="back_to_voter_select_from_rank"):
        st.session_state.stage = "vote_select"
        st.rerun()

# 점수 입력
elif st.session_state.stage == "score_input":
    if not st.session_state.current_voter:
        st.warning("투표자를 먼저 선택해주세요.")
        st.session_state.stage = "vote_select"
        st.rerun()

    voter = st.session_state.current_voter
    st.title(f"📊 {voter}님, 각 후보에 대한 선호 점수를 입력해주세요.")
    st.subheader(f"투표 주제: {st.session_state.get('title', '')}")

    st.markdown("#### 💯 선호 점수 입력 (Colab 벤담/내쉬 방식에 사용)")
    st.markdown("각 후보에 대해 얼마나 선호하는지 점수를 매겨주세요 (0점 ~ 10점, 높을수록 선호). **점수는 중복될 수 있습니다.**")
    
    scores_data = st.session_state.votes[voter]['score'] 

    sorted_candidates_by_rank = sorted(
        st.session_state.candidates, 
        key=lambda c: st.session_state.votes[voter]['rank'].get(c, float('inf'))
    )

    current_scores_input = {}
    for candidate_name_loop in sorted_candidates_by_rank:
        rank_for_display = st.session_state.votes[voter]['rank'].get(candidate_name_loop, 'N/A')
        current_scores_input[candidate_name_loop] = st.number_input(
            f"{candidate_name_loop} (입력 순위: {rank_for_display}위)의 점수", 
            min_value=0, 
            max_value=10, 
            value=int(scores_data.get(candidate_name_loop, 5)), # int로 변환
            step=1, 
            key=f"score_{candidate_name_loop}_{voter}" 
        )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 순위 다시 입력하기", key="score_to_rank_button"):
            st.session_state.votes[voter]['score'] = current_scores_input # 현재까지 입력한 점수 임시 저장
            st.session_state.stage = "vote_input"
            st.rerun()
    with col2:
        if st.button(f"{voter}님의 투표 제출하기 ➡️", key="submit_vote_button"):
            st.session_state.votes[voter]['score'] = current_scores_input
            st.session_state.completed[voter] = True
            st.success(f"{voter}님의 투표가 성공적으로 제출되었습니다!")
            # import time; time.sleep(1) # UX를 위해 짧은 지연 후 이동 (선택적)
            st.session_state.current_voter = None # 현재 투표자 초기화
            st.session_state.stage = "vote_select"
            st.rerun()

# 투표 방식 선택
elif st.session_state.stage == "method_select":
    st.title("🧠 투표 결과 산출 방식 선택")
    st.subheader(f"투표 주제: {st.session_state.get('title', '')}")
    method_options = ["보르다 (Colab)", "벤담 (Colab)", "내쉬 (Colab)", "콩도르세 (Colab)"]
    
    # 이전에 선택한 방식이 있으면 기본값으로 설정
    current_method_display = st.session_state.get("method_display_name", method_options[0])
    default_index = 0
    if current_method_display in method_options:
        default_index = method_options.index(current_method_display)

    method = st.radio(
        "결과를 보고 싶은 투표 방식을 선택하세요:", 
        method_options, 
        index=default_index,
        key="method_radio_select",
        help="Colab 코드 기반의 계산 방식을 사용합니다."
    )
    
    if method == "보르다 (Colab)": st.info("보르다 (Colab): 각 후보에게 매긴 순위값(1위=1)의 총합이 가장 '작은' 후보 선택.")
    elif method == "벤담 (Colab)": st.info("벤담 (Colab): 각 후보에게 매긴 선호도 점수(0~10)의 총합이 가장 '큰' 후보 선택.")
    elif method == "내쉬 (Colab)": st.info("내쉬 (Colab): 각 후보에 대한 모든 투표자의 선호도 점수를 '곱한' 값이 가장 '큰' 후보 선택 (0점은 0.00001로 처리).")
    elif method == "콩도르세 (Colab)": st.info("콩도르세 (Colab): 모든 후보쌍 대결 시 '1순위' 투표만 고려, 가장 많은 pairwise 승리를 한 후보 선택.")

    if st.button("선택한 방식으로 결과 보기", key="view_results_button"):
        st.session_state.method_display_name = method 
        if method == "보르다 (Colab)": st.session_state.method_internal = "borda_colab"
        elif method == "벤담 (Colab)": st.session_state.method_internal = "bentham_colab"
        elif method == "내쉬 (Colab)": st.session_state.method_internal = "nash_colab"
        elif method == "콩도르세 (Colab)": st.session_state.method_internal = "condorcet_colab"
        st.session_state.stage = "result"
        st.rerun()
    
    if st.button("이전 단계 (투표자 선택)으로 돌아가기", key="back_to_voter_select_from_method"):
        st.session_state.stage = "vote_select"
        st.rerun()

# 결과 출력
elif st.session_state.stage == "result":
    st.title(f"🏆 투표 결과: {st.session_state.get('title', '')}")
    method_display = st.session_state.get("method_display_name", "N/A")
    method_internal = st.session_state.get("method_internal", "N/A")
    st.subheader(f"✔ 선택된 방식: {method_display}")
    
    # candidates_list 와 votes_data_dict가 존재하는지 먼저 확인
    if 'candidates' not in st.session_state or 'votes' not in st.session_state:
        st.error("후보 또는 투표 정보가 설정되지 않았습니다. 설정 화면으로 돌아가세요.")
        if st.button("설정 화면으로 돌아가기", key="result_to_setup_error"):
            st.session_state.stage = "setup"
            st.rerun()
        st.stop() # 더 이상 진행하지 않음

    candidates_list = st.session_state.candidates
    votes_data_dict = st.session_state.votes
    
    scores_output = {}
    winners_list = []
    df_column_name = "점수" 

    if not votes_data_dict or not candidates_list:
        st.error("투표 데이터 또는 후보 정보가 없습니다. 설정을 다시 확인해주세요.")
    else:
        try:
            if method_internal == "borda_colab":
                scores_output, winners_list = calculate_borda_colab_style(votes_data_dict, candidates_list)
                df_column_name = "보르다 순위합 (작을수록 좋음)"
            elif method_internal == "bentham_colab":
                scores_output, winners_list = calculate_bentham_colab_style(votes_data_dict, candidates_list)
                df_column_name = "벤담 총점 (클수록 좋음)"
            elif method_internal == "nash_colab":
                scores_output, winners_list = calculate_nash_colab_style(votes_data_dict, candidates_list)
                df_column_name = "내쉬 곱셈점수 (클수록 좋음)"
            elif method_internal == "condorcet_colab":
                scores_output, winners_list = calculate_condorcet_colab_style(votes_data_dict, candidates_list)
                df_column_name = "콩도르세 Pairwise 승수 (1순위 기반)"
            else:
                st.error("선택된 투표 방식이 유효하지 않습니다.") # 혹시 모를 경우
                scores_output, winners_list = {}, []


            # --- 동률 처리 로직 강화 ---
            if winners_list:
                if len(winners_list) > 1:
                    st.warning(f"동률 발생 ({method_display}): {', '.join(winners_list)}")
                    
                    tie_break_options = ["동점자 모두 인정", "후보 이름 가나다 순 (첫번째)", "무작위 선택"]
                    # 다른 방식 결과 참조는 복잡도 증가로 일단 제외, 필요시 추가
                    
                    # 이전에 선택한 타이브레이킹 옵션 기억 (선택적)
                    # selected_tie_break = st.session_state.get(f"tie_break_for_{method_internal}", tie_break_options[0])
                    # selected_tie_break_idx = tie_break_options.index(selected_tie_break) if selected_tie_break in tie_break_options else 0

                    tie_break_choice = st.radio( # selectbox 대신 radio로 한 번에 보이게
                        "동률 처리 방안을 선택하세요:",
                        tie_break_options,
                        # index=selected_tie_break_idx,
                        key=f"tie_break_radio_{method_internal}"
                    )
                    # st.session_state[f"tie_break_for_{method_internal}"] = tie_break_choice # 선택 기억

                    final_single_winner_display = None
                    if tie_break_choice == "후보 이름 가나다 순 (첫번째)":
                        final_single_winner_display = sorted(winners_list)[0]
                        st.success(f"타이브레이킹 ({tie_break_choice}) 최종 승자: {final_single_winner_display}")
                    elif tie_break_choice == "무작위 선택":
                        # 무작위 선택은 매번 바뀔 수 있음을 명시하거나, seed 고정 고려
                        final_single_winner_display = random.choice(winners_list)
                        st.success(f"타이브레이킹 ({tie_break_choice}) 최종 승자: {final_single_winner_display} (새로고침 시 변경될 수 있음)")
                    elif tie_break_choice == "동점자 모두 인정":
                        st.info("동점자 모두 최종 결과로 인정합니다.")
                
                else: # 단독 승자
                    st.success(f"🎉 {method_display} 최종 승자: {winners_list[0]}")
            
            elif isinstance(scores_output, dict) and scores_output: 
                 st.warning(f"{method_display} 방식으로는 명확한 승자를 결정할 수 없습니다 (예: 모든 후보 점수가 동일하거나 데이터 부족).")
            else: 
                st.error("결과를 계산할 수 없습니다. 투표 데이터를 확인해주세요.")

            if isinstance(scores_output, dict) and scores_output:
                df_data = [{"후보": c, df_column_name: s} for c, s in scores_output.items()]
                if df_data:
                    df = pd.DataFrame(df_data)
                    ascending_sort = (method_internal == "borda_colab")
                    try:
                        df_sorted = df.sort_values(by=df_column_name, ascending=ascending_sort)
                        st.dataframe(df_sorted.set_index("후보"), use_container_width=True)
                    except KeyError: # df_column_name이 df에 없을 경우 (거의 발생 안 함)
                        st.error(f"결과 표시 중 오류: '{df_column_name}' 컬럼을 찾을 수 없습니다.")
                        st.dataframe(df.set_index("후보") if "후보" in df.columns else df, use_container_width=True) # 정렬 없이 표시
                else:
                    st.info("결과 데이터가 없습니다.")
            elif not winners_list : # scores_output도 없고 winners_list도 없을때 (위에서 이미 처리되었을 수 있음)
                st.info("계산된 점수 데이터가 없습니다.")


        except Exception as e:
            st.error(f"결과 계산 중 오류 발생 ({method_display}): {e}")
            st.exception(e) # 개발 시 상세 오류 확인용

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 다른 방식으로 결과 보기", key="back_to_method_select_from_result"):
            st.session_state.stage = "method_select"
            st.rerun()
    with col2:
        if st.button("🔄 처음부터 다시하기 (모든 데이터 초기화)", key="reset_all_from_result"):
            # 세션 상태 초기화 (필요한 최소한의 것만 남기거나, 특정 키들만 삭제)
            for key in list(st.session_state.keys()):
                if key not in ['rerun_count']: # Streamlit 내부 키나 유지하고 싶은 키 제외
                    del st.session_state[key]
            st.session_state.stage = "home" # stage는 home으로 재설정
            st.rerun()