#!/usr/bin/python    

# Reference:
# https://developer.spotify.com/documentation/web-api/reference/
# https://spotipy.readthedocs.io/en/2.24.0/

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import configparser
import json
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from ttkthemes import ThemedTk
import webbrowser

def getCurrentSong():
    global sp
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

    global sp
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
                singleTrack.uri = track["track"]["uri"]
                tracks.append(singleTrack)
            if response["next"]:
                OFFSET+=50
            else: 
                end=True
        else:
            end=True
    return tracks

def filterByArtist(tracks, artist):
    filteredTracks = []
    for track in tracks:
        for singleArtist in track.artist:
            ## Se l'artista è presente nella lista degli artisti del brano, aggiungilo alla lista. Controllo anche i featuring
            if singleArtist['name'].lower() == artist.lower():
                filteredTracks.append(track)
                break
    return filteredTracks

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

def createPlaylist(name):
    # ENDPOINT https://api.spotify.com/v1/users/{user_id}/playlists
    # PARAMETRI GET PER QUESTA CHIAMATA:
    ## user (OBBLIGATORIO)          : l'id dell'utente
    ## name (OBBLIGATORIO)          : il nome della playlist
    ## public (OPZIONALE)           : se è pubblica o privata
    ## collaborative (OPZIONALE)    : se la playlist è in collaborazione
    ## description (OPZIONALE)      : descrizione della playlist
    
    global sp

    #Spotify permette con lo stesso nome di creare anche più di una playlist. E' da evitare
    user_id = sp.me()["id"]
    return sp.user_playlist_create(user=user_id, name=name)

def retrievePlaylists():
    # ENDPOINT https://api.spotify.com/v1/users/{user_id}/playlists
    # PARAMETRI GET PER QUESTA CHIAMATA:
    ## user (OBBLIGATORIO)          : l'id dell'utente
    ## limit (OPZIONALE)            : Numero massimo di elementi da restituire (fino a 50)
    ## offset (OPZIONALE)           : Da dove iniziare a restituire risultati

    ## N.B. il metodo user_playlists utilizza già i parametri limit=50, offset=0.
    ##      è necessario ridefinirlo per poter ottere risultati più di 50 playlist
    
    global sp

    user_id = sp.me()["id"]
    return sp.user_playlists(user=user_id) # Ritorna le playlist dell'utente fino a un massimo di 50

def checkPlaylistExists(name, playlists):
    found = False
    for playlist in playlists["items"]:
            if name == playlist["name"]:
                found = True
                return playlist
    return found

def addItemsToPlaylist(playlist_id, uri):
    # ENDPOINT https://api.spotify.com/v1/playlists/{playlist_id}/tracks
    # PARAMETRI PER QUESTA CHIAMATA
    # playlist_id (OBBLIGATORIO): l'ID spotify della playlist
    # position (OPZIONALE)      : La posizione dove inserire l'eelemento. Per inserire l'elemento in prima posizione position=0
    #                             Se omesso, la traccia sarà posta in coda alla playlist
    #uris (OPZIONALE)           : l'URI della traccia da aggiungere. E' di tipo lista

    global sp

    user_id = sp.me()["id"]
    sp.playlist_add_items(playlist_id, [uri])

def checkPlaylistItems(playlist_id, track_id):
    # ENDPOINT https://api.spotify.com/v1/playlists/{playlist_id}/tracks
    # PARAMETRI PER QUESTA CHIAMATA
    # playlist_id (OBBLIGATORIO)    : l'id della playlist spotify
    # market (OPZIONALE)            : se specificato, verranno ritornati solo contenuti presenti nel paese indicato
    # fields (OPZIONALE)            : filtro sulla query. Se omesso, tutti i campi verranno ritornati
    # limit (OPZIONALE)             : Numero massimo di elementi da restituire (fino a 50)
    # offset (OPZIONALE)            : Da dove iniziare a restituire risultati

    found = False
    empty = False
    finish = False
    global sp

    MARKET="IT"

    user_id = sp.me()["id"]

    while not empty and not found and not finish:
        response = sp.user_playlist_tracks(user_id, playlist_id, fields='items,uri,name,id,total', market='IT')
        if not response["items"]:
            empty = True
        for song in response["items"]:
            if song["track"]["id"] == track_id:
                found = True
                break
        if not found:
            finish = True
        
    return found

