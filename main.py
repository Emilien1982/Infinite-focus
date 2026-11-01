import os
import sys
import webview
from audio_engine import AudioEngine
from presets_manager import PresetsManager
from bridge import Bridge

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ui_dir = os.path.join(base_dir, "ui")
    index_path = os.path.join(ui_dir, "index.html")

    print("[Infinite Focus] Initialisation des composants...")
    audio_engine = AudioEngine(sample_rate=32000)
    presets_manager = PresetsManager()
    bridge = Bridge(audio_engine, presets_manager)

    def on_closed():
        print("[Infinite Focus] Fermeture de l'application...")
        audio_engine.close()

    window = webview.create_window(
        title="Infinite Focus",
        url=f"file://{index_path}",
        js_api=bridge,
        width=840,
        height=680,
        min_size=(760, 580),
        background_color="#0b0d13",
        text_select=False
    )
    window.events.closed += on_closed

    print("[Infinite Focus] Lancement de l'interface...")
    webview.start(debug=False)

if __name__ == "__main__":
    main()
