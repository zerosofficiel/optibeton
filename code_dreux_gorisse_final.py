# -*- coding: utf-8 -*-
# Code optimisé et corrigé - Version exécutable directement dans VSCode

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d, RBFInterpolator
import math
import pandas as pd

def main():
    # ============================================
    # PHASE 1 : COLLECTE DE TOUTES LES ENTREES
    # ============================================
    
    print("\n⚡ OPTIMISATEUR DE FORMULATION DE BÉTON DREUX-GORISSE ⚡")
    print("=====================================================")
    
    # 1.1 Paramètres granulométriques
    print("\n🔍 GRANULOMÉTRIE")
    diams = choisir_diametres()
    granulats = saisir_granulats(diams)
    mf_auto = detecter_module_finesse(granulats, diams)
    Dmax = max(d for g in granulats.values() for d,v in zip(diams, g) if v is not None)
    
    # 1.2 Paramètres béton
    print("\n🧱 CARACTÉRISTIQUES DU BÉTON")
    fc28 = float(input('Résistance caractéristique fc28 (MPa) : '))
    qualite_granulats = input('Qualité des granulats (Excellente/Bonne/Passable) : ')
    denomination_ciment = input('Dénomination ciment (ex: CEM I 32.5) : ')
    affaissement_cm = float(input('Affaissement (cm) : '))
    
    # 1.3 Propriétés granulats
    print("\n🔶 PROPRIÉTÉS DES GRANULATS")
    type_sable = input("Type de sable (roulé/concassé) : ").strip().lower()
    while type_sable not in ["roulé", "concassé"]:
        type_sable = input("Entrez 'roulé' ou 'concassé' : ").strip().lower()
        
    type_gravier = input("Type de gravier (roulé/concassé) : ").strip().lower()
    while type_gravier not in ["roulé", "concassé"]:
        type_gravier = input("Entrez 'roulé' ou 'concassé' : ").strip().lower()
    
    # 1.4 Masses volumiques
    print("\n📏 MASSE VOLUMIQUE DES GRANULATS (en kg/m³)")
    rho_granulats = {}
    for nom in granulats.keys():
        if "sable" in nom.lower():
            default_value = 2650
            prompt = f"Masse volumique du sable [{nom}] (ex: {default_value} kg/m³) : "
        else:
            default_value = 2600
            prompt = f"Masse volumique du gravier [{nom}] (ex: {default_value} kg/m³) : "
        
        while True:
            try:
                rho_input = input(prompt).strip()
                rho = float(rho_input) if rho_input else default_value
                if rho <= 0:
                    print("⚠️ La masse volumique doit être positive.")
                    continue
                rho_granulats[nom] = rho
                break
            except ValueError:
                print("⚠️ Veuillez entrer un nombre valide.")
    
    # 1.5 Paramètres méthode Dreux
    print("\n⚙ PARAMÈTRES MÉTHODE DREUX-GORISSE")
    forme, vibration, mfs, kp = demander_parametres_Kprime(mfs_auto=mf_auto, forme_defaut=type_sable)
    
    # ============================================
    # PHASE 2 : CALCULS
    # ============================================
    
    # 2.1 Calcul préliminaire
    fcm = fc28 * 1.15
    sigma_c28 = classe_vraie_ciment(denomination_ciment)
    G = determiner_G(Dmax, qualite_granulats)
    rapport_CE = fcm / (G * sigma_c28) + G
    
    # Interpolation RBF pour Copt
    points = np.array([[1.6, 8], [2.0, 10], [2.4, 2]])
    copt_values = np.array([327.27, 427.27, 425.00])
    rbf_model = RBFInterpolator(points, copt_values, kernel='thin_plate_spline')
    Copt = float(rbf_model([[rapport_CE, affaissement_cm]])[0])
    
    # 2.2 Calcul K'
    dosage_standard = determiner_dosage_standard(Copt)
    Kp = calcul_Kprime(forme, vibration, dosage_standard, mfs, kp)
    
    # 2.3 Suite des calculs
    courbe = courbe_reference(Dmax, Kp)
    lignes, inters, proportions = calcul_proportions(granulats, diams, courbe)
    
    # Calcul des proportions
    n_granulats = len(granulats)
    p_sable_vol = proportions[list(proportions.keys())[0]]/100
    p_g1_vol = proportions[list(proportions.keys())[1]]/100
    p_g2_vol = proportions[list(proportions.keys())[2]]/100 if n_granulats > 2 else 0.0
    p_g3_vol = proportions[list(proportions.keys())[3]]/100 if n_granulats > 3 else 0.0
    
    # Calculs eau corrigée
    correction_pct = get_correction_Dmax(Dmax)
    E = Copt / rapport_CE
    E_corrige = E * (1 + correction_pct / 100)
    
    # Plasticité/serrage
    plasticite, serrage = evaluer_ouvrabilite(affaissement_cm)
    
    # Calcul gamma
    gamma_brut = interpoler_gamma(plasticite, serrage, Dmax)
    gamma_corrige = gamma_brut + correction_gamma(type_sable, type_gravier)
    
    # ============================================
    # CALCULS VOLUMES ET MASSES
    # ============================================
    
    rho_ciment = 3100  # kg/m³
    
    # Volumes de base
    Vc = max(Copt / rho_ciment, 0)
    Vg = max(gamma_corrige - Vc, 0)
    Ve = max(E_corrige / 1000, 0)
    
    # Ajustement volume total
    total_vol = Vc + Vg + Ve
    if total_vol > 1.0:
        ratio = 1.0 / total_vol
        Vc *= ratio
        Vg *= ratio
        Ve *= ratio
    
    # Conversion en litres
    Vc_l = Vc * 1000
    Vg_l = Vg * 1000
    Ve_l = Ve * 1000
    
    # Volumes spécifiques
    Vs = max(Vg * p_sable_vol, 0)
    Vg1 = max(Vg * p_g1_vol, 0)
    Vg2 = max(Vg * p_g2_vol, 0) if n_granulats > 2 else 0.0
    Vg3 = max(Vg * p_g3_vol, 0) if n_granulats > 3 else 0.0
    
    # Conversion en litres
    Vs_l = Vs * 1000
    Vg1_l = Vg1 * 1000
    Vg2_l = Vg2 * 1000 if n_granulats > 2 else 0.0
    Vg3_l = Vg3 * 1000 if n_granulats > 3 else 0.0
    
    # Masses
    Ms = max(Vs * rho_granulats[list(granulats.keys())[0]], 0)
    Mg1 = max(Vg1 * rho_granulats[list(granulats.keys())[1]], 0)
    Mg2 = max(Vg2 * rho_granulats[list(granulats.keys())[2]], 0) if n_granulats > 2 else 0.0
    Mg3 = max(Vg3 * rho_granulats[list(granulats.keys())[3]], 0) if n_granulats > 3 else 0.0
    Mc = max(Copt, 0)
    Me = max(E_corrige, 0)
    
    # Contrôles
    warnings = []
    if not (0 <= affaissement_cm <= 12):
        warnings.append("❌ Affaissement hors plage 0-12 cm")
    if not (0.9 <= rapport_CE <= 2.7):
        warnings.append("❌ Rapport C/E hors plage 0.9-2.7")
    if Copt > 400:
        warnings.append("⚠️ Copt > 400 kg/m³ : adjuvant nécessaire")
    if Copt < 200:
        warnings.append("⚠️ Copt très faible")
    
    if Vc <= 0 or Vg <= 0 or Ve <= 0:
        warnings.append("⚠️ Volume(s) nul(s) ou négatif(s)")
    
    if abs((Vc + Vg + Ve) - 1.0) > 0.01:
        warnings.append(f"⚠️ Somme volumes = {(Vc + Vg + Ve)*1000:.1f} l")
    
    if abs(sum(proportions.values()) - 100) > 1:
        warnings.append(f"⚠️ Somme proportions = {sum(proportions.values()):.1f}%")
    
    for nom, rho in rho_granulats.items():
        if "sable" in nom.lower() and not (2400 <= rho <= 2800):
            warnings.append(f"⚠️ ρ {nom} = {rho} kg/m³")
        elif "gravier" in nom.lower() and not (2500 <= rho <= 2700):
            warnings.append(f"⚠️ ρ {nom} = {rho} kg/m³")
    
    # ============================================
    # PHASE 3 : RESULTATS
    # ============================================
    
    print("\n📊 PROPORTIONS CALCULÉES :")
    for nom, pr in proportions.items():
        print(f"- {nom} : {pr:.1f}%")
    
    print("\n🔍 SYNTHÈSE DES PARAMÈTRES :")
    print(f"- Forme : Sable={type_sable}, Gravier={type_gravier}")
    print(f"- Copt : {Copt:.1f} kg/m³")
    print(f"- Catégorie K' : {dosage_standard}")
    print(f"- K' final : {Kp:.2f}")
    print("\n📏 MASSE VOLUMIQUE UTILISÉE :")
    for nom, rho in rho_granulats.items():
        print(f"- {nom} : {rho:.0f} kg/m³")
    
    # Préparation des résultats
    resultats = {
        "Description": [
            "Volume ciment (l)", "Volume granulats (l)", "Volume eau (l)",
            f"Volume {list(granulats.keys())[0]} (l)",
            f"Volume {list(granulats.keys())[1]} (l)",
            f"Volume {list(granulats.keys())[2]} (l)" if n_granulats > 2 else None,
            f"Volume {list(granulats.keys())[3]} (l)" if n_granulats > 3 else None,
            "Masse ciment (kg)", "Masse eau (kg)",
            f"Masse {list(granulats.keys())[0]} (kg)",
            f"Masse {list(granulats.keys())[1]} (kg)",
            f"Masse {list(granulats.keys())[2]} (kg)" if n_granulats > 2 else None,
            f"Masse {list(granulats.keys())[3]} (kg)" if n_granulats > 3 else None,
            "Avertissements"
        ],
        "Valeur": [
            round(Vc_l, 1), round(Vg_l, 1), round(Ve_l, 1),
            round(Vs_l, 1), round(Vg1_l, 1),
            round(Vg2_l, 1) if n_granulats > 2 else None,
            round(Vg3_l, 1) if n_granulats > 3 else None,
            round(Mc, 1), round(Me, 1),
            round(Ms, 1), round(Mg1, 1),
            round(Mg2, 1) if n_granulats > 2 else None,
            round(Mg3, 1) if n_granulats > 3 else None,
            " / ".join(warnings) if warnings else "✅ OK"
        ]
    }
    
    # Nettoyage des valeurs None
    resultats["Description"] = [x for x in resultats["Description"] if x is not None]
    resultats["Valeur"] = [x for x in resultats["Valeur"] if x is not None]
    
    df = pd.DataFrame(resultats)
    
    print("\n📊 RÉSULTATS FINAUX :")
    print(df.to_string(index=False))
    
    # Visualisation
    tracer(granulats, diams, courbe, lignes, inters, proportions)

