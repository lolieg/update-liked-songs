import base64
from time import sleep

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import CLIENT_ID, CLIENT_SECRET, USERNAME, PLAYLIST_NAME, UPDATE_INTERVALL

scope = "playlist-modify-public playlist-modify-private playlist-read-private user-library-read ugc-image-upload"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, username=USERNAME, redirect_uri="http://localhost:8080"))

def update():
    def get_mult_items(func, playlist_id=None):
        items = []
        current_offset = 0

        while True:
            if playlist_id:
                resp = func(playlist_id, limit=50, offset=current_offset)
            else:
                resp = func(limit=50, offset=current_offset)
            for item in resp["items"]:
                items.append(item)
            current_offset += 50
            if current_offset >= 1000:
                break
        return items
    
    def edit_mult_items(func, items):
        added = 0
        while True:
            items_ = [item["track"]["id"] for item in items][added:added+100]
            func(playlist_id=playlist["id"], items=items_)
            added += 100
            if added > len(items):
                break

    saved_tracks = get_mult_items(sp.current_user_saved_tracks)
    playlists = get_mult_items(sp.current_user_playlists)


    playlist = None
    for playlist_ in playlists:
        if PLAYLIST_NAME in playlist_["name"]:
            playlist = playlist_

    if playlist == None:
        playlist = sp.user_playlist_create(USERNAME, PLAYLIST_NAME, description="Automatically generated playlist.")
        with open("cover.jpg", "rb") as img:
            sp.playlist_upload_cover_image(playlist_id=playlist["id"], image_b64=base64.b64encode(img.read()))
        edit_mult_items(sp.playlist_add_items, saved_tracks)

    else:
        playlist_tracks = get_mult_items(sp.playlist_tracks, playlist_id=playlist["id"])
        if len(playlist_tracks) == 0:
            return edit_mult_items(sp.playlist_add_items, saved_tracks)
            
        new_tracks = []
        for track in saved_tracks:
            if track["track"]["id"] not in [item["track"]["id"] for item in playlist_tracks]:
                new_tracks.append(track)
        if len(new_tracks) > 0:
            edit_mult_items(sp.playlist_add_items, new_tracks)
            
        removed_tracks = []
        for track in playlist_tracks:
            if track["track"]["id"] not in [item["track"]["id"] for item in saved_tracks]:
                removed_tracks.append(track)
        if len(removed_tracks) > 0:
            edit_mult_items(sp.playlist_remove_all_occurrences_of_items, removed_tracks)
    

while True:
    print("updating...")
    try:
        update()
        print("updated!")
    except Exception as e:
        print("Couldn't update!")
        print(e)
    sleep(UPDATE_INTERVALL)