import config
import sys
import requests
import jq

# Define the command-line arguments
c = config.Config()
if not c.check("tautulliAPIkey", "radarrAPIkey"):
    print("ERROR: Required Tautulli/Radarr API key not set. Cannot continue.")
    sys.exit(1)

# check if the API keys are valid
c.apicheck(c.radarrHost, c.radarrAPIkey)


# function to get users from tautulli
def get_users():
    users = requests.get(
        f"{c.tautulliHost}/api/v2/?apikey={c.tautulliAPIkey}&cmd=get_users"
    )
    return (users)


# function to get user_ids from users
def get_user_id(users):
    # Define the jq filter to extract user_id
    filter_expr = jq.compile('.response.data[].user_id')
    # Apply filter to data
    user_ids = [user_id for user_id in filter_expr.input(users.json()).all()]
    return (user_ids)


# function to get playlists from tautulli
def get_playlists(user_id):
    playlists = requests.get(
        f"{c.tautulliHost}/api/v2?apikey={c.tautulliAPIkey}&cmd=get_playlists_table&section_id=1&user_id={user_id}"
    )
    return (playlists)


# function to get playlist rating_key from playlists
def get_playlist_rating_key(data):
    # Extract the 'data' field from the response
    playlist_data = data['response']['data']['data']
    # Search for the playlist with the specified title
    for playlist in playlist_data:
        if playlist['title'] == c.protectedPlaylistName:
            return playlist['ratingKey']
    # Return None if the playlist is not found
    return None


# function to get playlist content from tautulli
def get_playlist_content(rkey):
    movielist = requests.get(
        f"{c.tautulliHost}/api/v2?apikey={c.tautulliAPIkey}&cmd=get_children_metadata&rating_key={rkey}&media_type=playlist"
    )
    return (movielist)


# function to pick out the rating_keys from the movielist and return them
def get_rating_keys(movielist):
    rating_keys = [movie['rating_key']
                   for movie in movielist['response']['data']['children_list']]
    return rating_keys


# fucntion to get movie info from tautulli
def get_movie_info(rkey):
    movie = requests.get(
        f"{c.tautulliHost}/api/v2?apikey={c.tautulliAPIkey}&cmd=get_metadata&rating_key={rkey}"
    )
    return (movie)


# function to get guids from movie info
def get_movie_guids(movie):
    guids = jq.compile(".[].data.guids").input(movie.json()).first()
    return guids


# function to pick out the tmdbid from the guids
def get_tmdbid(guids):
    tmdbid = None
    try:
        if guids:
            tmdbid = [i for i in guids if i.startswith("tmdb://")][0].split(
                "tmdb://", 1
            )[1]
        else:
            raise ValueError("Empty guids")
    except Exception as e:
        print(
            f"WARNING: Unexpected GUID metadata from Tautulli. Please refresh your library's metadata in Plex. Using less-accurate 'search mode' for this title. Error message: "
            + str(e)
        )
        tmdbid = None
    return tmdbid


# function to append tmdbid to a file
def write_tmdbid(tmdbid):
    with open("/app/protected", "a") as file:
        file.write(tmdbid + "\n")
        

# function to call all the above functions
def main():
    users = get_users()
    user_ids = get_user_id(users)

    # Loop for each user
    for user_id in user_ids:
        playlists = get_playlists(user_id)
        rkey = get_playlist_rating_key(playlists.json())
        movielist = get_playlist_content(rkey)
        rating_keys = get_rating_keys(movielist.json())
        write_tmdbid("########### " + str(user_id) + " ###########")

        # Loop for each movie in the playlist
        for rating_key in rating_keys:
            movie = get_movie_info(rating_key)
            guids = get_movie_guids(movie)
            tmdbid = get_tmdbid(guids)
            write_tmdbid(tmdbid)

        # Separate users with "#" as line separator
        with open("/app/protected", "a") as file:
            file.write("#\n")


# Call the main function
if __name__ == "__main__":
    main()
