# Code optimisé pour la formulation de béton avec toutes les fonctionnalités originales

def determiner_rapport_e_c_interactif():
    """Étape 1 : Détermine le rapport E/C en fonction de la résistance et de la présence d'air"""
    print("🎯 Étape 1 : Objectif et déduction du rapport E/C (interactif avec arrondi par excès)\n")
    
    # Tableaux de référence
    tableau_sans_air = {15: 0.79, 20: 0.69, 25: 0.61, 30: 0.54, 35: 0.47, 40: 0.42, 45: 0.38}
    tableau_avec_air = {15: 0.70, 20: 0.60, 25: 0.52, 30: 0.45, 35: 0.39, 40: 0.34, 45: 0.30}

    try:
        resistance_voulue = int(input("📌 Entrez la résistance souhaitée (MPa) : "))
    except ValueError:
        print("❌ Entier requis.")
        return None, None, None

    air_entraine = input("🌬️ Béton avec air entraîné ? (oui/non) : ").strip().lower() in ["oui", "o", "y", "yes"]
    tableau = tableau_avec_air if air_entraine else tableau_sans_air
    
    # Trouve la résistance immédiatement supérieure dans le tableau
    resistance_choisie = next((r for r in sorted(tableau) if resistance_voulue <= r), max(tableau))
    rapport = tableau[resistance_choisie]

    print(f"\n📊 Résultat Étape 1 :")
    print(f"✔️ Résistance retenue : {resistance_choisie} MPa")
    print(f"🔄 Rapport E/C : {rapport:.2f}")
    print(f"🔘 Béton : {'Avec air entraîné' if air_entraine else 'Sans air entraîné'}")
    
    return resistance_choisie, rapport, air_entraine


def interpolation(val1, val2, x1, x2, x):
    """Effectue une interpolation linéaire entre deux points"""
    return val1 if x2 == x1 else val1 + ((val2 - val1) * (x - x1) / (x2 - x1))


def determiner_eau_gachage_interactif(air_entraine):
    """Étape 2 : Détermine la quantité d'eau de gâchage nécessaire"""
    print("\n🎯 Étape 2 : Détermination de la quantité d'eau (kg/m³)")
    
    try:
        affaissement = int(input("📌 Affaissement souhaité (mm) : "))
        dmax = float(input("📌 Dmax granulats (mm, ex: 11, 20, 35) : "))
    except ValueError:
        print("❌ Entier ou décimal requis.")
        return None, None

    # Tableaux de référence pour l'eau de gâchage
    eau_sans_air = {
        10: {50: 207, 100: 228, 175: 243},
        20: {50: 190, 100: 205, 175: 216},
        40: {50: 166, 100: 181, 175: 190},
        80: {50: 130, 100: 145, 175: 160}
    }
    
    eau_avec_air = {
        10: {50: 181, 100: 202, 175: 216},
        20: {50: 168, 100: 184, 175: 197},
        40: {50: 150, 100: 165, 175: 174},
        80: {50: 122, 100: 133, 175: 154}
    }

    def plage_affaissement(val):
        """Détermine la plage d'affaissement standard"""
        return 50 if val <= 50 else 100 if val <= 100 else 175

    aff = plage_affaissement(affaissement)
    tableau_eau = eau_avec_air if air_entraine else eau_sans_air
    points = sorted(tableau_eau.keys())
    
    # Trouve les points d'interpolation pour Dmax
    dmin, dmax_ref = None, None
    for i in range(len(points) - 1):
        if points[i] <= dmax <= points[i + 1]:
            dmin, dmax_ref = points[i], points[i + 1]
            break

    # Calcul de la quantité d'eau
    if dmax in tableau_eau:
        eau = tableau_eau[dmax][aff]
    elif dmin and dmax_ref:
        eau = interpolation(tableau_eau[dmin][aff], tableau_eau[dmax_ref][aff], dmin, dmax_ref, dmax)
    else:
        eau = interpolation(tableau_eau[points[-2]][aff], tableau_eau[points[-1]][aff], points[-2], points[-1], dmax)

    print(f"\n📊 Résultat Étape 2 :")
    print(f"🌀 Affaissement retenu : {aff} mm")
    print(f"📏 Dmax demandé : {dmax} mm")
    print(f"💧 Eau de gâchage estimée : {round(eau, 1)} kg/m³")
    
    return round(eau, 1), dmax


def calcul_dosage_ciment(eau, rapport_e_c):
    """Étape 3 : Calcule le dosage de ciment nécessaire"""
    print("\n🎯 Étape 3 : Calcul du dosage en ciment")
    ciment = eau / rapport_e_c
    print(f"📦 Dosage ciment = {eau} / {rapport_e_c:.2f} = {round(ciment, 1)} kg/m³")
    return round(ciment, 1)


