import streamlit as st
from collections import defaultdict
import uuid

# CSS 스타일 정의
page_bg = """
<style>
body {
    background-color: #ffe0b3 !important;
}
.center-button button {
    display: block;
    margin: 4rem auto;
    font-size: 2.5rem !important; /* 버튼 텍스트 크기 */
    padding: 2rem 4rem !important; /* 버튼 패딩 */
    background-color: #ff944d !important;
    color: white !important;
    border: none !important;
    border-radius: 15px !important;
    cursor: pointer;
    font-weight: bold !important;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important; /* 그림자 효과 */
}
.center-button button:hover {
    background-color: #e07b39 !important;
    transform: scale(1.1) !important; /* 호버 시 확대 */
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

# 모든 페이지에서 CSS 적용
st.markdown(page_bg, unsafe_allow_html=True)

# 투표 계산 함수들
def calculate_borda(votes, candidates):
    scores = {c: 0 for c in candidates}
    for vote in votes.values():
        for c, s in vote['score'].items():
            scores[c] += s
    max_score = max(scores.values())
    winners = [c for c, s in scores.items() if s == max_score]
    return scores, winners

def calculate_bentham(votes, candidates):
    scores = {c: 0 for c in candidates}
    for vote in votes.values():
        for c, s in vote['score'].items():
            scores[c] += s
    total = sum(scores.values())
    util = {c: round((v / total) * 100, 2) if total > 0 else 0 for c, v in scores.items()}
    max_util = max(util.values())
    winners = [c for c, u in util.items() if u == max_util]
    return util, winners

def calculate_nash(votes, candidates):
    min_scores = {c: float('inf') for c in candidates}
    for vote in votes.values():
        for c, s in vote['score'].items():
            if s < min_scores[c]:
                min_scores[c] = s
    max_min_score = max(min_scores.values())
    winners = [c for c, s in min_scores.items() if s == max_min_score]
    return min_scores, winners

def calculate_condorcet(votes, candidates):
    wins = {c: 0 for c in candidates}
    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            a, b = candidates[i], candidates[j]
            a_wins, b_wins = 0, 0
            for vote in votes.values():
                rank = vote['rank']
                if rank[a] < rank[b]:
                    a_wins += 1
                elif rank[b] < rank[a]:
                    b_wins += 1
            if a_wins > b_wins:
                wins[a] += 1
            elif b_wins > a_wins:
                wins[b] += 1
    max_wins = max(wins.values())
    winners = [c for c, w in wins.items() if w == max_wins]
    return wins, winners

# 메인 애플리케이션
if 'stage' not in st.session_state:
    st.session_state.stage = "home"

# 홈 화면
if st.session_state.stage == "home":
    st.markdown("<h1 class='title'>💚 모두의 투표 💚</h1>", unsafe_allow_html=True)

    st.markdown("<div class='center-button'>", unsafe_allow_html=True)
    if st.button("Start", help="투표를 시작하려면 클릭하세요"):
        st.session_state.stage = "setup"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    ### 모두의투표: 당신의 선택, 우리의 미래

    #### 모두의투표가 뭔가요?
    모두의투표는 여러 가지 방법으로 공정하게 투표할 수 있는 서비스입니다. 동료들과 점심 메뉴 정하기, 팀장 선출, 회사 워크숍 장소 결정 등 일상의 크고 작은 선택부터 중요한 의사결정까지 모두 활용할 수 있어요. 단순히 "찬성, 반대"로만 결정하는 것이 아니라, 다양한 의견을 골고루 반영해서 더 공평한 결과를 만들어냅니다.

    ### 4가지 투표 방법을 소개할게요

    #### 🏆 보르다 방식
    **"1순위, 2순위, 3순위로 선택하세요"**  
    여러 후보 중에서 순서대로 번호를 매기는 방식입니다. 1위는 가장 높은 점수, 2위는 그 다음 점수를 받아서 총점이 가장 높은 후보가 선택됩니다.  
    - 장점: 모든 사람의 의견을 고려해서 극단적인 결과를 피할 수 있어요  
    - 단점: 때로는 전략적으로 투표하려는 사람들이 생길 수 있어요

    #### ⚖️ 내쉬 방식
    **"모두가 어느 정도 만족할 수 있는 선택"**  
    각자의 선호도를 최대한 고려해서 가장 균형 잡힌 결과를 찾는 방법입니다. 경제학에서 나온 아이디어를 투표에 적용했어요.  
    - 장점: 공정하면서도 효율적인 결과를 만들어요  
    - 단점: 계산 과정이 복잡해서 결과를 이해하기 어려울 수 있어요

    #### 🥊 콩도르세 방식
    **"일대일 대결에서 누가 이길까?"**  
    모든 후보들을 서로 일대일로 붙여서 가장 많이 이기는 후보를 선택하는 방법입니다. 토너먼트 같은 느낌이에요.  
    - 장점: 직관적이고 이해하기 쉬워요  
    - 단점: 가위바위보처럼 순환하는 결과가 나올 수 있어요

    #### 💯 벤담 방식
    **"얼마나 좋아하는지 점수로 표현하세요"**  
    각 선택지에 대해 얼마나 선호하는지 점수를 매겨서, 전체적으로 가장 만족도가 높은 선택을 찾는 방법입니다.  
    - 장점: 내가 얼마나 좋아하는지 강도를 표현할 수 있어요  
    - 단점: 사람마다 점수 기준이 달라서 일관성을 유지하기 어려워요

    ### 왜 이런 투표 시스템이 필요할까요?
    일반적인 "찬성/반대" 투표만으로는 복잡한 문제를 해결하기 어려워요. 모두의투표는 이런 점에서 도움이 됩니다:

    - 🤝 더 공정한 결정: 소수의 의견도 무시하지 않고, 다양한 생각들을 골고루 반영해서 더 균형 잡힌 결과를 만들어요.
    - 🗳️ 더 많은 참여: 투명하고 공정한 방식으로 모든 사람의 목소리를 들어서, 투표에 대한 신뢰도가 높아져요.
    - 🎯 복잡한 문제 해결: 회사, 동아리, 지역사회에서 여러 사람이 함께 결정해야 할 때 최적의 해답을 찾을 수 있어요.
    - 📚 배움의 기회: 다양한 투표 방식을 경험하면서 민주주의와 선택에 대해 더 깊이 생각해볼 수 있어요.

    **모두의투표로 더 공정하고 투명한 의사결정을 경험해보세요. 당신의 소중한 의견이 제대로 반영되는 새로운 투표의 세계에 지금 참여하세요!**
    """)

