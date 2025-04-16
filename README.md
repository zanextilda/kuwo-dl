# kuwo-dl

A Python script to download fully tagged tracks and albums from from kuwo.cn and save the track metadata.

## Features

- Config menu is inside the python file at the top.
- Download tracks or albums by providing a URL.

  ` - https://www.kuwo.cn/album_detail/xxxxxxxx`

  ` - https://www.kuwo.cn/play_detail/xxxxxxxxx`

- Supports both MP3 and FLAC downloads without needing Auth/VIP.
- Tags audio with the max quality album art.
- Saves album art after download as its own file. (can be disabled in the config options)
- Dumps metadata into JSON files for tracks and albums. (can be disabled in the config options)
- Provides a clean `tqdm` progress bar during downloads.

## Requirements

- `requests`
- `tqdm`
- `mutagen`

I will work on adding a search function next and I will be adding color with `colorama`.
Any suggestions on what could be added, please let me know. :)

<img width="610" alt="image" src="https://github.com/user-attachments/assets/21551867-243c-4605-933d-0d28b48b922e" />

<img width="412" alt="image" src="https://github.com/user-attachments/assets/95a6476c-1730-4c2c-9791-84e4b4db0092" />