def volume_gravier_interactif(dmax):
    """Étape 4 : Détermine le volume de gravier nécessaire"""
    print("\n🎯 Étape 4 : Détermination du volume de gros granulats")
    
    mf_points = [2.4, 2.6, 2.8, 3.0]
    while True:
        try:
            mf = float(input("📌 Entrez le module de finesse du sable (entre 2.4 et 3.0) : "))
            if 2.4 <= mf <= 3.0:
                break
            print("❌ Le module de finesse doit être entre 2.4 et 3.0.")
        except ValueError:
            print("❌ Valeur numérique requise.")

    # Tableau de référence pour le volume de gravier
    tableau = {
        10: {2.4: 0.50, 2.6: 0.48, 2.8: 0.46, 3.0: 0.44},
        20: {2.4: 0.66, 2.6: 0.64, 2.8: 0.62, 3.0: 0.60},
        40: {2.4: 0.75, 2.6: 0.73, 2.8: 0.71, 3.0: 0.69},
        80: {2.4: 0.82, 2.6: 0.80, 2.8: 0.78, 3.0: 0.76}
    }

    d_list = sorted(tableau.keys())
    dmin = max([d for d in d_list if d <= dmax], default=d_list[0])
    dmax_ref = min([d for d in d_list if d >= dmax], default=d_list[-1])
    mf_min = max([m for m in mf_points if m <= mf])
    mf_max = min([m for m in mf_points if m >= mf])

    def get(d, m): return tableau[d][m]

    # Calcul du volume de gravier avec interpolation si nécessaire
    if mf_min == mf_max:
        if dmin == dmax_ref:
            vg = get(dmin, mf_min)
        else:
            vg = interpolation(get(dmin, mf_min), get(dmax_ref, mf_min), dmin, dmax_ref, dmax)
    else:
        v1 = interpolation(get(dmin, mf_min), get(dmin, mf_max), mf_min, mf_max, mf)
        v2 = interpolation(get(dmax_ref, mf_min), get(dmax_ref, mf_max), mf_min, mf_max, mf)
        vg = interpolation(v1, v2, dmin, dmax_ref, dmax)

    print(f"\n📊 Résultat Étape 4 :")
    print(f"📐 Dmax utilisé : {dmax} mm")
    print(f"🌾 Mf : {mf}")
    print(f"📦 Volume gravier : {round(vg, 3)} m³/m³")
    
    return round(vg, 3)


def calcul_volumes_ciment_eau(ciment, eau, dc=3.15, de=1.0):
    """Étape 5 : Calcule les volumes de ciment et d'eau"""
    print("\n🎯 Étape 5 : Volumes de ciment et d'eau (m³)")
    vc = ciment / (dc * 1000)
    ve = eau / (de * 1000)
    print(f"🧱 Volume ciment : {round(vc, 4)} m³")
    print(f"💧 Volume eau : {round(ve, 4)} m³")
    return round(vc, 4), round(ve, 4)


def calcul_volume_sable(vc, ve, vg, air=0.02, vol_adj=0):
    """Étape 6 : Calcule le volume de sable nécessaire"""
    print("\n🎯 Étape 6 : Volume de sable (m³)")
    volume_total = vc + ve + vg + air + vol_adj
    vs = 1 - volume_total

    # Ajustement si volume de sable insuffisant
    if vs < 0.12:
        print("⚠️ Volume sable insuffisant ou dépassement. Ajustement du gravier...")
        while vs < 0.12 and vg > 0.5:
            vg -= 0.01
            volume_total = vc + ve + vg + air + vol_adj
            vs = 1 - volume_total
            if vs > 0.12:
                break
        
        if vs < 0:
            print("❌ Même après ajustement, le volume dépasse 1 m³.")
            return None, vg
        
        print(f"✔️ Nouveau volume gravier ajusté : {round(vg, 3)} m³")

    print(f"📐 Volume total = {round(volume_total, 4)} m³")
    print(f"🏖️ Volume sable = 1 - {round(volume_total, 4)} = {round(vs, 4)} m³")
    
    return round(vs, 4), vg


def calcul_masses_sable_gravier(vs, vg, ds_def=2.6, dg_def=2.7):
    """Étape 7 : Calcule les masses de sable et gravier"""
    print("\n🎯 Étape 7 : Masse des granulats (kg/m³)")
    
    # Saisie des densités avec valeurs par défaut
    try:
        ds = input(f"📌 Densité sable (ou Entrée pour {ds_def}) : ")
        ds = float(ds) if ds.strip() else ds_def
    except ValueError:
        print("⚠️ Valeur invalide, densité sable par défaut utilisée.")
        ds = ds_def

    try:
        dg = input(f"📌 Densité gravier (ou Entrée pour {dg_def}) : ")
        dg = float(dg) if dg.strip() else dg_def
    except ValueError:
        print("⚠️ Valeur invalide, densité gravier par défaut utilisée.")
        dg = dg_def

    # Calcul des masses
    ms = vs * ds * 1000
    mg = vg * dg * 1000
    
    print(f"🏖️ Masse sable = {round(ms, 1)} kg/m³")
    print(f"🪨 Masse gravier = {round(mg, 1)} kg/m³")
    
    return round(ms, 1), round(mg, 1)


