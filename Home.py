import streamlit as st

# Configure the page (this should be the first Streamlit command)
st.set_page_config(
    page_title="pdfGPT - AI Document Chat",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/zeeshanhxider/ChatPDF',
        'Report a bug': 'https://github.com/zeeshanhxider/ChatPDF/issues',
        'About': "# pdfGPT\nAI-powered document chat application"
    }
)

st.title("📄 Welcome to pdfGPT")
st.write("Upload a pdf and start chatting!")

# Add some helpful information
st.markdown("""
### How to use pdfGPT:
1. **Manage Tags**: Create and organize tags for your documents
2. **Manage Documents**: Upload PDF files and associate them with tags
3. **Chat With Documents**: Ask questions about your uploaded documents

Navigate using the sidebar to get started!
""")