# ============================================
# FONCTIONS AUXILIAIRES
# ============================================

def determiner_dosage_standard(Copt):
    if Copt >= 400: return "400+fluid"
    elif Copt >= 350: return "400"
    elif Copt >= 300: return "350"
    elif Copt >= 250: return "300"
    elif Copt >= 200: return "250"
    else: return "200"

def demander_parametres_Kprime(mfs_auto=None, forme_defaut=None):
    forme = forme_defaut or input("Forme (roulé/concassé) : ").strip().lower()
    while forme not in ["roulé", "concassé"]:
        forme = input("Entrez 'roulé' ou 'concassé' : ").strip().lower()
        
    vibration = input("Vibration (faible/normale/puissante) : ").strip().lower()
    while vibration not in ["faible", "normale", "puissante"]:
        vibration = input("Entrez 'faible', 'normale' ou 'puissante' : ").strip().lower()
        
    if mfs_auto:
        mfs = mfs_auto
    else:
        mfs = float(input("Module finesse sable (ex: 2.5) : ").strip())
        
    pomp = input("Pompabilité (non/pompable/très pompable) : ").strip().lower()
    while pomp not in ["non", "pompable", "très pompable"]:
        pomp = input("Choix (non/pompable/très pompable) : ").strip().lower()
    kp = {"non": 0, "pompable": 5, "très pompable": 10}[pomp]
    
    return forme, vibration, mfs, kp