def etape_8_adjuvant(ciment, eau_init, air_init=0.02):
    """Étape 8 : Gère les ajustements liés aux adjuvants"""
    print("\n🎯 Étape 8 : Intégration des adjuvants")
    
    type_adjuvant = input("🧪 Quel type d'adjuvant ? (réducteur/superplastifiant/chlorure/aucun) : ").strip().lower()

    # Effets des différents adjuvants
    effets = {
        "réducteur": {"reduction_eau": 0.07, "ajout_air": 0.007},
        "superplastifiant": {"reduction_eau": 0.20, "ajout_air": 0.01},
        "chlorure": {"reduction_eau": 0.03, "ajout_air": 0.005},
        "aucun": {"reduction_eau": 0.0, "ajout_air": 0.0}
    }

    if type_adjuvant not in effets:
        print("⚠️ Type d'adjuvant non reconnu. Aucun effet appliqué.")
        type_adjuvant = "aucun"

    effet = effets[type_adjuvant]
    reduction = effet["reduction_eau"]
    ajout_air = effet["ajout_air"]

    # Calcul des nouvelles valeurs
    if type_adjuvant == "aucun":
        masse_adjuvant = 0
        volume_adjuvant = 0
    else:
        masse_adjuvant = ciment * 0.01
        volume_adjuvant = round(masse_adjuvant / 1000, 4)

    nouvelle_eau = round(eau_init * (1 - reduction), 1)
    nouvel_air = round(air_init + ajout_air, 4)

    print(f"🔧 Type d'adjuvant : {type_adjuvant}")
    print(f"💧 Nouvelle eau corrigée : {nouvelle_eau} kg/m³ (réduction de {int(reduction*100)}%)")
    print(f"🌀 Volume d'air ajusté : {nouvel_air} m³")
    print(f"🧪 Masse adjuvant : {masse_adjuvant:.2f} kg/m³ (volume : {volume_adjuvant} m³)")

    return nouvelle_eau, nouvel_air, masse_adjuvant, volume_adjuvant, type_adjuvant


def main_process():
    """Fonction principale orchestrant toutes les étapes du calcul"""
    # Étape 1: Rapport E/C
    res, e_c, air = determiner_rapport_e_c_interactif()
    if None in (res, e_c, air):
        return

    # Étape 2: Eau de gâchage
    eau_init, dmax = determiner_eau_gachage_interactif(air)
    if None in (eau_init, dmax):
        return

    # Étape 3: Dosage ciment
    ciment = calcul_dosage_ciment(eau_init, e_c)

    # Étape 8: Adjuvants
    eau_corr, air_corr, masse_adj, vol_adj, type_adj = etape_8_adjuvant(ciment, eau_init)

    # Étape 4: Volume gravier
    vg = volume_gravier_interactif(dmax)

    # Étape 5: Volumes ciment et eau
    vc, ve = calcul_volumes_ciment_eau(ciment, eau_corr)

    # Étape 6: Volume sable
    vs, vg = calcul_volume_sable(vc, ve, vg, air=air_corr, vol_adj=vol_adj)
    if vs is None:
        print("❌ Formulation impossible avec ces paramètres.")
        return

    # Étape 7: Masses granulats
    ms, mg = calcul_masses_sable_gravier(vs, vg)

    # Vérification volume total
    volume_final = vc + ve + vs + vg + air_corr + vol_adj
    if volume_final > 1.0:
        print(f"❌ Volume final = {round(volume_final, 3)} m³ > 1.00 m³")
        print("💥 Incohérence persistante : formulation impossible avec ces paramètres.")
        return

    # Affichage récapitulatif
    print("\n📦 RÉCAPITULATIF FINAL")
    print(f"Ciment : {ciment} kg/m³")
    print(f"Eau (corrigée) : {eau_corr} kg/m³")
    print(f"Adjuvant ({type_adj}) : {masse_adj:.2f} kg/m³")
    print(f"Air entraîné total : {air_corr:.4f} m³")
    print(f"Sable : {ms} kg/m³")
    print(f"Gravier : {mg} kg/m³")
    print(f"📐 Volume total estimé : {round(volume_final, 4)} m³")


# Point d'entrée du programme
if __name__ == "__main__":
    main_process()