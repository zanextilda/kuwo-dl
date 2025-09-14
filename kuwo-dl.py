import requests
import datetime
import tqdm
from tqdm import tqdm
from tqdm.utils import CallbackIOWrapper
import json
import re
import os
from mutagen.id3 import ID3, APIC
from mutagen.flac import Picture
from mutagen import File
from colorama import Fore, just_fix_windows_console

just_fix_windows_console()

red = Fore.RED
cyan = Fore.CYAN
yellow = Fore.YELLOW
magenta = Fore.MAGENTA
blue = Fore.BLUE
green = Fore.GREEN
white = Fore.WHITE

#config
search_result_limit = 5
dump_metadata = False
keep_album_art = False
create_album_folder = True
verbose = False
#

try:
    os.makedirs('downloads')
    os.makedirs('covers')
    os.makedirs('metadata')
except:
    pass

trackCheck = 'play_detail'
albumCheck = 'album_detail'

def download(url: str, fname: str, chunk_size=1024):
    dlcount = 0
    resp = requests.get(url, stream=True)
    total = int(resp.headers.get('content-length', 0))
    
    with open(fname, 'wb') as file, tqdm(bar_format='{l_bar}{bar:10}{r_bar}{bar:-50b}', desc= f" {yellow}[ + ]" , total=total, unit='iB', unit_scale=True, unit_divisor=1024) as bar:
        for data in resp.iter_content(chunk_size=chunk_size):
            size = file.write(data)
            bar.update(size)

def add_album_art(file_path, album_art_path):
    audio = File(file_path)
    
    if audio is None:
        if verbose == True:
            print(f" {white}Could not read file: {red}{file_path}{white}")
        return
    
    if file_path.lower().endswith('.mp3'):
        try:
            if not audio.tags:
                audio.add_tags()
            
            for tag in audio.tags.values():
                if isinstance(tag, APIC):
                    audio.tags.remove(tag)
            
            with open(album_art_path, 'rb') as img:
                audio.tags.add(
                    APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,
                        desc='Front Cover',
                        data=img.read()
                    )
                )
        except Exception as e:
            if verbose == True:
                print(f" {white}Could not add album art to: {red}{file_path} - {e}{white}")
    
    elif file_path.lower().endswith('.flac'):
        try:
            with open(album_art_path, 'rb') as img:
                pic = Picture()
                pic.data = img.read()
                pic.type = 3
                pic.mime = 'image/jpeg'
                pic.desc = 'Front Cover'

                audio.clear_pictures()
                audio.add_picture(pic)
        except Exception as e:
            if verbose == True:
                print(f" {white}Could not add album art to: {red}{file_path} - {e}{white}")

    audio.save()
    if verbose == True:
        print(f" {white}Album art added to: {green}{file_path}{white}")

def sanitize_filename(filename):
    disallowed_characters = re.compile(r"[=_()/\-?]")
    sanitized = disallowed_characters.sub('', filename)
    max_length = 255
    sanitized = sanitized[:max_length]
    sanitized = sanitized.strip()
    return sanitized