def choisir_diametres():
    print("\n🔍 Choix de la norme de tamisage :")
    print("1 - 🇫🇷 NFP 18-540 (sables + graviers)")
    print("2 - 🇪🇺 EN 933-2 (EN 12620)")
    print("3 - ✅ Tous les tamis disponibles")
    choix = input("Votre choix (1/2/3) : ").strip()
    if choix == "1":
        return [0.08, 0.16, 0.32, 0.63, 1.25, 2.5, 5.0, 6.3, 8, 10, 12.5, 16, 20, 25, 31.5]
    elif choix == "2":
        return [0.125, 0.25, 0.5, 1, 2, 4, 6.3, 8, 10, 12.5, 16, 20, 25, 31.5, 63]
    else:
        return [63, 50, 40, 31.5, 25, 20, 16, 12.5, 10, 8, 6.3, 5, 4, 2.5, 2, 1.25, 1,
                0.63, 0.5, 0.315, 0.25, 0.16, 0.125, 0.08, 0.063]

def saisir_granulats(diams):
    granulats = {}
    n = int(input("Nombre de granulats (2 à 4) : "))
    for i in range(n):
        nom = input(f"Nom granulat {i+1} : ") or f"Granulat_{i+1}"
        refus = []
        for d in diams:
            val = input(f"  Tamis {d} mm : ").strip()
            refus.append(float(val) if val else None)
        granulats[nom] = refus
    return granulats

