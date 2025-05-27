# app_genetique.py  –  Interface Streamlit (GA béton) – dynamique & export XLSX
import os, sys, importlib.util, builtins, io, contextlib, re
from io import BytesIO
import streamlit as st
import pandas as pd

# ── 1. Toujours travailler dans le dossier du script

# ── 2. Charger dynamiquement le moteur GA
SCRIPT_PATH = "algorithme genetique co.py"
import os
chemin_code = os.path.join(os.path.dirname(__file__), "..", "algorithme_genetique_co.py")
spec = importlib.util.spec_from_file_location("genetique", chemin_code)

ga_beton = importlib.util.module_from_spec(spec)
sys.modules["ga_beton"] = ga_beton
spec.loader.exec_module(ga_beton)

# ── 3. Monkey-patch input() pour nourrir le script
def run_optim(inputs_list):
    ans_iter = iter(inputs_list)
    backup = builtins.input
    builtins.input = lambda _="": next(ans_iter)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ga_beton.run_optimization()
    builtins.input = backup
    return buf.getvalue()

# ── 4. Parsing des infos utiles
def parse_results(txt):
    def grab(pat, cast=float):
        m = re.search(pat, txt)
        return cast(m.group(1)) if m else None
    return {
        "Ciment (kg/m³)"       : grab(r"Ciment\s*:\s*([\d.]+)"),
        "Eau (kg/m³)"          : grab(r"Eau\s*:\s*([\d.]+)"),
        "Sable (kg/m³)"        : grab(r"Sable\s*:\s*([\d.]+)"),
        "Gravier (kg/m³)"      : grab(r"Gravier\s*:\s*([\d.]+)"),
        "E/C"                  : grab(r"E/C\s*=\s*([\d.]+)"),
        "Ratio G/S (vol)"      : grab(r"Ratio G/S \(volumique\)\s*:\s*([\d.]+)"),
        "Ratio S/G masse (%)"  : grab(r"Ratio Sable/Gravier \(masse\)\s*:\s*([\d.]+)"),
        "Résistance (MPa)"     : grab(r"Résistance\s*:\s*([\d.]+)"),
        "Affaissement (mm)"    : grab(r"Affaissement\s*:\s*([\d.]+)"),
        "Coût (FCFA/m³)"       : grab(r"Coût total\s*:\s*([0-9,\s]+)", cast=lambda s: float(s.replace(",","")))
    }

# ── 5. Interface Streamlit (sans st.form)
st.set_page_config(page_title="🧬 Optimiseur Béton (GA)", layout="wide")
st.title("🧬 Formulation Béton – Algorithme Génétique")

# ------------- 1) Contraintes cibles -------------
st.subheader("1️⃣ Contraintes cibles")
col1, col2 = st.columns(2)
with col1:
    fc28  = st.number_input("Résistance cible fc28 (MPa)", 20, 50, 30, 1)
    dmax  = st.selectbox("Dmax granulats (mm)", [5, 10, 16, 20, 25], 3)
with col2:
    slump = st.number_input("Affaissement cible (mm)", 50, 200, 100, 5)
    profile_choice = st.selectbox(
        "Profil d’optimisation",
        ["1 – Résistance", "2 – Ouvrabilité", "3 – Économie", "4 – Équilibré"], 3
    )

# ---- Valeurs typiques dynamiques
typ_c = max(300, fc28 * 10)
typ_w = 150 + slump / 2
typ_s = 600
typ_g = 900

# ------------- 2) Bornes masse -------------
st.subheader("2️⃣ Bornes masse (kg/m³)")
col_min, col_max = st.columns(2)
with col_min:
    min_c = st.number_input("Min ciment", 0.0, value=0.9*typ_c, step=10.0, key="min_c")
    st.caption(f"💡 Typique : {typ_c:.0f}")
    min_w = st.number_input("Min eau",    0.0, value=0.9*typ_w, step=5.0,  key="min_w")
    st.caption(f"💡 Typique : {typ_w:.0f}")
    min_s = st.number_input("Min sable",  0.0, value=0.9*typ_s, step=10.0, key="min_s")
    st.caption(f"💡 Typique : {typ_s}")
    min_g = st.number_input("Min gravier",0.0, value=0.9*typ_g, step=10.0, key="min_g")
    st.caption(f"💡 Typique : {typ_g}")
