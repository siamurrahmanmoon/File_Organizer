"""
core/parser.py - Advanced AI & Regex Pattern Recognition for Media Files.
"""

import re
import difflib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Known release groups or regex match for leading bracketed tag
KNOWN_GROUPS = {
    "subsplease",
    "erai-raws",
    "horriblesubs",
    "judas",
    "asw",
    "ember",
    "yameii",
    "commie",
    "coalgirls",
    "golumpa",
    "doki",
    "anime-time",
    "kaylith",
    "cleo",
    "davinci",
    "kametsu",
    "scy",
    "smokin",
    "nep",
    "tactical",
    "neo",
    "gjm",
    "lostyears",
    "chibiki",
    "beetle",
    "vcb-studio",
    "chyu",
    "reinforce",
    "beatrice-raws",
    "moozzi2",
    "showtime",
}

YEAR_REGEX = re.compile(r"\b(19|20)\d{2}\b")
CRC32_REGEX = re.compile(r"\[[0-9A-Fa-f]{8}\]")
RESOLUTION_REGEX = re.compile(
    r"\b(2160p|1440p|1080p|720p|480p|360p|4K|2K|FHD|HD)\b", re.IGNORECASE
)
CODEC_REGEX = re.compile(
    r"\b(x264|x265|h264|h265|hevc|av1|vp9|xvid|divx|10bit|8bit|hi10p|hdr|sdr)\b",
    re.IGNORECASE,
)
AUDIO_REGEX = re.compile(
    r"\b(AAC|FLAC|AC3|EAC3|DTS|DTS-HD|TrueHD|Opus|MP3|Dual[- ]Audio|Multi[- ]Audio)\b",
    re.IGNORECASE,
)
LANGUAGE_REGEX = re.compile(
    r"\b(Hindi|English|Japanese|Jap|Eng|Hin|Bengali|Bangli|Bangla|Tamil|Telugu|Korean|Chinese|Dual|Multi)\b",
    re.IGNORECASE,
)
WEB_DOMAINS_REGEX = re.compile(
    r"\b[a-zA-Z0-9_\-]+\.(?:to|com|org|net|xyz|is|in|me|tv|cc|cx|club|vip|site|online)\b",
    re.IGNORECASE,
)
JUNK_TAGS_REGEX = re.compile(
    r"\b(Series|Complete|Full|Batch|Season\s*\d+|Episode\s*\d+|HD|FHD|UHD|4K|WEB-DL|WEBRip|BluRay|BRRip|BDRip|DVDRip|HDRip|REPACK|PROPER|REMUX)\b",
    re.IGNORECASE,
)


