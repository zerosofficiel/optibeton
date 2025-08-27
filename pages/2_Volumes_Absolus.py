import streamlit as st
import pandas as pd
import plotly.express as px
from new_formulation_aci import aci_formulation
import io

st.set_page_config(page_title="Méthode des Volumes Absolus", page_icon="📊", layout="wide")

st.title("📊 Méthode des Volumes Absolus (ACI 211.1-22)")
st.subheader("Formulation du béton par la méthode des volumes absolus")

st.markdown("""
<div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
Cette application calcule la formulation de béton selon la méthode ACI 211.1-22 en utilisant 
la méthode des volumes absolus. Les calculs sont basés sur les tables normatives de l'American Concrete Institute.
</div>
""", unsafe_allow_html=True)

st.markdown("### 📋 Données d'entrée")

with st.form("formulaire_aci"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Propriétés du béton")
        fc28 = st.number_input("Résistance caractéristique à 28 jours (MPa)", 
                              min_value=10.0, max_value=80.0, step=0.5, value=25.0,
                              help="f'c - Résistance en compression à 28 jours")
        
        slump = st.number_input("Affaissement souhaité (mm)", 
                               min_value=0.0, max_value=250.0, step=5.0, value=80.0,
                               help="Slump - Affaissement mesuré au cône d'Abrams")
        
        dmax = st.number_input("Diamètre maximal du granulat (mm)", 
                              min_value=5.0, max_value=100.0, step=5.0, value=25.0,
                              help="Dmax - Dimension maximale des granulats")
        
        mf = st.number_input("Module de finesse du sable", 
                            min_value=2.0, max_value=4.0, step=0.1, value=2.8,
                            help="Module de finesse du sable (granulométrie)")
        
        # Sélection de la classe d'exposition
        st.markdown("#### Classe d'exposition")
        exposition_options = {
            "F0": "F0 - Pas d'exposition gel/dégel",
            "F1": "F1 - Gel/dégel sans sels (exposition modérée)",
            "F2": "F2 - Gel/dégel avec humidité fréquente",
            "F3": "F3 - Gel/dégel sévère avec sels",
            "S0": "S0 - Pas d'exposition aux sulfates", 
            "S1": "S1 - Sulfates faibles",
            "S2": "S2 - Sulfates modérés", 
            "S3": "S3 - Sulfates élevés",
            "C0": "C0 - Pas de risque de corrosion",
            "C1": "C1 - Risque de corrosion sans chlorures externes",
            "C2": "C2 - Risque de corrosion avec chlorures externes"
        }
        exposition = st.selectbox("Sélectionnez la classe d'exposition", 
                                 options=list(exposition_options.keys()),
                                 format_func=lambda x: exposition_options[x],
                                 index=1)
    
    with col2:
        st.markdown("#### Propriétés des matériaux")
        
        st.markdown("##### Granulats")
        dry_rodded_density = st.number_input("Masse volumique sèche des granulats (kg/m³)", 
                                           min_value=1300.0, max_value=2000.0, step=10.0, value=1600.0,
                                           help="Masse volumique des granulats secs tassés")
        
        coarse_agg_abs = st.number_input("Absorption des gros granulats (%)", 
                                       min_value=0.0, max_value=10.0, step=0.1, value=1.0,
                                       help="Pourcentage d'absorption d'eau des gros granulats")
        
        fine_agg_abs = st.number_input("Absorption du sable (%)", 
                                     min_value=0.0, max_value=10.0, step=0.1, value=2.0,
                                     help="Pourcentage d'absorption d'eau du sable")
        
        st.markdown("##### Masses volumiques")
        cement_density = st.number_input("Masse volumique du ciment (kg/m³)", 
                                       min_value=2800.0, max_value=3200.0, step=10.0, value=3150.0,
                                       help="Masse volumique absolue du ciment")
        
        sand_density = st.number_input("Masse volumique du sable SSD (kg/m³)", 
                                     min_value=2500.0, max_value=2700.0, step=10.0, value=2630.0,
                                     help="Masse volumique du sable à l'état saturé surface sèche")
        
        gravel_density = st.number_input("Masse volumique du gravier SSD (kg/m³)", 
                                       min_value=2600.0, max_value=2800.0, step=10.0, value=2680.0,
                                       help="Masse volumique du gravier à l'état saturé surface sèche")
        
        water_density = st.number_input("Masse volumique de l'eau (kg/m³)", 
                                      min_value=995.0, max_value=1005.0, step=0.1, value=1000.0,
                                      help="Masse volumique de l'eau à 20°C")
        
        st.markdown("##### Air entraîné")
        air_entrained = st.checkbox("Béton avec air entraîné", value=False,
                                   help="Cocher si le béton contient un agent entraîneur d'air")

    submitted = st.form_submit_button("🚀 Lancer la formulation", use_container_width=True)

if submitted:
    try:
        # Conversion des masses volumiques en densités relatives
        sg_ciment = cement_density / 1000
        sg_sable = sand_density / 1000
        sg_gravier = gravel_density / 1000
        sg_eau = water_density / 1000
        
        # Détermination automatique de l'air entraîné basé sur la classe d'exposition
        air_entraine_auto = exposition.startswith("F") or air_entrained
        
        with st.spinner("Calcul en cours..."):
            resultats = aci_formulation(
                fc_mpa=fc28,
                exposition=exposition,
                slump_mm=slump,
                dmax_mm=dmax,
                mf_sable=mf,
                densite_gros_granulats_tasse_sec_kg_m3=dry_rodded_density,
                sg_ciment=sg_ciment,
                sg_sable=sg_sable,
                sg_gravier=sg_gravier,
                absorption_gravier_pct=coarse_agg_abs,
                air_entraine=air_entraine_auto
            )

        st.success("✅ Calcul terminé avec succès!")
        
        # Affichage des résultats
        st.markdown("### 📊 Résultats de la formulation")
        
        # Création des onglets pour une meilleure organisation
        tab1, tab2, tab3 = st.tabs(["📋 Paramètres", "⚖️ Dosages", "📐 Volumes"])
        
        with tab1:
            st.markdown("#### Paramètres retenus")
            param_data = []
            for key, value in resultats["Paramètres retenus"].items():
                param_data.append({"Paramètre": key, "Valeur": value})
            
            param_df = pd.DataFrame(param_data)
            st.dataframe(param_df, use_container_width=True, hide_index=True)
            
            # Informations supplémentaires
            st.info(f"""
            **Notes:**
            - Classe d'exposition: {exposition_options[exposition]}
            - Air entraîné: {'Oui' if air_entraine_auto else 'Non'}
            - Le ratio E/C a été déterminé selon les exigences de résistance et de durabilité
            """)
        
        with tab2:
            st.markdown("#### Dosages par mètre cube (état SSD)")
            dosages_data = []
            for key, value in resultats["Dosages par m³ (SSD)"].items():
                dosages_data.append({"Matériau": key, "Masse (kg/m³)": value})
            
            dosages_df = pd.DataFrame(dosages_data)
            st.dataframe(dosages_df, use_container_width=True, hide_index=True)
            
            # Calcul de la densité fraîche
            total_mass = sum(resultats["Dosages par m³ (SSD)"].values())
            st.metric("**Densité fraîche théorique**", f"{total_mass:.1f} kg/m³")
            
            # Ajustements pour absorption
            st.markdown("##### 🔄 Ajustements pour absorption d'eau")
            col_adj1, col_adj2 = st.columns(2)
            with col_adj1:
                st.write(f"**Sable:** +{fine_agg_abs}% = +{resultats['Dosages par m³ (SSD)']['Sable (kg)'] * fine_agg_abs/100:.1f} kg")
            with col_adj2:
                st.write(f"**Gravier:** +{coarse_agg_abs}% = +{resultats['Dosages par m³ (SSD)']['Gravier (kg)'] * coarse_agg_abs/100:.1f} kg")
        
        with tab3:
            st.markdown("#### Volumes absolus par mètre cube")
            volumes_data = []
            for key, value in resultats["Volumes par m³"].items():
                volumes_data.append({"Composant": key, "Volume (m³/m³)": value})
            
            volumes_df = pd.DataFrame(volumes_data)
            st.dataframe(volumes_df, use_container_width=True, hide_index=True)
            
            # Diagramme circulaire des volumes
            st.markdown("##### 📊 Répartition volumétrique")
            volumes_for_chart = {
                k: v for k, v in resultats["Volumes par m³"].items() 
                if k not in ['Total'] and v > 0
            }
            
            if volumes_for_chart:
                chart_data = pd.DataFrame({
                    'Composant': list(volumes_for_chart.keys()),
                    'Volume (m³)': list(volumes_for_chart.values())
                })
                st.plotly_chart(
                    px.pie(chart_data, values='Volume (m³)', names='Composant', 
                          title="Répartition des volumes absolus"),
                    use_container_width=True
                )
        
        # Section de téléchargement
        st.markdown("---")
        st.markdown("### 💾 Télécharger les résultats")
        
        # Création d'un DataFrame complet pour l'export
        export_data = []
        for category, data_dict in resultats.items():
            for key, value in data_dict.items():
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        export_data.append({
                            "Catégorie": category,
                            "Paramètre": f"{key} - {subkey}",
                            "Valeur": subvalue
                        })
                else:
                    export_data.append({
                        "Catégorie": category,
                        "Paramètre": key,
                        "Valeur": value
                    })
        
        export_df = pd.DataFrame(export_data)
        
        # Conversion en Excel
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            # Feuille principale avec tous les résultats
            export_df.to_excel(writer, sheet_name='Résultats détaillés', index=False)
            
            # Feuille avec les dosages
            dosages_df.to_excel(writer, sheet_name='Dosages', index=False)
            
            # Feuille avec les paramètres
            param_df.to_excel(writer, sheet_name='Paramètres', index=False)
            
            # Feuille avec les volumes
            volumes_df.to_excel(writer, sheet_name='Volumes', index=False)
            
            # Ajouter une feuille avec les données d'entrée
            input_data = [
                {"Paramètre": "Résistance caractéristique f'c (MPa)", "Valeur": fc28},
                {"Paramètre": "Affaissement (mm)", "Valeur": slump},
                {"Paramètre": "Diamètre maximal granulat (mm)", "Valeur": dmax},
                {"Paramètre": "Module de finesse sable", "Valeur": mf},
                {"Paramètre": "Classe d'exposition", "Valeur": exposition_options[exposition]},
                {"Paramètre": "Masse volumique granulats secs (kg/m³)", "Valeur": dry_rodded_density},
                {"Paramètre": "Absorption gros granulats (%)", "Valeur": coarse_agg_abs},
                {"Paramètre": "Absorption sable (%)", "Valeur": fine_agg_abs},
                {"Paramètre": "Masse volumique ciment (kg/m³)", "Valeur": cement_density},
                {"Paramètre": "Masse volumique sable SSD (kg/m³)", "Valeur": sand_density},
                {"Paramètre": "Masse volumique gravier SSD (kg/m³)", "Valeur": gravel_density},
                {"Paramètre": "Masse volumique eau (kg/m³)", "Valeur": water_density},
                {"Paramètre": "Air entraîné", "Valeur": "Oui" if air_entraine_auto else "Non"}
            ]
            pd.DataFrame(input_data).to_excel(writer, sheet_name='Données entrée', index=False)
        
        excel_buffer.seek(0)
        
        # Boutons de téléchargement
        col_dl1, col_dl2 = st.columns(2)
        
        with col_dl1:
            # Téléchargement Excel
            st.download_button(
                label="📊 Télécharger en Excel (.xlsx)",
                data=excel_buffer,
                file_name="formulation_beton_aci_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col_dl2:
            # Téléchargement CSV (optionnel)
            csv = export_df.to_csv(index=False, sep=';').encode('utf-8')
            st.download_button(
                label="📝 Télécharger en CSV (.csv)",
                data=csv,
                file_name="formulation_beton_aci_results.csv",
                mime="text/csv",
                use_container_width=True
            )
        
    except Exception as e:
        st.error(f"❌ Une erreur s'est produite lors du calcul: {str(e)}")
        st.info("""
        **Veuillez vérifier:**
        - Que tous les paramètres sont valides
        - Que les valeurs sont dans les plages recommandées
        - Que la combinaison de paramètres est cohérente
        """)

# Section d'information
st.markdown("---")
st.markdown("### 📚 Informations complémentaires")

with st.expander("ℹ️ À propos de la méthode ACI 211.1-22"):
    st.markdown("""
    La **méthode ACI 211.1-22** est une méthode normative de formulation de béton développée par 
    l'American Concrete Institute. Elle utilise le principe des **volumes absolus** pour déterminer 
    les proportions optimales des constituants du béton.
    
    **Principes clés:**
    - Calcul basé sur les volumes absolus de chaque constituant
    - Respect des exigences de résistance et de durabilité
    - Prise en compte des caractéristiques des matériaux locaux
    - Adaptation aux conditions d'exposition spécifiques
    
    **Avantages:**
    - Méthode scientifiquement validée
    - Prise en compte complète des paramètres influents
    - Résultats reproductibles et fiables
    """)

with st.expander("📖 Guide des classes d'exposition"):
    st.markdown("""
    **Classes F (Gel/Dégel):**
    - **F0**: Pas d'exposition au gel/dégel
    - **F1**: Exposition modérée sans sels
    - **F2**: Exposition humide fréquente
    - **F3**: Exposition sévère avec sels déverglaçants
    
    **Classes S (Sulfates):**
    - **S0**: Pas d'exposition aux sulfates  
    - **S1**: Sulfates faibles
    - **S2**: Sulfates modérés
    - **S3**: Sulfates élevés
    
    **Classes C (Corrosion):**
    - **C0**: Pas de risque de corrosion
    - **C1**: Risque modéré sans chlorures externes
    - **C2**: Risque élevé avec chlorures externes
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray;">
<small>Application développée avec Streamlit • Méthode ACI 211.1-22 • © 2024</small>
</div>
""", unsafe_allow_html=True)