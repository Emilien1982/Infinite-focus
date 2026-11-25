import time
import MediaPlayer
from AppKit import NSEvent, NSEventMaskSystemDefined

class MacMediaKeyManager:
    """
    Gestionnaire des touches multimédia macOS et du centre de contrôle (Now Playing).
    Capture les touches Clavier F8 (Play/Pause), F9 (Suivant) et F7 (Précédent),
    aussi bien lorsque l'application a le focus (moniteur local) qu'en arrière-plan.
    """
    def __init__(self, on_toggle_play=None, on_next=None, on_prev=None):
        self.on_toggle_play = on_toggle_play
        self.on_next = on_next
        self.on_prev = on_prev
        self._last_trigger = {}
        self._local_monitor = None
        self._global_monitor = None
        self._handlers = []

        self._setup_now_playing()
        self._setup_remote_commands()
        self._setup_system_event_monitors()

    def _debounced_call(self, action_name, callback):
        if not callback:
            return
        now = time.monotonic()
        last = self._last_trigger.get(action_name, 0.0)
        if now - last < 0.25:
            return
        self._last_trigger[action_name] = now
        try:
            callback()
        except Exception as e:
            print(f"[MediaKeys] Erreur lors de l'action {action_name}:", e)

    def _setup_now_playing(self):
        try:
            info_center = MediaPlayer.MPNowPlayingInfoCenter.defaultCenter()
            info = {
                MediaPlayer.MPMediaItemPropertyTitle: "Infinite Focus",
                MediaPlayer.MPMediaItemPropertyArtist: "Musique IA Générative",
                MediaPlayer.MPNowPlayingInfoPropertyIsLiveStream: True,
            }
            info_center.setNowPlayingInfo_(info)
            info_center.setPlaybackState_(MediaPlayer.MPNowPlayingPlaybackStateStopped)
        except Exception as e:
            print("[MediaKeys] Erreur initialisation NowPlaying:", e)

    def update_playback_state(self, is_playing: bool, prompt: str = None):
        try:
            info_center = MediaPlayer.MPNowPlayingInfoCenter.defaultCenter()
            info = {
                MediaPlayer.MPMediaItemPropertyTitle: "Infinite Focus",
                MediaPlayer.MPMediaItemPropertyArtist: (prompt[:48] if prompt else "Musique IA Générative"),
                MediaPlayer.MPNowPlayingInfoPropertyIsLiveStream: True,
            }
            info_center.setNowPlayingInfo_(info)
            state = (
                MediaPlayer.MPNowPlayingPlaybackStatePlaying
                if is_playing
                else MediaPlayer.MPNowPlayingPlaybackStatePaused
            )
            info_center.setPlaybackState_(state)
        except Exception:
            pass

    def _setup_remote_commands(self):
        try:
            center = MediaPlayer.MPRemoteCommandCenter.sharedCommandCenter()

            def handle_play_pause(event):
                self._debounced_call("toggle_play", self.on_toggle_play)
                return MediaPlayer.MPRemoteCommandHandlerStatusSuccess

            def handle_next(event):
                self._debounced_call("next", self.on_next)
                return MediaPlayer.MPRemoteCommandHandlerStatusSuccess

            def handle_prev(event):
                self._debounced_call("prev", self.on_prev)
                return MediaPlayer.MPRemoteCommandHandlerStatusSuccess

            self._handlers.extend([handle_play_pause, handle_next, handle_prev])

            center.togglePlayPauseCommand().setEnabled_(True)
            center.togglePlayPauseCommand().addTargetWithHandler_(handle_play_pause)

            center.playCommand().setEnabled_(True)
            center.playCommand().addTargetWithHandler_(handle_play_pause)

            center.pauseCommand().setEnabled_(True)
            center.pauseCommand().addTargetWithHandler_(handle_play_pause)

            center.nextTrackCommand().setEnabled_(True)
            center.nextTrackCommand().addTargetWithHandler_(handle_next)

            center.previousTrackCommand().setEnabled_(True)
            center.previousTrackCommand().addTargetWithHandler_(handle_prev)
        except Exception as e:
            print("[MediaKeys] Erreur initialisation RemoteCommandCenter:", e)

    def _handle_system_event(self, event):
        try:
            # System defined subtype 8 represents hardware media keys
            if event.subtype() == 8:
                data1 = event.data1()
                key_code = (data1 & 0xFFFF0000) >> 16
                key_flags = data1 & 0x0000FFFF
                key_down = ((key_flags & 0xFF00) >> 8) == 0xA

                if key_down:
                    # 16: NX_KEYTYPE_PLAY
                    # 17: NX_KEYTYPE_NEXT, 19: NX_KEYTYPE_FAST
                    # 18: NX_KEYTYPE_PREVIOUS, 20: NX_KEYTYPE_REWIND
                    if key_code == 16:
                        self._debounced_call("toggle_play", self.on_toggle_play)
                        return True
                    elif key_code in (17, 19):
                        self._debounced_call("next", self.on_next)
                        return True
                    elif key_code in (18, 20):
                        self._debounced_call("prev", self.on_prev)
                        return True
        except Exception:
            pass
        return False

    def _setup_system_event_monitors(self):
        """Moniteurs local (app au premier plan) et global (arrière-plan) pour F7, F8, F9."""
        try:
            def local_handler(event):
                handled = self._handle_system_event(event)
                return None if handled else event

            def global_handler(event):
                self._handle_system_event(event)

            self._handlers.extend([local_handler, global_handler])

            self._local_monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
                NSEventMaskSystemDefined,
                local_handler
            )
            self._global_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                NSEventMaskSystemDefined,
                global_handler
            )
        except Exception as e:
            print("[MediaKeys] Erreur moniteur NSEvent:", e)
