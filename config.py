import os
import sys
import json
import requests
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
        self.radarrProtectedTags = os.getenv("RADARR_PROTECTED_TAGS")
        self.sonarrHost = os.getenv("SONARR", "http://localhost:8989")
        self.sonarrAPIkey = os.getenv("SONARR_API")
        self.sonarrProtectedTags = os.getenv("SONARR_PROTECTED_TAGS")
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

    def apicheck(self, arrHost, arrAPIkey):
        apierrors = []

        result = self.apicheck_tautulli()
        if result is not None:
            apierrors.append(result)

        result = self.apicheck_arr(arrHost, arrAPIkey)
        if result is not None:
            apierrors.append(result)

        if self.overseerrAPIkey is not None:
            result = self.apicheck_overseerr()
            if result is not None:
                apierrors.append(result)

        if apierrors:
            print(*apierrors, sep="\n")
            sys.exit(1)

        return None

    def apicheck_tautulli(self):
        try:
            r = requests.get(
                f"{self.tautulliHost}/api/v2/?apikey={self.tautulliAPIkey}&cmd=arnold"
            )
            r.raise_for_status()
            apicheck = json.loads(r.text)
            if "result" in apicheck["response"]:
                if apicheck["response"]["result"] != "success":
                    return "ERROR: Tautulli error: API connection successful, but Tautulli does not report a status of 'success.' Is your Tautulli installation ok?"
            else:
                return "ERROR: Tautulli API connection failure. Please check your connection string/API key and try again."
        except Exception as e:
            return f"ERROR: Connection failure when attempting to contact your Tautulli API. Please double-check your connection string and API key configuration. Error raised:\n\t{e}"
        return None

    def apicheck_arr(self, arrHost, arrAPIkey):
        try:
            r = requests.get(f"{arrHost}/api/v3/config/host?apiKey={arrAPIkey}")
            r.raise_for_status()
            apicheck = json.loads(r.text)
            if not "apiKey" in apicheck:
                return "ERROR: Unexpected response from your Arr service's API. Please double-check your connection string/API key and try again."
        except Exception as e:
            return f"ERROR: Connection failure when attempting to contact your Arr service's API. Please double-check your connection string/API key and try again. Error raised:\n\t{e}"
        return None

    def apicheck_overseerr(self):
        try:
            headers = {"X-Api-Key": f"{self.overseerrAPIkey}"}
            r = requests.get(
                f"{self.overseerrHost}/api/v1/settings/main", headers=headers
            )
            r.raise_for_status()
            apicheck = json.loads(r.text)
            if not "apiKey" in apicheck:
                return "ERROR: Unexpected response from your Overseerr API. Please double-check your connection string/API key and try again."
        except Exception as e:
            return f"ERROR: Connection failure when attempting to contact your Overseerr API. Please double-check your connection string/API key and try again. Error raised:\n\t{e}"
        return None
