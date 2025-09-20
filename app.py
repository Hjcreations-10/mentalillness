import streamlit as st
import whisper
import tempfile
import spacy
from textblob import TextBlob
from transformers import pipeline
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI   # ✅ FIXED import
import pyttsx3
from streamlit_mic_recorder import mic_recorder
import time
import os
import random

# ----------------------------
# Page config & session init
# ----------------------------
st.set_page_config(page_title="Journey to Wellness Prototype", layout="centered")
if "page" not in st.session_state:
    st.session_state.page = "home"
if "transport" not in st.session_state:
    st.session_state.transport = None
if "credits" not in st.session_state:
    st.session_state.credits = 0
if "user_input" not in st.session_state:
    st.session_state.user_input = ""
if "user_original" not in st.session_state:
    st.session_state.user_original = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "moods" not in st.session_state:
    st.session_state.moods = []

# ----------------------------
# MUSIC EMBEDS
# ----------------------------
MUSIC_HOME = """<iframe width="0" height="0" allow="autoplay"
src="https://w.soundcloud.com/player/?url=https%3A%2F%2Fsoundcloud.com%2Fbrunuhville%2Fred-queens-lullaby&auto_play=true"></iframe>"""
MUSIC_MANSION = """<iframe width="0" height="0" allow="autoplay"
src="https://w.soundcloud.com/player/?url=https%3A%2F%2Fsoundcloud.com%2Fjustin-zaitsev-115677774%2Ffailure-to-success-main&auto_play=true"></iframe>"""

def play_music(embed_html: str):
    st.markdown(embed_html, unsafe_allow_html=True)

# ----------------------------
# Models
# ----------------------------
whisper_model = None
nlp_spacy = None
sentiment_pipeline = None
conversation_chain = None

def ensure_models():
    global whisper_model, nlp_spacy, sentiment_pipeline, conversation_chain
    if whisper_model is None:
        try:
            whisper_model = whisper.load_model("base")
            st.session_state.whisper_ready = True
        except:
            whisper_model = None
    if nlp_spacy is None:
        try:
            nlp_spacy = spacy.load("en_core_web_sm")
        except:
            pass
    if sentiment_pipeline is None:
        try:
            sentiment_pipeline = pipeline("sentiment-analysis")
        except:
            pass
    if conversation_chain is None:
        try:
            memory = ConversationBufferMemory()
            conversation_chain = ConversationChain(
                llm=ChatOpenAI(model_name="gpt-4", temperature=0.7), memory=memory
            )
        except:
            conversation_chain = None

def transcribe_audio(path):
    ensure_models()
    if 'whisper_ready' in st.session_state and whisper_model is not None:
        res = whisper_model.transcribe(path)
        return res.get("text","").strip()
    return ""

def analyze_text(text: str):
    ensure_models()
    sentiment = None
    tone = None
    entities = []
    try:
        if sentiment_pipeline:
            sentiment = sentiment_pipeline(text)[0]['label']
    except:
        pass
    try:
        blob = TextBlob(text)
        tone = "positive" if blob.sentiment.polarity > 0.3 else "negative" if blob.sentiment.polarity < -0.3 else "neutral"
    except:
        pass
    try:
        if nlp_spacy:
            entities = [(ent.text, ent.label_) for ent in nlp_spacy(text).ents]
    except:
        pass
    return sentiment, tone, entities

def get_chat_response(user_input:str):
    ensure_models()
    crisis = ["suicide","kill myself","end my life","want to die","hopeless"]
    if any(kw in user_input.lower() for kw in crisis):
        return "💜 You're not alone. If you're in danger, please call emergency services. In India: AASRA 91-9820466726."
    if conversation_chain:
        try:
            return conversation_chain.run(user_input)
        except:
            pass
    return "Thanks for sharing. I hear you — tell me more."

def speak_text_tts(text: str):
    try:
        engine = pyttsx3.init()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        path = tmp.name
        engine.save_to_file(text, path)
        engine.runAndWait()
        return path
    except:
        return None

