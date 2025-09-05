class LyricsParser:
    def parse(self, lrc_path):
        lyrics = []
        try:
            with open(lrc_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if line[0] == '[':
                        end_bracket = line.find(']')
                        if end_bracket > 0:
                            timestamp_str = line[1:end_bracket]
                            text = line[end_bracket+1:].strip()
                            try:
                                parts = timestamp_str.split(':')
                                if len(parts) == 2:
                                    minutes = int(parts[0])
                                    seconds_parts = parts[1].split('.')
                                    seconds = int(seconds_parts[0])
                                    hundredths = 0
                                    if len(seconds_parts) > 1:
                                        hundredths = int(seconds_parts[1].ljust(2, '0')[:2])
                                    total_seconds = minutes * 60 + seconds + hundredths / 100.0
                                    lyrics.append((total_seconds, text))
                            except:
                                continue
        except Exception as e:
            print(f"Error parsing LRC: {str(e)}")
        lyrics.sort(key=lambda x: x[0])
        return lyrics