
import streamlit as st
import whisper
import tempfile
import os
import random
import time
from streamlit_mic_recorder import mic_recorder
from PIL import Image, ImageDraw, ImageFont

# --- PAGE CONFIG & SESSION STATE INIT ---
st.set_page_config(page_title="Journey to Wellness Prototype", layout="centered")
for key, default_value in {
    "page": "home",
    "credits": 0,
    "user_input": "",
    "user_original": "",
    "chat_history": [],
    "moods": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

# --- UTILITY & MODEL FUNCTIONS ---
@st.cache_resource
def load_whisper_model():
    """Load the Whisper model, caching it for efficiency."""
    try:
        model = whisper.load_model("base")
        return model
    except Exception as e:
        st.error(f"Failed to load Whisper model: {e}")
        return None

def transcribe_audio(audio_path):
    """Transcribes an audio file using the Whisper model."""
    whisper_model = load_whisper_model()
    if whisper_model:
        try:
            result = whisper_model.transcribe(audio_path)
            return result["text"].strip()
        except Exception as e:
            return ""
    return ""

def get_simple_sentiment(text: str):
    """Provides a simple sentiment analysis based on keywords."""
    text_lower = text.lower()
    positive_words = ["happy", "good", "great", "well", "positive", "joy"]
    negative_words = ["sad", "bad", "unhappy", "stress", "anxious", "pain"]
    
    if any(word in text_lower for word in positive_words):
        return "positive"
    elif any(word in text_lower for word in negative_words):
        return "negative"
    return "neutral"

def get_simple_bot_response(user_input: str) -> str:
    """A simple, rule-based chatbot response function."""
    crisis_keywords = ["suicide", "kill myself", "end my life", "want to die", "hopeless"]
    if any(kw in user_input.lower() for kw in crisis_keywords):
        return "💜 You're not alone. If you're in danger, please call emergency services. In India: AASRA 91-9820466726."
    
    if "hello" in user_input.lower():
        return "Hello! Thanks for reaching out. How are you feeling today?"
    if "?" in user_input:
        return "That's a great question. Tell me more about what's on your mind."
    return "Thanks for sharing. I hear you — tell me more."

def create_image_from_text(story_text: str):
    """Generates an image from text using the Pillow library."""
    width, height = 1280, 720
    bg_color = (18, 24, 37)
    text_color = "white"
    
    img = Image.new('RGB', (width, height), color=bg_color)
    d = ImageDraw.Draw(img)
    
    try:
        font_path = "arial.ttf"  # This font might not be available
        font_size = 30
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        font = ImageFont.load_default()
        font_size = 20

    # Basic text wrapping
    lines = []
    max_width = width - 100
    words = story_text.split(' ')
    current_line = ""
    for word in words:
        if d.textsize(current_line + ' ' + word, font=font)[0] < max_width:
            current_line += ' ' + word
        else:
            lines.append(current_line.strip())
            current_line = word
    lines.append(current_line.strip())
    
    story_wrapped = "\n".join(lines)
    
    # Calculate text position
    text_width, text_height = d.textsize(story_wrapped, font=font)
    x = (width - text_width) / 2
    y = (height - text_height) / 2
    
    d.text((x, y), story_wrapped, font=font, fill=text_color)
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    img.save(temp_file.name)
    return temp_file.name

# --- PAGE COMPONENTS ---
def reflection_box():
    """Allows users to input text or record audio for reflection."""
    st.subheader("💬 Reflect — how are you feeling?")
    typed_text = st.text_area("Write your thoughts:", value=st.session_state.get("user_input", ""), height=150)
    audio_data = mic_recorder(start_prompt="🎙️", stop_prompt="⏹️", just_once=False, key="mic_recorder")

    reflection_text = typed_text.strip()
    
    if audio_data and audio_data.get("bytes"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_data["bytes"])
            audio_path = f.name
        
        transcribed_text = transcribe_audio(audio_path)
        os.remove(audio_path)
        
        if transcribed_text:
            st.success("🎙️ Transcribed: " + transcribed_text)
            reflection_text = transcribed_text
            st.session_state.user_input = reflection_text
            st.session_state.user_original = reflection_text
            st.experimental_rerun()

    if typed_text != st.session_state.user_input and typed_text:
        st.session_state.user_input = typed_text
        st.session_state.user_original = typed_text
        st.experimental_rerun()

def chatbot_in_game():
    """The main chatbot interface for the game pages."""
    st.subheader("🧠 Chat with the Wellness Bot")
    reflection_box()

    st.markdown("### Conversation")
    for sender, msg in st.session_state.chat_history:
        if sender == "user":
            st.markdown(f'<div style="background:#DCF8C6;padding:8px;border-radius:10px;margin:6px">🗣️ {msg}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="background:#F1F0F0;padding:8px;border-radius:10px;margin:6px">🤖 {msg}</div>', unsafe_allow_html=True)

    if st.button("➡ Send to Bot"):
        user_input = st.session_state.get("user_input", "").strip()
        if len(user_input) < 5:
            st.warning("Please share a bit more before sending.")
        else:
            sentiment = get_simple_sentiment(user_input)
            reply = get_simple_bot_response(user_input)
            st.session_state.chat_history.append(("user", user_input))
            st.session_state.chat_history.append(("bot", reply))
            st.session_state.moods.append({
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "text": user_input, "sentiment": sentiment
            })
            st.session_state.user_input = "" # Clear input area
            st.experimental_rerun()
            
    if st.session_state.moods:
        st.markdown("### Mood Tracker")
        for m in reversed(st.session_state.moods[-5:]):
            st.write(f"**{m['sentiment']}** — {m['time']}")
            st.caption(m["text"])

    if st.session_state.credits >= 3:
        if st.button("➡ Continue to Mansion"):
            st.session_state.page = "mansion"
            st.experimental_rerun()
    else:
        st.info(f"✨ Earn at least 3 credits from games to unlock your Mansion story. (Current: {st.session_state.credits})")

# --- GAME PAGE LOGIC ---
def train_game():
    st.header("🚆 Train: Object Hunt")
    st.write("Find the hidden objects using hints.")
    st.image("https://gamersunite.s3.amazonaws.com/uploads/june-s-journey-hidden-object-mystery-game/1531636021150", width='stretch')
    objects = {"butterfly": "A small creature with wings", "wheel": "Round part found on vehicles", "horseshoe": "Lucky, horse related"}
    hidden_objects = random.sample(list(objects.keys()), 3)
    
    with st.form("train_form"):
        for i, obj in enumerate(hidden_objects):
            st.write(f"Hint {i+1}: {objects[obj]}")
            st.text_input(f"Guess for Hint {i+1}:", key=f"train_guess_{i}")
        submitted = st.form_submit_button("Check Answers ✅")

    if submitted:
        score = sum(1 for i, obj in enumerate(hidden_objects) if st.session_state[f"train_guess_{i}"].strip().lower() == obj)
        st.session_state.credits += score
        st.success(f"Found {score}/3 objects. Total credits: {st.session_state.credits}")
        st.experimental_rerun()
        
    chatbot_in_game()

def car_game():
    st.header("🚗 Car: Puzzle Rush")
    puzzles = [("What has keys but can’t open locks?", "piano"), ("I’m tall when I’m young, and short when I’m old. What am I?", "candle")]
    question, answer = random.choice(puzzles)
    
    with st.form("car_form"):
        ans = st.text_input(question)
        submitted = st.form_submit_button("Submit Answer ✅")
        
    if submitted:
        if ans.strip().lower() == answer:
            st.session_state.credits += 1
            st.success("Correct! 🎉")
        else:
            st.error(f"Wrong — the answer was: {answer}")
        st.info(f"Credits: {st.session_state.credits}")
        st.experimental_rerun()
    
    chatbot_in_game()

def bus_game():
    st.header("🚌 Bus: Word Hunt")
    st.markdown("Find the missing words (bus stops). You can ask for hints if you need them!")
    st.image("https://puzzlestoplay.com/wp-content/uploads/2021/01/bus-driver-word-search-puzzle-photo-506x675.jpg", width='stretch')
    words = {"route": "From bottom, line 6", "driver": "Top, line 3", "ticket": "Center, line 8"}

    if st.button("💡 Show Hints"):
        for w, h in words.items():
            st.info(f"Hint: {h}")

    with st.form("bus_form"):
        for i, word in enumerate(words.keys()):
            st.text_input(f"Guess #{i+1}:", key=f"bus_guess_{i}")
        submitted = st.form_submit_button("Check Answers ✅")

    if submitted:
        score = sum(1 for i, word in enumerate(words.keys()) if st.session_state[f"bus_guess_{i}"].strip().lower() == word)
        st.session_state.credits += score
        st.success(f"Found {score}/{len(words)} — Total credits: {st.session_state.credits}")
        st.experimental_rerun()
    
    chatbot_in_game()

# --- MANSION PAGE ---
def mansion_page():
    st.title("🏰 Mansion — Your Success Story")
    st.image("https://img.freepik.com/premium-photo/free-photo-luxurious-mansion-with-lush-garden-beautiful-sunset-background_650144-557.jpg?w=2000", width='stretch')
    user_text = st.session_state.get("user_original", "")
    
    if not user_text:
        st.warning("No reflection found from your journey.")
    else:
        if st.button("🏰 Generate Story Image"):
            story = f"🌍 Once a traveler carried these thoughts:\n\n“{user_text}”\n\n✨ They found resilience, and finally reached their mansion of peace."
            with st.spinner("Rendering your story image..."):
                image_path = create_image_from_text(story)
                st.image(image_path)
                st.success("Your story is complete! 🌟")
                os.remove(image_path)
        
    if st.button("🔁 Restart Journey"):
        st.session_state.clear()
        st.experimental_rerun()

# --- HOME PAGE ---
def home_page():
    st.title("🚦 Start Your Journey")
    st.markdown("Choose your mode of travel:")
    st.image("https://wallpaperaccess.com/full/4515512.jpg", width='stretch')
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚆 Train"):
            st.session_state.page = "train"
            st.experimental_rerun()
    with col2:
        if st.button("🚌 Bus"):
            st.session_state.page = "bus"
            st.experimental_rerun()
    with col3:
        if st.button("🚗 Car"):
            st.session_state.page = "car"
            st.experimental_rerun()

# --- ROUTER ---
pages = {
    "home": home_page,
    "train": train_game,
    "car": car_game,
    "bus": bus_game,
    "mansion": mansion_page,
}
pages[st.session_state.page]()