# ----------------------------
# Reflection Box
# ----------------------------
def reflection_box():
    st.subheader("💬 Reflect — how are you feeling?")
    typed = st.text_area("Write your thoughts:", value=st.session_state.get("user_input",""), height=150)
    audio_data = mic_recorder(start_prompt="🎙️", stop_prompt="⏹️", just_once=False, key=f"mic_{st.session_state.page}")
    reflection_text = ""

    if audio_data and isinstance(audio_data, dict) and audio_data.get("bytes"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_data["bytes"])
            audio_path = f.name
        text = transcribe_audio(audio_path)
        reflection_text = text or ""
        os.remove(audio_path)
        if reflection_text:
            st.success("🎙️ Transcribed: " + reflection_text)
    elif typed and typed.strip():
        reflection_text = typed.strip()

    if reflection_text:
        st.session_state.user_input = reflection_text
        st.session_state.user_original = reflection_text

# ----------------------------
# Chatbot inside game
# ----------------------------
def chatbot_in_game():
    st.subheader("🧠 Chat with the Wellness Bot")
    reflection_box()

    st.markdown("### Conversation")
    for sender,msg in st.session_state.chat_history[-10:]:
        if sender=="user":
            st.markdown(f'<div style="background:#DCF8C6;padding:8px;border-radius:10px;margin:6px">🗣️ {msg}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="background:#F1F0F0;padding:8px;border-radius:10px;margin:6px">🤖 {msg}</div>', unsafe_allow_html=True)

    if st.button("➡ Send to Bot"):
        user_input = st.session_state.get("user_input","").strip()
        if len(user_input) < 5:
            st.warning("Please share a bit more before sending.")
        else:
            sentiment, tone, entities = analyze_text(user_input)
            reply = get_chat_response(user_input)
            st.session_state.chat_history.append(("user", user_input))
            st.session_state.chat_history.append(("bot", reply))
            st.session_state.moods.append({
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "text": user_input, "tone": tone, "sentiment": sentiment
            })
            tts_path = speak_text_tts(reply)
            if tts_path: st.audio(tts_path)

    if st.session_state.moods:
        st.markdown("### Mood tracker")
        for m in reversed(st.session_state.moods[-5:]):
            st.write(f"**{m['tone']}** ({m['sentiment']}) — {m['time']}")
            st.caption(m["text"])

    # Unlock Mansion only if 3+ credits
    if st.session_state.credits >= 3:
        if st.button("➡ Continue to Mansion"):
            st.session_state.page = "mansion"
    else:
        st.info("✨ Earn at least 3 credits from games to unlock your Mansion story.")

# ----------------------------
# Games
# ----------------------------
def train_game():
    st.header("🚆 Train: Object Hunt")
    st.write("Find the hidden objects using hints.")
    st.image("https://gamersunite.s3.amazonaws.com/uploads/june-s-journey-hidden-object-mystery-game/1531636021150", width='stretch')
    objects = {
        "butterfly":"🦋 A small creature with wings",
        "wheel":"⚙️ Round part found on vehicles",
        "horseshoe":"🐎 Lucky, horse related",
        "metal shield":"🛡️ Used for protection",
        "violin box":"🎻 Stores a violin",
        "compass":"🧭 Points north"
    }
    hidden = random.sample(list(objects.keys()), 3)
    for i,h in enumerate(hidden, start=1):
        st.write(f"Hint {i}: {objects[h]}")
    guesses=[st.text_input(f"Guess #{i+1}:", key=f"train_guess_{i}") for i in range(3)]
    if st.button("Check Answers ✅"):
        score=sum(1 for g,h in zip(guesses,hidden) if g.strip().lower()==h)
        st.session_state.credits += score
        st.success(f"Found {score}/3 — Total credits: {st.session_state.credits}")
    chatbot_in_game()

def car_game():
    st.header("🚗 Car: Puzzle Rush")
    puzzles=[("What has keys but can’t open locks?","piano"),
             ("I’m tall when I’m young, and short when I’m old. What am I?","candle"),
             ("What gets wetter the more it dries?","towel")]
    q,a=random.choice(puzzles)
    ans=st.text_input(q, key="car_ans")
    if st.button("Submit Answer ✅"):
        if ans.strip().lower()==a:
            st.session_state.credits +=1
            st.success("Correct! 🎉")
        else:
            st.error(f"Wrong — answer was: {a}")
        st.info(f"Credits: {st.session_state.credits}")
    chatbot_in_game()

