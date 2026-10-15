#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

DEFAULT_TITLE = "PDF JavaScript Security Test"
DEFAULT_MESSAGE = "Demonstration only: JavaScript executed in a compatible PDF viewer."
MAX_TITLE_LENGTH = 48
MAX_MESSAGE_LENGTH = 350


def _clean_display_text(value: str, *, max_length: int, label: str) -> str:
    """Normalize user text to one line and reject unexpectedly large values."""
    value = " ".join(value.split())
    if not value:
        raise ValueError(f"{label} must not be empty")
    if len(value) > max_length:
        raise ValueError(f"{label} must be at most {max_length} characters")
    return value


def _pdf_literal(value: str) -> bytes:
    """Encode an ASCII PDF literal string, escaping PDF string delimiters."""
    safe = value.encode("ascii", "replace").decode("ascii")
    safe = safe.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    safe = safe.replace("\r", " ").replace("\n", " ")
    return safe.encode("ascii")


def _wrap_words(text: str, width: int = 72) -> list[str]:
    """Wrap plain text without relying on PDF text-layout features."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]


def _stream(data: bytes, dictionary: bytes = b"") -> bytes:
    prefix = (dictionary + b" ") if dictionary else b""
    return b"<< " + prefix + b"/Length " + str(len(data)).encode("ascii") + b" >>\nstream\n" + data + b"\nendstream"


def build_pdf(title: str = DEFAULT_TITLE, message: str = DEFAULT_MESSAGE, *, mode: str = "alert") -> bytes:
    title = _clean_display_text(title, max_length=MAX_TITLE_LENGTH, label="title")
    message = _clean_display_text(message, max_length=MAX_MESSAGE_LENGTH, label="message")
    if mode not in {"alert", "static"}:
        raise ValueError("mode must be 'alert' or 'static'")

    # ASCII replacement keeps the content stream simple and predictable across viewers.
    title_pdf = _pdf_literal(title)
    message_lines = _wrap_words(message, 72)

    commands = [
        b"q",
        b"0.12 0.25 0.40 rg 0 676 612 116 re f",
        b"1 1 1 rg",
        b"BT /F2 20 Tf 48 728 Td (" + title_pdf + b") Tj ET",
        b"0.08 0.08 0.08 rg",
        b"BT /F2 13 Tf 48 625 Td (Purpose) Tj ET",
        b"BT /F1 11 Tf 48 600 Td (" + _pdf_literal("Observe PDF viewer handling of a benign JavaScript action.") + b") Tj ET",
    ]
    y = 570
    for line in message_lines[:7]:
        commands.append(b"BT /F1 11 Tf 48 " + str(y).encode("ascii") + b" Td (" + _pdf_literal(line) + b") Tj ET")
        y -= 18

    footer = "Safe test artifact: no input fields, network requests, or data collection."
    commands.extend([
        b"0.45 0.45 0.45 rg",
        b"BT /F1 9 Tf 48 72 Td (" + _pdf_literal(footer) + b") Tj ET",
        b"Q",
    ])
    content_stream = b"\n".join(commands) + b"\n"

    objects: list[bytes] = []
    catalog = b"<< /Type /Catalog /Pages 2 0 R"
    if mode == "alert":
        # json.dumps safely quotes user-supplied text as a JavaScript string literal.
        js_source = "app.alert({cMsg: " + json.dumps(message, ensure_ascii=True) + ", cTitle: " + json.dumps(title, ensure_ascii=True) + ", nIcon: 3});"
        js_pdf = _pdf_literal(js_source)
        catalog += b" /OpenAction << /S /JavaScript /JS (" + js_pdf + b") >>"
    catalog += b" >>"

    objects.append(catalog)  # 1: catalog
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")  # 2: pages
    objects.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> "
        b"/Contents 6 0 R >>"
    )  # 3: page
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")  # 4
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")  # 5
    objects.append(_stream(content_stream))  # 6: content

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: list[int] = []
