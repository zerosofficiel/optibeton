import numpy as np
import random
from collections import defaultdict

# =============================================
# FONCTION DE CONFIGURATION DES PARAMÈTRES ALGO
# =============================================
def configurer_parametres():
    print("\n⚙️ PERSONNALISATION DES PARAMÈTRES ALGORITHMIQUES")
    print("--------------------------------------------")
    
    parametres = {
        "POP_SIZE": {
            "defaut": 100,
            "description": "Nombre de solutions testées par génération",
            "conseil": "Augmenter (150-200) pour problèmes complexes, réduire (30-50) pour rapidité"
        },
        "N_GENERATIONS": {
            "defaut": 80,
            "description": "Nombre d'itérations de l'algorithme",
            "conseil": "Augmenter (>100) pour précision, réduire (<50) pour tests rapides"
        },
        "MUTATION_RATE": {
            "defaut": 0.15,
            "description": "Probabilité de modification aléatoire d'un dosage",
            "conseil": "Augmenter (0.2-0.3) pour explorer, réduire (0.05-0.1) pour affiner"
        },
        "N_PARENTS": {
            "defaut": 20,
            "description": "Nombre de meilleures solutions conservées",
            "conseil": "15-25% de POP_SIZE pour équilibre, 5-10% pour optimisation rapide"
        }
    }

    print("\nValeurs par défaut recommandées :")
    for nom, infos in parametres.items():
        print(f"- {nom}: {infos['defaut']} | {infos['description']}")

    if input("\nPersonnaliser les paramètres ? (o/n) ").lower() == 'o':
        for nom in parametres:
            print(f"\n● {nom} ({parametres[nom]['description']})")
            print(f"Conseil: {parametres[nom]['conseil']}")
            parametres[nom]["valeur"] = float(input(f"Valeur (défaut={parametres[nom]['defaut']}): ") or parametres[nom]['defaut'])
        return {nom: parametres[nom]["valeur"] for nom in parametres}
    else:
        return {nom: parametres[nom]["defaut"] for nom in parametres}

# =============================================
# CORE ALGORITHMIQUE
# =============================================
OPTIMIZATION_PROFILES = {
    1: {"name": "Résistance structurelle", "weights": (0.5, 0.3, 0.2)},
    2: {"name": "Ouvrabilité maximale", "weights": (0.3, 0.5, 0.2)},
    3: {"name": "Économie industrielle", "weights": (0.2, 0.3, 0.5)},
    4: {"name": "Approche équilibrée", "weights": (0.33, 0.33, 0.34)}
}

def resistance_compression(E_C, a=110.0, b=4.5):
    return a / (b ** (1.5 * E_C))

def calculate_slump(water, D_max=20):
    return 5.4816 * D_max + 4.6707 * water - 955.58

def compute_GS_target(slump_mm, D_max_mm, Mf):
    """Calcule le ratio volumique Gravier/Sable optimal."""
    return 1.6 - (0.004 * slump_mm) - (0.015 * Mf) + (0.012 * D_max_mm)

# =============================================
# FONCTIONS UTILITAIRES
# =============================================
def get_user_constraints():
    constraints = defaultdict(dict)
    print("\n🔧 PARAMÉTRAGE DU BÉTON")
    print("=======================")
    
    constraints["target_strength"] = float(input("→ Résistance cible (MPa) [20-50] : "))
    constraints["target_slump"] = float(input("→ Affaissement souhaité (mm) [50-200] : "))
    constraints["D_max"] = float(input("→ Dmax granulats (mm) [5-25] : ") or "20")

    materials = {
        "cement": {"name": "Ciment", "unit": "kg/m³", "default": max(300, constraints["target_strength"] * 10)},
        "water": {"name": "Eau", "unit": "kg/m³", "default": 150 + constraints["target_slump"] / 2},
        "sand": {"name": "Sable", "unit": "kg/m³", "default": 600},
        "gravel": {"name": "Gravier", "unit": "kg/m³", "default": 900}
    }

    for mat, props in materials.items():
        print(f"\n💎 {props['name'].upper()} (Typique: {props['default']} {props['unit']})")
        constraints[f"min_{mat}"] = float(input(f"→ Min {props['name']} ({props['unit']}) : ") or props["default"] * 0.9)
        constraints[f"max_{mat}"] = float(input(f"→ Max {props['name']} ({props['unit']}) : ") or props["default"] * 1.1)

    print("\n💰 COÛTS (FCFA)")
    cost_defaults = {"cement": 1000, "water": 1, "sand": 500, "gravel": 400}
    for mat in materials:
        constraints[f"cost_{mat}"] = float(input(f"→ {materials[mat]['name']} ({materials[mat]['unit']}) : ") or cost_defaults[mat])

    print("\n📏 PROPRIÉTÉS DES GRANULATS")
    constraints["Mf"] = float(input("→ Module de finesse du sable (Mf) [Défaut=2.5] : ") or "2.5")
    constraints["rho_sand"] = float(input("→ Masse volumique du sable (kg/m³) [Typique=1600] : ") or "1600")
    constraints["rho_gravel"] = float(input("→ Masse volumique du gravier (kg/m³) [Typique=1500] : ") or "1500")

    return constraints

