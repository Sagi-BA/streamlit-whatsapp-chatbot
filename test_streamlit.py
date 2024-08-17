import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="WhatsApp Bot Dashboard", page_icon=":speech_balloon:", layout="wide")

# Apply custom CSS for dark theme
st.markdown("""
<style>
.stApp {
    background-color: #1E1E1E;
    color: #FFFFFF;
}
.stTextInput > div > div > input {
    background-color: #2E2E2E;
    color: #FFFFFF;
}
</style>
""", unsafe_allow_html=True)

st.title("WhatsApp Bot Dashboard")

required_env_vars = [
    "OPENAI_API_KEY",
    "GREENAPI_ID_INSTANCE",
    "GREENAPI_ACCESS_TOKEN",
    "GROQ_API_KEY"
]

for var in required_env_vars:
    if os.getenv(var) is None or os.getenv(var) == "":
        st.error(f"{var} is not set")
        st.stop()

st.success("All required environment variables are set!")

# Create two columns
col1, col2 = st.columns(2)

with col1:
    st.subheader("Bot Logs")
    st.text_area("Latest Logs", "Bot logs will appear here", height=300)

with col2:
    st.subheader("Chat History")
    st.text_area("Recent Chat History", "Chat history will appear here", height=300)

st.write("Bot is ready to run.")

if __name__ == "__main__":
    st.write("Main function executed")
