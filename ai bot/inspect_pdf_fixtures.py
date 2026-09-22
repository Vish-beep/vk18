import os
import re
from PyPDF2 import PdfReader
from utils.pdf_loader import read_pdf, read_pdf_metadata
from utils.bibliography import extract_bibliographic_facts

filenames = [
    "NaturalLanguageProcessingRecipes_UnlockingTextDatawithMachineLearningandDeepLearningusingPython(PDFDrive).pdf",
    "NaturalLanguageProcessingNLPforDocument.pdf",
    "introduction-to-natural-language-processing.pdf",
]
for filename in filenames:
    path = os.path.join("uploads", filename)
    reader = PdfReader(path)
    text = read_pdf(path)
    metadata = read_pdf_metadata(path)
    facts = extract_bibliographic_facts(text, metadata)
    print("FILE:", filename)
    print("PAGES:", len(reader.pages), "CHARS:", len(text))
    print("METADATA:", metadata)
    print("FACTS:", facts)
    matches = [line.strip() for line in text.splitlines() if re.search(r"author|written by|submitted by|publisher|published by|copyright|isbn", line, re.I)]
    print("LABELS:", matches[:20])
    print("---")
