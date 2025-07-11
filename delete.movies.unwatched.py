import os
import config
import json
import requests
from datetime import datetime
import jq
import sys

c = config.Config()
if not c.check("tautulliAPIkey", "radarrAPIkey"):
    print("ERROR: Required Tautulli/Radarr API key not set. Cannot continue.")
    sys.exit(1)

c.apicheck(c.radarrHost, c.radarrAPIkey)

protected = []

if os.path.exists("./protected"):
    with open("./protected", "r") as file:
        for line in file:
            line = line.split("#", 1)[0].strip()
            if line.isdigit():
                protected.append(int(line))

try:
    protected_tags = [int(i) for i in c.radarrProtectedTags.split(",")]
except Exception as e:
    protected_tags = []


print("--------------------------------------")
print(datetime.now().isoformat())


def purge(movie):
    deletesize = 0
    tmdbid = None

    r = requests.get(
        f"{c.tautulliHost}/api/v2/?apikey={c.tautulliAPIkey}&cmd=get_metadata&rating_key={movie['rating_key']}"
    )

    guids = jq.compile(".[].data.guids").input(r.json()).first()
    try:
        if guids:
            tmdbid = [i for i in guids if i.startswith("tmdb://")][0].split(
                "tmdb://", 1
            )[1]
    except Exception as e:
        print(
            f"WARNING: {movie['title']}: Unexpected GUID metadata from Tautulli. Please refresh your library's metadata in Plex. Using less-accurate 'search mode' for this title. Error message: "
            + str(e)
        )
        guids = []

    f = requests.get(f"{c.radarrHost}/api/v3/movie?apiKey={c.radarrAPIkey}")
    try:
        if guids:
            radarr = (
                jq.compile(f".[] | select(.tmdbId == {tmdbid})").input(f.json()).first()
            )
        else:
            radarr = (
                jq.compile(f".[] | select(.title == \"{movie['title']}\")")
                .input(f.json())
                .first()
            )

        if radarr["tmdbId"] in protected:
            return deletesize

        if any(e in protected_tags for e in radarr["tags"]):
            return deletesize

        if not c.dryrun:
            response = requests.delete(
                f"{c.radarrHost}/api/v3/movie/"
                + str(radarr["id"])
                + f"?apiKey={c.radarrAPIkey}&deleteFiles=true"
            )

        try:
            if not c.dryrun and c.overseerrAPIkey is not None:
                headers = {"X-Api-Key": f"{c.overseerrAPIkey}"}
                o = requests.get(
                    f"{c.overseerrHost}/api/v1/movie/" + str(radarr["tmdbId"]),
                    headers=headers,
                )
                overseerr = json.loads(o.text)
                o = requests.delete(
                    f"{c.overseerrHost}/api/v1/media/"
                    + str(overseerr["mediaInfo"]["id"]),
                    headers=headers,
                )
        except Exception as e:
            print("ERROR: Unable to connect to overseerr. Error message: " + str(e))

        action = "DELETED"
        if c.dryrun:
            action = "DRY RUN"

        deletesize = int(movie["file_size"]) / 1073741824
        if movie["last_played"]:
            lastplayed = datetime.fromtimestamp(int(movie["last_played"])).strftime("%Y %b %d")
        else:
            lastplayed = "Never"
        print(
            action
            + ": "
            + movie["title"]
            + " | "
            + str("{:.2f}".format(deletesize))
            + "GB"
            + " | Radarr ID: "
            + str(radarr["id"])
            + " | TMDB ID: "
            + str(radarr["tmdbId"])
            + " | Last played: "
            + lastplayed
        )
    except StopIteration:
        pass
    except Exception as e:
        print("ERROR: " + movie["title"] + ": " + str(e))

    return deletesize


today = round(datetime.now().timestamp())
totalsize = 0
r = requests.get(
    f"{c.tautulliHost}/api/v2/?apikey={c.tautulliAPIkey}&cmd=get_library_media_info&section_id={c.tautulliMovieSectionID}&length={c.tautulliNumRows}&refresh=true"
)
movies = json.loads(r.text)
count = 0

try:
    for movie in movies["response"]["data"]["data"]:
        if movie["last_played"]:
            lp = round((today - int(movie["last_played"])) / 86400)
            if lp > c.daysSinceLastWatch:
                totalsize = totalsize + purge(movie)
                count = count + 1
        else:
            if c.daysWithoutWatch > 0:
                if movie["added_at"] and movie["play_count"] is None:
                    aa = round((today - int(movie["added_at"])) / 86400)
                    if aa > c.daysWithoutWatch:
                        totalsize = totalsize + purge(movie)
                        count = count + 1
except Exception as e:
    print(
        "ERROR: There was a problem connecting to Tautulli/Radarr/Overseerr. Please double-check that your connection settings and API keys are correct.\n\nError message:\n"
        + str(e)
    )
    sys.exit(1)

print("Total space reclaimed: " + str("{:.2f}".format(totalsize)) + "GB")
print("Total items deleted:   " + str(count))
