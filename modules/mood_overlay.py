import streamlit as st

NEGATIVE_EMOTIONS = {"confused", "sad", "angry", "tired", "sleepy", "fear"}

EMOJI = {
    "confused": "🤔",
    "sad": "😔",
    "angry": "😡",
    "tired": "🥱",
    "sleepy": "😴",
    "fear": "😰",
    "neutral": "🙂",
    "happy": "😄",
}

MESSAGES = {
    "confused": "You look confused. Want a simpler explanation?",
    "sad": "It’s okay to take it slow. I’m here with you.",
    "angry": "Looks like this is frustrating. Let’s try a calmer path.",
    "tired": "You seem tired. A tiny break might help.",
    "sleepy": "Your eyes look tired. Blink or stretch once?",
    "fear": "This topic feels scary? I’ll make it easier.",
}


def mood_overlay(emotion: str, mode="auto", log_index=0):
    """
    Interactive Overlay (Version B)
    Returns True = overlay active; False = no overlay
    """

    # Manual mode = small chip only
    if mode == "manual":
        st.markdown(
            f"<p style='font-size:14px; opacity:0.7;'>Mood: {EMOJI.get(emotion)} {emotion}</p>",
            unsafe_allow_html=True,
        )
        return False

    # Auto mode but emotion is neutral/happy → no overlay
    if mode == "auto" and emotion not in NEGATIVE_EMOTIONS:
        return False

    emoji = EMOJI.get(emotion, "🤔")
    msg = MESSAGES.get(emotion, "Want a simplified explanation? I can help.")

    # FULL SCREEN OVERLAY
    st.markdown(
        f"""
        <style>
            .aura-overlay {{
                position: fixed;
                top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(0,0,0,0.85);
                z-index: 999999 !important;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                color: white;
                text-align: center;
            }}
        </style>

        <div class="aura-overlay">
            <div style="font-size:74px; margin-bottom:20px;">
                {emoji}
            </div>

            <div style="font-size:28px; max-width:800px; margin-bottom:20px;">
                {msg}
            </div>

            <div style="font-size:18px; opacity:0.7; margin-bottom:35px;">
                Click Continue to resume
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Unique key so Streamlit doesn't duplicate
    pressed = st.button("Continue", key=f"continue_overlay_{log_index}")

    return not pressed
