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
- `colorama`
  
Any suggestions on what could be added, please let me know. :)

<img width="841" height="954" alt="image" src="https://github.com/user-attachments/assets/db3323ab-727d-42e2-8777-c50be07987ff" />