def detecter_module_finesse(granulats, diams):
    tamis_mf = [0.08, 0.16, 0.315, 0.63, 1.25, 2.5, 5.0]
    for nom, valeurs in granulats.items():
        if "sable" in nom.lower():
            total = 0
            for tm in tamis_mf:
                if tm in diams:
                    idx = diams.index(tm)
                    if idx < len(valeurs) and valeurs[idx] is not None:
                        total += 100 - valeurs[idx]
            mf = total / 100
            print(f"✅ Module de finesse (détecté sur '{nom}') : Mf = {mf:.2f}")
            return mf
    return None

def calcul_Kprime(forme, vibration, dosage, mfs, kp):
    tableau_K = {
        "faible": {
            "roulé": {"400+fluid":-2,"400":0,"350":2,"300":4,"250":6,"200":8},
            "concassé": {"400+fluid":0,"400":2,"350":4,"300":6,"250":8,"200":10}
        },
        "normale": {
            "roulé": {"400+fluid":-4,"400":-2,"350":0,"300":2,"250":4,"200":8},
            "concassé": {"400+fluid":-2,"400":0,"350":2,"300":4,"250":6,"200":8}
        },
        "puissante": {
            "roulé": {"400+fluid":-6,"400":-4,"350":-2,"300":0,"250":2,"200":4},
            "concassé": {"400+fluid":-4,"400":-2,"350":0,"300":2,"250":4,"200":6}
        }
    }
    K = tableau_K[vibration][forme][dosage]
    Ks = 6 * mfs - 15
    Kprime = K + Ks + kp
    print(f"Coefficients : K={K}, Ks={Ks:.2f}, Kp={kp} → K'={Kprime:.2f}")
    return Kprime

