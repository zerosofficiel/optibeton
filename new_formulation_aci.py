# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from textwrap import wrap

# =============================================
# 📚 DONNÉES DE BASE DE L'ACI 211.1-22 INTÉGRÉES
# Conversion: 1 lb/yd³ = 0.593276 kg/m³
# Conversion: 1 psi = 0.00689476 MPa
# =============================================

# Table 5.3.3 - Eau de gâchage approximative (kg/m³) et teneur en air (%)
# Basé sur un affaissement de 75 à 100 mm (3-4 in)
TABLE_5_3_3_EAU_AIR = {
    "non_air_entraine": {
        # Dmax (mm): [Eau (kg/m³), Air occlus (%)]
        9.5:  [207, 3.0],
        12.5: [199, 2.5],
        19:   [190, 2.0],
        25:   [179, 1.5],
        37.5: [166, 1.0],
        50:   [154, 0.5],
    },
    "air_entraine": {
        # Dmax (mm): [Eau (kg/m³), Air F1 (%), Air F2/F3 (%)]
        9.5:  [181, 6.0, 7.5],
        12.5: [175, 5.5, 7.0],
        19:   [168, 5.0, 6.0],
        25:   [160, 4.5, 6.0],
        37.5: [150, 4.5, 5.5],
        50:   [142, 4.0, 5.0],
    }
}

# Table 5.3.4 - Relation entre le ratio E/C et la résistance en compression
# (MPa): E/C
TABLE_5_3_4_RESISTANCE_EC = {
    "non_air_entraine": {
        48.3: 0.34, 41.4: 0.41, 34.5: 0.48, 27.6: 0.57, 20.7: 0.68, 13.8: 0.82
    },
    "air_entraine": {
        41.4: 0.33, 34.5: 0.40, 27.6: 0.48, 20.7: 0.59, 13.8: 0.74
    }
}

# Table 4.7.3 - Exigences de durabilité
# Exposition: [E/C max, f'c min (MPa)]
TABLE_4_7_3_DURABILITE = {
    "F0": [None, 17],
    "F1": [0.55, 24],
    "F2": [0.45, 31],
    "F3": [0.40, 34.5],
    "S0": [None, 17],
    "S1": [0.50, 28],
    "S2": [0.45, 31],
    "S3": [0.45, 31],
    "C0": [None, 17],
    "C1": [0.50, 28],
    "C2": [0.40, 34.5]  # béton non-précontraint
}

# Table 5.3.6 - Volume de gros granulats par unité de volume de béton
# Dmax (mm): {Module de Finesse: Volume}
TABLE_5_3_6_VOL_GROS_GRANULATS = {
    9.5:  {2.4: 0.50, 2.6: 0.48, 2.8: 0.46, 3.0: 0.44},
    12.5: {2.4: 0.59, 2.6: 0.57, 2.8: 0.55, 3.0: 0.53},
    19:   {2.4: 0.66, 2.6: 0.64, 2.8: 0.62, 3.0: 0.60},
    25:   {2.4: 0.71, 2.6: 0.69, 2.8: 0.67, 3.0: 0.65},
    37.5: {2.4: 0.75, 2.6: 0.73, 2.8: 0.71, 3.0: 0.69},
    50:   {2.4: 0.78, 2.6: 0.76, 2.8: 0.74, 3.0: 0.72},
}

