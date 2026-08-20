"""
utils/metadata_parser.py - Robust parsing of video/audio/subtitle metadata.
"""

from typing import Dict, Any, List


def parse_resolution(height: int, width: int = 0) -> str:
    """Classifies resolution into clean standard labels (4K, 1440p, 1080p, 720p, 480p, etc.)."""
    if height >= 2160 or width >= 3800:
        return "4K"
    if height >= 1440 or width >= 2500:
        return "1440p"
    if height >= 1050 or width >= 1900:
        return "1080p"
    if height >= 700 or width >= 1200:
        return "720p"
    if height >= 460 or width >= 700:
        return "480p"
    if height > 0:
        return f"{height}p"
    return "Unknown"


def parse_video_codec(codec_name: str) -> str:
    """Normalizes video codec name to industry standard format."""
    if not codec_name:
        return ""
    codec_map = {
        "h264": "x264",
        "avc": "x264",
        "avc1": "x264",
        "hevc": "x265",
        "h265": "x265",
        "hev1": "x265",
        "av1": "AV1",
        "av01": "AV1",
        "vp9": "VP9",
        "vp8": "VP8",
        "mpeg4": "XviD",
        "msmpeg4v3": "DivX",
        "vc1": "VC-1",
        "theora": "Theora",
        "prores": "ProRes",
    }
    return codec_map.get(codec_name.lower(), codec_name.upper())


def parse_audio_codec(codec_name: str) -> str:
    """Normalizes audio codec name."""
    if not codec_name:
        return ""
    codec_map = {
        "aac": "AAC",
        "flac": "FLAC",
        "ac3": "AC3",
        "eac3": "EAC3",
        "dts": "DTS",
        "dts-hd": "DTS-HD",
        "mp3": "MP3",
        "opus": "Opus",
        "vorbis": "Vorbis",
        "pcm_s16le": "PCM",
        "pcm_s24le": "PCM",
        "truehd": "TrueHD",
        "alac": "ALAC",
    }
    return codec_map.get(codec_name.lower(), codec_name.upper())


def parse_audio_channels(channels: int) -> str:
    """Normalizes audio channels count into standard surround/stereo labels."""
    if channels >= 8:
        return "7.1"
    if channels >= 6:
        return "5.1"
    if channels == 2:
        return "Stereo"
    if channels == 1:
        return "Mono"
    return f"{channels}ch" if channels > 0 else ""


def parse_bitrate(bit_rate: Any) -> str:
    """Converts raw bit rate string/int into Mbps or Kbps."""
    try:
        bps = int(bit_rate)
        if bps <= 0:
            return ""
        if bps >= 1_000_000:
            return f"{bps / 1_000_000:.1f}Mbps"
        return f"{bps / 1_000:.0f}Kbps"
    except Exception:
        return ""


def parse_frame_rate(r_frame_rate: str) -> str:
    """Parses ffprobe frame rate fraction (e.g. '24000/1001') to standard fps string."""
    try:
        if not r_frame_rate or "/" not in r_frame_rate:
            return ""
        num, den = map(int, r_frame_rate.split("/"))
        if den == 0:
            return ""
        fps = num / den
        if 23.9 <= fps <= 24.1:
            return "24fps"
        if 29.9 <= fps <= 30.1:
            return "30fps"
        if 59.9 <= fps <= 60.1:
            return "60fps"
        return f"{fps:.1f}fps"
    except Exception:
        return ""


def get_smart_metadata(file_path: str, metadata_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses raw ffprobe JSON into a clean dictionary of tags.
    Returns:
      Resolution, VideoCodec, AudioCodec, AudioChannels, Bitrate, FPS,
      AudioLanguages, SubtitleLanguages, Duration
    """
    tags: Dict[str, Any] = {
        "Resolution": "",
        "VideoCodec": "",
        "AudioCodec": "",
        "AudioChannels": "",
        "Bitrate": "",
        "FPS": "",
        "AudioLanguages": [],
        "SubtitleLanguages": [],
        "Duration": 0.0,
    }
    if not metadata_json:
        return tags

    streams = metadata_json.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    subtitle_streams = [s for s in streams if s.get("codec_type") == "subtitle"]
    format_info = metadata_json.get("format", {})

    if video_stream:
        height = int(video_stream.get("height", 0) or 0)
        width = int(video_stream.get("width", 0) or 0)
        if height > 0 or width > 0:
            tags["Resolution"] = parse_resolution(height, width)
        codec = video_stream.get("codec_name", "")
        if codec:
            tags["VideoCodec"] = parse_video_codec(codec)
        fps = video_stream.get("r_frame_rate", "")
        if fps:
            tags["FPS"] = parse_frame_rate(fps)

    if audio_streams:
        primary_audio = audio_streams[0]
        codec = primary_audio.get("codec_name", "")
        if codec:
            tags["AudioCodec"] = parse_audio_codec(codec)
        channels = int(primary_audio.get("channels", 0) or 0)
        if channels > 0:
            tags["AudioChannels"] = parse_audio_channels(channels)

        # Collect audio languages
        audio_langs = []
        for a in audio_streams:
            lang = a.get("tags", {}).get("language", "")
            if lang and lang.lower() != "und" and lang not in audio_langs:
                audio_langs.append(lang.capitalize())
        tags["AudioLanguages"] = audio_langs

    # Subtitle languages
    sub_langs = []
    for s in subtitle_streams:
        lang = s.get("tags", {}).get("language", "")
        if lang and lang.lower() != "und" and lang not in sub_langs:
            sub_langs.append(lang.capitalize())
    tags["SubtitleLanguages"] = sub_langs

    bit_rate = format_info.get("bit_rate") or (video_stream.get("bit_rate") if video_stream else None)
    if bit_rate:
        tags["Bitrate"] = parse_bitrate(bit_rate)

    try:
        tags["Duration"] = float(format_info.get("duration", 0.0) or 0.0)
    except Exception:
        tags["Duration"] = 0.0

    return tags


def format_metadata_tags(tags: Dict[str, Any], options: Dict[str, Any]) -> str:
    """Formats the extracted tags into a bracketed string to be appended to filenames."""
    parts = []
    if options.get("include_resolution") and tags.get("Resolution"):
        parts.append(tags["Resolution"])
    if options.get("include_video_codec") and tags.get("VideoCodec"):
        parts.append(tags["VideoCodec"])
    if options.get("include_audio_codec") and tags.get("AudioCodec"):
        parts.append(tags["AudioCodec"])
    if options.get("include_audio_channels") and tags.get("AudioChannels"):
        parts.append(tags["AudioChannels"])
    if options.get("include_bitrate") and tags.get("Bitrate"):
        parts.append(tags["Bitrate"])
    if options.get("include_fps") and tags.get("FPS"):
        parts.append(tags["FPS"])

    return " [" + "] [".join(parts) + "]" if parts else ""