def interpoler(gr, cible, diams, nom="", role=""):
    di = [d for d, v in zip(diams, gr) if v is not None]
    va = [v for v in gr if v is not None]
    if not va:
        return None, None
    if min(va) <= cible <= max(va):
        f = interp1d(va, di, kind='linear')
        return float(f(cible)), cible
    else:
        candidats = [v for v in va if abs(v - cible) <= 10]
        if not candidats:
            print(f"⚠️ Point {cible}% introuvable pour '{nom}'")
            return None, None
        v_proche = min(candidats, key=lambda v: abs(v - cible))
        print(f"🔄 Point {cible}% remplacé par {v_proche}% pour '{nom}'")
        f = interp1d(va, di, kind='linear')
        return float(f(v_proche)), v_proche

def courbe_reference(Dmax, Kprime):
    XA = Dmax/2 if Dmax <= 20 else (math.log10(Dmax)+38)/2
    YA = 50 - math.sqrt(Dmax) + Kprime
    return [(0.08, 0), (XA, YA), (Dmax, 100)]

def calcul_proportions(granulats, diams, courbe):
    noms = list(granulats.keys())
    fO = interp1d(np.log10([x for x, _ in courbe]), 
                  [y for _, y in courbe], fill_value="extrapolate")
    inters, lignes, projections = [], [], []
    for i in range(len(noms) - 1):
        g1, g2 = granulats[noms[i]], granulats[noms[i+1]]
        d1, p1 = interpoler(g1, 95, diams, noms[i], "95")
        d2, p2 = interpoler(g2, 5, diams, noms[i+1], "5")
        if None in [d1, p1, d2, p2] or d1 == d2:
            continue
        a = (p2 - p1) / (np.log10(d2) - np.log10(d1))
        b = p1 - a * np.log10(d1)
        xlog = np.linspace(np.log10(min(d1,d2)), np.log10(max(d1,d2)), 1000)
        xC_log = xlog[np.argmin(np.abs(a * xlog + b - fO(xlog)))]
        xC, yC = 10 ** xC_log, a * xC_log + b
        lignes.append(((d1,p1),(d2,p2)))
        inters.append((xC, yC))
        projections.append(yC)
    proportions = {}
    if projections:
        noms_util = noms[:len(projections)+1]
        proportions[noms_util[0]] = projections[0]
        for i in range(1, len(projections)):
            proportions[noms_util[i]] = projections[i] - projections[i-1]
        proportions[noms_util[-1]] = 100 - projections[-1]
    return lignes, inters, proportions

def tracer(granulats, diams, courbe, lignes, inters, proportions):
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xscale("log")
    ax.set_xlabel("Tamis (mm)")
    ax.set_ylabel("% passant")
    ax.set_title("Dreux-Gorisse : analyse multi-granulats")
    ax.grid(True, which='both', linestyle='--', alpha=0.5)

    for nom, vals in granulats.items():
        d = [d for d,v in zip(diams, vals) if v is not None]
        v = [v for v in vals if v is not None]
        label = f"{nom} ({proportions[nom]:.1f}%)" if nom in proportions else nom
        ax.plot(d, v, 'o-', label=label)

    xref, yref = zip(*courbe)
    ax.plot(xref, yref, 'k--', label="OAB")

    for (x1, y1), (x2, y2) in lignes:
        ax.plot([x1, x2], [y1, y2], 'r--')

    for x, y in inters:
        ax.plot(x, y, 'ro')
        ax.annotate(f"{y:.1f}%", (x, y), textcoords="offset points", xytext=(5, -10), fontsize=9)
        ax.axhline(y, color='gray', linestyle=':', linewidth=1)

    ax.legend()
    plt.tight_layout()
    plt.show()

def classe_vraie_ciment(denomination):
    mapping = {"32.5": 45, "42.5": 55, "52.5": 60}
    return mapping.get(denomination.strip().split()[-1], 45)

