"""
core/template_engine.py - Custom Naming Template Engine with Smart Token Evaluator.
"""

import re
from typing import Dict, Any, List, Tuple
from core.security import SecurityValidator


class TemplateEngine:
    """
    Renders custom output filename paths using user-defined format templates.
    Supports conditional bracket tokens, integer formatting specs, and sanitization.
    """

    AVAILABLE_TOKENS: List[str] = [
        "Title",
        "Year",
        "Season",
        "Episode",
        "EpisodeRange",
        "Resolution",
        "Codec",
        "VideoCodec",
        "AudioCodec",
        "AudioChannels",
        "AudioLang",
        "Group",
        "ReleaseGroup",
        "Bitrate",
        "FPS",
        "Type",
        "MediaType",
        "CRC32",
        "Version",
    ]

    @staticmethod
    def render(
        template: str,
        context: Dict[str, Any],
        extension: str = "",
        sanitize: bool = True
    ) -> str:
        """
        Renders a template string using context dictionary.
        Example template: "{Title} ({Year}) [{Resolution}] - S{Season}E{Episode}"
        """
        if not template:
            template = "{Title} ({Year}) [{Resolution}] - S{Season}E{Episode}"

        # Standardize aliases in context
        ctx = dict(context)
        if "ReleaseGroup" in ctx and "Group" not in ctx:
            ctx["Group"] = ctx["ReleaseGroup"]
        if "Group" in ctx and "ReleaseGroup" not in ctx:
            ctx["ReleaseGroup"] = ctx["Group"]
        if "VideoCodec" in ctx and "Codec" not in ctx:
            ctx["Codec"] = ctx["VideoCodec"]
        if "Codec" in ctx and "VideoCodec" not in ctx:
            ctx["VideoCodec"] = ctx["Codec"]
        if "MediaType" in ctx and "Type" not in ctx:
            ctx["Type"] = ctx["MediaType"]
        if "AudioLanguages" in ctx and "AudioLang" not in ctx:
            langs = ctx["AudioLanguages"]
            ctx["AudioLang"] = "-".join(langs) if isinstance(langs, list) else str(langs)
        if isinstance(ctx.get("Languages"), list):
            ctx["Languages"] = ", ".join(ctx["Languages"])

        # 1. Evaluate bracketed expressions conditionally: e.g. [{Resolution}] or ({Year})
        # If the inner token is empty, remove the enclosing brackets/parentheses
        result = template

        def clean_empty_containers(text: str) -> str:
            # Matches [ token ] or ( token )
            pattern = re.compile(r"(\[|\(|\{)([^\[\]\(\)\{\}]*?)(\]|\)|\})")
            return text

        # 2. Token substitution with formatting support
        for token_name in TemplateEngine.AVAILABLE_TOKENS:
            token_val = ctx.get(token_name, "")
            if token_val is None:
                token_val = ""

            # Check if token is string or number
            val_str = str(token_val).strip()

            # Replace formatted versions e.g. {Season:02d}
            fmt_pattern = re.compile(rf"\{{{token_name}:([^}}]+)\}}")
            for match in fmt_pattern.finditer(result):
                spec = match.group(1)
                try:
                    num = int(val_str)
                    formatted_val = format(num, spec)
                except Exception:
                    formatted_val = val_str
                result = result.replace(match.group(0), formatted_val)

            # Replace standard {Token}
            result = result.replace(f"{{{token_name}}}", val_str)

        # 3. Clean up empty brackets: e.g. " []", " ()", " --"
        result = re.sub(r"\[\s*\]", "", result)
        result = re.sub(r"\(\s*\)", "", result)
        result = re.sub(r"\{\s*\}", "", result)
        result = re.sub(r"\s*-\s*-\s*", " - ", result)
        result = re.sub(r"^\s*-\s*", "", result)
        result = re.sub(r"\s*-\s*$", "", result)
        result = re.sub(r"\s+", " ", result).strip()

        if sanitize:
            result = SecurityValidator.sanitize_filename(result)

        if extension:
            ext = extension if extension.startswith(".") else f".{extension}"
            # Check if template already included subdirectories
            result = f"{result}{ext}"

        return result

    @staticmethod
    def validate_template(template: str) -> Tuple[bool, str]:
        """Validates that template has matched braces and valid tokens."""
        if not template:
            return False, "Template cannot be empty."

        open_braces = template.count("{")
        close_braces = template.count("}")
        if open_braces != close_braces:
            return False, f"Mismatched braces: {open_braces} open vs {close_braces} close."

        found_tokens = re.findall(r"\{([a-zA-Z0-9_]+)(?::[^}]+)?\}", template)
        for token in found_tokens:
            if token not in TemplateEngine.AVAILABLE_TOKENS:
                return False, f"Unknown token: {{{token}}}. Available tokens: {', '.join(TemplateEngine.AVAILABLE_TOKENS)}"

        return True, "Template syntax is valid."
