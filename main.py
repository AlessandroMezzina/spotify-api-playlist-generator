import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

CLIENT_ID = "a1d30ac423254bd58878ef580dc3f416";
CLIENT_SECRET = "8e753bd92f1b4a7a9e2f2c869f1bbcb3"
REDIRECT_URI = "https://open.spotify.com/"

# multiple scopes
oAuthscope = "user-read-email,user-read-private,user-library-read,user-read-playback-state,user-modify-playback-state,user-read-currently-playing"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI,scope=oAuthscope))

def getCurrentSong():
    response_current_track = sp.current_user_playing_track()
    if response_current_track  is not None and response_current_track["item"] is not None:
        song = response_current_track["item"]
        print(song['artists'][0]['name'], " – ", song['name'])

def getUserLikedTracks():
    # ENDPOINT: https://api.spotify.com/v1/me/tracks
    # PARAMETRI GET PER QUESTA CHIAMATA:
    ### market  : se definito, verranno mostrati solo risultati disponibili nel paese specificato
    ### limit   : numero massimo di elementi da restituire. MINIMO=20, MASSIMO=50
    ### offset  : indice da dove iniziare la restituzione degli elementi

    OFFSET=0
    LIMIT=50
    MARKET="IT"

    tracks=[]
    end = False

    while not end:
        response = sp.current_user_saved_tracks(market=MARKET, limit=LIMIT, offset=OFFSET)
        likedTracks = response["items"]
        for track in likedTracks:
            tracks.append(track["track"]["name"])
        if response["next"]:
            OFFSET+=50
        else:
            end=True
    return tracks

tracks = getUserLikedTracks()
print("Hai messo 'mi piace' a " + str(len(tracks)) + " brani")