class Track:
    songName = ""
    artist = ""
    id = ""
    uri = ""

class FinestraPrincipale:
    def __init__(self, master=None):
        # Crea la finestra principale
        # Crea un Frame per un layout migliore
        mainFrame = ttk.Frame(window, padding="10")
        mainFrame.pack(fill=tk.BOTH, expand=True)
        # Assicurati che le colonne si espandano adeguatamente
        mainFrame.grid_columnconfigure(0, weight=1)
        mainFrame.grid_columnconfigure(1, weight=1)


        # Aggiungi una casella di testo per l'artista
        artistLabel = ttk.Label(mainFrame, text="Inserisci l'artista:")
        artistLabel.grid(row=0, column=0, pady=10, columnspan=2)  # Allinea al centro
        self.artistEntry = ttk.Entry(mainFrame)
        self.artistEntry.grid(row=1, column=0, padx=5, pady=10, sticky="ew", columnspan=2)

        # Aggiungi un pulsante per generare la playlist
        generateButton = ttk.Button(mainFrame, text="Genera Playlist", command=self.generatePlaylist)
        generateButton.config(width=20)  # Imposta la larghezza di generateButton
        generateButton.grid(row=2, column=0, pady=10)  # Occupa la colonna 0, espande da est a ovest
        # Aggiungi il bottone "Stop" accanto a "Genera Playlist"
        stopButton = ttk.Button(mainFrame, text="Stop", command=self.stopPlaylistGeneration)
        stopButton.config(width=20)      # Imposta la larghezza di stopButton
        stopButton.grid(row=2, column=1, pady=10)  # Occupa la colonna 1, espande da est a ovest


        # Crea l'etichetta per i messaggi di stato
        self.statusLabel = ttk.Label(mainFrame, text="In attesa della generazione...")
        self.statusLabel.grid(row=3, column=0, columnspan=2, pady=10)  # Occupa 2 colonne
    
    def generatePlaylist(self):
        global is_generating
        is_generating = True

        artist = self.artistEntry.get()
        self.updateStatus("Generazione della playlist per l'artista: " + artist + "...")
        tracks = getUserLikedTracks()
        #Trova solo i brani nuovi
        tracks = checkNewTracks(tracks)
        tracks = filterByArtist(tracks, artist)

        if tracks:
            self.updateStatus("Sono stati scansionati nuovi " + str(len(tracks)) + " brani piaciuti")
        else:
            self.updateStatus("Nessun nuovo brano piaciuto è stato riconosciuto per l'artista: " + artist)
            return
        playlists = retrievePlaylists()
        # Elementi utili: playlists["items"]["i"]["id"], playlists["items"]["i"]["name"]

        # Spotify permette con lo stesso nome di creare anche più di una playlist. E' da evitare
        # Quindi verifico se la playlist esiste già. Se non esiste la creo
        playlistName = artist + "- PY"
        createdPlaylist = checkPlaylistExists(playlistName, playlists)
        if createdPlaylist == False:
            # Se la playlist non esiste, la creo e aggiungo la traccia
            createdPlaylist = createPlaylist(playlistName)
        # Adesso sono certo che la playlist generata esista. Posso aggiungere la traccia
        self.updateStatus("Playlist generata: " + playlistName)

        for track in tracks:
            if not is_generating:
                return
            # Della playlist creata mi interessa createdPlaylist["id"] per poter aggiungere nuove tracce
            if not checkPlaylistItems(createdPlaylist["id"], track.id):
                addItemsToPlaylist(createdPlaylist["id"], track.uri)
        self.updateStatus("Playlist aggiornata con successo!")
    
    # Funzione per aggiornare il messaggio di stato
    def updateStatus(self, message):
        self.statusLabel.config(text=message)
        window.update()
    
    def stopPlaylistGeneration(self):
        global is_generating
        is_generating = False
        self.updateStatus("Generazione della playlist interrotta.")


