import time
import numpy as np
from audio_engine import AudioEngine
from presets_manager import PresetsManager
from bridge import Bridge

def test_prompt_switch():
    print("=== TEST DU CHANGEMENT IMMÉDIAT DE PROMPT ===")
    
    pm = PresetsManager()
    engine = AudioEngine(sample_rate=32000)
    # Fast test movements: 12 seconds per movement
    engine.movement_duration_sec = 12.0
    engine.crossfade_sec = 4.0
    engine.prompt_switch_xf_sec = 1.0
    engine.loop_crossfade_sec = 2.0
    
    bridge = Bridge(engine, pm)
    
    print("1. Attente chargement modèle...")
    while not engine.is_model_loaded:
        time.sleep(0.5)
    print("Modèle prêt.")
    
    prompt_a = "peaceful ambient lofi piano chords"
    print(f"\n2. Lancement du Prompt A: '{prompt_a}'...")
    bridge.play(prompt_a)
    
    # Wait for Movement 1 of Prompt A to start playing
    t0 = time.time()
    while len(engine.audio_buffer) == 0:
        time.sleep(0.5)
        if time.time() - t0 > 60:
            raise TimeoutError("Initial generation took too long")
            
    print(f"Prompt A en cours de lecture! Buffer: {len(engine.audio_buffer)/32000:.1f}s")
    assert engine.active_prompt == prompt_a
    
    # Now simulate user switching prompt right away to Prompt B!
    prompt_b = "deep cosmic synth space drone"
    print(f"\n3. L'utilisateur change immédiatement de prompt vers Prompt B: '{prompt_b}'...")
    t_switch = time.time()
    bridge.set_prompt(prompt_b)
    
    st = bridge.get_state()
    print("État après changement de prompt:", st)
    assert st['current_prompt'] == prompt_b
    assert st['pending_switch'] == True
    
    print("\n4. Attente de la transition vers Prompt B...")
    while engine.active_prompt != prompt_b:
        time.sleep(0.5)
        if time.time() - t_switch > 60:
            raise TimeoutError("Prompt switch took too long")
            
    print(f"-> Transition vers Prompt B réussie en {time.time() - t_switch:.1f}s!")
    final_st = bridge.get_state()
    print("État final avec Prompt B actif:", final_st)
    assert final_st['active_prompt'] == prompt_b
    assert final_st['pending_switch'] == False
    assert final_st['movement_count'] == 1
    
    engine.close()
    print("\n=== TEST DE CHANGEMENT IMMÉDIAT DE PROMPT VALIDÉ AVEC SUCCÈS ===")

if __name__ == "__main__":
    test_prompt_switch()