# ============================================================
# 🆕 AJOUT MINIMAL : Aide AVANT la saisie de la classe (input)
# ============================================================
CLASS_DESCRIPTIONS = {
    # Gel/Dégel (F)
    "F0": ("Pas d'exposition gel/dégel",
           "Locaux intérieurs secs, éléments non exposés au gel."),
    "F1": ("Gel/dégel sans sels (exposition modérée)",
           "Ouvrages extérieurs humides mais sans sels de déverglaçage."),
    "F2": ("Gel/dégel avec humidité fréquente (sans sels)",
           "Éléments extérieurs exposés à l'eau/froid, faible à moyenne saturation."),
    "F3": ("Gel/dégel sévère avec sels",
           "Voiries salées, tabliers, rampes de parking, zones très sévères."),

    # Sulfates (S)
    "S0": ("Pas d'exposition aux sulfates",
           "Sol/eaux non agressifs en sulfates."),
    "S1": ("Sulfates faibles",
           "Milieux légèrement sulfatés."),
    "S2": ("Sulfates modérés",
           "Milieux modérément sulfatés."),
    "S3": ("Sulfates élevés",
           "Milieux fortement sulfatés (stations d'épuration, effluents)."),

    # Chlorures (C)
    "C0": ("Milieu sec ou protégé (pas de risque particulier)",
           "Locaux intérieurs secs, éléments protégés."),
    "C1": ("Risque de corrosion (sans chlorures externes)",
           "Milieux humides/urbains sans apport de chlorures."),
    "C2": ("Risque de corrosion avec chlorures externes",
           "Milieux marins/embruns, sels de voirie, éclaboussures.")
}

def _print_class_help():
    """Affiche la correspondance des classes avant la saisie utilisateur."""
    print("\n📖 Aide au choix des classes d'exposition (tapez F0-F3, S0-S3, C0-C2)")
    print("------------------------------------------------------------------")
    groupes = [
        ("Gel/Dégel (F)", ["F0", "F1", "F2", "F3"]),
        ("Sulfates (S)",  ["S0", "S1", "S2", "S3"]),
        ("Chlorures (C)", ["C0", "C1", "C2"])
    ]
    for titre, codes in groupes:
        print(f"\n▶ {titre}")
        for code in codes:
            if code in CLASS_DESCRIPTIONS:
                titre_cls, exemple = CLASS_DESCRIPTIONS[code]
                print(f"  • {code:<2}  {titre_cls}")
                for line in wrap(f"     Exemples/repères : {exemple}", width=95):
                    print(line)

# =============================================
# 🔎 Utilitaires
# =============================================
def _afficher_description_exposition(expo: str):
    if expo.upper() in CLASS_DESCRIPTIONS:
        titre, exemple = CLASS_DESCRIPTIONS[expo.upper()]
        print(f"   ↳ Classe sélectionnée {expo.upper()} : {titre}")
    else:
        print(f"   ↳ Classe sélectionnée {expo.upper()}")

def _normalize_dmax(val):
    # autoriser 40 → 37.5 etc.
    possibles = [9.5, 12.5, 19, 25, 37.5, 50]
    try:
        x = float(val)
        return min(possibles, key=lambda d: abs(d - x))
    except:
        return 19.0