loop = True
while loop == True:
    downloadTask = False
    print()
    url = input(f" {cyan}Enter URL or Type to Search (track, album):{white} ")
    print()

    ID = url.split('/')[-1]

    if trackCheck in url:
        media_type = 'track'

    if albumCheck in url:
        media_type = 'album'

    if trackCheck not in url and albumCheck not in url:
        media_type = 'search'

    if media_type == 'search':
        results = ''
        search_term = url
        search_url = f'https://search.kuwo.cn/r.s?client=kt&all={search_term}&pn=0&rn={str(search_result_limit)}&vipver=1&ft=music&encoding=utf8&rformat=json&mobi=1'
        try:
            response = requests.get(search_url)
            data = response.json()

            for item in data['abslist']:
                minfo = item['MINFO'].replace('|AAC48', '')
                tid = item['DC_TARGETID']
                aid = item['ALBUMID']
                album = item['ALBUM'].replace('(Explicit)', '[E]')
                artist = item['ARTIST'].replace('&', ', ')
                song = item['SONGNAME'].replace('(Explicit)', '[E]')
                cover_url = "http://img2.sycdn.kuwo.cn/star/albumcover/" + item['web_albumpic_short']
                album_url = "https://www.kuwo.cn/album_detail/" + item['ALBUMID']
                song_url = "https://www.kuwo.cn/play_detail/" + item['DC_TARGETID']

                entries = minfo.split(';')
                parsed_output = []
                for entry in entries:
                    fields = entry.split(',')
                    fmt = ''
                    bitrate = ''
                    size = ''
                    
                    for field in fields:
                        key, value = field.split(':')
                        if key == 'format':
                            fmt = value
                        elif key == 'bitrate':
                            bitrate = value
                        elif key == 'size':
                            size = value.upper()

                    if not 'ogg' in fmt:     
                        parsed_output.append(f"{fmt}_{bitrate}|{size}")
                
                for line in parsed_output[::-1]:
                    codec = line
                
                quality = codec.split('|')[0].split('_')[0]
                size = codec.split('|')[1]
                
                results += (f" {green}{artist} - {song} {white}({magenta}{quality.upper()}{white}) [{yellow}{size}{white}] {white}({blue}{album}{white})\n {cyan}Track URL:{white} {song_url}\n {cyan}Album URL:{white} {album_url}\n\n")
        except:
            pass
        print(results)


    if media_type == 'track':
        downloadTask = True
        info = ''
        results = ''
        
        print(f' {magenta}Parsing track...{white}')
        print()
        trackInfo = f"https://musicpay.kuwo.cn/music.pay?op=query&action=download&ids={ID}"
        tinfo = requests.get(trackInfo).json()['songs'][0]
        songname = tinfo['name'].replace('(Explicit)', '[E]')
        duration = tinfo['duration']
        artist = tinfo['artist'].replace('&', ', ')
        releaseUnix = tinfo['timingonline']
        dt_object = datetime.datetime.fromtimestamp(int(releaseUnix))
        release = str(dt_object.strftime('%Y-%m-%d'))
        minfo = tinfo['MINFO']
        album = tinfo['album']
        trackNo = '0'
        tid = tinfo['id']
        coverUrl = requests.get(f"https://artistpicserver.kuwo.cn/pic.web?corp=kuwo&type=rid_pic&pictype=0&size=0&rid={tid}").text

        entries = minfo.split(';')
        parsed_output = []
        for entry in entries:
            fields = entry.split(',')
            fmt = ''
            bitrate = ''
            size = ''
            
            for field in fields:
                key, value = field.split(':')
                if key == 'format':
                    fmt = value
                elif key == 'bitrate':
                    bitrate = value
                elif key == 'size':
                    size = value.upper()
                    
            if not 'ogg' in fmt:     
                parsed_output.append(f"{fmt}_{bitrate}|{size}")

        for line in parsed_output[::-1]:
            codec = line
        
        quality = codec.split('|')[0].split('_')[0]
        bitrate = codec.split('|')[0].split('_')[-1] + 'kbps'
        size = codec.split('|')[1]

        info += f"{songname.replace(' [E]','')}|{artist}|{album}|{trackNo}|{quality}|{bitrate}|{release}|{size}|{tid}\n"
        results += f" {green}{artist} - {songname} {white}({magenta}{quality.upper()}{white}) [{yellow}{size}{white}]\n"

    if media_type == 'album':
        downloadTask = True
        print(f' {magenta}Parsing album...{white}')
        print()
        info = ''
        results = ''
        albumInfo = f"https://search.kuwo.cn/r.s?albumid={ID}&stype=albuminfo&pcjson=1"

        ainfo = requests.get(albumInfo).json()

        album = ainfo['name']
        release = ainfo['pub']
        print(f"[{cyan}{album}{white}] ({yellow}{release}{white})")
        coverUrl = ainfo['img'].replace('/120/', '/0/').replace('/240/', '/0/')
        
        tracks = ainfo['musiclist']

        for track in tracks:
            songname = track['name'].replace('(Explicit)', '[E]')
            
            artist = track['artist'].replace('&', ', ')
            formats = track['formats'].replace('|AAC48', '')
            bestFormat = formats.split('|')[-1]
            trackNo = track['track']
            tid = track['id']
            minfo = track['MINFO']

            entries = minfo.split(';')
            parsed_output = []
            for entry in entries:
                fields = entry.split(',')
                fmt = ''
                bitrate = ''
                size = ''
                
                for field in fields:
                    key, value = field.split(':')
                    if key == 'format':
                        fmt = value
                    elif key == 'bitrate':
                        bitrate = value
                    elif key == 'size':
                        size = value.upper()
                        
                if not 'ogg' in fmt:
                    parsed_output.append(f"{fmt}_{bitrate}|{size}")

            for line in parsed_output[::-1]:
                codec = line

            quality = codec.split('|')[0].split('_')[0]
            bitrate = codec.split('|')[0].split('_')[-1] + 'kbps'
            size = codec.split('|')[1]
              
            info += f"{songname.replace(' [E]','')}|{artist}|{album}|{trackNo}|{quality}|{bitrate}|{release}|{size}|{tid}\n"
            results += f" {trackNo}. {green}{artist} - {songname} {white}({magenta}{quality.upper()}{white}) [{yellow}{size}{white}]\n"
            
    if downloadTask == True:
        print(results)

        continueCheck = input(f' {cyan}Would you like to download the above track(s)? (Y/n):{white} ')

        if continueCheck == 'Y' or continueCheck == 'y' or continueCheck == 'Yes' or continueCheck == 'YES' or continueCheck == 'yes':
            dl = True

        elif continueCheck == 'N' or continueCheck == 'n' or continueCheck == 'No' or continueCheck == 'NO' or continueCheck == 'no':
            dl = False

        else:
            dl = False

        if dl == False:
            dlStatus = f' {red}Aborted download!{white}'
        elif dl == True:
            dlStatus = f' {green}Starting download(s)...{white}'

        print()
        print(dlStatus)

        if dl == True:
            if dump_metadata == True:
                if media_type == 'track':
                    tn = tinfo['name'].replace('(Explicit)', '')
                    an = tinfo['artist']

                    jsonName = f"{tn}"
                    jsonName = sanitize_filename(jsonName)
                    
                    with open(f'metadata/{jsonName}.json', 'w', encoding='utf-8') as json_file:
                        json.dump(tinfo, json_file, ensure_ascii=False, indent=4)
                    if verbose == True:
                        print(f' Metadata dumped to: {green}metadata/{jsonName}.json{white}')
                    print()

                

                elif media_type == 'album':
                    try:
                        if media_type == 'album' and create_album_folder == True:
                            dest1 = f'metadata/{sanitize_filename(album.replace(" (Explicit)","").replace(" [Explicit]",""))}/'
                            os.makedirs(dest1)
                        else:
                            dest1 = f'metadata/'
                    except:
                        a = True
                    
                    
                    for track in tracks:
                        tn = track['name'].replace('(Explicit)', '[E]').replace(' [E]','')
                        an = track['artist']

                        jsonName = f"{tn}"
                        jsonName = sanitize_filename(jsonName)
                        
                        with open(f'{dest1}/{jsonName}.json', 'w', encoding='utf-8') as json_file:
                            json.dump(track, json_file, ensure_ascii=False, indent=4)
                        if verbose == True:
                            print(f' Metadata dumped to: {green}metadata/{jsonName}.json{white}')
                    print()

                
            try: 
                localImgfile = 'covers/img.jpg'
                imgdata = requests.get(coverUrl)
                with open(localImgfile, 'wb')as imgfile:
                    imgfile.write(imgdata.content)
                    if verbose == True:
                        print(f' {white}Cover downloaded: {green}{localImgfile}{white}')
            except:
                 if verbose == True:
                    print(f' {white}Cover not downloaded: {red}{localImgfile}{white}')
            print()

            try:
                if media_type == 'album' and create_album_folder == True:
                    dest = f'downloads/{sanitize_filename(album.replace(" (Explicit)","").replace(" [Explicit]",""))}/'
                    os.makedirs(dest)
                else:
                    dest = f'downloads/'
            except:
                a = True
                
            for line in info.splitlines():
                trackId = line.split('|')[-1]
                trackName = line.split('|')[0]
                quality = line.split('|')[4]
                url_response = requests.get(f"https://music-api.gdstudio.xyz/api.php?types=url&source=kuwo&id={trackId}&btwaf=3257700").json()
                sourceUrl = url_response['url'].split('?')[0]
                ext = url.split('.')[-1]
                print(f" {green}{trackName}.{quality}{white}")
                localFile = f'{dest}/{sanitize_filename(trackName)}.{quality}'
                download(sourceUrl, localFile)

                album_art_path = localImgfile

                if quality == 'mp3':
                    mp3_file = localFile
                    add_album_art(mp3_file, album_art_path)
                elif quality == 'flac':
                    flac_file = localFile
                    add_album_art(flac_file, album_art_path)
                
                print()
            try:
                if keep_album_art == True:
                    os.rename(localImgfile, f'covers/ - {sanitize_filename(album.replace(" (Explicit)","").replace(" [Explicit]",""))}.jpg')
                    if verbose == True:
                        print(f' {white}Cover: {green}Saving{white}')
                elif keep_album_art == False:
                    os.remove(localImgfile)
                    if verbose == True:
                        print(f' {white}Cover: {red}Removed{white}')
            except:
                if verbose == True:
                    print(f' {white}Cover: {yellow}Exists{white}')
