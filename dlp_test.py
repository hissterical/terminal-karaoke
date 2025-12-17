import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from terminal_karaoke.downloader import SongDownloader

def test_download():
    downloader = SongDownloader()
    
    # Test search
    query = "Rick Astley - Never Gonna Give You Up"
    print(f"Searching for: {query}")
    
    url, error = downloader.search_youtube(query)
    if error:
        print(f"Search error: {error}")
        return
    
    print(f"Found URL: {url}")
    
    # Test download
    print("\nDownloading...")
    mp3_path, error = downloader.download_audio(url, query)
    
    if error:
        print(f"\nDownload error: {error}")
        return
    
    if mp3_path:
        print(f"\nSuccess! Downloaded to: {mp3_path}")
        print(f"File exists: {os.path.exists(mp3_path)}")
    else:
        print("\nDownload failed - no path returned")

if __name__ == "__main__":
    test_download()