def select_optimization_profile():
    print("\n🎯 STRATÉGIE D'OPTIMISATION")
    print("=========================")
    for k, v in OPTIMIZATION_PROFILES.items():
        print(f"{k}. {v['name']} (Résistance={v['weights'][0]*100}%, Ouvrabilité={v['weights'][1]*100}%, Coût={v['weights'][2]*100}%)")
    
    while True:
        choice = int(input("→ Choix [1-4] : "))
        if choice in OPTIMIZATION_PROFILES:
            return OPTIMIZATION_PROFILES[choice]["weights"]
        print("⚠ Choix invalide !")

def donner_conseils(best, constraints, GS_target, weights):
    """Analyse les résultats et donne des conseils d'optimisation."""
    C, E, S, G = best["cement"], best["water"], best["sand"], best["gravel"]
    E_C = E / C
    GS_real = (G / constraints["rho_gravel"]) / (S / constraints["rho_sand"])
    S_ratio = S / (S + G)
    strength = resistance_compression(E_C)
    slump = calculate_slump(E, constraints["D_max"])
    cost = sum([C * constraints["cost_cement"], E * constraints["cost_water"], 
                S * constraints["cost_sand"], G * constraints["cost_gravel"]])

    conseils = []
    
    # 1. Analyse du ratio G/S
    if abs(GS_real - GS_target) > 0.2 * GS_target:
        if GS_real > GS_target:
            conseils.append("🔍 Trop de gravier (G/S volumique trop élevé). Solution : Réduire max_gravel de 10% ou augmenter min_sand de 5%")
        else:
            conseils.append("🔍 Pas assez de gravier (G/S volumique trop bas). Solution : Augmenter max_gravel de 10% ou réduire min_sand de 5%")
    
    # 2. Analyse du ratio masse
    if S_ratio < 0.35:
        conseils.append("🏖️ Trop de gravier (ratio masse <35%). Solution : Augmenter min_sand ou réduire max_gravel")
    elif S_ratio > 0.45:
        conseils.append("🏖️ Trop de sable (ratio masse >45%). Solution : Réduire min_sand ou augmenter max_gravel")
    
    # 3. Analyse résistance
    if strength < constraints["target_strength"] * 0.9:
        conseils.append("🏗️ Résistance trop faible. Solution : Augmenter min_cement de 5% ou réduire max_water de 10%")
    elif strength > constraints["target_strength"] * 1.1:
        conseils.append("🏗️ Résistance excessive. Solution : Diminuer min_cement de 5% pour économiser")
    
    # 4. Analyse affaissement
    if slump < constraints["target_slump"] * 0.9:
        conseils.append("💧 Béton trop sec. Solution : Augmenter min_water de 5% ou vérifier Dmax")
    elif slump > constraints["target_slump"] * 1.1:
        conseils.append("💧 Béton trop fluide. Solution : Réduire max_water de 5% ou augmenter Dmax")
    
    # 5. Conseil sur le profil
    if weights[2] < 0.3 and cost > (constraints["cost_cement"]*350 + constraints["cost_sand"]*600 + constraints["cost_gravel"]*900)*1.2:
        conseils.append("💰 Coût élevé : Essayez le profil 'Économie industrielle' (option 3)")

    # Affichage conditionnel
    if conseils:
        print("\n💡 CONSEILS D'OPTIMISATION")
        print("========================")
        for i, conseil in enumerate(conseils, 1):
            print(f"{i}. {conseil}")
    else:
        print("\n✅ Aucun ajustement nécessaire : la formulation est optimale !")

