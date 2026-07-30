#!/usr/bin/env python3
"""Normalize visible ADT text into natural spoken Swahili for TTS."""

from __future__ import annotations

import re


UNITS = ["sifuri", "moja", "mbili", "tatu", "nne", "tano", "sita", "saba", "nane", "tisa"]
TENS = {
    10: "kumi",
    20: "ishirini",
    30: "thelathini",
    40: "arobaini",
    50: "hamsini",
    60: "sitini",
    70: "sabini",
    80: "themanini",
    90: "tisini",
}
ORDINALS = {
    1: "kwanza",
    2: "pili",
    3: "tatu",
    4: "nne",
    5: "tano",
    6: "sita",
    7: "saba",
    8: "nane",
    9: "tisa",
    10: "kumi",
}
ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9, "x": 10}


def number_to_words(value: int) -> str:
    if value < 0:
        return "hasi " + number_to_words(-value)
    if value < 10:
        return UNITS[value]
    if value < 100:
        tens, remainder = divmod(value, 10)
        base = TENS[tens * 10]
        return base if remainder == 0 else f"{base} na {number_to_words(remainder)}"
    if value < 1000:
        hundreds, remainder = divmod(value, 100)
        base = f"mia {number_to_words(hundreds)}"
        return base if remainder == 0 else f"{base} na {number_to_words(remainder)}"
    if value < 1_000_000:
        thousands, remainder = divmod(value, 1000)
        base = f"elfu {number_to_words(thousands)}"
        return base if remainder == 0 else f"{base} na {number_to_words(remainder)}"
    millions, remainder = divmod(value, 1_000_000)
    base = f"milioni {number_to_words(millions)}"
    return base if remainder == 0 else f"{base} na {number_to_words(remainder)}"


def digits_individually(value: str) -> str:
    return " ".join(UNITS[int(char)] for char in value if char.isdigit())


def normalize_for_speech(text: str) -> str:
    spoken = text
    spoken = re.sub(r"\bDarasa la\s+I\s+na\s+II\b", "Darasa la kwanza na la pili", spoken, flags=re.I)
    spoken = re.sub(r"\bDarasa la\s+II\b", "Darasa la pili", spoken, flags=re.I)
    spoken = re.sub(r"\bDarasa la\s+I\b", "Darasa la kwanza", spoken, flags=re.I)

    def roman_range(match: re.Match[str]) -> str:
        return f"{number_to_words(ROMAN[match.group(1).lower()])} mpaka {number_to_words(ROMAN[match.group(2).lower()])}"

    spoken = re.sub(r"\((i{1,3}|iv|v|vi{0,3}|ix|x)\)\s*[-–]\s*\((i{1,3}|iv|v|vi{0,3}|ix|x)\)", roman_range, spoken, flags=re.I)
    spoken = re.sub(r"\b(i{1,3}|iv|v|vi{0,3}|ix|x)\s*[-–]\s*(i{1,3}|iv|v|vi{0,3}|ix|x)\b", roman_range, spoken, flags=re.I)
    spoken = re.sub(r"\b([a-z])\s*[-–]\s*([a-z])\b", lambda m: f"{m.group(1)} mpaka {m.group(2)}", spoken, flags=re.I)
    spoken = re.sub(r"\((i{1,3}|iv|v|vi{0,3}|ix|x)\)", lambda m: number_to_words(ROMAN[m.group(1).lower()]), spoken, flags=re.I)
    spoken = re.sub(r"\b(?:Toleo|Darasa|Zoezi) la\s+(\d+)\b", lambda m: m.group(0).rsplit(" ", 1)[0] + " " + ORDINALS.get(int(m.group(1)), number_to_words(int(m.group(1)))), spoken, flags=re.I)
    spoken = re.sub(r"\b(?:Shughuli|Sura) ya\s+(\d+)\b", lambda m: m.group(0).rsplit(" ", 1)[0] + " " + ORDINALS.get(int(m.group(1)), number_to_words(int(m.group(1)))), spoken, flags=re.I)

    spoken = re.sub(
        r"\b(\d{1,2})/(\d{1,2})/(\d{4})(?:\s+(\d{1,2}):(\d{2}):(\d{2}))?\b",
        lambda m: "tarehe " + number_to_words(int(m.group(1))) + " mwezi wa " + number_to_words(int(m.group(2))) + " mwaka " + number_to_words(int(m.group(3))) + (" saa " + number_to_words(int(m.group(4))) + " na dakika " + number_to_words(int(m.group(5))) + " na sekunde " + number_to_words(int(m.group(6))) if m.group(4) else ""),
        spoken,
    )

    spoken = re.sub(r"(?i)\bISBN\s+([\d-]+)", lambda m: "ISBN " + digits_individually(m.group(1)), spoken)
    spoken = re.sub(r"(?i)(Simu:\s*)([+\d][+\d\s/]+)", lambda m: m.group(1) + " au ".join(digits_individually(part) for part in m.group(2).split("/") if part.strip()), spoken)
    agreements = {
        r"\b(kiumbehai|mnyama|mmea)\s+1\b": lambda m: f"{m.group(1)} mmoja",
        r"\b(viumbehai|wanyama)\s+2\b": lambda m: f"{m.group(1)} wawili",
        r"\b(vitu|vitabu)\s+2\b": lambda m: f"{m.group(1)} viwili",
        r"\b(makundi)\s+2\b": lambda m: f"{m.group(1)} mawili",
    }
    for pattern, replacement in agreements.items():
        spoken = re.sub(pattern, replacement, spoken, flags=re.I)
    spoken = re.sub(r"\b\d+\b", lambda m: number_to_words(int(m.group(0))), spoken)
    spoken = re.sub(r"([A-Za-zÀ-ÿ])/([A-Za-zÀ-ÿ])", r"\1 au \2", spoken)
    spoken = re.sub(r"\s+", " ", spoken).strip()
    return spoken


if __name__ == "__main__":
    import sys

    print(normalize_for_speech(" ".join(sys.argv[1:])))
