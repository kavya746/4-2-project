import streamlit as st
from langchain_community.vectorstores import FAISS
from sentence_transformers import SentenceTransformer
from patient.chat_db import save_message, load_chat, clear_chat


# ---------- LOCAL EMBEDDINGS ---------- #
class LocalEmbeddings:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def embed_documents(self, texts):
        return self.model.encode(texts).tolist()

    def embed_query(self, text):
        return self.model.encode([text])[0].tolist()

    def __call__(self, text):
        return self.embed_query(text)


# ---------- LOAD RAG ---------- #
@st.cache_resource
def load_rag():

    with open("features/maternal_data.txt", "r") as f:
        text = f.read()

    # ✅ Split into blocks (label + content)
    chunks = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]

    embeddings = LocalEmbeddings()
    db = FAISS.from_texts(chunks, embedding=embeddings)

    return db


# ---------- QUERY IMPROVEMENT ---------- #
def improve_query(user_input):
    q = user_input.lower()

    if "avoid" in q:
        return "FOOD_AVOID pregnancy diet avoid"
    elif "eat" in q:
        return "FOOD_EAT pregnancy diet eat"
    elif "bp" in q or "pressure" in q:
        return "BP blood pressure pregnancy"
    elif "sugar" in q or "diabetes" in q:
        return "SUGAR pregnancy diabetes"
    elif "exercise" in q:
        return "EXERCISE pregnancy"
    elif "sleep" in q:
        return "SLEEP pregnancy"
    elif "vitamin" in q:
        return "VITAMINS pregnancy"
    elif "symptom" in q:
        return "SYMPTOMS pregnancy danger signs"
    else:
        return user_input


# ---------- CHATBOT PAGE ---------- #
def chatbot_page():

    if st.session_state.get("role") != "patient":
        st.error("Chatbot is only for patients")
        return

    st.markdown("<h2 style='text-align:center;'>🤖 Maternal Care Chatbot</h2>", unsafe_allow_html=True)

    db = load_rag()
    user_id = st.session_state.get("user_id")

    # ---------- LOAD CHAT ---------- #
    if "messages" not in st.session_state:
        st.session_state.messages = []

        db_data = load_chat(user_id)
        for role, msg in db_data:
            st.session_state.messages.append({"role": role, "content": msg})

    # ---------- CLEAR CHAT ---------- #
    col1, col2 = st.columns([8, 2])
    with col2:
        if st.button("🗑 Clear Chat"):
            clear_chat(user_id)
            st.session_state.messages = []
            st.rerun()

    # ---------- SHOW CHAT ---------- #
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # ---------- INPUT ---------- #
    user_input = st.chat_input("Ask your question...")

    if user_input:

        # Show user message
        st.chat_message("user").write(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})
        save_message(user_id, "user", user_input)

        # ✅ Improve query
        improved_query = improve_query(user_input)
        
        
        docs_with_score = db.similarity_search_with_score(improved_query, k=1)
        if docs_with_score:
            doc, score = docs_with_score[0]

    # 🔍 DEBUG (remove later)
            print("Score:", score)

    # ✅ Threshold check (IMPORTANT)
            if score < 1.5:
                result = doc.page_content

                if ":" in result:
                    response = result.split(":", 1)[1].strip()
                else:
                    response = result
                    
            else:
                response = "I'm not confident about this information. Please consult your doctor or healthcare professional for proper guidance."
                
        else:
            response = "I'm not confident about this information. Please consult your doctor or healthcare professional for proper guidance."

        # ---------- SHOW RESPONSE ---------- #
        st.chat_message("assistant").write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        save_message(user_id, "assistant", response)