# =============================================
# ⚙️ CONFIGURATION DES PARAMÈTRES D'ENTRÉE
# =============================================
def demander_parametres_utilisateur():
    print("\n🔧 PARAMÈTRES D'ENTRÉE POUR LA FORMULATION ACI 211.1-22 (CORRIGÉ)")
    print("==================================================================")

    # --- Propriétés requises du béton ---
    fc_mpa = float(input("→ Résistance caractéristique f'c (MPa) [ex: 28] : ") or 28)

    # 🆕 Afficher l'aide AVANT l'input de la classe
    _print_class_help()
    exposition = (input("→ Classe d'exposition (ex. F2, S3, C2…) : ") or "F1").upper()
    while exposition not in CLASS_DESCRIPTIONS:
        print("❗ Code inconnu. Saisir par ex. F2, S3, C2…")
        exposition = (input("→ Classe d'exposition (ex. F2, S3, C2…) : ") or "F1").upper()
    _afficher_description_exposition(exposition)

    slump_mm = float(input("→ Affaissement souhaité (mm) [ex: 90] : ") or 90)

    # --- Propriétés des granulats ---
    dmax_in = input("→ Dimension maximale des granulats Dmax (mm) [9.5, 12.5, 19, 25, 37.5, 50] [19] : ").strip() or "19"
    dmax_mm = _normalize_dmax(dmax_in)
    mf_sable = float(input("→ Module de finesse du sable Mf [ex: 2.8] : ") or 2.8)
    densite_gros_granulats_tasse_sec_kg_m3 = float(input("→ Masse volumique gros granulats tassée à sec (kg/m³) [ex: 1600] : ") or 1600)

    # --- Propriétés des matériaux (masses volumiques relatives) ---
    sg_ciment = float(input("→ Masse volumique relative ciment [3.15] : ") or 3.15)
    sg_sable = float(input("→ Masse volumique relative sable (SSD) [2.63] : ") or 2.63)
    sg_gravier = float(input("→ Masse volumique relative gravier (SSD) [2.68] : ") or 2.68)
    absorption_gravier_pct = float(input("→ Absorption gros granulats (%) [ex: 0.5] : ") or 0.5)

    # Règle existante : air entraîné si classe F*, sinon non (on garde ce comportement)
    air_entraine = exposition.startswith("F")

    return (fc_mpa, exposition, slump_mm, dmax_mm, mf_sable,
            densite_gros_granulats_tasse_sec_kg_m3, sg_ciment,
            sg_sable, sg_gravier, absorption_gravier_pct, air_entraine)