class SmartMediaParser:
    """Parses complex video filenames into structured metadata dictionary."""

    @staticmethod
    def parse_filename(filename: str, parent_folder_name: str = "") -> Dict[str, Any]:
        """
        Extracts Title, Year, Season, Episode, Release Group, Media Type,
        Resolution, Codec, Audio, Languages, Version, and CRC32 from filename.
        """
        stem = Path(filename).stem
        info: Dict[str, Any] = {
            "OriginalName": filename,
            "Title": stem,
            "Year": "",
            "Season": "01",
            "Episode": "",
            "EpisodeRange": "",
            "ReleaseGroup": "",
            "MediaType": "Episode",  # Episode, Movie, OVA, ONA, Special, NCED, NCOP, Preview
            "Resolution": "",
            "VideoCodec": "",
            "AudioCodec": "",
            "Languages": [],
            "Version": "",
            "CRC32": "",
        }

        # 1. Detect CRC32 checksum e.g. [8A4F12C3]
        crc_match = CRC32_REGEX.search(stem)
        if crc_match:
            info["CRC32"] = crc_match.group(0).strip("[]")

        # 2. Detect Release Group e.g. [SubsPlease] or [Erai-raws]
        group_match = re.match(r"^\[([a-zA-Z0-9_\-\.\s]+)\]", stem)
        if group_match:
            candidate = group_match.group(1).strip()
            # If not a resolution or codec
            if not RESOLUTION_REGEX.fullmatch(candidate) and not CRC32_REGEX.fullmatch(
                f"[{candidate}]"
            ):
                info["ReleaseGroup"] = candidate

        # 3. Detect Media Type (Movie, OVA, Special, etc.)
        if re.search(r"\b(Movie|Gekijouban)\b", stem, re.IGNORECASE):
            info["MediaType"] = "Movie"
        elif re.search(r"\b(OVA|OAV)\b", stem, re.IGNORECASE):
            info["MediaType"] = "OVA"
        elif re.search(r"\bONA\b", stem, re.IGNORECASE):
            info["MediaType"] = "ONA"
        elif re.search(r"\b(Special|SP)\b", stem, re.IGNORECASE):
            info["MediaType"] = "Special"
        elif re.search(r"\b(NCOP|NCED|OP|ED|Opening|Ending)\b", stem, re.IGNORECASE):
            info["MediaType"] = "ThemeSong"
        elif re.search(r"\b(Preview|PV|Trailer)\b", stem, re.IGNORECASE):
            info["MediaType"] = "Preview"

        # 4. Detect Year in filename or parent folder
        year_match = YEAR_REGEX.search(stem)
        if year_match:
            info["Year"] = year_match.group(0)
        elif parent_folder_name:
            p_year = YEAR_REGEX.search(parent_folder_name)
            if p_year:
                info["Year"] = p_year.group(0)

        # 5. Detect Languages
        found_langs = []
        language_sources = [stem]
        if parent_folder_name:
            language_sources.append(parent_folder_name)
        language_aliases = {
            "eng": "English",
            "english": "English",
            "hin": "Hindi",
            "hindi": "Hindi",
            "jap": "Japanese",
            "japanese": "Japanese",
            "bangla": "Bangli",
            "bangli": "Bangli",
            "bengali": "Bangli",
        }
        for source in language_sources:
            for lang_m in LANGUAGE_REGEX.finditer(source):
                matched = language_aliases.get(
                    lang_m.group(0).lower(), lang_m.group(0).capitalize()
                )
                if matched not in found_langs:
                    found_langs.append(matched)
        info["Languages"] = found_langs

        # 6. Detect Version e.g. v2, v3
        v_match = re.search(r"\b[vV](\d)\b", stem)
        if v_match:
            info["Version"] = f"v{v_match.group(1)}"

        # 7. Detect Resolution in filename string
        res_m = RESOLUTION_REGEX.search(stem)
        if res_m:
            info["Resolution"] = res_m.group(0).upper()

        # 8. Detect Codec in filename string
        codec_m = CODEC_REGEX.search(stem)
        if codec_m:
            info["VideoCodec"] = codec_m.group(0).upper()

        # 9. Extract Season and Episode numbers
        season, ep, ep_range = SmartMediaParser._extract_season_episode(stem)
        if season:
            info["Season"] = season
        if ep:
            info["Episode"] = ep
        if ep_range:
            info["EpisodeRange"] = ep_range

        # 10. Extract Clean Title
        info["Title"] = SmartMediaParser.clean_title(stem, info)

        return info

    @staticmethod
    def _extract_season_episode(text: str) -> Tuple[str, str, str]:
        """Detects Season, Episode, or Multi-Episode range."""
        season = "01"
        episode = ""
        episode_range = ""

        # Pattern 1: S01E01-E04 or S01E01-04 or S01E01 - E02
        s_range_m = re.search(
            r"S(\d{1,2})\s*E(\d{1,3})\s*-\s*(?:E)?(\d{1,3})(?![pPkK\d])",
            text,
            re.IGNORECASE,
        )
        if s_range_m:
            ep_start = int(s_range_m.group(2))
            ep_end = int(s_range_m.group(3))
            if 0 < ep_end - ep_start <= 30:
                season = f"{int(s_range_m.group(1)):02d}"
                episode = f"{ep_start:02d}"
                episode_range = f"S{season}E{ep_start:02d}-E{ep_end:02d}"
                return season, episode, episode_range

        # Pattern 2: Standard S01E05 / S1E5 / S02EP04 / S1E1
        s_ep_m = re.search(r"S(\d{1,2})\s*(?:E|EP)(\d{1,4})", text, re.IGNORECASE)
        if s_ep_m:
            season = f"{int(s_ep_m.group(1)):02d}"
            episode = f"{int(s_ep_m.group(2)):02d}"
            return season, episode, ""

        # Pattern 3: Season 2 Episode 05 / Season 2 - 05
        season_m = re.search(r"\bSeason\s*(\d{1,2})\b", text, re.IGNORECASE)
        if season_m:
            season = f"{int(season_m.group(1)):02d}"

        # Pattern 4: Episode 05 / Ep 05 / #05 / E05
        ep_m = re.search(r"\b(?:Episode|Ep|E|#)\s*(\d{1,4})\b", text, re.IGNORECASE)
        if ep_m:
            episode = f"{int(ep_m.group(1)):02d}"
            return season, episode, ""

        # Pattern 5: Multi-episode without S prefix: 01-04 or 01-02
        range_m = re.search(r"\b(\d{1,3})\s*-\s*(\d{1,3})\b", text)
        if range_m:
            start_num = int(range_m.group(1))
            end_num = int(range_m.group(2))
            if start_num < end_num and end_num - start_num <= 30:
                episode = f"{start_num:02d}"
                episode_range = f"E{start_num:02d}-E{end_num:02d}"
                return season, episode, episode_range

        # Pattern 6: Standalone episode number at the end or separated by dashes: "Anime Title - 05"
        dash_ep_m = re.search(r"-\s*(\d{1,4})(?:\s*\[|\s*\(|\s*$)", text)
        if dash_ep_m:
            episode = f"{int(dash_ep_m.group(1)):02d}"
            return season, episode, ""

        # Pattern 7: Any isolated 2-4 digit number that isn't a year
        for num_m in re.finditer(r"\b(\d{1,4})\b", text):
            val = int(num_m.group(1))
            if not (1900 <= val <= 2099):
                episode = f"{val:02d}"
                break

        return season, episode, ""

    @staticmethod
    def clean_title(
        raw_title: str, parsed_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """Strips tags, release group brackets, resolutions, and noise from anime title."""
        title = raw_title

        # Remove release group if present at start
        if parsed_info and parsed_info.get("ReleaseGroup"):
            group = parsed_info["ReleaseGroup"]
            title = re.sub(
                rf"^\[{re.escape(group)}\]\s*", "", title, flags=re.IGNORECASE
            )

        # Remove bracketed tags like [1080p] [x265] [Dual-Audio] [8A7B6C]
        title = CRC32_REGEX.sub("", title)
        title = re.sub(r"\[.*?\]", " ", title)
        title = re.sub(r"\(.*?\)", " ", title)

        # Remove years
        title = YEAR_REGEX.sub("", title)

        # Remove resolution and codecs
        title = RESOLUTION_REGEX.sub("", title)
        title = CODEC_REGEX.sub("", title)
        title = AUDIO_REGEX.sub("", title)
        title = LANGUAGE_REGEX.sub("", title)
        title = JUNK_TAGS_REGEX.sub("", title)
        title = WEB_DOMAINS_REGEX.sub("", title)

        # Remove S01E01 patterns from title
        title = re.sub(
            r"S\d{1,2}\s*(?:E|EP)?\d{1,4}(?:\s*-\s*(?:E)?\d{1,4})?",
            "",
            title,
            flags=re.IGNORECASE,
        )
        title = re.sub(
            r"\b(?:Episode|Ep|E)\s*\d{1,4}\b", "", title, flags=re.IGNORECASE
        )
        title = re.sub(r"\bSeason[\s._-]*\d{1,2}\b", "", title, flags=re.IGNORECASE)
        title = re.sub(r"-\s*\d{1,4}\s*$", "", title)

        # Clean noise characters
        title = title.replace("_", " ").replace(".", " ")
        title = re.sub(r"[\-\–\—\:]+", " ", title)
        title = re.sub(r"\s+", " ", title).strip()

        return title or "Untitled"

    @staticmethod
    def calculate_title_similarity(title1: str, title2: str) -> float:
        """Computes Levenshtein/Gestalt sequence similarity score between two titles (0.0 to 1.0)."""
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()
        if t1 == t2:
            return 1.0
        matcher = difflib.SequenceMatcher(None, t1, t2)
        return matcher.ratio()
