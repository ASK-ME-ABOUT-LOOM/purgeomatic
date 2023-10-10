# Configuration steps for using these scripts on Synology
### Credit to [/u/OkBoomerEh](https://www.reddit.com/user/OkBoomerEh) on reddit

## ENV File

Create a new folder under /docker/purgeomatic and create a file there called purgeomatic.env. You can reference this from the command line as `/volume1/docker/purgeomatic/purgeomatic.env`.

## SSH Permission

To avoid the error "permission denied while trying to connect to the Docker daemon socket," when running the command interactively from the prompt, make sure you run `sudo -i` and enter the Synology admin password, which will allow the `docker` command to run as root.

## Scheduled Task

To get the script working with scheduled tasks/cron, be sure to disable interactive mode when executing the `docker` command by removing the `-it` from the command line, otherwise you'll get the error "the input device is not a TTY."

1. Download the [sample .env](https://github.com/ASK-ME-ABOUT-LOOM/purgeomatic/blob/main/.env.example) file and rename it to purgeomatic.env
2. Create a new folder on Synology NAS under `/docker/purgeomatic` and copy purgeomatic.env into that folder. Edit the file as needed (highly recommend uncommenting the dry run line until you are 100% sure things are working).
3. From the Synology DSM UI set up a Cleanup Movies task:
   1. In Control Panel &rarr; Task Scheduler &rarr; Create Scheduled Task &rarr; User Defined Script.
   2. Name the task "Cleanup Movies", and choose the user root.
   3. In the User Defined Script box paste in `docker run --rm --env-file /volume1/docker/purgeomatic/purgeomatic.env --network=host ghcr.io/ask-me-about-loom/purgeomatic:latest python delete.movies.unwatched.py`
4. From the Synology DSM UI set up a Cleanup TV Series task:
   1. In Control Panel &rarr; Task Scheduler &rarr; Create Scheduled Task &rarr; User Defined Script.
   2. Name the task "Cleanup TV Series", and choose the user root.
   3. In the User Defined Script box paste in `docker run --rm --env-file /volume1/docker/purgeomatic/purgeomatic.env --network=host ghcr.io/ask-me-about-loom/purgeomatic:latest python delete.tv.unwatched.py`
5. Click on the task, and then the Run button.  Watch your email for results.

## Nothing Found

I kept running the script in dry-run mode, and it would find nothing regardless of how many days I set in the env file. Turns out that my Tautulli section IDs weren't default for whatever reason. I figured out the section ID by clicking on Libraries in Tautulli, then clicked Movies or TV Shows, then looked at the URL to find the Section ID. Edit those section IDs in the .env file and uncomment those lines.
