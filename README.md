# purgeomatic - Seek out and delete content nobody is watching. 
## 💣 This software will delete your data! 💣

![Python](https://img.shields.io/badge/python-3.10%20|%203.11-blue) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## Introduction

### Features

 - Compatible with cron
 - Delete unwatched movies & tv series
 - Delete a single movie from Radarr/Tautulli/Overseerr using delete.movie.py
 - Supports a 'dry run' mode so you can test it
 - Supports a whitelist of content that should never be deleted using TMDB/TVDB IDs in the `protected` file

### Summary

I could never get the [JBOPS scripts](https://github.com/blacktwin/JBOPS) to work, and disk utilization has been a problem that crops up every few months for several years running, so I finally sat down and wrote my own script. It relies on being able to access an API for tautulli/radarr/sonarr, and it will also delete the media entry from overseerr if you use it.

The gist of the code is that it uses Tautulli's API to list all of the media in the media_info table for Tautulli's movie & tv sections (in my case those are "section_id=1" for movies and "section_id=2" for tv). Then it steps through every media item it finds and checks if it's been watched in a while. If it hasn't, it gets deleted!

The delete is accomplished by it looking up the item using Radarr/Sonarr's API. It also connects to Overseerr's API and deletes the movie based on the TMDB/TVDB ID it pulls from Radarr/Sonarr's entry.

## How to use

### Requirements

 - Tautulli
 - Radarr (if deleting movies)
 - Sonarr (if deleting TV)
 - Overseerr (optional: the script will work without an overseer configuration)

*Please note:* these scripts rely on Plex's metadata to supply TMDB/TVDB IDs. **Please take a moment to refresh the metadata in your Plex libraries before running them.**

### Scripts

There are three main scripts in this package:

- `delete.movies.unwatched.py`: For bulk-deleting movies that nobody has watched in a while.
- `delete.tv.unwatched.py`: For bulk-deleting entire TV series that nobody has watched in a while.
- `delete.movie.py`: For deleting a single movie from Radar/Overseerr/Tautulli. 

### Usage

The easiest way to use this software is via the published container image. You can either pass all of the variables on the command line (`-e VARIABLE`) or use a local .env file, which I recommend. You can pull the [.env.example](https://github.com/ASK-ME-ABOUT-LOOM/purgeomatic/blob/main/.env.example) file from this project and rename it to .env to start. 

There are defaults for nearly every setting. You'll absolutely need to set the API keys for your Radarr/Sonarr/Overseerr/Tautulli applications. Anything commented out in that example file is the default setting. If it works for you, you don't need to set it! 

If your *arr applications are running on the same machine you're using to run these scripts, you'll need to use the `--network=host` configuration flag, or the container won't be able to talk to localhost.

Once you've got your .env file configured, call it with:

`docker run --rm -it --env-file .env --network=host ghcr.io/ask-me-about-loom/purgeomatic:latest python delete.movies.unwatched.py`

Example output:

```
$ docker run --rm -it --env-file .env --network=host ghcr.io/ask-me-about-loom/purgeomatic:latest python delete.movies.unwatched.py
DRY_RUN enabled!
--------------------------------------
2023-08-25T12:40:57.288608
DRY RUN: Chaos Walking | Radarr ID: 1445 | TMDB ID: 412656
DRY RUN: Captain Marvel | Radarr ID: 885 | TMDB ID: 299537
DRY RUN: Captain America: Civil War | Radarr ID: 1768 | TMDB ID: 271110
DRY RUN: Black Widow | Radarr ID: 1517 | TMDB ID: 497698
DRY RUN: Birds of Prey (and the Fantabulous Emancipation of One Harley Quinn) | Radarr ID: 1092 | TMDB ID: 495764
DRY RUN: Bill & Ted's Excellent Adventure | Radarr ID: 1777 | TMDB ID: 1648
DRY RUN: Bill & Ted's Bogus Journey | Radarr ID: 1778 | TMDB ID: 1649
DRY RUN: Big Hero 6 | Radarr ID: 71 | TMDB ID: 177572
DRY RUN: Big | Radarr ID: 71 | TMDB ID: 177572
DRY RUN: Batman Begins | Radarr ID: 1745 | TMDB ID: 272
DRY RUN: Assault on Precinct 13 | Radarr ID: 1212 | TMDB ID: 17814
DRY RUN: 21 Jump Street | Radarr ID: 1096 | TMDB ID: 64688
Total space reclaimed: 164.88GB
```

### Protected items

If you like, you can protect items from deletion. Create a file called `protected` and put the TMDB or TVDB IDs you never want to delete in it, one per line. When you invoke the script, volume mount the protected file into `/app/protected` and any specific media IDs found in the file will be ignored, even in dry run mode.

Example command:

```
docker run --rm -it --env-file .env --network=host -v /home/user/protected:/app/protected ghcr.io/ask-me-about-loom/purgeomatic:latest python delete.movies.unwatched.py
```

An example of the contents of a `protected` file:

```
4011
278
238
10386
```

Note: because the `protected` file uses TMDB & TVDB IDs, there is a possibility of overlap. If you're concerned about this, I suggest you create separate files for running with the TV and movie deletes, i.e. `-v /home/user/protectedtv:/app/protected` and `-v /home/user/protectedmovies:/app/protected`.

### Protected Tags

Additionally, you may also specify tags from Radarr/Sonarr for which content must not be deleted. Those tags can be provided as a comma-separated list of IDs (**not tag names!**) using the `RADARR_PROTECTED_TAGS` and `SONARR_PROTECTED_TAGS` environment variables. That's a great way to simplify protecting specific media - you might also use the automated tagging feature within Radarr/Sonarr to automatically protect media matching specific criteria.

The best way to get the corresponding tag IDs is to simply browse to http://\<Radarr|Sonarr\>/api/v3/tag?apikey=\<Your API-Key\> - The output should look like this:

```json
[
  {
    "label": "rssimport",
    "id": 21
  },
  {
    "label": "example",
    "id": 22
  },
  {
    "label": "noautodelete",
    "id": 26
  }
]
```

If we'd like to exclude the tags "example" and "noautodelete", we'd set `<RADARR|SONARR>_PROTECTED_TAGS=22,26`. 

### Alternate usage

If you wish, you can also run the python code yourself. This code has been tested on python 3.10 and 3.11.

Example steps (may vary depending on your environment):

1) Clone the repo:

```
git clone https://github.com/ASK-ME-ABOUT-LOOM/purgeomatic.git
```

2) Update your .env file:

```
cd purgeomatic
mv .env.example .env
```

3) Create your venv:

```
make venv
source .venv/bin/activate
pip install -r requirements.txt
```

4) Run the code:

```
python delete.movies.unwatched.py
```

### Configuration

The scripts use the following environment variables for configuration:

- `RADARR`: The URL & port of your Radarr installation, e.g. `http://localhost:7878`

- `RADARR_API`: The API key for accessing your Radarr installation

- `TAUTULLI`: The URL & port of your Tautulli installation, e.g. `http://localhost:8181`

- `TAUTULLI_API`: The API key for accessing your Tautulli installation

- `SONARR`: The URL & port of your Sonarr installation, e.g. `http://localhost:8989`

- `SONARR_API`: The API key for accessing your Sonarr installation

- `OVERSEERR`: The URL & port of your Overseerr installation, e.g. `http://localhost:5055`

- `OVERSEERR_API`: The API key for accessing your Overseerr installation. Be sure to comment out the Overseerr connection variables in your `.env` file if you don't use Overseerr. It will keep your logs neat.
 
- `RADARR_PROTECTED_TAGS`: A comma-separated list of Radarr tag IDs to dynamically exclude content from deletion. Browse to http://\<Radarr\>/api/v3/tag?apikey=\<Your API-Key\> to see the IDs corresponding to your tags. Movies containing that tag will not be deleted. Leave blank or set to 0 to disable.

- `SONARR_PROTECTED_TAGS`: A comma-separated list of Sonarr tag IDs to dynamically exclude content from deletion. Browse to http://\<Sonarr\>/api/v3/tag?apikey=\<Your API-Key\> to see the IDs corresponding to your tags. Shows containing that tag will not be deleted. Leave blank or set to 0 to disable.

- `TAUTULLI_MOVIE_SECTIONID`: Default: 1. The section ID in Tautulli containing watch history metadata of movies. You can get this by going to Tautulli, clicking "Libraries," then clicking the library you want to use. Look at the URL bar and you'll see "library?section_id=". You want the number after "section_id=".

- `TAUTULLI_TV_SECTIONID`: Default: 2. The section ID in Tautulli containing watch history metadata of TV shows. You can get this by going to Tautulli, clicking "Libraries," then clicking the library you want to use. Look at the URL bar and you'll see "library?section_id=". You want the number after "section_id=".

- `TAUTULLI_NUM_ROWS`: Default: 3000. The maximum number of rows to fetch from Tautulli. This is required by the API call. Do you have more than 3000 media items? Increase the number. Otherwise the default will do just fine.

- `DAYS_SINCE_LAST_WATCH`: Default: 500. The default of 500 means that if it has been 500 days since anybody watched this media item, the script should delete it.

