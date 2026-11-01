# 🧘 Infinite Focus

**Infinite Focus** est une application macOS native et minimaliste conçue pour Apple Silicon (M1/M2/M3/M4). Elle génère en temps réel et en continu une musique favorisant la concentration, l'étude et le flow state, grâce à un modèle d'intelligence artificielle open-source exécuté 100% en local.

---

## ✨ Points Clés

- **⚡ Apple Silicon MPS (Metal Performance Shaders)** : Accélération matérielle native sur la puce Apple Silicon (GPU/Neural Engine) pour une latence minimale.
- **🎵 Morceaux Longs (~2 min 30 s à 3 min)** : Chaque mouvement musical généré par l'IA est structuré de façon organique et continue sur plusieurs minutes, favorisant une immersion profonde sans coupures intempestives.
- **🌊 Fondu Enchaîné Gracieux (25 secondes)** : Les morceaux s'enchaînent avec un fondu enchaîné sinusoidal à énergie constante (**25 secondes**) pour une transition imperceptible et veloutée.
- **🔇 Zéro Grondement / Son Pur** : Suppression totale de tout bruit parasite ou onde synthétique basse fréquence. Le flux est 100% composé par le modèle neuronal MusicGen avec une normalisation douce.
- **💾 100% en Mémoire RAM (Zéro Fichier Disque)** : Tout le flux est calculé et streamé directement en mémoire vive vers CoreAudio (`sounddevice` / PortAudio). Aucun fichier `.wav`, `.mp3` ou temporaire n'est écrit sur le disque.
- **🎨 Interface macOS Minimaliste & Épurée** :
  - Design sombre aux finitions verre dépoli (Frosted Glass / SF Pro).
  - Bouton Play/Pause central avec visualiseur d'ondes audio réactif en temps réel.
  - Champ de saisie libre de prompt sonore.
  - Section de **Préréglages de concentration** (Deep Focus 432Hz, Lo-Fi Study Beats, Ethereal Ambient, Rainy Cafe, Cosmic Drone, Zen Temple, etc.).
  - Gestion de vos **prompts personnalisés sauvegardés** (sauvegarde & suppression en 1 clic).

---

## 🚀 Lancement de l'Application

Vous pouvez lancer l'application de 3 manières différentes :

1. **Depuis le Finder, le Dock ou Spotlight** :
   Ouvrez simplement l'application **Infinite Focus** installée dans votre dossier `/Applications` :
   ```bash
   open "/Applications/Infinite Focus.app"
   ```

2. **Depuis le Terminal** :
   ```bash
   infinite-focus
   ```

3. **Depuis le répertoire du projet** :
   ```bash
   cd "/Users/utilisateur/dev_ai/Infinite Focus"
   .venv/bin/python main.py
   ```

---

## 🧠 Modèle IA Utilisé

- **Modèle** : `facebook/musicgen-small` (Meta AI)
- **Taille** : ~300M paramètres (léger, ~1.2 Go en mémoire unifiée).
- **Licence** : Open Source (MIT / CC-BY-NC).
- **Échantillonnage audio** : 32 000 Hz, stéréo spatialisé 432Hz.

---

## 📁 Structure du Projet

```text
/Users/utilisateur/dev_ai/Infinite Focus/
├── Infinite Focus.app/      # Bundle Application macOS (lié dans /Applications)
├── .venv/                   # Environnement virtuel autonome Python 3.11
├── audio_engine.py          # Moteur de génération IA & streaming audio en RAM (morceaux longs & fondu 25s)
├── presets_manager.py       # Gestionnaire des préréglages & favoris
├── bridge.py                # Passerelle JS/Python (PyWebView)
├── main.py                  # Point d'entrée de l'application
├── build_app.py             # Script de build et d'installation de l'App macOS
├── create_icon.py           # Générateur de l'icône haute résolution .icns
├── ui/                      # Interface utilisateur webview minimaliste
│   ├── index.html           # Structure HTML5
│   ├── style.css            # Styles macOS dark glass & animations
│   └── app.js               # Visualiseur Canvas & logique interactive
├── AppIcon.icns             # Icône officielle de l'application
└── README.md                # Documentation
```
# Infinite-focus