# 투표 설정
elif st.session_state.stage == "setup":
    st.title("🗳️ 투표 설정하기")
    st.session_state.title = st.text_input("투표 주제", value="", help="예: 점심 메뉴 선택")
    candidate_input = st.text_input("후보 목록 (쉼표로 구분)", value="", help="예: 피자, 햄버거, 파스타")
    voter_input = st.text_input("투표자 목록 (쉼표로 구분)", value="", help="예: 홍길동, 김영희")

    if st.button("투표 시작"):
        candidates = [x.strip() for x in candidate_input.split(",") if x.strip()]
        voters = [x.strip() for x in voter_input.split(",") if x.strip()]
        
        # 입력 유효성 검사
        if len(candidates) < 2:
            st.error("최소 2명의 후보를 입력하세요.")
        elif len(set(candidates)) != len(candidates):
            st.error("후보 이름은 중복될 수 없습니다.")
        elif len(voters) < 1:
            st.error("최소 1명의 투표자를 입력하세요.")
        elif len(set(voters)) != len(voters):
            st.error("투표자 이름은 중복될 수 없습니다.")
        else:
            st.session_state.candidates = candidates
            st.session_state.voters = voters
            st.session_state.votes = {voter: {} for voter in voters}
            st.session_state.completed = {voter: False for voter in voters}
            st.session_state.stage = "vote_select"
            st.rerun()

# 투표자 선택
elif st.session_state.stage == "vote_select":
    st.title("🔒 비밀 투표 - 투표자 선택")
    completed_count = sum(1 for v in st.session_state.completed.values() if v)
    total_voters = len(st.session_state.voters)
    st.markdown(f"<p class='progress-text'>투표 진행: {completed_count}/{total_voters} 완료</p>", unsafe_allow_html=True)
    
    voter = st.selectbox("투표자 선택", [v for v in st.session_state.voters if not st.session_state.completed[v]], key="voter_select")
    if st.button("투표 시작하기"):
        st.session_state.current_voter = voter
        st.session_state.stage = "vote_input"
        st.rerun()

    if all(st.session_state.completed.values()):
        if st.button("모든 투표 완료 → 방식 선택으로 이동"):
            st.session_state.stage = "method_select"
            st.rerun()

