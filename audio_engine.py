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
        self.movement_duration_sec = 160.0   # ~2.6 minutes per movement
        self.crossfade_sec = 25.0            # 25 seconds graceful crossfade (same prompt)
        self.prompt_switch_xf_sec = 2.5      # 2.5 seconds immediate cutover crossfade (new prompt)
        self.loop_crossfade_sec = 5.0        # 5 seconds seamless motif overlap
        
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
            self.status_detail = f"Changement de thème : composition immédiate ({self.current_prompt[:24]}...)"
        elif buf_len > 0:
            self.status = "playing"
            self.status_detail = f"En écoute • Morceau {self.movement_count} ({self.active_prompt[:24]}...)"
        else:
            self.status = "generating"
            self.status_detail = "Composition du premier morceau IA (MusicGen)..."

        self._wake_event.set()

    def pause(self):
        self.is_playing = False
        self.status = "paused"
        self.status_detail = "En pause"

    def toggle_play(self, prompt=None):
        if self.is_playing:
            self.pause()
            return False
        else:
            self.play(prompt)
            return True

    def set_volume(self, val):
        self.volume = max(0.0, min(1.0, float(val)))

    def set_prompt(self, prompt):
        if prompt and prompt.strip():
            new_p = prompt.strip()
            if new_p != self.active_prompt:
                self.current_prompt = new_p
                self.pending_prompt_switch = True
                self.status = "generating"
                self.status_detail = f"Changement de thème : composition immédiate ({new_p[:24]}...)"
                self._wake_event.set()

    def get_state(self):
        with self.buffer_lock:
            buf_seconds = len(self.audio_buffer) / self.sample_rate
            
        return {
            "status": self.status,
            "status_detail": self.status_detail,
            "is_playing": self.is_playing,
            "is_generating": self.is_generating,
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
        """Crossfades the tail with the head to create a clickless, rumble-free seamless loop."""
        n = len(audio_mono)
        if n <= xf_samples * 2:
            return audio_mono
        core = audio_mono[xf_samples:-xf_samples]
        head = audio_mono[:xf_samples]
        tail = audio_mono[-xf_samples:]
        t = np.linspace(0, np.pi / 2, xf_samples)
        seam = tail * np.cos(t) + head * np.sin(t)
        return np.concatenate([seam, core])

    def _build_long_movement(self, clip_mono, target_duration_sec):
        """Expands a 30s AI motif into a multi-minute cohesive focus movement."""
        xf_samples = int(self.loop_crossfade_sec * self.sample_rate)
        loopable = self._make_seamless_loop(clip_mono, xf_samples)
        
        target_samples = int(target_duration_sec * self.sample_rate)
        repeats = int(np.ceil(target_samples / len(loopable)))
        tiled = np.tile(loopable, repeats)[:target_samples]
        
        # Clean stereo (identical L & R without comb filtering)
        return np.column_stack([tiled, tiled]).astype(np.float32)

    def _crossfade_movements(self, current_buffer, new_movement, xf_sec):
        """Gracefully merges next movement of the SAME prompt over 25 seconds."""
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

    def _immediate_cutover_crossfade(self, current_buffer, new_movement, xf_sec=2.5):
        """
        Immediately switches from the old prompt to the new prompt,
        crossfading over 2.5s and discarding the remaining minutes of the old track.
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
                outdata[:] = self.audio_buffer[:frames] * self.volume
                self.audio_buffer = self.audio_buffer[frames:]
            elif buf_len > 0:
                outdata[:buf_len] = self.audio_buffer * self.volume
                outdata[buf_len:].fill(0)
                self.audio_buffer = np.zeros((0, 2), dtype=np.float32)
            else:
                outdata.fill(0)

        # Smooth RMS calculation for UI visualizer
        rms = float(np.sqrt(np.mean(outdata**2)))
        self.current_level = min(1.0, rms * 4.5)

    def _generate_ai_motif(self, prompt):
        """Generates a pristine 30-second AI musical motif from MusicGen."""
        inputs = self.processor(
            text=[prompt],
            padding=True,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            audio_values = self.model.generate(
                **inputs,
                max_new_tokens=1500,  # 30.0 seconds
                do_sample=True,
                guidance_scale=1.5
            )

        clip = audio_values[0, 0].cpu().numpy().astype(np.float32)
        
        # Peak normalize cleanly to comfortable listening level
        peak = np.max(np.abs(clip))
        if peak > 0.001:
            clip = (clip / peak) * 0.40
            
        return clip

    def _generation_worker(self):
        """Manages generation: immediate cutover on prompt change, 25s crossfade on same prompt."""
        while self._running:
            if not self.is_playing or not self.is_model_loaded:
                self._wake_event.wait(timeout=0.5)
                self._wake_event.clear()
                continue

            with self.buffer_lock:
                buf_sec = len(self.audio_buffer) / self.sample_rate

            # CASE 1: PROMPT CHANGED -> IMMEDIATE REGENERATION & CUTOVER
            if self.pending_prompt_switch or (self.current_prompt != self.active_prompt):
                target_prompt = self.current_prompt
                self.is_generating = True
                self.status = "generating"
                self.status_detail = f"Changement de thème : composition de '{target_prompt[:24]}...'..."

                try:
                    motif = self._generate_ai_motif(target_prompt)
                    new_movement = self._build_long_movement(motif, self.movement_duration_sec)
                    
                    with self.buffer_lock:
                        # Immediately switch from the old track to the new track over 2.5 seconds!
                        # Discards the rest of the old track immediately.
                        self.audio_buffer = self._immediate_cutover_crossfade(
                            self.audio_buffer,
                            new_movement,
                            xf_sec=self.prompt_switch_xf_sec
                        )
                        
                    self.active_prompt = target_prompt
                    self.pending_prompt_switch = False
                    self.movement_count = 1
                    
                    if self.is_playing:
                        self.status = "playing"
                        self.status_detail = f"En écoute • Nouveau thème : {target_prompt[:24]}..."
                except Exception as e:
                    print(f"Error switching prompt: {e}")
                    time.sleep(1.0)
                finally:
                    self.is_generating = False
                continue

            # CASE 2: INITIAL START (buffer is empty)
            if buf_sec == 0:
                self.is_generating = True
                prompt = self.current_prompt
                self.status = "generating"
                self.status_detail = f"Composition du Morceau 1 ({prompt[:24]}...)"

                try:
                    motif = self._generate_ai_motif(prompt)
                    movement = self._build_long_movement(motif, self.movement_duration_sec)
                    
                    # Soft 2-second fade-in at the very beginning
                    fade_samples = int(2.0 * self.sample_rate)
                    movement[:fade_samples] *= np.linspace(0.0, 1.0, fade_samples)[:, np.newaxis]
                    
                    with self.buffer_lock:
                        # If a prompt change happened while we were generating, don't keep this
                        if not self.pending_prompt_switch and self.current_prompt == prompt:
                            self.audio_buffer = movement
                            self.movement_count = 1
                            self.active_prompt = prompt
                            if self.is_playing:
                                self.status = "playing"
                                self.status_detail = f"En écoute • Morceau 1 (~2m30) • {prompt[:24]}..."
                except Exception as e:
                    print(f"Error generating initial movement: {e}")
                    time.sleep(1.0)
                finally:
                    self.is_generating = False
                continue

            # CASE 3: CONTINUOUS PLAYBACK FOR THE SAME PROMPT
            # Only chain subsequent movements if prompt has NOT changed!
            lead_time_sec = self.crossfade_sec + 45.0
            if buf_sec <= lead_time_sec and not self.is_generating and not self.pending_prompt_switch:
                self.is_generating = True
                prompt = self.active_prompt
                next_num = self.movement_count + 1
                if self.is_playing:
                    self.status_detail = f"Préparation Morceau {next_num} ({prompt[:20]}...) • Fondu 25s"

                try:
                    motif = self._generate_ai_motif(prompt)
                    new_movement = self._build_long_movement(motif, self.movement_duration_sec)
                    
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

            time.sleep(1.0)

    def close(self):
        self._running = False
        self._wake_event.set()
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
