import os
import config
import json
import requests
from datetime import datetime
import jq
import sys

c = config.Config()
if not c.check("tautulliAPIkey", "sonarrAPIkey"):
    print("ERROR: Required Tautulli/Sonarr API key not set. Cannot continue.")
    sys.exit(1)

c.apicheck(c.sonarrHost, c.sonarrAPIkey)

protected = []

try:
    protected_tags = [int(i) for i in c.sonarrProtectedTags.split(",")]
except Exception as e:
    protected_tags = []

if os.path.exists("./protected"):
    with open("./protected", "r") as file:
        while line := file.readline():
            protected.append(int(line.rstrip()))

print("--------------------------------------")
print(datetime.now().isoformat())


def purge(series):
    deletesize = 0
    tvdbid = None

    r = requests.get(
        f"{c.tautulliHost}/api/v2/?apikey={c.tautulliAPIkey}&cmd=get_metadata&rating_key={series['rating_key']}"
    )

    guids = jq.compile(".[].data.guids").input(r.json()).first()

    try:
        if guids:
            tvdbid = [i for i in guids if i.startswith("tvdb://")][0].split(
                "tvdb://", 1
            )[1]
    except Exception as e:
        print(
            f"WARNING: {series['title']}: Unexpected GUID metadata from Tautulli. Please refresh your library's metadata in Plex. Using less-accurate 'search mode' for this title. Error message: "
            + str(e)
        )
        guids = []

    f = requests.get(f"{c.sonarrHost}/api/v3/series?apiKey={c.sonarrAPIkey}")
    try:
        if guids:
            sonarr = (
                jq.compile(f".[] | select(.tvdbId == {tvdbid})").input(f.json()).first()
            )
        else:
            sonarr = (
                jq.compile(f".[] | select(.title == \"{series['title']}\")")
                .input(f.json())
                .first()
            )

        if sonarr["tvdbId"] in protected:
            return deletesize

        if any(e in protected_tags for e in sonarr["tags"]):
            return deletesize

        if not c.dryrun:
            response = requests.delete(
                f"{c.sonarrHost}/api/v3/series/"
                + str(sonarr["id"])
                + f"?apiKey={c.sonarrAPIkey}&deleteFiles=true"
            )

        try:
            if not c.dryrun and c.overseerrAPIkey is not None:
                headers = {"X-Api-Key": f"{c.overseerrAPIkey}"}
                o = requests.get(
                    f"{c.overseerrHost}/api/v1/search/?query=tvdb%3A"
                    + str(sonarr["tvdbId"]),
                    headers=headers,
                )
                overseerrid = jq.compile(
                    "[select (.results[].mediainfo.tvdbId = "
                    + str(sonarr["tvdbId"])
                    + ")][0].results[0].mediaInfo.id"
                ).input(o.json())
                o = requests.delete(
                    f"{c.overseerrHost}/api/v1/media/" + str(overseerrid.text()),
                    headers=headers,
                )
        except Exception as e:
            print("ERROR: Overseerr API error. Error message: " + str(e))

        action = "DELETED"
        if c.dryrun:
            action = "DRY RUN"

        deletesize = int(sonarr["statistics"]["sizeOnDisk"]) / 1073741824
        print(
            action
            + ": "
            + series["title"]
            + " | "
            + str("{:.2f}".format(totalsize))
            + "GB"
            + " | Sonarr ID: "
            + str(sonarr["id"])
            + " | TVDB ID: "
            + str(sonarr["tvdbId"])
        )
    except StopIteration:
        pass
    except Exception as e:
        print("ERROR: " + series["title"] + ": " + str(e))

    return deletesize


today = round(datetime.now().timestamp())
totalsize = 0
r = requests.get(
    f"{c.tautulliHost}/api/v2/?apikey={c.tautulliAPIkey}&cmd=get_library_media_info&section_id={c.tautulliTvSectionID}&length={c.tautulliNumRows}&refresh=true"
)
shows = json.loads(r.text)

try:
    for series in shows["response"]["data"]["data"]:
        if series["last_played"]:
            lp = round((today - int(series["last_played"])) / 86400)
            if lp > c.daysSinceLastWatch:
                totalsize = totalsize + purge(series)
        else:
            if c.daysWithoutWatch > 0:
                if series["added_at"] and series["play_count"] is None:
                    aa = round((today - int(series["added_at"])) / 86400)
                    if aa > c.daysWithoutWatch:
                        totalsize = totalsize + purge(series)
except Exception as e:
    print(
        "ERROR: There was a problem connecting to Tautulli/Sonarr/Overseerr. Please double-check that your connection settings and API keys are correct.\n\nError message:\n"
        + str(e)
    )
    sys.exit(1)

print("Total space reclaimed: " + str("{:.2f}".format(totalsize)) + "GB")
