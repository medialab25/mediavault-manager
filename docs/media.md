# Media Overview

## Folder Structure

- media
  - movies-{media-quality}
    - {Movie Title} ({Release Year})
      - {Movie Title} ({Release Year}) {Quality Full}
      - {additional files from download}
  - tv-{media-quality}
    - tv-title {year}       # Year optional
      - Season {season}
        - {Series Title} - S{season:00}E{episode:00} - {Episode Title} {Quality Full}
      - {additional files from download}

  - movies-merged # Output of the merge function
  - tv-merged   # Output of the merge function

Notes:
- All paths defined in the config.json for media
- Any media file that does not follow the format needs 

