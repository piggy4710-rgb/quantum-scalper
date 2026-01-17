import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime

# ==========================================
# 🎨 UI 커스텀 스타일 (CSS) - [최종: 버튼 박멸 버전]
# ==========================================
def apply_custom_style():
    st.markdown("""
        <style>
        /* 1. 기본 폰트 및 스타일 */
        h1 {
            font-family: 'Suit', sans-serif;
            font-weight: 700;
            color: #1E1E1E;
        }
        .stButton>button {
            border-radius: 12px;
            font-weight: bold;
            border: none;
            transition: 0.3s;
        }
        .notice-box {
            background-color: #FFF3CD;
            color: #856404;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            border: 1px solid #FFEEBA;
        }

        /* [핵심] 2. 화면에 보이는 모든 장식 제거 */
        
        /* (1) 상단 헤더 & 툴바 제거 */
        header { visibility: hidden !important; display: none !important; }
        [data-testid="stToolbar"] { visibility: hidden !important; display: none !important; }
        [data-testid="stDecoration"] { visibility: hidden !important; display: none !important; }
        [data-testid="stHeader"] { visibility: hidden !important; display: none !important; }

        /* (2) 하단 푸터 제거 */
        footer { visibility: hidden !important; display: none !important; }

        /* ★★★ (3) 범인 검거: 오른쪽 아래 버튼들 제거 ★★★ */
        
        /* 왕관 모양 버튼 (Deploy Button) */
        .stAppDeployButton {
            visibility: hidden !important;
            display: none !important;
        }
        
        /* 사람/로고 모양 버튼 (Status Widget) */
        [data-testid="stStatusWidget"] {
            visibility: hidden !important;
            display: none !important;
        }

        /* 3. 모바일 화면 강제 조정 */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 5rem !important;
        }
        .stApp {
            margin-top: 0px !important;
        }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# ⚙️ 엔진 설정 (로직)
# ==========================================
class QuantumEngine:
    def __init__(self, ticker):
        self.ticker = ticker.upper()
        self.df = None

    def check_status(self):
        try:
            df = yf.download(self.ticker, period="1d", interval="1m", progress=False, auto_adjust=True)
            if df.empty: return False, "데이터 없음"
            
            if isinstance(df.columns, pd.MultiIndex):
                try: df.columns = df.columns.droplevel('Ticker')
                except: df.columns = df.columns.droplevel(1)
            
            self.df = df
            return True, df.index[-1]
        except Exception as e:
            return False, str(e)

    def analyze(self, mode, period_len):
        df = self.df
        if period_len == "1h": df = df.tail(60)
        elif period_len == "3h": df = df.tail(180)

        if len(df) < 5: return 0, ["데이터가 아직 부족해요 (장 시작 직후)"]

        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        score = 0
        reasons = []

        if (prev['Close'] < prev['Open']) and (curr['Close'] > curr['Open']) and \
           (curr['Open'] <= prev['Close']) and (curr['Close'] >= prev['Open']):
            score += 40
            reasons.append("🔥 하락세를 잡아먹는 '상승 장악형' 캔들!")

        body = abs(curr['Close'] - curr['Open'])
        lower_shadow = curr['Open'] - curr['Low'] if curr['Close'] > curr['Open'] else curr['Close'] - curr['Low']
        if lower_shadow > body * 2:
            score += 30
            reasons.append("🔨 바닥을 다지는 '망치형' 캔들!")

        if mode == "beast":
            vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
            if pd.isna(vol_avg) or vol_avg == 0: vol_avg = 1
            
            if curr['Volume'] > vol_avg * 3:
                score += 30
                reasons.append(f"💪 거래량 {curr['Volume']/vol_avg:.1f}배 폭발! (수급 쏠림)")
            
            pct_change = (curr['Close'] - curr['Open']) / curr['Open'] * 100
            if pct_change >= 1.0:
                reasons.append(f"🚀 1분 만에 +{pct_change:.2f}% 급등 중!")
            elif pct_change < 0:
                score = 0
                reasons.append("⛔ 현재 파란불(음봉)입니다. 진입 주의!")

        return score, reasons

# ==========================================
# 🏠 메인 화면 구성
# ==========================================
def main():
    st.set_page_config(page_title="급등주 포착기", page_icon="📈", layout="centered")
    apply_custom_style() # CSS 적용

    if 'notice_text' not in st.session_state:
        st.session_state['notice_text'] = "📢 오늘 미장 휴장일입니다. 이용에 참고해주세요!" 

    with st.sidebar:
        st.header("내 지갑 👛")
        if 'points' not in st.session_state: st.session_state.points = 5000 
        st.subheader(f"{st.session_state.points:,}원")
        
        if st.button("📺 광고 보고 500원 충전"):
            st.session_state.points += 500
            st.toast("500원이 충전되었습니다!", icon="💰")

        st.divider()
        st.markdown("### 🔒 관리자(Master) 메뉴")
        admin_pw = st.text_input("관리자 암호", type="password", placeholder="비밀번호 입력")
        
        if admin_pw == "master1234":
            st.success("관리자 인증 완료")
            new_notice = st.text_area("공지사항 수정하기", value=st.session_state['notice_text'])
            if st.button("공지 등록"):
                st.session_state['notice_text'] = new_notice
                st.rerun()
        elif admin_pw:
            st.error("암호가 틀렸습니다.")

    st.title("📈 실전 급등주 포착기")
    st.caption("AI 기반 실시간 캔들 & 수급 분석 솔루션")
    
    st.markdown(f"""
        <div class="notice-box">
            <b>[Master 공지]</b><br>
            {st.session_state['notice_text']}
        </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.subheader("1️⃣ 종목 상태 확인")
        col1, col2 = st.columns([3, 1])
        with col1:
            ticker = st.text_input("종목 코드 (예: SOXL)", value="SOXL", label_visibility="collapsed").upper()
        with col2:
            check_btn = st.button("🔍 조회", use_container_width=True)

        if 'engine_status' not in st.session_state: st.session_state['engine_status'] = None

        if check_btn:
            with st.spinner("거래소 데이터 연결 중..."):
                engine = QuantumEngine(ticker)
                success, result = engine.check_status()
                if success:
                    st.session_state['engine'] = engine
                    st.session_state['last_time'] = result
                    st.session_state['engine_status'] = "checked"
                    st.session_state['target_ticker'] = ticker
                else:
                    st.error("종목을 찾을 수 없습니다.")

    if st.session_state.get('engine_status') == "checked":
        last_time = st.session_state['last_time']
        st.success(f"✅ **{st.session_state['target_ticker']}** 데이터 수신 완료! (기준: {last_time.strftime('%H:%M:%S')})")
        st.warning("⚠️ **잠깐!** 무료 서버 특성상 15분 지연될 수 있습니다. 현재 시간과 비교 후 이용하세요.")

        with st.container(border=True):
            st.subheader("2️⃣ 분석 모드 선택")
            
            tab1, tab2 = st.tabs(["⏱️ 단기 분석 (1시간)", "🛡️ 추세 분석 (3시간)"])
            period_len = "1h"

            with tab1:
                st.caption("최근 60분간의 급박한 움직임을 분석합니다.")
                period_len = "1h"
                col_a, col_b = st.columns(2)
                with col_a:
                    st.info("**🕯️ 패턴 분석 (500원)**\n\n차트의 모양(관상)만 봅니다.")
                    if st.button("패턴 분석 시작", key="btn_p1"):
                        run_analysis(period_len, "pattern", 500)
                with col_b:
                    st.error("**🦁 야수 모드 (2,000원)**\n\n모양 + 수급 + 속도 (추천)")
                    if st.button("야수 모드 시작", key="btn_b1"):
                        run_analysis(period_len, "beast", 2000)

            with tab2:
                st.caption("오전장 전체 흐름을 보고 안전하게 들어갑니다.")
                period_len = "3h"
                col_c, col_d = st.columns(2)
                with col_c:
                    if st.button("패턴 분석 시작", key="btn_p2"):
                        run_analysis(period_len, "pattern", 500)
                with col_d:
                    if st.button("야수 모드 시작", key="btn_b2"):
                        run_analysis(period_len, "beast", 2000)

def run_analysis(period_len, mode, cost):
    engine = st.session_state['engine']
    if st.session_state.points < cost:
        st.toast("잔액이 부족합니다! 충전해주세요.", icon="❌")
        return

    st.session_state.points -= cost
    
    with st.status("🧠 AI 분석 엔진 가동 중...", expanded=True):
        time.sleep(0.7)
        st.write("캔들 패턴 스캐닝...")
        time.sleep(0.3)
        st.write("수급 및 거래량 분석...")
        score, report = engine.analyze(mode, period_len)
        st.write("완료!")

    st.divider()
    
    st.markdown(f"### 📝 {st.session_state['target_ticker']} 분석 결과")
    current_price = engine.df['Close'].iloc[-1]
    st.metric("현재가", f"${current_price:.2f}")

    if not report:
        st.info("🤷‍♂️ 특이한 신호가 잡히지 않습니다. (관망 추천)")
    else:
        for r in report:
            if "🔥" in r or "🚀" in r:
                st.success(r)
            elif "⛔" in r:
                st.error(r)
            else:
                st.info(r)

    st.markdown("---")
    if mode == "beast":
        if score >= 50: 
            st.balloons()
            st.markdown("""
                <div style="background-color:#d4edda; padding:20px; border-radius:10px; text-align:center; border:2px solid #28a745;">
                    <h2 style="color:#155724; margin:0;">🚀 강력 매수 추천!</h2>
                    <p>수급과 패턴이 완벽합니다. 지금이 타이밍입니다.</p>
                </div>
            """, unsafe_allow_html=True)
        else: 
            st.markdown("""
                <div style="background-color:#f8d7da; padding:20px; border-radius:10px; text-align:center; border:2px solid #dc3545;">
                    <h2 style="color:#721c24; margin:0;">🛑 진입 금지</h2>
                    <p>연료(거래량)가 부족하거나 떨어지는 중입니다.</p>
                </div>
            """, unsafe_allow_html=True)
    else:
        if score >= 40: 
            st.markdown("### 🟢 **매수 관점 (차트 양호)**")
        else: 
            st.markdown("### ⚪ **관망 (확실한 자리 대기)**")

if __name__ == "__main__":
    main()
