import threading
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from prompt_enhancer.base import BasePromptEnhancer

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"

SYSTEM_BASE = (
    "You are an expert sound designer and audio prompt engineer for AI music generation (MusicGen). "
    "Transform the user's music idea into a rich, textured, focus-enhancing audio prompt in ENGLISH (20 to 35 words). "
    "MANDATORY RULES:\n"
    "1. Always output ONLY in ENGLISH (translate French or any other language to English).\n"
    "2. Include specific acoustic textures (e.g., warm analog synth pads, mellow Rhodes piano, gentle vinyl crackle, 432Hz calm).\n"
    "3. Output ONLY the prompt text. No quotes, intros, or explanations."
)

SYSTEM_LAYER = (
    "You are an expert sound designer for AI music generation (MusicGen). "
    "Given an existing English music prompt, generate ONLY 2 to 3 NEW complementary, smooth sonic textures, subtle instruments, "
    "or spatial/acoustic production layers in ENGLISH to enrich it further (10 to 20 words total). "
    "Good examples: warm tape flutter saturation, deep sub-bass drone, delicate felt piano harmonics, wide cathedral stereo reverb, "
    "granular ambient shimmer, soft Rhodes overtones, subtle rain texture, gentle analog chorus. "
    "Do NOT repeat elements already in the prompt. Output ONLY the comma-separated new textures, nothing else."
)

BASE_FEW_SHOT = [
    {"role": "system", "content": SYSTEM_BASE},
    {"role": "user", "content": "musique douce pour coder sous la pluie"},
    {"role": "assistant", "content": "gentle lofi rhodes piano chords with soft rain ambiance, warm analog synth pads, subtle vinyl crackle, slow relaxing tempo, 432Hz meditative focus"},
    {"role": "user", "content": "espace calme et zen"},
    {"role": "assistant", "content": "peaceful zen garden ambient soundscape, soft koto harp harmonics, warm bamboo flute, subtle drone pads, soothing binaural meditation"},
]

LAYER_FEW_SHOT = [
    {"role": "system", "content": SYSTEM_LAYER},
    {"role": "user", "content": "Existing prompt: gentle lofi rhodes piano chords with soft rain ambiance, warm analog synth pads, subtle vinyl crackle\nAdd 2-3 new textures:"},
    {"role": "assistant", "content": "deep warm sub-bass drone, delicate tape flutter saturation, wide stereo reverb"},
    {"role": "user", "content": "Existing prompt: peaceful zen garden ambient soundscape, soft koto harp harmonics, warm bamboo flute\nAdd 2-3 new textures:"},
    {"role": "assistant", "content": "gentle crystal bowl resonance, soft wind chimes, warm analog tape warmth"},
]

FRENCH_HINTS = {
    "pour", "avec", "douce", "doux", "calme", "musique", "pluie", "bois",
    "espace", "nuit", "travail", "coder", "et", "de", "la", "le", "les",
    "un", "une", "des", "sur", "sous", "sans", "dans", "très", "plus",
}


class LocalLLMEnhancer(BasePromptEnhancer):
    def __init__(self, model_id=MODEL_ID):
        self.model_id = model_id
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.tokenizer = None
        self.model = None
        self.is_loaded = False
        self._load_lock = threading.Lock()

    def _ensure_loaded(self):
        if self.is_loaded:
            return
        with self._load_lock:
            if self.is_loaded:
                return
            print(f"[PromptEnhancer] Chargement du mini-LLM local ({self.model_id}) sur {self.device}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                dtype=torch.float16 if self.device == "mps" else torch.float32
            )
            self.model.to(self.device)
            self.model.eval()
            self.is_loaded = True
            print("[PromptEnhancer] Mini-LLM prêt.")

    def _generate_text(self, messages, max_new_tokens=55):
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

        with torch.inference_mode():
            generated_ids = self.model.generate(
                **model_inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.82,
                top_p=0.9,
                do_sample=True,
                repetition_penalty=1.15
            )

        gen_tokens = generated_ids[0][len(model_inputs.input_ids[0]):]
        decoded = self.tokenizer.decode(gen_tokens, skip_special_tokens=True).strip(' "\'\n\r.,')

        # If hit token limit mid-phrase, trim incomplete trailing clause
        if len(gen_tokens) >= max_new_tokens - 1 and "," in decoded:
            decoded = decoded.rsplit(",", 1)[0].strip(' "\'\n\r.,')

        return decoded

    def enrich(self, prompt: str) -> str:
        clean_input = prompt.strip() if prompt else ""
        if not clean_input:
            clean_input = "deep ambient focus soundscape"

        self._ensure_loaded()

        words = clean_input.split()
        has_non_ascii = any(ord(c) > 127 for c in clean_input)
        has_french = any(w.lower().strip(",.;:!?") in FRENCH_HINTS for w in words)

        # First-pass or short/non-English input -> produce a complete textured English base prompt
        if len(words) < 8 or has_non_ascii or has_french:
            messages = list(BASE_FEW_SHOT) + [
                {"role": "user", "content": clean_input}
            ]
            enriched = self._generate_text(messages, max_new_tokens=60)
            if not enriched:
                enriched = "warm ambient synthesizer pads with gentle acoustic harmonics, 432Hz deep meditative drone, relaxing focus atmosphere"
            return enriched

        # Subsequent clicks on an already-English prompt -> layer new textures progressively
        messages = list(LAYER_FEW_SHOT) + [
            {"role": "user", "content": f"Existing prompt: {clean_input}\nAdd 2-3 new textures:"}
        ]
        new_layers = self._generate_text(messages, max_new_tokens=40)
        if new_layers:
            return f"{clean_input.rstrip(', ')}, {new_layers}"
        return clean_input
