import os
import re
import sys
import random
import vlc
import ytUrl
import selectors
import youtube_dl
import math
from termcolor import colored
from mutagen.mp3 import MP3

actions = colored("play", "green") + "        > play downloaded songs\n" \
          + colored("shuffle", "green") + "     > shuffle downloaded songs\n" \
          + colored("download", "green") + "    > download mp3 from a YouTube URL\n" \
          + colored("geturl", "green") + "      > get a YouTube URL from a search\n" \
          + colored("exit", "green") + "        > exit the player\n" \
          + colored("playls", "green") + "      > play songs from a playlist\n" \
          + colored("makepls", "green") + "     > make a new playlist\n" \
          + colored("editpls", "green") + "     > edit an existing playlist"


def getAllSongs():
    return sorted([s for s in os.listdir() if s.endswith('.mp3')])


def getAllPlaylists():
    return sorted([p for p in os.listdir() if p.endswith('.pls')])


def CamelCase(string):
    camelString = ''
    for word in string.split(" "):
        camelString += word.capitalize()
    return camelString


def songTime(seconds):
    bal = seconds
    minutes = int(str((seconds / 60)).split('.')[0])
    bal -= (minutes * 60)
    s = int(math.floor(bal))
    if len(str(s)) == 1:
        s = '0' + str(s)
    return str(minutes) + ":" + str(s)


def playSong(path):
    """Plays an mp3 file from a given path"""
    player = vlc.MediaPlayer(path)
    duration = MP3(path).info.length
    player.audio_set_delay(1000)  # keeps vlc from playback freezing issues (only sometimes)
    player.play()
    print("Playing " + colored(path[:-len(".mp3")], "green") + " --- " + colored(str(songTime(duration)), "blue"))

    sel = selectors.DefaultSelector()
    sel.register(sys.stdin.fileno(), selectors.EVENT_READ)
    try:
        while True:
            sys.stdout.write('> ')
            sys.stdout.flush()
            # Poll for command input as long as the player hasn't reached the end
            while player.get_state() != vlc.State.Ended:  # It's still running
                if sel.select(0.1):
                    break  # Input available - time to read input, so stop polling
            else:
                print()  # For beauty
                break  # Quit the command handling loop
            do = input().lower()
            if do == "time":
                print(colored(songTime(player.get_time() / 1000), "blue"))
            elif do == "pause":
                player.pause()
            elif do == "play":
                player.play()
            elif do == "stop" or do == "skip":
                player.stop()
                return
            elif do == "restart":
                player.stop()
                playSong(path)
                return
            elif do == "exit":
                player.stop()
                main()
    except EOFError:
        player.stop()
        sys.exit()


def getMeta(url):
    ydl_opts = {}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        meta = ydl.extract_info(url, download=False)
    return meta


def download(url, play=False):
    title = CamelCase(re.sub(r" ?\([^)]+\)", "", getMeta(url)['title'])).replace(":", "-").replace(" ", '')
    if title.endswith('.'):
        title = title[:-1]
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': title + '.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    if play:
        playSong(title + '.mp3')


def searchForSong(search):
    url = ytUrl.urlFromQuery(search)
    if url is not None:
        print("Your URL is:", colored(url, "blue"))
        if (input("Would you like to download " + colored(search, "green") + "? ")).lower()[0] == 'y':
            if (input("Do you want to play " + colored(search, "green") + " when it downloads? ")).lower()[0] == "y":
                print()
                download(url, play=True)
            else:
                print()
                download(url)
    else:
        print("A URL for " + search + " was not found.")


def shuffleSongs():
    songNames = getAllSongs()
    print()
    print('Shuffling songs... type "' + colored('skip', "yellow") + '" to skip one')
    playableSongs = songNames.copy()
    while len(playableSongs) > 0:
        playingSong = random.choice(playableSongs)
        playSong(playingSong)
        playableSongs.remove(playingSong)


