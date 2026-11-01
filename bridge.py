class Bridge:
    def __init__(self, audio_engine, presets_manager):
        self.audio = audio_engine
        self.presets = presets_manager

    def toggle_play(self, prompt=None):
        return self.audio.toggle_play(prompt)

    def play(self, prompt=None):
        self.audio.play(prompt)
        return True

    def pause(self):
        self.audio.pause()
        return True

    def set_volume(self, val):
        self.audio.set_volume(val)
        return True

    def set_prompt(self, prompt):
        self.audio.set_prompt(prompt)
        return True

    def get_state(self):
        return self.audio.get_state()

    def get_presets(self):
        return self.presets.get_all()

    def save_preset(self, name, prompt):
        res = self.presets.add_custom(name, prompt)
        return {"success": res is not None, "presets": self.presets.get_all()}

    def delete_preset(self, preset_id):
        res = self.presets.delete_custom(preset_id)
        return {"success": res, "presets": self.presets.get_all()}
