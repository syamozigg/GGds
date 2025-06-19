import datetime
import requests
import streamlit as st
import openai
from typing import Tuple

st.set_page_config(page_title="宇宙とあなたの運命", page_icon="✨", layout="centered")

# 🔑 APIキーの読み込み
if "OPENAI_API_KEY" not in st.secrets or "NASA_API_KEY" not in st.secrets:
    st.error("🔑 APIキーが設定されていません。`.streamlit/secrets.toml` に `OPENAI_API_KEY` と `NASA_API_KEY` を追加してください。")
    st.stop()

openai.api_key = st.secrets["OPENAI_API_KEY"]
NASA_API_KEY = st.secrets["NASA_API_KEY"]

# 🛰️ NASAの宇宙画像を取得
def get_apod(today: datetime.date) -> Tuple[str, str, str]:
    url = "https://api.nasa.gov/planetary/apod"
    params = {"api_key": NASA_API_KEY, "date": today.isoformat()}
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()

        if data.get("media_type") not in {"image", "video"}:
            raise ValueError("メディアタイプが image または video ではありません。")

        media_url = data["url"]
        title = data.get("title", "No Title")
        explanation = data.get("explanation", "")

        return media_url, title, explanation

    except requests.exceptions.HTTPError as e:
        if res.status_code == 404:
            yesterday = today - datetime.timedelta(days=1)
            if yesterday < datetime.date(1995, 6, 16):
                st.error("NASA APODのデータが見つかりません。")
                raise
            return get_apod(yesterday)
        else:
            st.error(f"💥 NASA データ取得に失敗しました。\n\nError: {e}")
            raise
    except Exception as e:
        st.error(f"💥 NASA データ取得に失敗しました。\n\nError: {e}")
        raise

# 🔮 GPTによる占い生成
def generate_fortune(text: str) -> str:
    prompt = (
        "あなたは詩的でスピリチュアルな占い師です。"
        "以下の宇宙画像の解説をインスピレーションに、"
        "日本語で300文字以内の今日の運勢を作成してください。\n\n"
        f"【解説】\n{text}"
    )
    try:
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a poetic spiritual fortune teller."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
        )
        return completion.choices[0].message.content.strip()

    except openai.RateLimitError:
        fallback = "宇宙は静かにあなたを見守っています。今日は焦らず、自分のペースで進みましょう。"
        st.warning("⚠️ OpenAIの利用上限に達しました。代わりに星からの囁きをお届けします。")
        return fallback

    except Exception as e:
        fallback = "今日は心を空に向けて、穏やかな呼吸を。運命はあなたの味方です。"
        st.error(f"💥 占い生成に失敗しました。\n\nError: {e}\n代わりに自動メッセージを表示します。")
        return fallback

# 🌍 NASA解説を日本語に翻訳
def translate_to_japanese(text: str) -> str:
    try:
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional English to Japanese translator."},
                {"role": "user", "content": f"以下の天文学に関する解説文を自然で正確な日本語に翻訳してください：\n\n{text}"},
            ],
            max_tokens=500,
        )
        return completion.choices[0].message.content.strip()

    except Exception as e:
        st.warning(f"⚠️ NASA解説の翻訳に失敗しました。英語のまま表示します。\nError: {e}")
        return text

# 🎨 UI構築
st.title("✨ 宇宙とあなたの運命 ✨")
st.caption("NASA の宇宙写真と GPT が紡ぐ、あなたへの星からのメッセージ")

if "fortune" not in st.session_state:
    st.session_state["fortune"] = None

if st.button("🔭 今日の宇宙画像を見る"):
    today = datetime.date.today()
    with st.spinner("宇宙からの光を受信中…"):
        media_url, title, explanation = get_apod(today)
        explanation_jp = translate_to_japanese(explanation)
        fortune = generate_fortune(explanation)

        st.session_state["media_url"] = media_url
        st.session_state["title"] = title
        st.session_state["fortune"] = fortune
        st.session_state["media_type"] = (
            "video" if media_url.lower().endswith((".mp4", ".mov", ".avi")) else "image"
        )
        st.session_state["explanation"] = explanation
        st.session_state["explanation_jp"] = explanation_jp

if st.session_state.get("fortune"):
    if st.session_state["media_type"] == "image":
        st.image(st.session_state["media_url"], use_container_width=True)
    else:
        st.video(st.session_state["media_url"])

    st.subheader(st.session_state["title"])
    st.markdown(f"**{st.session_state['fortune']}**")

    with st.expander("🛰️ NASA 解説（日本語）"):
        st.write(st.session_state["explanation_jp"])

    with st.expander("🗽 NASA 解説（原文 / 英語）"):
        st.write(st.session_state["explanation"])
else:
    st.info("上のボタンを押して、今日の宇宙からのメッセージを受け取りましょう！")