# =============================================
# 🧠 CALCUL DE LA FORMULATION (CONFORME À ACI 211.1-22)
# =============================================
def aci_formulation(fc_mpa, exposition, slump_mm, dmax_mm, mf_sable,
                   densite_gros_granulats_tasse_sec_kg_m3, sg_ciment,
                   sg_sable, sg_gravier, absorption_gravier_pct, air_entraine):

    def trouver_cle_proche(data_dict, value):
        return min(data_dict.keys(), key=lambda x: abs(x - value))

    # --- ÉTAPE 3: Estimation de l'eau de gâchage et de la teneur en air ---
    type_beton = "air_entraine" if air_entraine else "non_air_entraine"

    # Eau de base pour un affaissement de 75-100 mm (centre ~ 85-100 mm)
    dmax_valide = trouver_cle_proche(TABLE_5_3_3_EAU_AIR["non_air_entraine"], dmax_mm)
    eau_kg_base = TABLE_5_3_3_EAU_AIR[type_beton][dmax_valide][0]

    # Ajustement pour l'affaissement (règle pratique ±10 kg/m³ par ±25 mm autour de ~85 mm)
    ajustement_slump = ((slump_mm - 85.0) / 25.0) * 10.0
    eau_kg = eau_kg_base + ajustement_slump

    # Teneur en air
    if air_entraine:
        # F1 ⇒ colonne F1 ; F2/F3 ⇒ colonne F2/F3
        if exposition in ["F2", "F3"]:
            air_pct = TABLE_5_3_3_EAU_AIR[type_beton][dmax_valide][2]
        else:
            air_pct = TABLE_5_3_3_EAU_AIR[type_beton][dmax_valide][1]
    else:
        air_pct = TABLE_5_3_3_EAU_AIR[type_beton][dmax_valide][1]

    # --- ÉTAPE 4: Ratio E/C (minimum entre résistance & durabilité) ---
    # 4a. E/C basé sur la résistance (Table 5.3.4) - f'cr = f'c + 7.0 (ou +8.5 si f'c>=35 MPa)
    f_cr_mpa = fc_mpa + (8.5 if fc_mpa >= 35 else 7.0)
    points_resistance = sorted(TABLE_5_3_4_RESISTANCE_EC[type_beton].items())
    ec_resistance = np.interp(
        f_cr_mpa,
        [k for k, v in points_resistance],
        [v for k, v in points_resistance]
    )

    # 4b. E/C basé sur la durabilité (Table 4.7.3)
    ec_durabilite = TABLE_4_7_3_DURABILITE.get(exposition, [None])[0]
    if ec_durabilite is None:
        ec_durabilite = ec_resistance

    # 4c. E/C final
    ec_final = min(ec_resistance, ec_durabilite)

    # --- ÉTAPE 5: Dosage ciment ---
    ciment_kg = round(eau_kg / ec_final, 1)

    # --- ÉTAPE 6: Dosage gros granulats (Table 5.3.6) ---
    # rapprocher Mf de la valeur tabulée disponible
    mf_candidats = sorted(TABLE_5_3_6_VOL_GROS_GRANULATS[dmax_valide].keys())
    mf_valide = min(mf_candidats, key=lambda x: abs(x - mf_sable))
    vol_facteur_gg = TABLE_5_3_6_VOL_GROS_GRANULATS[dmax_valide][mf_valide]
    m_gravier_sec = vol_facteur_gg * densite_gros_granulats_tasse_sec_kg_m3
    m_gravier_ssd = round(m_gravier_sec * (1 + absorption_gravier_pct / 100), 1)

    # --- ÉTAPE 7: Sable par différence de volume (méthode des volumes absolus) ---
    v_eau = eau_kg / 1000.0
    v_ciment = ciment_kg / (sg_ciment * 1000.0)
    v_air = air_pct / 100.0
    v_gravier = m_gravier_ssd / (sg_gravier * 1000.0)

    v_sable = 1.0 - (v_eau + v_ciment + v_air + v_gravier)
    v_sable = max(0.0, v_sable)  # clip si nécessaire
    m_sable_ssd = round(v_sable * sg_sable * 1000.0, 1)

    return {
        "Paramètres retenus": {
            "Classe d'exposition": exposition,
            "Dmax (mm)": dmax_valide,
            "Module de finesse": mf_valide,
            "Ratio E/C final": round(ec_final, 2),
            "Teneur en air (%)": air_pct
        },
        "Dosages par m³ (SSD)": {
            "Eau (kg)": round(eau_kg, 1),
            "Ciment (kg)": ciment_kg,
            "Sable (kg)": m_sable_ssd,
            "Gravier (kg)": m_gravier_ssd,
        },
        "Volumes par m³": {
            "Eau": round(v_eau, 3),
            "Ciment": round(v_ciment, 3),
            "Air": round(v_air, 3),
            "Sable": round(v_sable, 3),
            "Gravier": round(v_gravier, 3),
            "Total": round(v_eau + v_ciment + v_air + v_sable + v_gravier, 3)
        }
    }

# =============================================
# 🚀 LANCEMENT ET AFFICHAGE
# =============================================
if __name__ == "__main__":
    params = demander_parametres_utilisateur()
    res = aci_formulation(*params)

    print("\n" + "="*40)
    print("📊 RÉSULTATS DE LA FORMULATION (MÉTHODE ACI)")
    print("="*40)

    print("\n📋 Paramètres Finaux Calculés:")
    for key, value in res["Paramètres retenus"].items():
        print(f"  - {key}: {value}")

    df = pd.DataFrame.from_dict(res["Dosages par m³ (SSD)"], orient="index", columns=["Masse (kg)"])
    df["Volume (m³)"] = [
        res["Volumes par m³"]["Eau"],
        res["Volumes par m³"]["Ciment"],
        res["Volumes par m³"]["Sable"],
        res["Volumes par m³"]["Gravier"],
    ]
    df.loc['Air'] = [None, res["Volumes par m³"]["Air"]]

    total_mass = df["Masse (kg)"].sum()
    df.loc['Total'] = [total_mass, res["Volumes par m³"]["Total"]]

    print("\n" + "="*40)
    print("⚖️ Composition Détaillée par m³")
    print("="*40)
    print(df.to_string(float_format="%.3f"))
    print(f"\n Densité fraîche théorique: {total_mass:.1f} kg/m³")