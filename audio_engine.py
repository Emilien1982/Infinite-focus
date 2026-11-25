import time
import threading
import torch
import numpy as np
import sounddevice as sd
from transformers import AutoProcessor, MusicgenForConditionalGeneration

class AudioEngine:
    def __init__(self, sample_rate=32000):
        self.sample_rate = sample_rate
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        
        # Audio movement parameters
        self.movement_duration_sec = 160.0   # ~2.6 minutes per full movement
        self.seed_bridge_duration_sec = 42.0 # ~42 seconds for fast initial seed bridge
        self.crossfade_sec = 25.0            # 25 seconds graceful crossfade (same prompt)
        self.prompt_switch_xf_sec = 2.0      # 2.0 seconds immediate cutover crossfade (new prompt)
        self.loop_crossfade_sec = 5.0        # 5 seconds seamless motif overlap
        self.seed_loop_xf_sec = 1.5          # 1.5 seconds seed loop overlap
        
        # Possibility C: Acoustic transition filter (DJ low-pass sweep while waiting for new theme)
        self.enable_transition_filter = True
        self.is_transition_filtering = False
        self._filter_state = np.zeros(2, dtype=np.float32)
        
        self.processor = None
        self.model = None
        self.is_model_loaded = False
        
        self.stream = None
        self.is_playing = False
        self.volume = 0.85
        
        self.audio_buffer = np.zeros((0, 2), dtype=np.float32)
        self.buffer_lock = threading.Lock()
        
        self.current_prompt = "deep meditative ambient soundscape, warm analog synthesizer pads, 432Hz frequency, calming continuous drone"
        self.active_prompt = ""
        self.pending_prompt_switch = False
        self.is_generating = False
        self.movement_count = 0
        self.is_seed_phase = False
        
        self.status = "initializing"
        self.status_detail = "Initialisation du modèle IA sur Apple Silicon..."
        self.current_level = 0.0
        
        self._running = True
        self._wake_event = threading.Event()
        
        # Start model loader thread
        threading.Thread(target=self._load_model_thread, daemon=True).start()
        # Start continuous generation worker thread
        threading.Thread(target=self._generation_worker, daemon=True).start()

    def _load_model_thread(self):
        try:
            self.status = "loading_model"
            self.status_detail = f"Chargement de MusicGen ({self.device.upper()})..."
            
            self.processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
            self.model = MusicgenForConditionalGeneration.from_pretrained(
                "facebook/musicgen-small",
                torch_dtype=torch.float32
            )
            self.model.to(self.device)
            self.model.eval()
            
            self.is_model_loaded = True
            self.status = "ready"
            self.status_detail = "Prêt. Choisissez un prompt et cliquez sur Play."
        except Exception as e:
            self.status = "error"
            self.status_detail = f"Erreur de chargement: {str(e)}"
            print(f"Error loading model: {e}")

    def _ensure_stream(self):
        if self.stream is None:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=2,
                dtype=np.float32,
                callback=self._audio_callback,
                blocksize=2048
            )
            self.stream.start()

    def play(self, prompt=None):
        prompt_changed = False
        if prompt and prompt.strip():
            new_p = prompt.strip()
            if new_p != self.active_prompt:
                self.current_prompt = new_p
                self.pending_prompt_switch = True
                prompt_changed = True
            else:
                self.current_prompt = new_p

        self._ensure_stream()
        self.is_playing = True
        
        with self.buffer_lock:
            buf_len = len(self.audio_buffer)

        if prompt_changed:
            self.status = "generating"
            self.status_detail = f"Changement de thème : amorce rapide (~7s) pour '{self.current_prompt[:24]}'..."
            if buf_len > 0 and self.enable_transition_filter:
                self.is_transition_filtering = True
        elif buf_len > 0:
            self.status = "playing"
            self.status_detail = f"En écoute • Morceau {self.movement_count} ({self.active_prompt[:24]}...)"
        else:
            self.status = "generating"
            self.status_detail = "Composition de l'amorce rapide (prêt dans ~7s)..."

        self._wake_event.set()

    def pause(self):
        self.is_playing = False
        self.is_transition_filtering = False
        self.status = "paused"
        self.status_detail = "En pause"

    def toggle_play(self, prompt=None):
        if self.is_playing:
            self.pause()
            return False
        else:
            self.play(prompt)
            return True

    def skip_to_next_movement(self):
        """Déclenche immédiatement la composition et le passage au morceau suivant pour le même prompt."""
        if not self.is_playing:
            self.play()
            return
        self.pending_prompt_switch = True
        self.status = "generating"
        self.status_detail = f"Morceau suivant : composition immédiate ({self.current_prompt[:24]}...)"
        if self.enable_transition_filter:
            self.is_transition_filtering = True
        self._wake_event.set()

    def set_volume(self, val):
        self.volume = max(0.0, min(1.0, float(val)))

    def set_prompt(self, prompt):
        if prompt and prompt.strip():
            new_p = prompt.strip()
            if new_p != self.active_prompt:
                self.current_prompt = new_p
                self.pending_prompt_switch = True
                self.status = "generating"
                self.status_detail = f"Changement de thème : amorce rapide (~7s) pour '{new_p[:24]}'..."
                if self.is_playing and self.enable_transition_filter:
                    self.is_transition_filtering = True
                self._wake_event.set()

    def get_state(self):
        with self.buffer_lock:
            buf_seconds = len(self.audio_buffer) / self.sample_rate
            
        return {
            "status": self.status,
            "status_detail": self.status_detail,
            "is_playing": self.is_playing,
            "is_generating": self.is_generating,
            "is_seed_phase": self.is_seed_phase,
            "movement_count": self.movement_count,
            "volume": self.volume,
            "audio_level": self.current_level,
            "buffered_seconds": round(buf_seconds, 1),
            "current_prompt": self.current_prompt,
            "active_prompt": self.active_prompt,
            "pending_switch": self.pending_prompt_switch,
            "device": self.device.upper()
        }

    def _make_seamless_loop(self, audio_mono, xf_samples):
        """Crossfades tail with head to create an imperceptible seamless loop."""
        n = len(audio_mono)
        if n <= xf_samples * 2:
            return audio_mono
        core = audio_mono[xf_samples:-xf_samples]
        head = audio_mono[:xf_samples]
        tail = audio_mono[-xf_samples:]
        t = np.linspace(0, np.pi / 2, xf_samples)
        seam = tail * np.cos(t) + head * np.sin(t)
        return np.concatenate([seam, core])

    def _build_seed_bridge(self, clip_mono, target_duration_sec):
        """Loops a short 5-6s seed into a temporary ~40s smooth bridge."""
        xf_samples = int(self.seed_loop_xf_sec * self.sample_rate)
        loopable = self._make_seamless_loop(clip_mono, xf_samples)
        target_samples = int(target_duration_sec * self.sample_rate)
        repeats = int(np.ceil(target_samples / len(loopable)))
        tiled = np.tile(loopable, repeats)[:target_samples]
        return np.column_stack([tiled, tiled]).astype(np.float32)

    def _build_long_movement(self, clip_mono, target_duration_sec):
        """Expands a 30s AI motif into a multi-minute cohesive focus movement."""
        xf_samples = int(self.loop_crossfade_sec * self.sample_rate)
        loopable = self._make_seamless_loop(clip_mono, xf_samples)
        target_samples = int(target_duration_sec * self.sample_rate)
        repeats = int(np.ceil(target_samples / len(loopable)))
        tiled = np.tile(loopable, repeats)[:target_samples]
        return np.column_stack([tiled, tiled]).astype(np.float32)

    def _crossfade_movements(self, current_buffer, new_movement, xf_sec):
        """Merges next movement of the SAME prompt gracefully over xf_sec (e.g. 25s)."""
        xf_samples = int(xf_sec * self.sample_rate)
        buf_len = len(current_buffer)
        
        if buf_len <= xf_samples:
            xf_samples = buf_len
            t = np.linspace(0, np.pi / 2, xf_samples)[:, np.newaxis]
            blended = current_buffer * np.cos(t) + new_movement[:xf_samples] * np.sin(t)
            return np.vstack([blended, new_movement[xf_samples:]])
        else:
            keep = current_buffer[:-xf_samples]
            tail = current_buffer[-xf_samples:]
            t = np.linspace(0, np.pi / 2, xf_samples)[:, np.newaxis]
            blended = tail * np.cos(t) + new_movement[:xf_samples] * np.sin(t)
            return np.vstack([keep, blended, new_movement[xf_samples:]])

    def _immediate_cutover_crossfade(self, current_buffer, new_movement, xf_sec=2.0):
        """
        Immediately switches from the old prompt to the new prompt,
        crossfading over 2.0s and discarding the remaining minutes of the old track.
        """
        xf_samples = int(xf_sec * self.sample_rate)
        buf_len = len(current_buffer)
        
        if buf_len == 0:
            return new_movement
            
        actual_xf = min(buf_len, xf_samples)
        t = np.linspace(0, np.pi / 2, actual_xf)[:, np.newaxis]
        
        tail = current_buffer[:actual_xf]
        head = new_movement[:actual_xf]
        
        blended = tail * np.cos(t) + head * np.sin(t)
        return np.vstack([blended, new_movement[actual_xf:]])

    def _audio_callback(self, outdata, frames, time_info, status):
        if not self.is_playing:
            outdata.fill(0)
            self.current_level = 0.0
            return

        with self.buffer_lock:
            buf_len = len(self.audio_buffer)
            if buf_len >= frames:
                raw_chunk = self.audio_buffer[:frames]
                self.audio_buffer = self.audio_buffer[frames:]
            elif buf_len > 0:
                raw_chunk = np.zeros((frames, 2), dtype=np.float32)
                raw_chunk[:buf_len] = self.audio_buffer
                self.audio_buffer = np.zeros((0, 2), dtype=np.float32)
            else:
                outdata.fill(0)
                self.current_level = 0.0
                return

        # Possibility C: Gentle transition filter sweep if waiting for a new theme
        if self.enable_transition_filter and self.is_transition_filtering:
            alpha = 0.25
            filtered = np.empty_like(raw_chunk)
            for i in range(frames):
                self._filter_state = self._filter_state + alpha * (raw_chunk[i] - self._filter_state)
                filtered[i] = self._filter_state
            outdata[:] = filtered * self.volume
        else:
            self._filter_state = raw_chunk[-1].copy()
            outdata[:] = raw_chunk * self.volume

        # Smooth RMS calculation for UI visualizer
        rms = float(np.sqrt(np.mean(outdata**2)))
        self.current_level = min(1.0, rms * 4.5)

    def _generate_fast_seed(self, prompt):
        """
        User's idea + Possibility B:
        Generates a short 5.2s initial seed (260 tokens) in single-pass mode (guidance_scale=1.0).
        Calculated in ~6.6 seconds on Apple Silicon!
        """
        inputs = self.processor(
            text=[prompt],
            padding=True,
            return_tensors="pt"
        ).to(self.device)

        with torch.inference_mode():
            audio_values = self.model.generate(
                **inputs,
                max_new_tokens=260,     # ~5.2 seconds
                do_sample=True,
                guidance_scale=1.0      # Possibility B: Single pass, fastest computation
            )

        clip = audio_values[0, 0].cpu().numpy().astype(np.float32)
        peak = np.max(np.abs(clip))
        if peak > 0.001:
            clip = (clip / peak) * 0.40
        return clip

    def _generate_full_motif(self, prompt):
        """
        Generates a 15-second high-fidelity motif from MusicGen (750 tokens, guidance_scale=1.5).
        Loops seamlessly into a ~2.6-minute movement!
        """
        inputs = self.processor(
            text=[prompt],
            padding=True,
            return_tensors="pt"
        ).to(self.device)

        with torch.inference_mode():
            audio_values = self.model.generate(
                **inputs,
                max_new_tokens=750,     # 15.0 seconds
                do_sample=True,
                guidance_scale=1.5      # High quality conditioned generation
            )

        clip = audio_values[0, 0].cpu().numpy().astype(np.float32)
        peak = np.max(np.abs(clip))
        if peak > 0.001:
            clip = (clip / peak) * 0.40
        return clip

    def _generation_worker(self):
        """
        Two-stage generation:
        1. Fast Seed (5s, guidance_scale=1.0) -> audible in ~6-7 seconds!
        2. Brief pause, then Full Movement (15s motif -> 2.6min, guidance_scale=1.5) -> crossfaded in background.
        3. Graceful 25s crossfade for subsequent movements of the same prompt.
        """
        while self._running:
            if not self.is_playing or not self.is_model_loaded:
                self._wake_event.wait(timeout=0.4)
                self._wake_event.clear()
                continue

            with self.buffer_lock:
                buf_sec = len(self.audio_buffer) / self.sample_rate

            # =========================================================================
            # STAGE 1: PROMPT CHANGED OR INITIAL START -> FAST SEED (~6-7s)
            # =========================================================================
            if self.pending_prompt_switch or (buf_sec == 0 and self.active_prompt != self.current_prompt):
                target_prompt = self.current_prompt
                self.is_generating = True
                self.is_seed_phase = True
                self.status = "generating"
                self.status_detail = f"Changement de thème : amorce rapide (~7s) pour '{target_prompt[:22]}'..."
                if buf_sec > 0 and self.enable_transition_filter:
                    self.is_transition_filtering = True

                try:
                    # 1. Fast seed (5s clip in ~6.6s computation time)
                    seed_clip = self._generate_fast_seed(target_prompt)
                    seed_bridge = self._build_seed_bridge(seed_clip, self.seed_bridge_duration_sec)
                    
                    with self.buffer_lock:
                        # Immediately cutover crossfade into the new seed bridge (2.0s)
                        self.audio_buffer = self._immediate_cutover_crossfade(
                            self.audio_buffer,
                            seed_bridge,
                            xf_sec=self.prompt_switch_xf_sec
                        )
                        
                    self.is_transition_filtering = False
                    self.active_prompt = target_prompt
                    self.pending_prompt_switch = False
                    self.movement_count = 1
                    
                    if self.is_playing:
                        self.status = "playing"
                        self.status_detail = f"En écoute • Amorce active ({target_prompt[:20]}...) • Préparation du grand morceau..."

                except Exception as e:
                    print(f"Error in fast seed generation: {e}")
                    self.is_transition_filtering = False
                    time.sleep(1.0)
                finally:
                    self.is_generating = False
                    
                # Pause a brief moment (2.5s) so if the user clicks another prompt right away,
                # the worker can handle the newest prompt immediately without getting locked!
                for _ in range(5):
                    if self.pending_prompt_switch:
                        break
                    time.sleep(0.5)
                continue

            # =========================================================================
            # STAGE 2: GENERATE FULL HIGH-FIDELITY MOVEMENT (~2.6 min)
            # =========================================================================
            if self.is_seed_phase and not self.pending_prompt_switch:
                target_prompt = self.active_prompt
                self.is_generating = True
                if self.is_playing:
                    self.status_detail = f"Composition du grand morceau ({target_prompt[:20]}...)"

                try:
                    full_motif = self._generate_full_motif(target_prompt)
                    full_movement = self._build_long_movement(full_motif, self.movement_duration_sec)
                    
                    with self.buffer_lock:
                        # Only append if prompt hasn't changed during computation
                        if not self.pending_prompt_switch and self.current_prompt == target_prompt:
                            # Crossfade the full movement into the remainder of the seed bridge over 15s
                            self.audio_buffer = self._crossfade_movements(
                                self.audio_buffer,
                                full_movement,
                                xf_sec=15.0
                            )
                            self.is_seed_phase = False
                            if self.is_playing:
                                self.status = "playing"
                                self.status_detail = f"En écoute • Grand morceau 1 (~2m30) • {target_prompt[:22]}..."
                except Exception as e:
                    print(f"Error generating full movement: {e}")
                    time.sleep(1.0)
                finally:
                    self.is_generating = False
                continue

            # =========================================================================
            # STAGE 3: CONTINUOUS PLAYBACK FOR THE SAME PROMPT (25s crossfade)
            # =========================================================================
            lead_time_sec = self.crossfade_sec + 35.0
            if buf_sec <= lead_time_sec and not self.is_generating and not self.pending_prompt_switch and not self.is_seed_phase:
                self.is_generating = True
                prompt = self.active_prompt
                next_num = self.movement_count + 1
                if self.is_playing:
                    self.status_detail = f"Préparation Morceau {next_num} ({prompt[:20]}...) • Fondu 25s"

                try:
                    full_motif = self._generate_full_motif(prompt)
                    new_movement = self._build_long_movement(full_motif, self.movement_duration_sec)
                    
                    with self.buffer_lock:
                        # Verify prompt hasn't changed during generation
                        if not self.pending_prompt_switch and self.current_prompt == prompt:
                            # Gracefully crossfade the new movement over 25 seconds
                            self.audio_buffer = self._crossfade_movements(
                                self.audio_buffer,
                                new_movement,
                                xf_sec=self.crossfade_sec
                            )
                            self.movement_count = next_num
                            if self.is_playing:
                                self.status_detail = f"En écoute • Morceau {self.movement_count} • Enchaîné sur 25s"
                except Exception as e:
                    print(f"Error generating next movement: {e}")
                    time.sleep(1.0)
                finally:
                    self.is_generating = False

            time.sleep(0.5)

    def close(self):
        self._running = False
        self._wake_event.set()
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
