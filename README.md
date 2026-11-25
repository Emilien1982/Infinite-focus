# 🧘 Infinite Focus

**Infinite Focus** est une application macOS native et minimaliste conçue pour Apple Silicon (M1/M2/M3/M4). Elle génère en temps réel et en continu une musique favorisant la concentration, l'étude et le flow state, grâce à un modèle d'intelligence artificielle open-source exécuté 100% en local.

---

## ✨ Points Clés

- **⚡ Changement de Thème Ultra-Rapide (~6 à 7 secondes)** :
  - **Amorce rapide (Fast Seed)** : Dès que vous changez de thème, le moteur ne calcule plus un bloc lourd de 48 secondes mais une amorce instantanée de 5 secondes en mode single-pass (`guidance_scale = 1.0`).
  - **Basculement effectif en ~6,6 secondes** sur puce Apple Silicon.
  - Le grand morceau complet de ~2 min 30 s prend ensuite le relais en tâche de fond de manière transparente.
- **🎛️ Effet de Transition Acoustique (Filtre DJ Sweep)** :
  - Dès le clic sur un nouveau thème, le morceau en cours subit un léger filtre passe-bas progressif (high-cut doux) qui annonce acoustiquement le changement d'ambiance pendant les 6 secondes de calcul.
- **🌊 Fondu Enchaîné Gracieux (25 secondes pour un même prompt)** :
  - Tant que vous conservez le même prompt, chaque morceau est développé sur **~2 min 30 s** et s'enchaîne avec un fondu sinusoïdal à énergie constante de **25 secondes**.
- **💾 100% en Mémoire RAM (Zéro Fichier Disque)** :
  - Tout le flux est streamé directement vers CoreAudio en mémoire vive. Aucun fichier audio n'est stocké sur votre Mac.
- **🎨 Interface macOS Minimaliste & Épurée** :
  - Design sombre aux finitions verre dépoli (Frosted Glass / SF Pro).
  - Bouton Play/Pause central avec **anneau lumineux animé (spinner de composition)** actif lors des calculs en RAM.
  - Champ de saisie libre de prompt (4 lignes par défaut, barre de défilement et poignée de redimensionnement vertical) avec bouton *"Changer de thème (immédiat)"*.
  - Section de **Préréglages de concentration** et gestion de vos favoris personnels en 1 clic.
- **✨ Bouton "Enrichir" avec mini-LLM local embarqué** :
  - Situé à côté du bouton *"Idée"*. Reformule et texture progressivement votre prompt à chaque clic en ajoutant de nouvelles couches sonores (Rhodes, vinyle, pads 432Hz, saturation bande, réverbération).
  - **Traduction automatique en anglais** garantie pour une efficacité maximale avec MusicGen.
  - Moteur local ultra-léger et rapide (~0.5s par inférence) avec architecture modulaire découplée (`prompt_enhancer/`).
  - Aucun pré-chargement inutile en RAM : modèle chargé à la demande.
- **⌨️ Contrôle Intégral au Clavier & Touches Multimédia macOS** :
  - Touche `F8` (ou Espace) : Play / Pause.
  - Touches `F9` (Suivant) ou `F7` (Précédent) : Déclenche immédiatement une nouvelle variation musicale d'après le même prompt.
  - Intégration macOS *Now Playing* / Centre de Contrôle.
- **🪟 Mode Mini Lecteur Compact** :
  - Bouton `⤢` dans l'en-tête pour réduire l'application en un lecteur ultra-minimaliste (380x140 px).
  - Affiche uniquement le bouton play avec son animation, le statut et le réglage volume.
  - Clic sur `⤢` pour restaurer la vue complète à tout moment.

---

## 🚀 Lancement de l'Application

Vous pouvez lancer l'application :

1. **Depuis Spotlight, le Dock ou le Finder** :
   ```bash
   open "/Applications/Infinite Focus.app"
   ```

2. **Depuis le Terminal** :
   ```bash
   infinite-focus
   ```

3. **Depuis le dossier source** :
   ```bash
   cd "/Users/utilisateur/dev_ai/Infinite Focus"
   .venv/bin/python main.py
   ```

---

## 🧠 Modèles IA Embarqués

- **Génération Musicale** : `facebook/musicgen-small` (Meta AI)
  - Accélération : Apple Silicon MPS (Metal Performance Shaders)
  - Taille : ~300M paramètres (~1.2 Go en mémoire unifiée).
- **Enrichissement de Prompts** : `Qwen/Qwen2.5-0.5B-Instruct` (Alibaba / Qwen)
  - Accélération : Apple Silicon MPS (float16)
  - Taille : ~490M paramètres (~980 Mo de poids locaux).
  - Exécution : ~0.5s à 0.8s par reformulation.

---

## 🗺️ Prochaines Améliorations (Roadmap)

- **⚡ Réactivité accrue (changement de prompt & avance rapide)** : Réduire encore davantage le temps de latence avant le démarrage effectif d'un nouveau morceau lors d'un changement de thème ou d'un appui sur Suivant (`F9`).
- **🧠 Optimisation de la mémoire vive (RAM)** : Réduire l'empreinte mémoire des modèles et des buffers pour garantir une exécution fluide sur les configurations milieu de gamme disposant de **moins de 16 Go de RAM**.
