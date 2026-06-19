from fileinput import close

Liked_songss = {
    "Bad Habits": "Ed Sheeran",
    "I'm Just Ken": "Ryan Gosling",
    "Mastermind": "Taylor Swift",
    "Uptown Funk": "Mark Ronson ft. Bruno Mars",
    "Ghost": "Justin Bieber"
}


with open("C:\\Users\\arbaz\\OneDrive\\Desktop\\codedex\\filer.txt","w") as file:
    file.write(str(Liked_songss))
    close()
print('done')

with open("C:\\Users\\arbaz\\OneDrive\\Desktop\\codedex\\filer.txt","r") as file:
    data = file.read()
    songs = eval(data)
    for artist, song in songs.items():
        print(f"{artist} by {song}")