with col_max:
    max_c = st.number_input("Max ciment",  0.0, value=1.1*typ_c, step=10.0, key="max_c")
    st.caption(f"💡 Typique : {typ_c:.0f}")
    max_w = st.number_input("Max eau",     0.0, value=1.1*typ_w, step=5.0,  key="max_w")
    st.caption(f"💡 Typique : {typ_w:.0f}")
    max_s = st.number_input("Max sable",   0.0, value=1.1*typ_s, step=10.0, key="max_s")
    st.caption(f"💡 Typique : {typ_s}")
    max_g = st.number_input("Max gravier", 0.0, value=1.1*typ_g, step=10.0, key="max_g")
    st.caption(f"💡 Typique : {typ_g}")

# ------------- 3) Coûts -------------
st.subheader("3️⃣ Coûts unitaires (FCFA/kg)")
cost_c = st.number_input("Ciment",  value=1200.0, step=50.0, min_value=0.0)
cost_w = st.number_input("Eau",     value=1.0,    step=0.5,  min_value=0.0)
cost_s = st.number_input("Sable",   value=800.0,  step=10.0, min_value=0.0)
cost_g = st.number_input("Gravier", value=700.0,  step=10.0, min_value=0.0)

# ------------- 4) Propriétés granulats -------------
st.subheader("4️⃣ Propriétés granulats")
mf    = st.slider("Module de finesse sable (Mf)", 2.0, 3.5, 2.5, 0.05)
rho_s = st.number_input("ρ sable (kg/m³)",   0.0, value=1600.0, step=10.0)
rho_g = st.number_input("ρ gravier (kg/m³)", 0.0, value=1500.0, step=10.0)

# ------------- 5) Paramètres GA -------------
with st.expander("5️⃣ Paramètres de l’algorithme génétique (avancé)", expanded=True):
    colA, colB = st.columns(2)
    with colA:
        pop_size = st.number_input("POP_SIZE", 20, 500, 100, 10,
                                   help="Nombre de solutions testées par génération.")
        mut_rate = st.slider("MUTATION_RATE", 0.05, 0.5, 0.15, 0.01,
                             help="Probabilité de mutation.")
    with colB:
        gen_nbr  = st.number_input("N_GENERATIONS", 10, 500, 80, 10,
                                   help="Nombre d'itérations.")
        n_parent = st.number_input("N_PARENTS", 5, 200, 20, 1,
                                   help="Meilleures solutions conservées.")

just_calculated = False

