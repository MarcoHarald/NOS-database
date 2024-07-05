# Imports
import streamlit as st
import streamlit_shadcn_ui as ui

# Creating two columns in Streamlit
col1, col2 = st.columns(2)

# Streamlit
with col1:
    st.metric(label="Revenue", value="$343,798", delta="-32,184")
    
# Shadcn UI
with col2:
    ui.metric_card(title="Revenue", content="$432,983", description="-74,982")