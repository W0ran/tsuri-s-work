import zipfile
import io
import hashlib
import os

OUT = "./testfiles"
os.makedirs(OUT, exist_ok=True)

minimal_pdf_v2 = b"""%PDF-1.7
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 150]>>endobj
4 0 obj<</Title(retest-doc-v2)/Producer(qa-polyglot-generator)>>endobj
xref
0 5
0000000000 65535 f 
trailer<</Size 5/Root 1 0 R/Info 4 0 R>>
startxref
0
%%EOF
"""

zip_part_v2 = io.BytesIO()
with zipfile.ZipFile(zip_part_v2, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("evidence_v2.txt", "Second polyglot payload - independent content, retest of TC-9 fix")
    z.writestr("readme_v2.txt", "This is a distinct polyglot test file, different SHA-256 from the original tc9 sample")

out_path = f"{OUT}/tc9_polyglot_v2_pdf_zip.pdf"
with open(out_path, "wb") as f:
    f.write(minimal_pdf_v2)
    f.write(zip_part_v2.getvalue())

with open(out_path, "rb") as f:
    data = f.read()

sha256 = hashlib.sha256(data).hexdigest()

print(f"Файл создан: {out_path}")
print(f"Размер: {len(data)} байт")
print(f"SHA-256: {sha256}")
print(f"Начинается с %PDF: {data[:4] == b'%PDF'}")
print(f"Содержит ZIP-сигнатуру (PK): {b'PK' + bytes([0x03, 0x04]) in data}")