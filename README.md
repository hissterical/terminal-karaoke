# 🎤 Terminal Karaoke 🎵

**Sing your heart out in the comfort of your terminal!**

[![PyPI version](https://img.shields.io/pypi/v/terminal-karaoke.svg)](https://pypi.org/project/terminal-karaoke/)
[![License](https://img.shields.io/pypi/l/terminal-karaoke.svg)](https://github.com/yourusername/terminal-karaoke/blob/main/LICENSE)

![Terminal Karaoke Demo](image.png)

## 🌟 Features

- 🎶 **Auto-downloading**: Just type a song name and we'll fetch the audio & lyrics!
- 🎭 **Synchronized lyrics**: Words light up as they're meant to be sung
- 🐱 **Dancing ASCII cat**: Because why not?
- 🎨 **Color-coded lyrics**: Know what's coming up and what you've sung
- 🕹️ **Simple controls**: Pause, skip, and quit with ease
- 📚 **Library management**: Keep your downloaded songs for later

## 🚀 Installation

```bash
pip install terminal-karaoke
```

> **Windows users**: You might need to install `windows-curses`:
>
> ```bash
> pip install windows-curses
> ```

## 🎮 How to Use

1. **Start the app**:

   ```bash
   terminal-karaoke
   ```

2. **Choose your adventure**:

   - 🔍 **Search & Download**: Find any song on YouTube
   - 📚 **Play from Library**: Access your previously downloaded hits
   - 📁 **Load Local Files**: Use your own MP3s and LRC files

3. **Controls** (during playback):
   - `p` - Pause/Play
   - `←` - Skip back 5 seconds
   - `→` - Skip forward 5 seconds
   - `q` - Quit

Note: The library/ folder is automatically created in your current working directory whenever you download songs. All downloaded MP3 and LRC files are stored there for easy access.

## 🎯 Tips & Tricks

- Search works best with `"Artist - Song Title"` format
- Downloaded songs live in your `library/` folder
- Lyrics come from [LRCLIB](https://lrclib.net/) - the community-powered lyrics database
- No lyrics found? We'll let you know instead of giving you fake ones!

## 🛠️ Requirements

- Python 3.9+
- A sense of rhythm
- Optional: Good singing voice (but we don't judge!)

## 🎤 Example Searches

```
Tame Impala - Let it happen
Travis Scott - My eyes
```

## 🙏 Acknowledgments

- [LRCLIB](https://lrclib.net/) for the amazing lyrics database
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for audio downloading
- Pygame for audio playback

---

**Now get out there and show everyone what you're made of! 🎉**

_Made with ❤️ and lots of terrible karaoke singing_