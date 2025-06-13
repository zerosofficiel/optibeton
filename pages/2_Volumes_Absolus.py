# app_volume.py ─ Interface Streamlit améliorée (Volumes Absolus)
# --------------------------------------------------------------
# Affichage harmonisé avec Dreux-Gorisse et Génétique :
#  • Cartes métriques (ciment, eau, E/C, résistance, slump, coût)
#  • Tableau récapitulatif Paramètre / Valeur
#  • Téléchargement synthèse XLSX + sortie brute TXT (xlsxwriter si dispo, sinon openpyxl)

import streamlit as st
import importlib.util, sys, io, contextlib, builtins, re, pandas as pd

# ------------------------------------------------------------------
# 0. Choix dynamique du moteur Excel (xlsxwriter ➜ openpyxl)
# ------------------------------------------------------------------
try:
    import xlsxwriter  # noqa: F401  # essayé uniquement pour vérifier la dispo
    EXCEL_ENGINE = "xlsxwriter"
except ModuleNotFoundError:
    EXCEL_ENGINE = "openpyxl"  # généralement présent avec pandas

# ------------------------------------------------------------------
# 1. Charger dynamiquement le script « volume_absolu_deep.py »
# ------------------------------------------------------------------
SCRIPT_PATH = "volume_absolu_deep.py"

import os
chemin_code = os.path.join(os.path.dirname(__file__), "..", "volume_absolu_deep.py")
spec = importlib.util.spec_from_file_location("vol_abs", chemin_code)
vol_abs = importlib.util.module_from_spec(spec)
sys.modules["vol_abs"] = vol_abs
spec.loader.exec_module(vol_abs)

# ------------------------------------------------------------------
# 2. Exécuter le calcul en détournant input() / stdout
# ------------------------------------------------------------------

def run_calcul(params: dict) -> str:
    """Exécute main_process et renvoie tout le texte affiché."""
    answers = iter(params.values())
    backup_input = builtins.input
    builtins.input = lambda _: next(answers)

    fake_out = io.StringIO()
    with contextlib.redirect_stdout(fake_out):
        vol_abs.main_process()

    builtins.input = backup_input
    return fake_out.getvalue()

# ------------------------------------------------------------------
# 3. Extraction des valeurs clés dans la sortie brute
# ------------------------------------------------------------------
CLEFS_REGX = {
    "Ciment":        r"Ciment\s*:\s*([\d.]+)",
    "Eau":           r"Eau.*?:\s*([\d.]+)",
    "Sable":         r"Sable\s*:\s*([\d.]+)",
    "Gravier":       r"Gravier\s*:\s*([\d.]+)",
    "E/C":           r"E/C\s*=\s*([\d.]+)",
    "Résistance":    r"Résistance.*?:\s*([\d.]+)",
    "Slump":         r"Affaissement.*?:\s*([\d.]+)",
    "Coût":          r"Coût.*?:\s*([\d.]+)"
}

def extraire_valeurs(txt: str) -> dict:
    d = {}
    for cle, rgx in CLEFS_REGX.items():
        m = re.search(rgx, txt)
        if m:
            d[cle] = float(m.group(1))
    # Calculs complémentaires (ratio S/G masse)
    if "Gravier" in d and "Sable" in d:
        s_ratio = d["Sable"] / (d["Sable"] + d["Gravier"])
        d["Ratio S/G masse (%)"] = round(s_ratio * 100, 1)
    return d

# ------------------------------------------------------------------
# 4. Interface Streamlit
# ------------------------------------------------------------------
st.set_page_config(page_title="⚖️ Volumes Absolus", layout="centered")

st.title("⚖️ Formulation Béton – Méthode des Volumes Absolus")

with st.form("parametres"):
    st.subheader("Paramètres généraux")

    fc28 = st.number_input("Résistance cible fc28 (MPa)", 15, 60, 25)
    air  = st.checkbox("Béton avec air entraîné", value=False)

    affaisse = st.number_input("Affaissement (mm)", 20, 200, 80, step=5)
    dmax = st.selectbox("Dmax granulats (mm)", [10, 20, 40, 80], index=1)

    adjuvant = st.selectbox("Type d’adjuvant", ["aucun", "réducteur", "superplastifiant", "chlorure"], index=0)

    mf = st.slider("Module de finesse du sable (Mf)", 2.4, 3.0, 2.6, 0.1)

    dens_s = st.number_input("Densité sable (t/m³)", 1.5, 2.9, 2.60, 0.01)
    dens_g = st.number_input("Densité gravier (t/m³)", 1.5, 3.0, 2.70, 0.01)

    submitted = st.form_submit_button("🚀 Calculer")

if submitted:
    param_order = {
        "resistance":   str(int(fc28)),
        "air_entraine": "oui" if air else "non",
        "affaissement": str(int(affaisse)),
        "dmax":         str(float(dmax)),
        "adjuvant":     adjuvant,
        "mf":           str(mf),
        "dens_sable":   str(dens_s),
        "dens_gravier": str(dens_g)
    }

    try:
        sortie = run_calcul(param_order)
        dict_vals = extraire_valeurs(sortie)

        # Sauvegarde dans session_state
        st.session_state["volume_sortie"] = sortie
        st.session_state["volume_df"] = dict_vals

        st.success("Calcul terminé ✅")

    except StopIteration:
        st.error("Erreur : le script a demandé plus de valeurs que prévu.")
    except Exception as e:
        st.exception(e)



# 🔁 AFFICHAGE DES RÉSULTATS STOCKÉS (persistants)
if "volume_sortie" in st.session_state and "volume_df" in st.session_state:
    st.success("📁 Résultats disponibles ci-dessous")

    dict_vals = st.session_state["volume_df"]
    sortie = st.session_state["volume_sortie"]

    labels = [
        ("Ciment", "Ciment (kg/m³)"),
        ("Eau", "Eau (kg/m³)"),
        ("E/C", "E/C"),
        ("Résistance", "Résistance (MPa)"),
        ("Slump", "Slump (mm)"),
        ("Coût", "Coût (FCFA/m³)")
    ]
    cols = st.columns(len(labels))
    for col, (k, lab) in zip(cols, labels):
        if k in dict_vals:
            col.metric(lab, f"{dict_vals[k]:.1f}")
        else:
            col.empty()

    df = pd.DataFrame({"Paramètre": dict_vals.keys(), "Valeur": dict_vals.values()})
    st.table(df)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine=EXCEL_ENGINE) as writer:
        df.to_excel(writer, index=False, sheet_name="Synthèse")
        pd.DataFrame({"Log": sortie.splitlines()}).to_excel(writer, index=False, sheet_name="Log")

    st.download_button("💾 Télécharger synthèse (XLSX)",
                       data=buffer.getvalue(),
                       file_name="volume_absolu_synthese.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.download_button("📄 Télécharger sortie brute (TXT)",
                       sortie.encode(),
                       "volume_absolu_log.txt")

    with st.expander("📝 Sortie détaillée du moteur"):
        st.text_area("", sortie, height=400)
