import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        self.tautulliHost = os.getenv("TAUTULLI", "http://localhost:8181")
        self.tautulliAPIkey = os.getenv("TAUTULLI_API")
        self.overseerrHost = os.getenv("OVERSEERR", "http://localhost:5055")
        self.overseerrAPIkey = os.getenv("OVERSEERR_API")
        self.tautulliMovieSectionID = os.getenv("TAUTULLI_MOVIE_SECTIONID", "1")
        self.tautulliTvSectionID = os.getenv("TAUTULLI_TV_SECTIONID", "2")
        self.tautulliNumRows = os.getenv("TAUTULLI_NUM_ROWS", "3000")
        self.daysSinceLastWatch = int(os.getenv("DAYS_SINCE_LAST_WATCH", "500"))
        self.daysWithoutWatch = int(os.getenv("DAYS_WITHOUT_WATCH", 60))
        self.dryrun = os.getenv("DRY_RUN", None) != None
        self.radarrHost = os.getenv("RADARR", "http://localhost:7878")
        self.radarrAPIkey = os.getenv("RADARR_API")
        self.sonarrHost = os.getenv("SONARR", "http://localhost:8989")
        self.sonarrAPIkey = os.getenv("SONARR_API")
        if self.dryrun:
            print("DRY_RUN enabled!")

    def check(self, *keys):
        retval = True
        for k in keys:
            v = getattr(self, k, None)
            if v is None:
                print(f"ERROR: '{k}' env not set. Cannot continue.")
                retval = False
        return retval
