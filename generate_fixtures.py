"""Генерация тестовых файлов для тестов загрузки документов (fixtures/).

Вызывается автоматически из tests/conftest.py перед прогоном тестов, чтобы
fixtures/sample_documents и fixtures/invalid_documents всегда были на месте,
даже на чистом клоне репозитория (эти файлы не хранятся в git).
"""

import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SAMPLE_DIR = ROOT / "fixtures" / "sample_documents"
INVALID_DIR = ROOT / "fixtures" / "invalid_documents"

MINIMAL_PDF = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 20 100 Td (QA sample PDF) Tj ET
endstream
endobj
xref
0 6
0000000000 65535 f
trailer
<< /Size 6 /Root 1 0 R >>
startxref
0
%%EOF
"""

# PNG-заглушка (валидная сигнатура + IHDR/IDAT/IEND, 1x1 пиксель) на случай,
# если Pillow не установлен
MINIMAL_PNG_FALLBACK = bytes.fromhex(
    "89504e470d0a1a0a"          # сигнатура PNG
    "0000000d49484452"          # длина+тип чанка IHDR
    "0000000100000001"          # width=1, height=1
    "0806000000"                # bitdepth=8, colortype=6 (RGBA), compression/filter/interlace=0
    "1f15c489"                  # CRC32(IHDR)
    "0000000a49444154"          # длина+тип чанка IDAT
    "789c6300010000050001"      # сжатые (zlib) данные пикселя
    "0d0a2db4"                  # CRC32(IDAT)
    "0000000049454e44"          # длина+тип чанка IEND
    "ae426082"                  # CRC32(IEND)
)

EXE_STUB = b"MZ" + b"\x00" * 62 + b"This program cannot be run in DOS mode.\r\r\n$" + b"\x00" * 200

_SECTOR = 512
_ENDOFCHAIN = 0xFFFFFFFE
_FREESECT = 0xFFFFFFFF
_FATSECT = 0xFFFFFFFD


def _ole_name_field(name: str) -> bytes:
    encoded = name.encode("utf-16-le") + b"\x00\x00"
    return encoded + b"\x00" * (64 - len(encoded))


def _ole_dir_entry(
    name: str,
    object_type: int,
    color: int,
    child: int,
    start_sector: int,
    stream_size: int,
) -> bytes:
    name_len = (len(name) + 1) * 2 if name else 0
    return (
        _ole_name_field(name)
        + struct.pack("<H", name_len)
        + bytes([object_type, color])
        + struct.pack("<I", _FREESECT)  # left sibling
        + struct.pack("<I", _FREESECT)  # right sibling
        + struct.pack("<I", child)
        + b"\x00" * 16  # CLSID
        + struct.pack("<I", 0)  # state bits
        + b"\x00" * 8  # creation time
        + b"\x00" * 8  # modified time
        + struct.pack("<I", start_sector)
        + struct.pack("<Q", stream_size)
    )


def _build_minimal_doc() -> bytes:
    """Минимальный, но структурно валидный OLE2 Compound File Binary (.doc)
    с одним потоком "WordDocument". Поток начинается с классической FIB-магии
    Word 97-2003 (0xA5EC, little-endian) и дополнен нулями до 4096 байт —
    это ровно порог mini-stream, так что поток целиком лежит в обычных
    секторах и не требует реализации MiniFAT."""
    stream_data = bytes([0xEC, 0xA5]) + b"\x00" * (4096 - 2)
    n_stream_sectors = len(stream_data) // _SECTOR  # 8
    dir_sector = 1
    stream_start = 2

    header = (
        b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"  # сигнатура CFB
        + b"\x00" * 16  # CLSID
        + struct.pack("<H", 0x003E)  # minor version
        + struct.pack("<H", 0x0003)  # major version (3 -> сектор 512Б)
        + struct.pack("<H", 0xFFFE)  # byte order mark
        + struct.pack("<H", 9)  # sector shift (2^9 = 512)
        + struct.pack("<H", 6)  # mini sector shift (2^6 = 64)
        + b"\x00" * 6  # reserved
        + struct.pack("<I", 0)  # число directory-секторов (0 для v3)
        + struct.pack("<I", 1)  # число FAT-секторов
        + struct.pack("<I", dir_sector)  # первый directory-сектор
        + struct.pack("<I", 0)  # transaction signature
        + struct.pack("<I", 0x1000)  # mini stream cutoff (4096)
        + struct.pack("<I", _ENDOFCHAIN)  # первый mini FAT сектор (нет)
        + struct.pack("<I", 0)  # число mini FAT секторов
        + struct.pack("<I", _ENDOFCHAIN)  # первый DIFAT сектор (нет)
        + struct.pack("<I", 0)  # число DIFAT секторов
        + struct.pack("<I", 0)  # DIFAT[0] = сектор 0 (FAT)
        + struct.pack("<I", _FREESECT) * 108  # остальные DIFAT — не используются
    )
    assert len(header) == 512

    fat_entries = [_FATSECT, _ENDOFCHAIN]
    for i in range(n_stream_sectors):
        sector = stream_start + i
        fat_entries.append(_ENDOFCHAIN if i == n_stream_sectors - 1 else sector + 1)
    fat_entries += [_FREESECT] * (_SECTOR // 4 - len(fat_entries))
    fat_sector = b"".join(struct.pack("<I", v) for v in fat_entries)
    assert len(fat_sector) == 512

    root_entry = _ole_dir_entry("Root Entry", 0x05, 0x01, child=1, start_sector=_ENDOFCHAIN, stream_size=0)
    word_entry = _ole_dir_entry(
        "WordDocument", 0x02, 0x01, child=_FREESECT, start_sector=stream_start, stream_size=len(stream_data)
    )
    empty_entry = _ole_dir_entry("", 0x00, 0x00, child=_FREESECT, start_sector=0, stream_size=0)
    dir_sector_bytes = root_entry + word_entry + empty_entry + empty_entry
    assert len(dir_sector_bytes) == 512

    return header + fat_sector + dir_sector_bytes + stream_data


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(data)


def _write_image(png_path: Path, jpg_path: Path) -> None:
    if png_path.exists() and jpg_path.exists():
        return
    try:
        from PIL import Image

        img = Image.new("RGB", (10, 10), color=(200, 30, 30))
        if not png_path.exists():
            png_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(png_path, format="PNG")
        if not jpg_path.exists():
            jpg_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(jpg_path, format="JPEG")
    except ImportError:
        # Pillow не установлен (его нет в requirements.txt — он нужен только для
        # генерации тестовых картинок) — используем заглушку с корректной сигнатурой PNG
        _write(png_path, MINIMAL_PNG_FALLBACK)
        _write(jpg_path, MINIMAL_PNG_FALLBACK)


def _write_docx(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    content_types = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
    rels = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
    document = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body><w:p><w:r><w:t>QA sample DOCX</w:t></w:r></w:p></w:body>
</w:document>"""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document)


def _write_zip(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("readme.txt", "just a zip for negative upload testing")


def ensure_fixture_files() -> None:
    """Создаёт недостающие тестовые файлы в fixtures/. Идемпотентно — существующие не трогает."""
    _write(SAMPLE_DIR / "sample.pdf", MINIMAL_PDF)
    _write_image(SAMPLE_DIR / "sample.png", SAMPLE_DIR / "sample.jpg")
    _write(SAMPLE_DIR / "sample.doc", _build_minimal_doc())
    _write_docx(SAMPLE_DIR / "sample.docx")

    for name in [
        "документ_с_кириллицей.pdf",
        "file with spaces.pdf",
        "файл-№1 (копия).pdf",
    ]:
        _write(SAMPLE_DIR / name, MINIMAL_PDF)

    _write(INVALID_DIR / "sample.exe", EXE_STUB)
    _write_zip(INVALID_DIR / "sample.zip")
    _write(INVALID_DIR / "sample.txt", b"This is a plain text file used for negative upload testing.\n")
    _write(INVALID_DIR / "fake_executable.pdf", EXE_STUB)


if __name__ == "__main__":
    ensure_fixture_files()
