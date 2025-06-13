import streamlit as st
import base64

st.set_page_config(page_title="OptiBéton", layout="centered")

# ===== STYLE UNIVERSEL AVEC COULEUR DU LOGO =====
st.markdown("""
    <style>
    .logo-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-top: 50px;
        margin-bottom: 30px;
    }
    .logo-title {
        font-size: 3.8rem;
        font-weight: 800;
        color: #6b7280; /* Gris neutre visible en clair et sombre (logo color) */
        margin-top: 25px;
    }
    .subtitle {
        font-size: 1.6rem;
        color: #4b5563;
        margin-bottom: 50px;
    }
    .footer {
        margin-top: 80px;
        text-align: center;
        color: #6b7280;
        font-size: 1.1rem;
    }
    .btn {
        display: block;
        width: 100%;
        padding: 0.85rem 1.5rem;
        font-weight: 700;
        background-color: #1f2937;
        color: white;
        text-align: center;
        border-radius: 8px;
        border: none;
        cursor: pointer;
        font-size: 1.1rem;
        transition: 0.2s ease-in-out;
    }
    .btn:hover {
        background-color: #374151;
        transform: scale(1.03);
    }
    </style>
""", unsafe_allow_html=True)

# ===== LOGO + TITRE =====
with open("logo.png", "rb") as image_file:
    encoded = base64.b64encode(image_file.read()).decode()
    st.markdown(f"""
        <div class="logo-container">
            <img src="data:image/png;base64,{encoded}" width="190">
            <div class="logo-title">OptiBéton</div>
            <div class="subtitle">Choisissez une méthode de formulation</div>
        </div>
    """, unsafe_allow_html=True)

# ===== NAVIGATION =====
methodes = {
    "Méthode Dreux-Gorisse": "pages/1_Dreux_Gorisse.py",
    "Méthode des Volumes Absolus": "pages/2_Volumes_Absolus.py",
    "Algorithme Génétique": "pages/3_Genetique.py"
}

choix = st.selectbox("Méthode de formulation :", list(methodes.keys()))

if st.button("🚀 Accéder à cette méthode", use_container_width=True):
    st.switch_page(methodes[choix])

# ===== FOOTER =====
st.markdown("""
    <div class="footer">
        OptiBéton – développé pour les ingénieurs, chercheurs et étudiants du BTP.
    </div>
""", unsafe_allow_html=True)