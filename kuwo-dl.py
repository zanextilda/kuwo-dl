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

#config
dump_metadata = True
keep_album_art = True
create_album_folder = True
#

try:
    os.makedirs('downloads')
    os.makedirs('covers')
    os.makedirs('metadata')
except:
    a = True

trackCheck = 'play_detail'
albumCheck = 'album_detail'

def download(url: str, fname: str, chunk_size=1024):
    dlcount = 0
    resp = requests.get(url, stream=True)
    total = int(resp.headers.get('content-length', 0))
    
    with open(fname, 'wb') as file, tqdm(bar_format='{l_bar}{bar:10}{r_bar}{bar:-50b}', desc= " [ + ]" , total=total, unit='iB', unit_scale=True, unit_divisor=1024) as bar:
        for data in resp.iter_content(chunk_size=chunk_size):
            size = file.write(data)
            bar.update(size)

def add_album_art(file_path, album_art_path):
    audio = File(file_path)
    
    if audio is None:
        print(f"Could not read file: {file_path}")
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
            print(f"Could not add album art to {file_path}: {e}")
    
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
            print(f"Could not add album art to {file_path}: {e}")

    audio.save()
    print(f"Album art added to {file_path}.")
    
def sanitize_filename(filename):
    allowed_characters = re.compile(r"[^a-zA-Z0-9_.()'\-]")
    sanitized = allowed_characters.sub(' ', filename)
    max_length = 255
    sanitized = sanitized[:max_length]
    sanitized = sanitized.strip('. ')
    return sanitized

loop = True
while loop == True:
    print()
    url = input("Enter URL (track, album): ")
    print()

    ID = url.split('/')[-1]

    if trackCheck in url:
        media_type = 'track'

    if albumCheck in url:
        media_type = 'album'


    if media_type == 'track':
        info = ''
        results = ''
        
        print('Parsing track...')
        print()
        trackInfo = f"https://musicpay.kuwo.cn/music.pay?op=query&action=download&ids={ID}"
        tinfo = requests.get(trackInfo).json()['songs'][0]
        songname = tinfo['name'].replace('(Explicit)', '[E]')
        duration = tinfo['duration']
        artist = tinfo['artist']
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
                    
            parsed_output.append(f"{fmt}_{bitrate}|{size}")

        for line in parsed_output[::-1]:
            codec = line
        
        quality = codec.split('|')[0].split('_')[0]
        bitrate = codec.split('|')[0].split('_')[-1] + 'kbps'
        size = codec.split('|')[1]

        info += f"{songname.replace(' [E]','')}|{artist}|{album}|{trackNo}|{quality}|{bitrate}|{release}|{size}|{tid}\n"
        results += f" {artist} - {songname} ({quality.upper()} {bitrate}) [{size}]\n"

    if media_type == 'album':
        print('Parsing album...')
        print()
        info = ''
        results = ''
        albumInfo = f"https://search.kuwo.cn/r.s?albumid={ID}&stype=albuminfo&pcjson=1"

        ainfo = requests.get(albumInfo).json()

        album = ainfo['name']
        release = ainfo['pub']
        print(f"[{album}] ({release})")
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
                        
                parsed_output.append(f"{fmt}_{bitrate}|{size}")

            for line in parsed_output[::-1]:
                codec = line

            quality = codec.split('|')[0].split('_')[0]
            bitrate = codec.split('|')[0].split('_')[-1] + 'kbps'
            size = codec.split('|')[1]
              
            info += f"{songname.replace(' [E]','')}|{artist}|{album}|{trackNo}|{quality}|{bitrate}|{release}|{size}|{tid}\n"
            results += f" {trackNo}. {artist} - {songname} ({quality.upper()} {bitrate}) [{size}]\n"
            
    
    print(results)

    continueCheck = input('Would you like to download the above track(s)? (Y/n): ')

    if continueCheck == 'Y' or continueCheck == 'y' or continueCheck == 'Yes' or continueCheck == 'YES' or continueCheck == 'yes':
        dl = True

    elif continueCheck == 'N' or continueCheck == 'n' or continueCheck == 'No' or continueCheck == 'NO' or continueCheck == 'no':
        dl = False

    else:
        dl = False

    if dl == False:
        dlStatus = 'Aborted download!'
    elif dl == True:
        dlStatus = 'Starting download(s)...'

    print()
    print(dlStatus)
    print()

    if dl == True:
        if dump_metadata == True:
            if media_type == 'track':
                tn = tinfo['name'].replace('(Explicit)', '[E]')
                an = tinfo['artist']

                jsonName = f"{tn}"
                jsonName = sanitize_filename(jsonName)
                
                with open(f'metadata/{jsonName}.json', 'w', encoding='utf-8') as json_file:
                    json.dump(tinfo, json_file, ensure_ascii=False, indent=4)
                print(f'Metadata dumped to: metadata/{jsonName}.json')
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
                    print(f'Metadata dumped to: {dest1}/{jsonName}.json')
                print()

            
        localImgfile = 'covers/img.jpg'
        imgdata = requests.get(coverUrl)
        with open(localImgfile, 'wb')as imgfile:
            imgfile.write(imgdata.content)

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
            sourceUrl = requests.get(f"https://mobi.kuwo.cn/mobi.s?f=web&type=&type=convert_url_with_sign&source=kwplayer_ar_4.4.2.7_B_nuoweida_vh.apk&rid={trackId}&format=mp3&br=2000kflac").json()['data']['url'].split('?')[0]
            print(f" {trackName}.{quality}")
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
        if keep_album_art == True:
            os.rename(localImgfile, f'covers/ - {sanitize_filename(album.replace(" (Explicit)","").replace(" [Explicit]",""))}.jpg')
        elif keep_album_art == False:
            os.remove(localImgfile)

