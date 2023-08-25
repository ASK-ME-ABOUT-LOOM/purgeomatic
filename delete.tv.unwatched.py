import os
import config
import json
import requests
from datetime import datetime
import jq
import sys

c = config.Config()
if not c.check("tautulliAPIkey","overseerrAPIkey","sonarrAPIkey"):
    print("ERROR: Required Tautulli/Overseerr/Sonarr API key not set. Cannot continue.")
    sys.exit(1)

print("--------------------------------------")
print(datetime.now().isoformat())

def purge(series):

  deletesize = 0

  f = requests.get(f"{c.sonarrHost}/api/v3/series?apiKey={c.sonarrAPIkey}")

  try:
   sonarr = jq.compile('.[] | select(.title | contains("' + series['title'] + '"))').input(f.json()).first()
   if not c.dryrun:
       response = requests.delete(f"{c.sonarrHost}/api/v3/series/" + str(sonarr['id']) + f"?apiKey={c.sonarrAPIkey}&deleteFiles=true")

   try:
     # The overseer API key header
     headers = {"X-Api-Key": f"{c.overseerrAPIkey}"}
     o = requests.get(f"{c.overseerrHost}/api/v1/series/" + str(sonarr['tvdbId']), headers=headers)
     overseerr = json.loads(o.text)
     if not c.dryrun:
       o = requests.delete(f"{c.overseerrHost}/api/v1/media/" + str(overseerr['mediaInfo']['id']), headers=headers)
   except Exception as e:
     print("ERROR: Unable to connect to overseerr.")

   action = "DELETED"
   if c.dryrun:
       action = "DRY RUN"

   print(action + ": " + series['title'] + " | Sonarr ID: " + str(sonarr['id']) + " | TVDB ID: " + str(sonarr['tvdbId']))
   deletesize = (int(sonarr['statistics']['sizeOnDisk'])/1073741824)
  except StopIteration:
   pass
  except Exception as e:
   print("ERROR: " + series['title'] + ": " + str(e))

  return deletesize

today = round(datetime.now().timestamp())

totalsize = 0

r = requests.get(f"{c.tautulliHost}/api/v2/?apikey={c.tautulliAPIkey}&cmd=get_library_media_info&section_id={c.tautulliTvSectionID}&length={c.tautulliNumRows}&refresh=true")

shows = json.loads(r.text)
try:
  for series in shows['response']['data']['data']:
  
    if series['last_played']: 
      lp = round((today - int(series['last_played']))/86400)
      if lp > c.daysSinceLastWatch:
        totalsize = totalsize + purge(series) 
except Exception as e:
  print("ERROR: There was a problem connecting to Tautulli/Sonarr/Overseerr. Please double-check that your connection settings and API keys are correct.\n\nError message:\n" + str(e))
  sys.exit(1)

print("Total space reclaimed: " + str("{:.2f}".format(totalsize)) + "GB")
