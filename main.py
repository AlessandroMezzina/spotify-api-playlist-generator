#!/usr/bin/python    

# Reference:
# https://developer.spotify.com/documentation/web-api/reference/
# https://spotipy.readthedocs.io/en/2.24.0/

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import configparser
import json

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

    configOffset = json.load(open("utils.json", "r"))
    OFFSET=0
    LIMIT=50
    MARKET="IT"

    tracks=[]
    end = False

    ## Sono restituiti in ordine da 1 a n i brani piaciuti
    ## I brani più recenti 1,2... sono restituiti per primi
    while not end:
        response = sp.current_user_saved_tracks(market=MARKET, limit=LIMIT, offset=OFFSET)
        likedTracks = response["items"]

        if likedTracks:
            for track in likedTracks:
                singleTrack = Track()
                singleTrack.songName = track["track"]["name"]
                singleTrack.artist = track["track"]["artists"]
                singleTrack.id = track["track"]["id"]
                tracks.append(singleTrack)
            if response["next"]:
                OFFSET+=50
            else: 
                end=True
        else:
            end=True
    return tracks

def checkNewTracks(tracks):
    numNewTracks = len(tracks)
    configOffset = json.load(open("utils.json", "r"))
    if configOffset["OFFSET"].strip()!= "" :
        ## Se OFFSET è stato settato, riprendi la scansione nuovi brani da li
        OFFSET = int(configOffset["OFFSET"])
    else:
        OFFSET=0
    
    if len(tracks)>OFFSET:
        ## Significa che ci sono brani nuovi. Calcolo quanti sono
        numNewTracks = len(tracks) - OFFSET
    elif len(tracks) <= OFFSET:
        numNewTracks = 0

    OFFSET = len(tracks)
                
    configOffset["OFFSET"] = str(OFFSET)
    with open("utils.json", 'w') as f:
        f.write(json.dumps(configOffset, sort_keys=True, indent=4, separators=(',', ': ')))

    return tracks[:numNewTracks]

def createPlaylist():
    # ENDPOINT https://api.spotify.com/v1/users/{user_id}/playlists
    # PARAMETRI GET PER QUESTA CHIAMATA:
    ## user (OBBLIGATORIO)          : l'id dell'utente
    ## name (OBBLIGATORIO)          : il nome della playlist
    ## public (OPZIONALE)           : se è pubblica o privata
    ## collaborative (OPZIONALE)    : se la playlist è in collaborazione
    ## description (OPZIONALE)      : descrizione della playlist

    user_id = sp.me()["id"];
    sp.user_playlist_create(user=user_id, name="Playlist prova", description="Playlist prova")
    return

class Track:
    songName = ""
    artist = ""
    id = ""


config = configparser.RawConfigParser()
config.read('properties.properties')

CLIENT_ID = config.get("Authentication","CLIENT_ID")
CLIENT_SECRET = config.get("Authentication","CLIENT_SECRET")
REDIRECT_URI = config.get("Authentication","REDIRECT_URI")

# multiple scopes
# playlist-modify-public -> Necessario per interagire con le playlist
oAuthscope = "user-read-email,user-read-private,user-library-read,user-read-playback-state,user-modify-playback-state,user-read-currently-playing, playlist-modify-public"

#autenticazione
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI,scope=oAuthscope))

#getCurrentSong()
tracks = getUserLikedTracks()
#Trova solo i brani nuovi
tracks = checkNewTracks(tracks)

if tracks:
    print("Sono stati scansionati nuovi " + str(len(tracks)) + " brani piaciuti")
else:
    print("Nessun nuovo brano piaciuto è stato riconosciuto")

#createPlaylist()