def determiner_G(Dmax, qualite):
    if Dmax <= 12.5:
        return {"Excellente": 0.55, "Bonne": 0.45, "Passable": 0.35}[qualite]
    elif Dmax <= 31.5:
        return {"Excellente": 0.60, "Bonne": 0.50, "Passable": 0.40}[qualite]
    else:
        return {"Excellente": 0.65, "Bonne": 0.55, "Passable": 0.45}[qualite]

def get_correction_Dmax(Dmax):
    table_corrections = {5: +15, 8: +9, 12.5: +4, 20: 0, 31.5: -4, 50: -8, 80: -12}
    d_vals = np.array(list(table_corrections.keys()))
    correction_vals = np.array(list(table_corrections.values()))
    return np.interp(Dmax, d_vals, correction_vals)

def evaluer_ouvrabilite(affaissement_cm):
    """
    Traduit l’affaissement en plasticité et serrage compatibles avec la table gamma_table.
    Cette version garantit que toutes les sorties sont reconnues par l’interpolation.
    """
    if affaissement_cm <= 2:
        return "Ferme", "Vibration puissante"
    elif affaissement_cm <= 5:
        return "Ferme", "Vibration normale"
    elif affaissement_cm <= 9:
        return "Plastique", "Vibration normale"
    elif affaissement_cm <= 13:
        return "Mou", "Piquage"
    elif affaissement_cm <= 15:
        return "Mou", "Piquage"
    else:
        return "Mou", "Piquage"


def interpoler_gamma(plasticite, serrage, Dmax):
    gamma_table = {
        "Mou": {
            "Piquage": {5:0.750, 8:0.780, 12.5:0.795, 20:0.805, 31.5:0.810, 50:0.815, 80:0.820},
            "Vibration faible": {5:0.755, 8:0.785, 12.5:0.800, 20:0.810, 31.5:0.815, 50:0.820, 80:0.825},
            "Vibration normale": {5:0.760, 8:0.790, 12.5:0.805, 20:0.815, 31.5:0.820, 50:0.825, 80:0.830},
        },
        "Plastique": {
            "Piquage": {5:0.760, 8:0.790, 12.5:0.805, 20:0.815, 31.5:0.820, 50:0.825, 80:0.830},
            "Vibration faible": {5:0.765, 8:0.795, 12.5:0.810, 20:0.820, 31.5:0.825, 50:0.830, 80:0.835},
            "Vibration normale": {5:0.770, 8:0.800, 12.5:0.815, 20:0.825, 31.5:0.830, 50:0.835, 80:0.840},
            "Vibration puissante": {5:0.775, 8:0.805, 12.5:0.820, 20:0.830, 31.5:0.835, 50:0.840, 80:0.845},
        },
        "Ferme": {
            "Vibration faible": {5:0.775, 8:0.805, 12.5:0.820, 20:0.830, 31.5:0.835, 50:0.840, 80:0.845},
            "Vibration normale": {5:0.780, 8:0.810, 12.5:0.825, 20:0.835, 31.5:0.840, 50:0.845, 80:0.850},
            "Vibration puissante": {5:0.785, 8:0.815, 12.5:0.830, 20:0.840, 31.5:0.845, 50:0.850, 80:0.855},
        }
    }

    try:
        d_vals = np.array(list(gamma_table[plasticite][serrage].keys()))
        gamma_vals = np.array(list(gamma_table[plasticite][serrage].values()))
        return np.interp(Dmax, d_vals, gamma_vals)
    except KeyError:
        print(f"⚠️ Combinaison non trouvée: {plasticite}/{serrage} - Valeurs par défaut utilisées")
        d_vals = np.array(list(gamma_table["Plastique"]["Vibration normale"].keys()))
        gamma_vals = np.array(list(gamma_table["Plastique"]["Vibration normale"].values()))
        return np.interp(Dmax, d_vals, gamma_vals)

def correction_gamma(type_sable, type_gravier):
    if type_sable == "roulé" and type_gravier == "concassé":
        return -0.01
    elif type_sable == "concassé" and type_gravier == "concassé":
        return -0.03
    return 0.0

if __name__ == "__main__":
    main()