config = configparser.RawConfigParser()
config.read('properties.properties')

CLIENT_ID = config.get("Authentication","CLIENT_ID")
CLIENT_SECRET = config.get("Authentication","CLIENT_SECRET")
REDIRECT_URI = config.get("Authentication","REDIRECT_URI")

#Variabili globali
is_generating = False  # Variabile per tenere traccia dello stato di generazione della playlist
sp = None  # Variabile globale per l'oggetto SpotifyOAuth

# multiple scopes
# playlist-modify-public -> Necessario per interagire con le playlist
oAuthscope = "user-read-email,user-read-private,user-library-read,user-read-playback-state,user-modify-playback-state,user-read-currently-playing, playlist-modify-public, playlist-modify-private"


def apri_finestra_principale():
    # Crea la finestra principale
    FinestraPrincipale(window)

# Funzione per gestire l'autenticazione
def autentica():
    global sp
    sp_oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=oAuthscope)
    # Verifica se è già stata effettuata l'autenticazione
    token_info = sp_oauth.get_cached_token()
    if not token_info:
        auth_url = sp_oauth.get_authorize_url()
        try:
            webbrowser.open(auth_url)
            # Aspetta che l'utente confermi l'autenticazione
            tk.messagebox.showinfo("Autenticazione", "Effettua l'accesso a Spotify, poi chiudi questa finestra.")
            code = sp_oauth.parse_response_code(auth_url)
            token_info = sp_oauth.get_access_token(code)
            if token_info:
                # Chiudi la finestra di autenticazione
                mainFrame.destroy()
                sp = spotipy.Spotify(auth=token_info['access_token'])
                # Apri la finestra principale
                apri_finestra_principale()
        except Exception as e:
            tk.messagebox.showerror("Errore", str(e))
    else:
        # Se l'utente è già autenticato, apri direttamente la finestra principale
        mainFrame.destroy()
        sp = spotipy.Spotify(auth=token_info['access_token'])
        apri_finestra_principale()

# Autenticato come
window = ThemedTk(theme="yaru")  # Utilizza il tema 'yaru' per un aspetto simile a Material Design
window.title("Generatore di Playlist Spotify")
window.geometry("400x200")  # Imposta le dimensioni della finestra
#window.resizable(False, False)  # Impedisce all'utente di modificare le dimensioni della finestra

# Crea la finestra di autenticazione
# Crea un Frame per un layout migliore
mainFrame = ttk.Frame(window, padding="10")
mainFrame.pack(fill=tk.BOTH, expand=True)
# Assicurati che le colonne si espandano adeguatamente
mainFrame.grid_columnconfigure(0, weight=1)
mainFrame.grid_columnconfigure(1, weight=1)

# Configura le righe per espandersi, permettendo il centramento verticale
mainFrame.grid_rowconfigure(0, weight=1)
mainFrame.grid_rowconfigure(1, weight=1)
mainFrame.grid_rowconfigure(2, weight=1)

# Aggiungi una casella di testo per l'artista
artistLabel = ttk.Label(mainFrame, text="Clicca per autenticarti con Spotify")
# Centra l'etichetta orizzontalmente e verticalmente
artistLabel.grid(row=0, column=0, columnspan=2, pady=10)

# Aggiungi un pulsante per generare la playlist
generateButton = ttk.Button(mainFrame, text="Login", command=autentica)
generateButton.config(width=20)  # Imposta la larghezza di generateButton
# Centra il pulsante orizzontalmente e verticalmente
generateButton.grid(row=1, column=0, columnspan=2, pady=10)

mainFrame.mainloop()