# 순위 입력
elif st.session_state.stage == "vote_input":
    voter = st.session_state.current_voter
    st.title(f"🗳️ {voter}의 투표 입력")
    
    st.subheader("🔢 순위 입력")
    st.markdown("각 후보에 대해 순위를 선택하세요 (1이 가장 선호). 중복 순위는 입력 가능하지만, 다음 단계로 넘어가기 위해서는 고유해야 합니다.")
    
    # 순위 선택 초기화
    if f"rank_choices_{voter}" not in st.session_state:
        st.session_state[f"rank_choices_{voter}"] = {c: 1 for c in st.session_state.candidates}
    
    ranks = {}
    available_ranks = list(range(1, len(st.session_state.candidates) + 1))
    
    for candidate in st.session_state.candidates:
        rank = st.selectbox(
            f"{candidate}의 순위",
            options=available_ranks,
            index=available_ranks.index(st.session_state[f"rank_choices_{voter}"][candidate]) if st.session_state[f"rank_choices_{voter}"][candidate] in available_ranks else 0,
            key=f"rank_{candidate}_{voter}_{uuid.uuid4()}"
        )
        st.session_state[f"rank_choices_{voter}"][candidate] = rank
        ranks[candidate] = rank
    
    # 순위 유효성 검사
    selected_ranks = list(ranks.values())
    if len(selected_ranks) != len(st.session_state.candidates):
        st.error("모든 후보에 순위를 지정해야 합니다.")
    elif st.button("순위 입력 완료 → 점수 입력으로 이동"):
        if len(set(selected_ranks)) != len(selected_ranks):
            st.error("각 후보는 고유한 순위를 가져야 합니다. 중복된 순위를 수정해주세요.")
        else:
            st.session_state.votes[voter]['rank'] = ranks
            st.session_state.stage = "score_input"
            st.rerun()

# 점수 입력
elif st.session_state.stage == "score_input":
    voter = st.session_state.current_voter
    st.title(f"📊 {voter}의 선호 점수 입력")
    
    st.markdown("각 후보에 대해 점수를 입력하세요 (0~100). 중복 점수는 입력 가능하지만, 다음 단계로 넘어가기 전에 확인됩니다.")
    sorted_candidates = sorted(st.session_state.votes[voter]['rank'].items(), key=lambda x: x[1])
    scores = {}
    
    for candidate, _ in sorted_candidates:
        scores[candidate] = st.number_input(
            f"{candidate}의 점수",
            min_value=0,
            max_value=100,
            step=1,
            value=50,
            key=f"score_{candidate}_{voter}_{uuid.uuid4()}"
        )
    
    if st.button("입력 완료 → 비밀투표 화면으로 돌아가기"):
        selected_scores = list(scores.values())
        if len(set(selected_scores)) < len(selected_scores):
            st.warning("중복된 점수가 있습니다. 벤담 방식에서는 괜찮지만, 다른 방식에서 결과가 왜곡될 수 있습니다. 계속 진행하시겠습니까?")
            if st.button("계속 진행"):
                st.session_state.votes[voter]['score'] = scores
                st.session_state.completed[voter] = True
                st.session_state.stage = "vote_select"
                st.rerun()
        else:
            st.session_state.votes[voter]['score'] = scores
            st.session_state.completed[voter] = True
            st.session_state.stage = "vote_select"
            st.rerun()

# 투표 방식 선택
elif st.session_state.stage == "method_select":
    st.title("🧠 투표 방식 선택")
    method = st.radio("방식 선택", ["보르다", "벤담", "내쉬", "콩도르세"], help="각 방식의 결과를 비교해보세요.")
    
    if st.button("결과 보기"):
        st.session_state.method = method
        st.session_state.stage = "result"
        st.rerun()

# 결과 출력
elif st.session_state.stage == "result":
    st.title("🏆 투표 결과")
    method = st.session_state.method
    st.subheader(f"✔ 선택된 방식: {method}")
    
    candidates = st.session_state.candidates
    votes = st.session_state.votes
    
    if method == "보르다":
        scores, winners = calculate_borda(votes, candidates)
        if len(winners) > 1:
            st.warning(f"동률 발생: {', '.join(winners)}")
        else:
            st.success(f"🎉 보르다 승자: {winners[0]}")
        st.dataframe(scores)
    
    elif method == "벤담":
        util, winners = calculate_bentham(votes, candidates)
        if len(winners) > 1:
            st.warning(f"동률 발생: {', '.join(winners)}")
        else:
            st.success(f"📈 벤담 승자: {winners[0]}")
        st.dataframe(util)
    
    elif method == "내쉬":
        min_scores, winners = calculate_nash(votes, candidates)
        if len(winners) > 1:
            st.warning(f"동률 발생: {', '.join(winners)}")
        else:
            st.success(f"📊 내쉬 승자: {winners[0]}")
        st.dataframe(min_scores)
    
    elif method == "콩도르세":
        wins, winners = calculate_condorcet(votes, candidates)
        if len(winners) > 1:
            st.warning(f"동률 발생: {', '.join(winners)}")
        else:
            st.success(f"👑 콩도르세 승자: {winners[0]}")
        st.dataframe(wins)
    
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← 이전으로 돌아가기"):
            st.session_state.stage = "method_select"
            st.rerun()
    with col2:
        if st.button("종료하기"):
            for key in ["stage", "title", "candidates", "voters", "votes", "completed", "method", "current_voter"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.stage = "home"
            st.rerun()