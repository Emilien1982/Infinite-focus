from prompt_enhancer import get_enhancer

class Bridge:
    def __init__(self, audio_engine, presets_manager):
        self.audio = audio_engine
        self.presets = presets_manager
        self.enhancer = get_enhancer("local")
        self.window = None
        self.media_keys = None
        self.is_mini = False

    def set_window(self, window):
        self.window = window

    def set_media_keys(self, media_keys):
        self.media_keys = media_keys

    def _sync_media_keys(self):
        if self.media_keys:
            st = self.audio.get_state()
            self.media_keys.update_playback_state(st.get("is_playing", False), st.get("current_prompt"))

    def toggle_play(self, prompt=None):
        res = self.audio.toggle_play(prompt)
        self._sync_media_keys()
        return res

    def play(self, prompt=None):
        self.audio.play(prompt)
        self._sync_media_keys()
        return True

    def pause(self):
        self.audio.pause()
        self._sync_media_keys()
        return True

    def skip_next(self):
        self.audio.skip_to_next_movement()
        self._sync_media_keys()
        return True

    def set_volume(self, val):
        self.audio.set_volume(val)
        return True

    def set_prompt(self, prompt):
        self.audio.set_prompt(prompt)
        return True

    def get_state(self):
        st = self.audio.get_state()
        st["is_mini"] = self.is_mini
        return st

    def get_presets(self):
        return self.presets.get_all()

    def save_preset(self, name, prompt):
        res = self.presets.add_custom(name, prompt)
        return {"success": res is not None, "presets": self.presets.get_all()}

    def delete_preset(self, preset_id):
        res = self.presets.delete_custom(preset_id)
        return {"success": res, "presets": self.presets.get_all()}

    def enrich_prompt(self, prompt):
        """Enrichit le prompt sonore grâce au mini-LLM local embarqué."""
        try:
            enriched = self.enhancer.enrich(prompt)
            return {"success": True, "enriched": enriched}
        except Exception as e:
            print("[Bridge] Erreur enrichissement prompt:", e)
            return {"success": False, "error": str(e)}

    def toggle_mini_mode(self):
        """Bascule entre la vue complète et le mode mini lecteur compact."""
        self.is_mini = not self.is_mini
        if self.window:
            if self.is_mini:
                self.window.resize(380, 140)
            else:
                self.window.resize(840, 680)
        return {"is_mini": self.is_mini}
