import sys
import urllib.parse
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmc
import os
import requests
import threading
from requests.auth import HTTPBasicAuth
from library_service import AudioBookShelfLibraryService
from login_service import AudioBookShelfService
from player import BookShelfPlayer


# Get addon instance and settings
addon = xbmcaddon.Addon()
ip_address = addon.getSetting('ipaddress')
port = addon.getSetting('port')
username = addon.getSetting('username')
password = addon.getSetting('password')
addon_handle = int(sys.argv[1])
addon_url = sys.argv[0]
selected_library = {}
url=""
token = ""
def get_auth_header():
    return HTTPBasicAuth(username, password)

def build_url(query):
    xbmc.log(f"Query: {query}", xbmc.LOGINFO)
    return f"{addon_url}?{urllib.parse.urlencode(query)}"

def list_categories():
    categories = ['Current', 'New', 'Finished']
    for category in categories:
        url = build_url({'action': 'list', 'category': category})
        list_item = xbmcgui.ListItem(label=category)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=list_item, isFolder=True)
        
class SettingsDialog(xbmcgui.Dialog):
    def get_input(self, title):
        return xbmcgui.Dialog().input(title)

    def get_and_store_settings(self):
        ip = self.get_input("Enter IP Address")
        addon.setSetting("ipaddress", ip)

        port = self.get_input("Enter Port")
        addon.setSetting("port", port)

        username = self.get_input("Enter Username")
        addon.setSetting("username", username)

        password = self.get_input("Enter Password")
        addon.setSetting("password", password)
        
        
        
def select_library():
    library_service = AudioBookShelfLibraryService(f"http://{ip_address}:{port}", get_token())

    data = library_service.get_all_libraries()
    libraries = data['libraries']
    library_names = [lib['name'] for lib in libraries]

    dialog = xbmcgui.Dialog()
    selected = dialog.select('Wählen Sie eine Bibliothek', library_names)

    if selected != -1:
        selected_library = libraries[selected]
        items = library_service.get_library_items(selected_library['id'])
        audiobooks = []

        for item in items["results"]:
            cover_path = item['media'].get('coverPath', "") or ""
            icon_id = os.path.basename(os.path.dirname(cover_path))
            cover_url = f"{url}/api/items/{icon_id}/cover?token={token}"
            title = item['media']['metadata'].get('title', "") or ""
            description = item['media']['metadata'].get('description', "") or ""
            narrator_name = item['media']['metadata'].get('narratorName', "") or ""
            #xbmc.log("Roger, addon here..item" + str(item), xbmc.LOGINFO)
            publisher = item['media']['metadata'].get('publisher', "") or ""
            published_year = item['media']['metadata'].get('publishedYear', "") or ""
            duration = item['media'].get('duration', 0.0) or 0.0
            iid = item['id']

            audiobook = {
                "id": iid,
                "title": title,
                "cover_url": cover_url,
                "description": description,
                "narrator_name": "Narrator: "+narrator_name,
                "published_year": "Year: "+published_year,
                "publisher": "Publisher: "+publisher,
                "duration": duration,
            }
            audiobooks.append(audiobook)

        return audiobooks

def list_audiobooks(category):
    if not ip_address or not port or not username or not password:
        dialog = SettingsDialog()
        dialog.get_and_store_settings()

    url = f"http://{ip_address}:{port}"
    service = AudioBookShelfService(url)

    try:
        server_status = service.server_status()
    except Exception:
        xbmcgui.Dialog().ok('Fehler', 'Audiobookshelf Server ist nicht erreichbar')
        exit()

    try:
        response_data = service.login(username, password)
        global token
        token = response_data.get('token')
        #xbmc.log("Roger, addon here..token: " + str(token), xbmc.LOGINFO)
        if not token:
            raise ValueError("Kein Token in der Antwort")
    except Exception:
        xbmcgui.Dialog().ok('Fehler', 'überprüfen Sie Benutzernamen oder Passwort')
        exit()

    audiobooks = select_library()

    for book in audiobooks:
        url2 = build_url({'action': 'play', 'book_id': book['id']})
        list_item = xbmcgui.ListItem(label=book['title'])
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url2, listitem=list_item, isFolder=True)

def play_audiobook(book_id):
    global url
    global token
    
    library_service = AudioBookShelfLibraryService(f"http://{ip_address}:{port}", token=get_token())
    files = library_service.get_file_url(book_id)
    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist.clear()
    for file in files:
        playlist.add(file['url'])
    player = BookShelfPlayer(window=xbmcgui.Window(10000))
    player.play(playlist)
    xbmc.sleep(500)  # Wait until playback starts
    monitor = xbmc.Monitor()
    monitor.waitForAbort()
    
def get_token():
    token = addon.getSetting('api_token')
    url = addon.getSetting('url')
    if not url:
        url = f"http://{ip_address}:{port}"
        addon.setSetting('url', url)
    if not token:
        service = AudioBookShelfService(url)
        response_data = service.login(username, password)
        token = response_data.get('token')
        addon.setSetting('api_token', token)
    return token

if __name__ == '__main__':
    args = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)
    xbmc.log(f"Args: {sys.argv}", xbmc.LOGINFO)
    action = args.get('action', [None])[0]
    category = args.get('category', [None])[0]
    book_id = args.get('book_id', [None])[0]
    
    if action == 'list' and category:
        list_audiobooks(category)
    elif action == 'play' and book_id:
        play_audiobook(book_id)
    else:
        list_categories()

    xbmcplugin.endOfDirectory(addon_handle)