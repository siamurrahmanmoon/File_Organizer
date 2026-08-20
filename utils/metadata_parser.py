# utils/metadata_parser.py
from typing import Dict, Any


def parse_resolution(height: int) -> str:
    if height >= 2160:
        return "4K"
    if height >= 1440:
        return "1440p"
    if height >= 1080:
        return "1080p"
    if height >= 720:
        return "720p"
    if height >= 480:
        return "480p"
    return f"{height}p"


def parse_video_codec(codec_name: str) -> str:
    codec_map = {
        "h264": "x264",
        "avc": "x264",
        "hevc": "x265",
        "h265": "x265",
        "av1": "AV1",
        "vp9": "VP9",
        "mpeg4": "XviD",
    }
    return codec_map.get(codec_name.lower(), codec_name.upper())


def parse_audio_codec(codec_name: str) -> str:
    codec_map = {
        "aac": "AAC",
        "flac": "FLAC",
        "ac3": "AC3",
        "eac3": "EAC3",
        "dts": "DTS",
        "mp3": "MP3",
        "opus": "Opus",
        "vorbis": "Vorbis",
    }
    return codec_map.get(codec_name.lower(), codec_name.upper())


def parse_audio_channels(channels: int) -> str:
    if channels >= 8:
        return "7.1"
    if channels >= 6:
        return "5.1"
    if channels == 2:
        return "Stereo"
    if channels == 1:
        return "Mono"
    return f"{channels}ch"


def parse_bitrate(bit_rate: str) -> str:
    try:
        bps = int(bit_rate)
        return (
            f"{bps / 1_000_000:.1f} Mbps"
            if bps > 1_000_000
            else f"{bps / 1_000:.0f} Kbps"
        )
    except:
        return ""


def parse_frame_rate(r_frame_rate: str) -> str:
    try:
        num, den = map(int, r_frame_rate.split("/"))
        fps = num / den
        if 23.9 <= fps <= 24.1:
            return "24fps"
        if 29.9 <= fps <= 30.1:
            return "30fps"
        if 59.9 <= fps <= 60.1:
            return "60fps"
        return f"{fps:.1f}fps"
    except:
        return ""


def get_smart_metadata(file_path: str, metadata_json: Dict[str, Any]) -> Dict[str, str]:
    """Parses raw ffprobe JSON into a clean dictionary of tags."""
    tags = {}
    if not metadata_json:
        return tags

    video_stream = next(
        (s for s in metadata_json.get("streams", []) if s.get("codec_type") == "video"),
        None,
    )
    audio_stream = next(
        (s for s in metadata_json.get("streams", []) if s.get("codec_type") == "audio"),
        None,
    )
    format_info = metadata_json.get("format", {})

    if video_stream:
        height = int(video_stream.get("height", 0))
        if height > 0:
            tags["Resolution"] = parse_resolution(height)
        codec = video_stream.get("codec_name", "")
        if codec:
            tags["VideoCodec"] = parse_video_codec(codec)
        fps = video_stream.get("r_frame_rate", "")
        if fps:
            tags["FPS"] = parse_frame_rate(fps)

    if audio_stream:
        codec = audio_stream.get("codec_name", "")
        if codec:
            tags["AudioCodec"] = parse_audio_codec(codec)
        channels = int(audio_stream.get("channels", 0))
        if channels > 0:
            tags["AudioChannels"] = parse_audio_channels(channels)

    bit_rate = format_info.get("bit_rate", "")
    if bit_rate:
        tags["Bitrate"] = parse_bitrate(bit_rate)

    return tags


def format_metadata_tags(tags: Dict[str, str], options: Dict[str, bool]) -> str:
    """Formats the extracted tags into a string to be appended to the filename."""
    parts = []
    if options.get("include_resolution") and "Resolution" in tags:
        parts.append(tags["Resolution"])
    if options.get("include_video_codec") and "VideoCodec" in tags:
        parts.append(tags["VideoCodec"])
    if options.get("include_audio_codec") and "AudioCodec" in tags:
        parts.append(tags["AudioCodec"])
    if options.get("include_audio_channels") and "AudioChannels" in tags:
        parts.append(tags["AudioChannels"])
    if options.get("include_bitrate") and "Bitrate" in tags:
        parts.append(tags["Bitrate"])
    if options.get("include_fps") and "FPS" in tags:
        parts.append(tags["FPS"])

    return " [" + "] [".join(parts) + "]" if parts else ""
