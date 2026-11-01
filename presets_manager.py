import os
import json
import uuid

PRESETS_FILE = os.path.expanduser("~/.infinite_focus_presets.json")

DEFAULT_CURATED_PRESETS = [
    {
        "id": "curated_deep_focus",
        "name": "Deep Focus (432Hz)",
        "icon": "🌌",
        "category": "Méditation & Clarté",
        "prompt": "deep meditative ambient soundscape, warm analog synthesizer pads, 432Hz tuning, calming continuous drone, binaural study atmosphere, soft acoustic reverberation"
    },
    {
        "id": "curated_lofi_study",
        "name": "Lo-Fi Study Beats",
        "icon": "☕",
        "category": "Rythme Doux",
        "prompt": "chill lo-fi hip hop beat, mellow electric rhodes piano, soft vinyl crackle, steady relaxing focus rhythm, jazzy warm chords, soothing bassline"
    },
    {
        "id": "curated_ambient_flow",
        "name": "Ethereal Flow State",
        "icon": "🌊",
        "category": "Ambiance Pure",
        "prompt": "ethereal ambient music, slow evolving synthesizer textures, gentle reverb pads, peaceful concentration flow, serene sonic atmosphere, crystalline harmonics"
    },
    {
        "id": "curated_rainy_jazz",
        "name": "Rainy Cafe Chords",
        "icon": "🌧️",
        "category": "Atmosphère",
        "prompt": "peaceful rainy coffee shop jazz, soft distant rain drops, gentle rhodes piano chords, warm upright bass, cozy study background"
    },
    {
        "id": "curated_cosmic_drone",
        "name": "Cosmic Synth Drone",
        "icon": "🪐",
        "category": "Méditation & Clarté",
        "prompt": "deep space ambient drone, subtle harmonic resonance, wide stereo synth textures, hypnotic focus meditation, celestial overtone harmonics"
    },
    {
        "id": "curated_zen_garden",
        "name": "Zen Temple & Strings",
        "icon": "🍃",
        "category": "Acoustique",
        "prompt": "peaceful minimalist acoustic meditation, soft koto harp notes, warm ambient wooden flute and gentle pads, zen tranquility"
    },
    {
        "id": "curated_flow_pulse",
        "name": "Minimal Tech Pulse",
        "icon": "⚡",
        "category": "Rythme Doux",
        "prompt": "minimal techno ambient, subtle warm electronic pulse, hypnotic focus tempo, understated bass groove, clean modular synth sequences"
    }
]

class PresetsManager:
    def __init__(self, filepath=PRESETS_FILE):
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            try:
                with open(self.filepath, "w", encoding="utf-8") as f:
                    json.dump([], f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Error initializing presets file: {e}")

    def load_custom_presets(self):
        try:
            if os.path.exists(self.filepath):
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading custom presets: {e}")
        return []

    def get_all(self):
        custom = self.load_custom_presets()
        return {
            "curated": DEFAULT_CURATED_PRESETS,
            "custom": custom
        }

    def add_custom(self, name, prompt):
        if not name or not prompt:
            return None
        presets = self.load_custom_presets()
        new_preset = {
            "id": f"custom_{uuid.uuid4().hex[:8]}",
            "name": name.strip(),
            "icon": "✨",
            "category": "Mes Prompts",
            "prompt": prompt.strip()
        }
        presets.insert(0, new_preset)
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(presets, f, indent=2, ensure_ascii=False)
            return new_preset
        except Exception as e:
            print(f"Error saving custom preset: {e}")
            return None

    def delete_custom(self, preset_id):
        presets = self.load_custom_presets()
        initial_len = len(presets)
        presets = [p for p in presets if p.get("id") != preset_id]
        if len(presets) != initial_len:
            try:
                with open(self.filepath, "w", encoding="utf-8") as f:
                    json.dump(presets, f, indent=2, ensure_ascii=False)
                return True
            except Exception as e:
                print(f"Error deleting preset: {e}")
        return False
