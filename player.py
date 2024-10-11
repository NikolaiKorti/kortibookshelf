
import xbmc
from library_service import AudioBookShelfLibraryService
import xbmc
from library_service import AudioBookShelfLibraryService
import threading

ID = 'plugin.audio.kortibookshelf'
monitor = xbmc.Monitor()

class BookShelfPlayer(xbmc.Player):
    player_keys = {
        'twitch_playing': ID + '-twitch_playing'
    }
    seek_keys = {
        'seek_time': ID + '-seek_time',
    }
    reconnect_keys = {
        'stream': ID + '-livestream'
    }
    
    def __new__(cls, window, *args, **kwargs):
        return super(BookShelfPlayer, cls).__new__(cls, *args, **kwargs)
    
    def __init__(self, window, *args, **kwargs):
        xbmc.log(f"__init__ started.", xbmc.LOGINFO)
        self.window = window
        
    def onPlayBackStarted(self):
        #self._start_thread(self.update_time_periodically)
        xbmc.log("Playback started. 123", xbmc.LOGINFO)

    def onPlayBackPaused(self):
        xbmc.log(f"Playback paused.", xbmc.LOGINFO)
        
    def onPlayBackResumed(self):
        xbmc.log(f"Playback onPlayBackResumed.", xbmc.LOGINFO)    
        
        
    def onPlayBackEnded(self):
        xbmc.log(f"Playback onPlayBackEnded.", xbmc.LOGINFO)
                
    def skip_to_time(self, time):
        xbmc.log("skip_to_time" + str(time), xbmc.LOGINFO)
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        playlist_size = playlist.size()

        for i in range(playlist_size):
            playlist_item = playlist[i]
            start_offset = playlist_item.getProperty("StartOffset")
            duration = playlist_item.getProperty("Duration")
            start_offset = int(start_offset) if start_offset else 0
            duration = int(duration) if duration else 0

            if time > start_offset and time < (start_offset + duration):
                title = playlist_item.getLabel()
                url = playlist_item.getPath()
                xbmc.log(f"current_track that should be playing: {title}", xbmc.LOGINFO)
                xbmc.log(f"current_track that should be playing: {url}", xbmc.LOGINFO)
                self.play(url)
                while not self.isPlaying():
                    xbmc.sleep(500)
                self.seekTime(time - start_offset)
                break

    def _start_thread(self, target):
        thread = threading.Thread(target=target)
        thread.start()
        self.threads.append(thread)

    def play_custom(self):
        self.skip_to_time(self.current_time)

    def get_current_time_total(self):
        xbmc.log("onAction get_current_time_totalget_current_time_totalget_current_time_total ", xbmc.LOGINFO)
        time = self.getTime()
        for i in range(self.current_track):
            time = time + self.audio_tracks[i]["duration"]
        return time

    def update_time_periodically(self):
        while self.isPlayingAudio():
            self.current_time = self.get_current_time_total()
            self.library_service.update_media_progress(self.id, {"currentTime": self.current_time})
            xbmc.log(f"updating current time {self.current_time}", xbmc.LOGINFO)
            xbmc.sleep(15000)

    def get_time_current_track(self):
        xbmc.log("onAction get_time_current_trackget_time_current_trackget_time_current_track ", xbmc.LOGINFO)
        time = self.audio_tracks[self.current_track]["duration"]
        return time