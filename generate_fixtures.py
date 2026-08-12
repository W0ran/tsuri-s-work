"""Генерация тестовых файлов для тестов загрузки документов (fixtures/).

Вызывается автоматически из tests/conftest.py перед прогоном тестов, чтобы
fixtures/sample_documents и fixtures/invalid_documents всегда были на месте,
даже на чистом клоне репозитория (эти файлы не хранятся в git).
"""

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

DOC_MAGIC = bytes.fromhex("D0CF11E0A1B11AE1") + b"\x00" * 504

EXE_STUB = b"MZ" + b"\x00" * 62 + b"This program cannot be run in DOS mode.\r\r\n$" + b"\x00" * 200


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
    _write(SAMPLE_DIR / "sample.doc", DOC_MAGIC)
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
