import streamlit as st

from agent import soru_sor

st.set_page_config(page_title="AeroCargo Copilot", page_icon="✈️")
st.title("AeroCargo Copilot")
st.caption(
    "Kapasite optimizasyonu ve operasyonel politikalar (kapasite, önceliklendirme, "
    "aksama yönetimi) hakkında soru sorabilirsiniz."
)

if "mesajlar" not in st.session_state:
    st.session_state.mesajlar = []

for mesaj in st.session_state.mesajlar:
    with st.chat_message(mesaj["role"]):
        st.markdown(mesaj["content"])

soru = st.chat_input("Bir soru sorun...")
if soru:
    st.session_state.mesajlar.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        with st.spinner("Düşünüyor..."):
            cevap = soru_sor(soru)
        st.markdown(cevap)
    st.session_state.mesajlar.append({"role": "assistant", "content": cevap})
