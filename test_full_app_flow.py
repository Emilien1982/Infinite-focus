import time
import os
from audio_engine import AudioEngine
from presets_manager import PresetsManager
from bridge import Bridge

def test_flow():
    print("=== TEST COMPLET DU LOGICIEL INFINITE FOCUS ===")
    
    # Check zero file baseline
    before_files = set(os.listdir("."))
    
    print("\n1. Initialisation du PresetsManager...")
    pm = PresetsManager()
    presets = pm.get_all()
    print(f"Curated presets: {len(presets['curated'])}")
    print(f"Custom presets: {len(presets['custom'])}")
    assert len(presets['curated']) > 0, "Curated presets missing!"
    
    print("\n2. Initialisation de l'AudioEngine...")
    engine = AudioEngine(sample_rate=32000)
    bridge = Bridge(engine, pm)
    
    print("En attente du chargement du modèle en mémoire unifiée Apple Silicon (MPS)...")
    wait_start = time.time()
    while not engine.is_model_loaded:
        if time.time() - wait_start > 30:
            raise TimeoutError("Le modèle a mis trop de temps à charger.")
        time.sleep(0.5)
    print(f"Modèle chargé avec succès en {time.time() - wait_start:.1f}s sur {engine.device.upper()}!")
    
    test_prompt = "deep calm ambient drone with warm synth pads, 432Hz focus meditation"
    print(f"\n3. Déclenchement de Play avec le prompt: '{test_prompt}'...")
    t_play = time.time()
    bridge.play(test_prompt)
    elapsed_to_play = time.time() - t_play
    print(f"-> Play démarré en {elapsed_to_play*1000:.1f}ms (dès que l'on presse 'play')!")
    
    state = bridge.get_state()
    print("État immédiat:", state)
    assert state['is_playing'] == True, "L'état devrait être is_playing=True"
    assert state['buffered_seconds'] > 0, "Le tampon audio devrait déjà contenir du son immédiat"
    
    print("\n4. Attente de la première génération IA en arrière-plan...")
    gen_start = time.time()
    # Wait until at least 1 AI chunk has been generated
    while engine.chunks_generated < 1:
        time.sleep(0.5)
        st = bridge.get_state()
        if st['audio_level'] > 0:
            print(f"  [Lecture active] Niveau audio: {st['audio_level']:.2f}, Buffer: {st['buffered_seconds']}s, IA chunks: {st['chunks_generated']}")
        if time.time() - gen_start > 30:
            raise TimeoutError("Timeout en attente de la première génération IA")

    print(f"Première génération IA terminée avec succès en {time.time() - gen_start:.1f}s!")
    final_state = bridge.get_state()
    print("État après génération IA:", final_state)
    assert final_state['chunks_generated'] >= 1, "Au moins 1 morceau IA doit avoir été généré"
    assert final_state['is_playing'] == True, "La lecture doit être en cours"
    
    print("\n5. Test de la mise en pause...")
    bridge.pause()
    time.sleep(0.3)
    assert bridge.get_state()['is_playing'] == False, "L'état devrait être paused"
    print("Pause validée avec succès.")
    
    print("\n6. Test de la reprise (resume)...")
    bridge.play()
    time.sleep(0.3)
    assert bridge.get_state()['is_playing'] == True, "L'état devrait être playing"
    print("Reprise validée avec succès.")
    
    print("\n7. Test réglage du volume...")
    bridge.set_volume(0.5)
    assert bridge.get_state()['volume'] == 0.5, "Le volume doit être à 0.5"
    print("Volume réglé à 50%.")
    
    print("\n8. Test ajout et suppression de preset personnalisé...")
    save_res = bridge.save_preset("Mon Super Focus Test", "chill beats test prompt")
    assert save_res['success'] == True
    custom_id = save_res['presets']['custom'][0]['id']
    print(f"Preset créé: {custom_id}")
    del_res = bridge.delete_preset(custom_id)
    assert del_res['success'] == True
    print("Preset supprimé avec succès.")
    
    # Nettoyage
    engine.close()
    
    # Check that zero audio files were created
    after_files = set(os.listdir("."))
    new_files = after_files - before_files
    print(f"\n9. Vérification fichiers créés: {new_files}")
    for f in new_files:
        assert not f.endswith((".wav", ".mp3", ".flac", ".ogg", ".raw")), f"Fichier audio non autorisé créé: {f}"
        
    print("\n=== TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS (100% EN MÉMOIRE SANS STOCKAGE) ===")

if __name__ == "__main__":
    test_flow()