- `DAYS_WITHOUT_WATCH`: Default: 60. Sometimes people add media, but never watch it. The default of 60 means that if media got added, but nobody has watched it in 60 days, it gets purged. Set this to 0 to disable.

- `DRY_RUN`: Default: off. Enabling dry run mode means none of these scripts will execute a delete. The very _existence_ of this variable enables dry run mode - setting it to nothing or "" or even to "false" will still enable it. Disable it by commenting it out from your .env file or removing it entirely.

## Examples

### delete.movies.unwatched.py

```
$ docker run --rm -it --env-file .env --network=host ghcr.io/ask-me-about-loom/purgeomatic:latest python delete.movies.unwatched.py
--------------------------------------
2023-08-25T13:08:48.093402
DELETED: Willard | Radarr ID: 1906 | TMDB ID: 42532
DELETED: Up | Radarr ID: 908 | TMDB ID: 14160
DELETED: Super Mario Bros. | Radarr ID: 2133 | TMDB ID: 9607
DELETED: Spider-Man | Radarr ID: 997 | TMDB ID: 429617
DELETED: Predator | Radarr ID: 1982 | TMDB ID: 106
DELETED: Plane | Radarr ID: 2067 | TMDB ID: 646389
DELETED: Fall | Radarr ID: 2025 | TMDB ID: 985939
DELETED: Dune | Radarr ID: 1613 | TMDB ID: 841
DELETED: Dog | Radarr ID: 1837 | TMDB ID: 626735
Total space reclaimed: 158.70GB
```

### delete.tv.unwatched.py

```
$ docker run --rm -it --env-file .env --network=host ghcr.io/ask-me-about-loom/purgeomatic:latest python delete.tv.unwatched.py
--------------------------------------
2023-08-25T13:12:54.044326
DELETED: Tiny Beautiful Things | Sonarr ID: 566 | TVDB ID: 420985
DELETED: National Treasure: Edge of History | Sonarr ID: 539 | TVDB ID: 382210
DELETED: American Idol | Sonarr ID: 520 | TVDB ID: 70814
Total space reclaimed: 117.63GB
```

### delete.movie.py

```
$ docker run --rm -it --env-file .env --network=host ghcr.io/ask-me-about-loom/purgeomatic:latest python delete.movie.py --title "Harry Potter"
[0] Delete nothing
[1] Harry Potter and the Sorcerer's Stone (2001)
[2] Harry Potter and the Prisoner of Azkaban (2004)
[3] Harry Potter and the Order of the Phoenix (2007)
[4] Harry Potter and the Goblet of Fire (2005)
[5] Harry Potter and the Deathly Hallows: Part 2 (2011)
[6] Harry Potter and the Deathly Hallows: Part 1 (2010)
[7] Harry Potter and the Chamber of Secrets (2002)
*** The selected movie will be deleted ***
Choose a movie to delete [0]: 7
DELETED: Harry Potter and the Chamber of Secrets | Radarr ID: 2292 | TMDB ID: 672
Total space reclaimed: 17.03GB
```

## Transmission

If you're looking for support for Transmission, this project doesn't have it, but you can find a fork here which does:
[https://github.com/ronilaukkarinen/purgeomatic](https://github.com/ronilaukkarinen/purgeomatic)

Thanks [ronilaukkarinen](https://github.com/ronilaukkarinen)!

## Synology

Here's a [great writeup for getting this project working on your Synology box](README_synology.md) if you're just getting started. Credit to [/u/OkBoomerEh](https://www.reddit.com/user/OkBoomerEh) on reddit. 

## Common Problems

### I'm getting this weird Python error about JSON / connection string / whatever. What am I doing wrong?

Before opening an issue, *please* double-check your connection settings in your `.env` file or the environment variables! Nearly every time, the problem has been a typo in the API key or connection string, or it's been that the Section IDs are not correct. 

As a reminder, to get the correct section ID for a given library, go to Tautulli, click "Libraries," then click the library you want to use. Look at the URL bar and you'll see "library?section_id=". You want the number after "section_id=".

### I get the error "the input device is not a TTY" when I run the script with cron.

Make sure to remove the `-it` from the command line, which indicates to Docker that you'd like an interactive shell. 

## Contributors

<a href="https://github.com/ask-me-about-loom/purgeomatic/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=ask-me-about-loom/purgeomatic" />
</a>

[![HitCount](https://hits.dwyl.com/ask-me-about-loom/purgeomatic.svg)](https://hits.dwyl.com/ask-me-about-loom/purgeomatic)
