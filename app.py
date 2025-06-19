# app.py
# 「宇宙とあなたの運命」
#
# ──────────────────────────────────────────
# 必要ライブラリ:
#   pip install streamlit requests openai python-dotenv
#   （streamlit run app.py で起動）
# ──────────────────────────────────────────

import datetime
import requests
import streamlit as st
import openai
from typing import Tuple

# ──────────────  0. 共通設定  ──────────────
st.set_page_config(page_title="宇宙とあなたの運命", page_icon="✨", layout="centered")

openai.api_key = st.secrets["OPENAI_API_KEY"]
NASA_API_KEY = st.secrets["NASA_API_KEY"]

# ──────────────  1. ヘルパー関数  ──────────────
def get_apod(today: datetime.date) -> Tuple[str, str, str]:
    """
    NASA APOD (Astronomy Picture of the Day) から
    画像／タイトル／説明文を取得して返す
    """
    url = "https://api.nasa.gov/planetary/apod"
    params = {"api_key": NASA_API_KEY, "date": today.isoformat()}
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()

        if data.get("media_type") not in {"image", "video"}:
            raise ValueError("メディアタイプが image/video ではありません")

        media_url = data["url"]
        title = data.get("title", "No Title")
        explanation = data.get("explanation", "")

        return media_url, title, explanation
    except Exception as e:
        # 英語エラーを併記して表示
        st.error(f"💥 NASA データ取得に失敗しました。\n\nError: {e}")
        raise


def generate_fortune(text: str) -> str:
    """
    APOD の説明文をもとに GPT で
    詩的・スピリチュアルな今日の運勢 (300 文字以内) を生成
    """
    prompt = (
        "あなたは詩的でスピリチュアルな占い師です。"
        "以下の宇宙画像の解説をインスピレーションに、"
        "日本語で 300 文字以内の今日の運勢を作成してください。\n\n"
        f"【解説】\n{text}"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # 任意の GPT モデル
            messages=[
                {"role": "system", "content": "You are a poetic spiritual fortune teller."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
        )
        fortune = response.choices[0].message.content.strip()
        return fortune
    except Exception as e:
        st.error(f"💥 占い生成に失敗しました。\n\nError: {e}")
        raise


# ──────────────  2. UI  ──────────────
st.title("✨ 宇宙とあなたの運命 ✨")
st.caption("NASA の宇宙写真と GPT が紡ぐ、あなたへの星からのメッセージ")

if "fortune" not in st.session_state:
    st.session_state["fortune"] = None

if st.button("🔭 今日の宇宙画像を見る"):
    today = datetime.date.today()
    with st.spinner("宇宙からの光を受信中…"):
        media_url, title, explanation = get_apod(today)
        fortune = generate_fortune(explanation)
        # 結果をセッションに保存（リロード対策）
        st.session_state["media_url"] = media_url
        st.session_state["title"] = title
        st.session_state["fortune"] = fortune
        st.session_state["media_type"] = (
            "video" if media_url.lower().endswith((".mp4", ".mov", ".avi")) else "image"
        )

# ──────────────  3. 出力表示  ──────────────
if st.session_state.get("fortune"):
    if st.session_state["media_type"] == "image":
        st.image(st.session_state["media_url"], use_column_width=True)
    else:
        st.video(st.session_state["media_url"])

    st.subheader(st.session_state["title"])
    st.markdown(f"**{st.session_state['fortune']}**")

    with st.expander("🛰️ NASA 解説（原文）"):
        st.write(explanation)
else:
    st.info("上のボタンを押して、今日の宇宙からのメッセージを受け取りましょう！")