def createPlaylist():
    while True:
        playlistName = input("What would you like to name this playlist? ")
        if ' ' in playlistName:
            playlistName = CamelCase(playlistName)
            print("No spaces allowed in playlist name. " + colored(playlistName, 'green') + " will be the name.")
        elif playlistName.endswith('.pls'):
            playlistName = playlistName.replace('.pls', '')  # The far-fetched possibility of 'crap.pls.pls'
        filename = playlistName + '.pls'
        if os.path.exists(filename):
            if input("A playlist with that name already exits. Would you like to overwrite it? ").lower()[0] == 'y':
                break
        else:
            break
    playlist = []
    songNames = getAllSongs()
    print()
    print(colored("Choose an option: ", 'blue'))
    print("[0] " + colored("Exit", "red"))
    songID = 1
    for songName in songNames:
        print("[" + str(songID) + "] Add " + colored(songName[:-len(".mp3")], "green"))
        songID += 1
    print()
    print(colored("Select the songs to add. Type " + colored("stop", 'green') + colored(" when you are finished.", 'blue'), "blue"))
    while True:
        action = input('Enter song number to add: ')
        if action == 'stop' or action == '' or action == '0':
            if len(playlist) != 0:
                data = ""
                for song in playlist:
                    data += song + "\n"
                with open(filename, 'w') as plsFile:
                    plsFile.write(data)
                break
            else:
                break
        else:
            playlist.append(songNames[int(action) - 1])


def playPlaylist(playlist=None):
    if not playlist:
        playlistNames = getAllPlaylists()
        if len(playlistNames) != 0:
            pID = 1
            print()
            print(colored("Choose an option: ", 'blue'))
            print("[0] " + colored("Exit", "red"))
            for playlistName in playlistNames:
                print("[" + str(pID) + "] Play " + colored(playlistName[:-len(".pls")], "green"))
                pID += 1
            action = int(input("Enter the playlist number to play: "))
            if action == 0:
                return
            playlist = playlistNames[action - 1]
        else:
            if input("No playlists found. Would you like to create one? ").lower()[0] == 'y':
                createPlaylist()
            return
    with open(playlist, 'r') as plsFile:
        songSequence = [line.strip('\n') for line in plsFile]
    for song in songSequence:
        playSong(song)


def editPlaylist(playlist=None):
    if not playlist:
        playlistNames = getAllPlaylists()
        if len(playlistNames) != 0:
            pID = 1
            print()
            print(colored("Choose an option: ", 'blue'))
            print("[0] " + colored("Exit", "red"))
            for playlistName in playlistNames:
                print("[" + str(pID) + "] Edit " + colored(playlistName[:-len(".pls")], "green"))
                pID += 1
            action = int(input("Enter the playlist number to edit: "))
            if action == 0:
                return
            playlist = playlistNames[action - 1]
        else:
            print("No playlists found. ")
            return
    allSongs = getAllSongs()
    with open(playlist, 'r') as plsFile:
        currentPlaylistData = plsFile.read().split('\n')
    if '' in currentPlaylistData:
        currentPlaylistData.remove('')
    #  print(currentPlaylistData)
    songID = 1
    print()
    print(colored("Song List:", 'blue'))
    for song in allSongs:
        print("[" + str(songID) + "] " + colored(song[:-len(".mp3")], "green"))
        songID += 1
    print()
    csongID = 1
    for csong in currentPlaylistData:
        print("Song #" + str(csongID) + ": " + colored(csong, 'green') + ':')
        newSongNumber = input('New song number: ')
        if newSongNumber == '':
            pass
        else:
            currentPlaylistData[csongID - 1] = allSongs[int(newSongNumber) - 1]
        csongID += 1
    while True:
        newSongNumber = input("Song #" + str(csongID) + ': ')
        csongID += 1
        if newSongNumber == '':
            break
        else:
            currentPlaylistData.append(allSongs[int(newSongNumber) - 1])
    if input("Would you like to write the changes to " + colored(playlist[:-len('.pls')], 'green') + "? ").lower()[0] == 'y':
        data = ""
        for song in currentPlaylistData:
            data += song + "\n"
        with open(playlist, 'w') as plsFile:
            plsFile.write(data)
        print(colored(playlist[len('.pls'):], 'green') + " was saved. ")