# =============================================
# ALGORITHME PRINCIPAL
# =============================================
def run_optimization():
    # Chargement des configurations
    parametres = configurer_parametres()
    POP_SIZE = int(parametres["POP_SIZE"])
    N_GENERATIONS = int(parametres["N_GENERATIONS"])
    MUTATION_RATE = parametres["MUTATION_RATE"]
    N_PARENTS = int(parametres["N_PARENTS"])
    
    constraints = get_user_constraints()
    weights = select_optimization_profile()
    
    # Calcul du G/S cible
    GS_target = compute_GS_target(constraints["target_slump"], constraints["D_max"], constraints["Mf"])
    
    # Initialisation population
    def generate_individual():
        return {
            "cement": random.uniform(constraints["min_cement"], constraints["max_cement"]),
            "water": random.uniform(constraints["min_water"], constraints["max_water"]),
            "sand": random.uniform(constraints["min_sand"], constraints["max_sand"]),
            "gravel": random.uniform(constraints["min_gravel"], constraints["max_gravel"])
        }
    
    population = [generate_individual() for _ in range(POP_SIZE)]
    
    # Évolution
    for gen in range(N_GENERATIONS):
        # Évaluation
        def compute_fitness(ind):
            C, E, S, G = ind["cement"], ind["water"], ind["sand"], ind["gravel"]
            E_C = E / C
            
            if not (0.30 <= E_C <= 0.65): return -1e9
            
            # Calcul des indicateurs
            strength = resistance_compression(E_C)
            slump_dev = abs(calculate_slump(E, constraints["D_max"]) - constraints["target_slump"])
            cost = sum([
                C * constraints["cost_cement"],
                E * constraints["cost_water"],
                S * constraints["cost_sand"],
                G * constraints["cost_gravel"]
            ])
            
            # Vérification G/S
            GS_real = (G / constraints["rho_gravel"]) / (S / constraints["rho_sand"])
            GS_penalty = 0
            if abs(GS_real - GS_target) > 0.2 * GS_target:
                GS_penalty = 1e6
                
            # Vérification ratio masse
            S_ratio = S / (S + G)
            mass_ratio_penalty = 0
            if not 0.35 <= S_ratio <= 0.45:
                mass_ratio_penalty = 1e6

            # Normalisation
            strength_norm = strength / 50
            slump_norm = 1 - (slump_dev / 150)
            cost_norm = 1e6 / (cost + 1e4)
            
            w_str, w_work, w_cost = weights
            return (w_str * strength_norm * 10 +
                    w_work * slump_norm * 5 +
                    w_cost * cost_norm -
                    GS_penalty - mass_ratio_penalty)
        
        fitnesses = [compute_fitness(ind) for ind in population]
        
        # Sélection
        parents = [population[i] for i in np.argpartition(fitnesses, -N_PARENTS)[-N_PARENTS:]]
        
        # Reproduction
        next_gen = []
        while len(next_gen) < POP_SIZE:
            p1, p2 = random.sample(parents, 2)
            alpha = random.uniform(0.4, 0.6)
            child = {
                k: alpha * p1[k] + (1 - alpha) * p2[k]
                for k in p1.keys()
            }
            
            # Mutation
            for k in child:
                if random.random() < MUTATION_RATE * (0.5 + 0.5 * np.exp(-gen / 20)):
                    delta = random.gauss(0, (constraints[f"max_{k}"] - constraints[f"min_{k}"]) / 20)
                    child[k] = np.clip(child[k] + delta, constraints[f"min_{k}"], constraints[f"max_{k}"])
            
            next_gen.append(child)
        
        population = next_gen
    
    # Résultats
    best = max(population, key=lambda x: compute_fitness(x))
    C, E, S, G = best["cement"], best["water"], best["sand"], best["gravel"]
    E_C = E / C
    S_ratio = S / (S + G)
    GS_real = (G / constraints["rho_gravel"]) / (S / constraints["rho_sand"])
    
    print("\n✅ RÉSULTATS OPTIMISÉS")
    print("=====================")
    print(f"🧱 Ciment : {C:.0f} kg/m³")
    print(f"💧 Eau : {E:.0f} kg/m³ | E/C = {E_C:.3f}")
    print(f"🏖 Sable : {S:.0f} kg/m³ ({S_ratio*100:.1f}%)")
    print(f"🗻 Gravier : {G:.0f} kg/m³ ({(1-S_ratio)*100:.1f}%)")
    print(f"📐 Ratio G/S (volumique) : {GS_real:.2f} (Cible={GS_target:.2f})")
    if abs(GS_real - GS_target) > 0.2 * GS_target:
        print("⚠️ Écart > 20% avec le G/S optimal !")
    print(f"📏 Ratio Sable/Gravier (masse) : {S_ratio*100:.1f}% (Cible 35-45%)")
    print(f"🏋️ Résistance : {resistance_compression(E_C):.1f} MPa (Cible: {constraints['target_strength']} MPa)")
    print(f"📏 Affaissement : {calculate_slump(E, constraints['D_max']):.0f} mm (Cible: {constraints['target_slump']} mm)")
    
    cost = sum([
        C * constraints["cost_cement"],
        E * constraints["cost_water"],
        S * constraints["cost_sand"],
        G * constraints["cost_gravel"]
    ])
    print(f"💰 Coût total : {cost:,.0f} FCFA/m³")
    
    # Conseils
    profile = next(p for p in OPTIMIZATION_PROFILES.values() if p["weights"] == weights)
    print(f"\n⚙ PROFIL APPLIQUÉ : {profile['name']}")
    print(f"- Résistance={weights[0]*100:.0f}%, Ouvrabilité={weights[1]*100:.0f}%, Coût={weights[2]*100:.0f}%")
    
    # Appel du nouveau module de conseils
    donner_conseils(best, constraints, GS_target, weights)

# =============================================
# LANCEMENT
# =============================================
if __name__ == "__main__":
    print("\n⚡ OPTIMISATEUR DE FORMULATION DE BÉTON INTELLIGENT ⚡")
    print("===================================================")
    run_optimization()