# ------------- Bouton de lancement -------------
if st.button("🚀 Lancer l’optimisation"):
    inputs_script = [
        "o",
        str(pop_size), str(gen_nbr), str(mut_rate), str(n_parent),
        str(fc28), str(slump), str(dmax),
        str(min_c), str(max_c), str(min_w), str(max_w),
        str(min_s), str(max_s), str(min_g), str(max_g),
        str(cost_c), str(cost_w), str(cost_s), str(cost_g),
        str(mf), str(rho_s), str(rho_g),
        profile_choice.split(" ")[0]
    ]

    try:
        raw_output = run_optim(inputs_script)
        st.success("Optimisation terminée ✅")
        just_calculated = True

        # -- Résumé structuré
        info = parse_results(raw_output)
        met1, met2, met3, met4, met5, met6 = st.columns(6)
        met1.metric("Ciment (kg/m³)", info["Ciment (kg/m³)"])
        met2.metric("Eau (kg/m³)",    info["Eau (kg/m³)"])
        met3.metric("E/C",            f'{info["E/C"]:.3f}' if info["E/C"] else "—")
        met4.metric("Résistance (MPa)", info["Résistance (MPa)"])
        met5.metric("Slump (mm)",       info["Affaissement (mm)"])
        met6.metric("Coût (FCFA/m³)",
                    f'{info["Coût (FCFA/m³)"]:,.0f}' if info["Coût (FCFA/m³)"] else "—")

        st.markdown("---")
        df_summary = pd.DataFrame([
            ["Ciment (kg/m³)",      info["Ciment (kg/m³)"]],
            ["Eau (kg/m³)",         info["Eau (kg/m³)"]],
            ["Sable (kg/m³)",       info["Sable (kg/m³)"]],
            ["Gravier (kg/m³)",     info["Gravier (kg/m³)"]],
            ["E/C",                 round(info["E/C"],3) if info["E/C"] else None],
            ["Ratio G/S (vol)",     info["Ratio G/S (vol)"]],
            ["Ratio S/G masse (%)", info["Ratio S/G masse (%)"]],
            ["Résistance (MPa)",    info["Résistance (MPa)"]],
            ["Slump (mm)",          info["Affaissement (mm)"]],
            ["Coût (FCFA/m³)",      info["Coût (FCFA/m³)"]]
        ], columns=["Paramètre", "Valeur"])
        st.table(df_summary)
        # -- Sauvegarde pour persistance
        st.session_state["ga_raw"] = raw_output
        st.session_state["ga_info"] = info
        st.session_state["ga_df"] = df_summary


        # -- Export XLSX (openpyxl)
        xls_buf = BytesIO()
        with pd.ExcelWriter(xls_buf, engine="openpyxl") as writer:
            df_summary.to_excel(writer, index=False, sheet_name="Synthese")
        st.download_button(
            "📥 Télécharger synthèse (XLSX)",
            xls_buf.getvalue(),
            "synthese_GA.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # -- Export TXT brut
        st.download_button(
            "📥 Télécharger sortie brute (TXT)",
            raw_output.encode('utf-8'),
            "sortie_GA_brute.txt",
            "text/plain"
        )

        with st.expander("🔍 Sortie détaillée du moteur"):
            st.text(raw_output)

    except StopIteration:
        st.error("Flux d’entrées désynchronisé – vérifiez l’ordre des champs.")
    except Exception as exc:
        st.exception(exc)



# 🔁 AFFICHAGE PERSISTANT SI DONNÉES DÉJÀ DISPONIBLES
if not just_calculated and "ga_raw" in st.session_state and "ga_df" in st.session_state:
    st.success("📁 Résultats disponibles – session active")
    raw_output = st.session_state["ga_raw"]
    info = st.session_state["ga_info"]
    df_summary = st.session_state["ga_df"]

    met1, met2, met3, met4, met5, met6 = st.columns(6)
    met1.metric("Ciment (kg/m³)", info["Ciment (kg/m³)"])
    met2.metric("Eau (kg/m³)",    info["Eau (kg/m³)"])
    met3.metric("E/C",            f'{info["E/C"]:.3f}' if info["E/C"] else "—")
    met4.metric("Résistance (MPa)", info["Résistance (MPa)"])
    met5.metric("Slump (mm)",       info["Affaissement (mm)"])
    met6.metric("Coût (FCFA/m³)", f'{info["Coût (FCFA/m³)"]:,.0f}' if info["Coût (FCFA/m³)"] else "—")

    st.markdown("---")
    st.table(df_summary)

    xls_buf = BytesIO()
    with pd.ExcelWriter(xls_buf, engine="openpyxl") as writer:
        df_summary.to_excel(writer, index=False, sheet_name="Synthese")
    st.download_button(
        "📥 Télécharger synthèse (XLSX)",
        xls_buf.getvalue(),
        "synthese_GA.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="dl_xlsx"
    )

    st.download_button(
        "📥 Télécharger sortie brute (TXT)",
        raw_output.encode("utf-8"),
        "sortie_GA_brute.txt",
        "text/plain",
        key="dl_txt"
    )

    with st.expander("🔍 Sortie détaillée du moteur"):
        st.text(raw_output)