def main():
    while True:
        action = input('What would you like to do? ("' + colored('show', "yellow") + '" to show commands): ')

        if action == "show":
            print("\n" + actions + "\n")

        elif action == "exit":
            sys.exit()

        elif action == 'editpls':
            editPlaylist()

        elif action == 'playls':
            playPlaylist()

        elif action.startswith('playls') and len(action) > 6:
            try:
                action.split(' ')
            except IndexError:
                print(colored("Invalid playls commmand", 'red'))
                main()
            playlist = CamelCase(action[len("playls "):])
            if os.path.exists(playlist):  # They said playlist.pls (VERY unlikely ;)
                playPlaylist(playlist=playlist)
            else:
                playlist = playlist + ".pls"
                if os.path.exists(playlist):
                    playPlaylist(playlist)
                else:  # If we're still here, there ain't no such playlist
                    print(colored("Playlist not found.", 'red'))

        elif action == "play":
            print()
            songNames = getAllSongs()
            print(colored("Choose an option: ", 'blue'))
            print("[0] " + colored("Exit", "red"))
            print("[1] " + colored("Shuffle All", "magenta"))
            songID = 2
            for songName in songNames:
                print("[" + str(songID) + "] Play " + colored(songName[:-len(".mp3")], "green"))
                songID += 1
            print()
            command = input("Enter action number: ")

            if command.strip() == "1":  # This is a shuffle play mode
                shuffleSongs()

            # back to main if command is 0
            elif command.strip() == "0":
                main()

            else:  # we need to play the songID number
                playingSong = songNames[int(command) - 2]
                playSong(playingSong)

        elif action.startswith("play") and len(action) > 4:
            try:
                action.split(" ")[1]
            except IndexError:
                print(colored("Invalid play command.", "red"))
                main()
            song = action[len("play "):]
            capitalSong = CamelCase(song)
            if song.endswith(".mp3"):  # the song is equal to the path
                if os.path.exists(song):
                    playSong(song)
                else:
                    print(colored("Song not found.", "red"))
            elif capitalSong.endswith('.pls'):
                if os.path.exists(capitalSong):
                    playPlaylist(capitalSong)
                elif os.path.exists(capitalSong + '.pls'):
                    playPlaylist(capitalSong + '.pls')
            else:
                songList = [x for x in os.listdir() if x.endswith(".mp3")]
                if len(capitalSong) <= 3:
                    print(colored("Song not found.", "red"))
                elif len(capitalSong) >= 4:
                    for s in songList:
                        ls = s.lower()[:-len(".mp3")]
                        if capitalSong.lower() in ls or capitalSong.lower() == ls:
                            playSong(s)
                            main()
                    # if we're still here, there was no such song
                    # so let's see if it was supposed to be a playlist!
                    if capitalSong + '.pls' in os.listdir():
                        playPlaylist(capitalSong + '.pls')
                    print(colored("Song not found.", "red"))
                    if input("Would you like to search YouTube for " + colored(song, 'green') + "? ").lower()[0] == 'y':
                        searchForSong(song)

        elif action == "geturl":
            search = input("What are you searching for? ")
            searchForSong(search)

        elif action == "download":
            url = input("Enter the URL to download mp3 from: ")
            if (input("Do you want to play the song when it downloads? ")).lower()[0] == "y":
                print()
                download(url, play=True)
            else:
                print()
                download(url)

        elif action == "shuffle":
            shuffleSongs()

        elif action == "makepls":
            createPlaylist()

        else:
            print(action + ": " + colored("command not found.", 'red'))


if __name__ == "__main__":
    try:
        if sys.argv[1].endswith(".mp3"):
            playSong(sys.argv[1])
        elif sys.argv[1].endswith('.pls'):
            playPlaylist(sys.argv[1])
    except IndexError:
        main()
    print()