def bus_game():
    # 🎵 Play transport page music
    

    st.header("🚌 Bus: Word Hunt")
    st.markdown("Find the missing words (bus stops). You can ask for hints if you need them!")
    st.image("https://puzzlestoplay.com/wp-content/uploads/2021/01/bus-driver-word-search-puzzle-photo-506x675.jpg", width='stretch')
    # Hidden words with hints
    words = {
        "route": "From bottom, line 6",
        "driver": "Top, line 3",
        "ticket": "Center, line 8",
        "wheel": "Right side, vertical"
    }

    # Show "Get Hints" button
    if "bus_hints_shown" not in st.session_state:
        st.session_state.bus_hints_shown = False

    if st.button("💡 Show Hints"):
        st.session_state.bus_hints_shown = True

    if st.session_state.bus_hints_shown:
        st.markdown("### 🔍 Hints")
        for i, (w, h) in enumerate(words.items(), start=1):
            st.write(f"Hint {i}: {h}")

    # Input boxes for guesses
    guesses = [
        st.text_input(f"Guess #{i+1}:", key=f"bus_guess_{i}")
        for i in range(len(words))
    ]

    # Check answers button
    if st.button("Check Answers ✅"):
        hidden = list(words.keys())
        score = sum(1 for g, h in zip(guesses, hidden) if g.strip().lower() == h)
        st.session_state.credits += score
        st.success(f"Found {score}/{len(hidden)} — Total credits: {st.session_state.credits}")

    # After game, chatbot stage
    chatbot_in_game()


# ----------------------------
# Mansion Page
# ----------------------------
def build_success_story(user_input: str) -> str:
    return (f"🌍 Once upon a time, a traveler set out carrying these thoughts:\n\n"
            f"“{user_input}”\n\n"
            "✨ They faced challenges but found resilience, clarity, and growth.\n\n"
            "🏰 Finally, they reached a grand mansion — built of peace and self-trust.")



def mansion_page():
    play_music(MUSIC_MANSION)
    st.title("🏰 Mansion — Your Success Story")
    st.image("https://img.freepik.com/premium-photo/free-photo-luxurious-mansion-with-lush-garden-beautiful-sunset-background_650144-557.jpg?w=2000", width='stretch')
    user_text = st.session_state.get("user_original","")
    if not user_text:
        st.warning("No reflection found.")
    else:
        if st.button("🏰 Generate Story Movie"):
            with st.spinner("Rendering short motivational video..."):
                path = create_video_from_text(build_success_story(user_text))
                st.video(path)
                st.success("Your story is complete! 🌟")
                st.markdown("## 🎁 Bonus — Suggested Books")
                st.write("📖 Man’s Search for Meaning — Viktor E. Frankl")
                st.write("📖 The Untethered Soul — Michael A. Singer")
                st.write("📖 Atomic Habits — James Clear")

    if st.button("🔁 Restart Journey"):
        for k in list(st.session_state.keys()):
            st.session_state[k]=None
        st.session_state.page="home"

# ----------------------------
# Home Page
# ----------------------------
def home_page():
    play_music(MUSIC_HOME)
    st.title("🚦 Start Your Journey")
    st.markdown("Choose your mode of travel:")
    st.image("https://wallpaperaccess.com/full/4515512.jpg", width='stretch')
    c1,c2,c3 = st.columns(3)
    with c1:
        if st.button("🚆 Train"):
            st.session_state.page="train"
    with c2:
        if st.button("🚌 Bus"):
            st.session_state.page="bus"
    with c3:
        if st.button("🚗 Car"):
            st.session_state.page="car"

# ----------------------------
# Router
# ----------------------------
page=st.session_state.page
if page=="home": home_page()
elif page=="train": train_game()
elif page=="car": car_game()
elif page=="bus": bus_game()
elif page=="mansion": mansion_page()
else: home_page()
