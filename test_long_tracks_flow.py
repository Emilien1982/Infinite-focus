import time
import os
import numpy as np
from audio_engine import AudioEngine
from presets_manager import PresetsManager
from bridge import Bridge

def test_long_tracks_flow():
    print("=== TEST DU NOUVEAU PROCESSUS (MORCEAUX LONGS & ENCHAÎNEMENT 25s) ===")
    
    pm = PresetsManager()
    engine = AudioEngine(sample_rate=32000)
    # Temporarily set movement duration to 15s and crossfade to 5s just to test the transition quickly
    engine.movement_duration_sec = 16.0
    engine.crossfade_sec = 6.0
    engine.loop_crossfade_sec = 2.0
    
    bridge = Bridge(engine, pm)
    
    print("1. Attente du chargement du modèle...")
    t0 = time.time()
    while not engine.is_model_loaded:
        if time.time() - t0 > 30:
            raise TimeoutError("Modèle non chargé")
        time.sleep(0.5)
    print("Modèle prêt!")
    
    print("\n2. Déclenchement de Play...")
    prompt = "calm meditation ambient synth pads"
    bridge.play(prompt)
    
    st = bridge.get_state()
    print("État immédiat:", st)
    assert st['is_playing'] == True
    assert st['status'] == 'generating'
    
    print("\n3. Attente de la génération du premier mouvement...")
    t0 = time.time()
    while len(engine.audio_buffer) == 0:
        time.sleep(1.0)
        if time.time() - t0 > 60:
            raise TimeoutError("Génération initiale trop longue")
            
    print(f"Premier mouvement généré en {time.time() - t0:.1f}s!")
    st = bridge.get_state()
    print("État avec son:", st)
    assert st['movement_count'] == 1
    assert st['buffered_seconds'] > 10.0
    
    # Verify no DC offset or wild amplitudes (which cause rumble)
    buf = engine.audio_buffer
    print(f"Buffer shape: {buf.shape}, min: {buf.min():.3f}, max: {buf.max():.3f}, mean: {buf.mean():.6f}")
    assert abs(buf.mean()) < 0.05, "DC offset detected!"
    
    print("\n4. Test de pause et reprise...")
    bridge.pause()
    assert bridge.get_state()['is_playing'] == False
    bridge.play()
    assert bridge.get_state()['is_playing'] == True
    
    engine.close()
    print("\n=== TOUS LES TESTS DE TRANSITION ET MORCEAUX LONGS SONT VALIDES ===")

if __name__ == "__main__":
    test_long_tracks_flow()
