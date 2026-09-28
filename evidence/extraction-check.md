# Extraction-quality check (Word documents)

The assignment asks to check extraction quality for non-plain-text sources. The originals are Markdown (read as they are) and seven `.docx` files, read by `src/wiki/extract.py` with the standard library (offline).

| Document | paragraphs extracted | words extracted | words counted in the raw XML (see below) | tables | images |
|---|---|---|---|---|---|
| AuraTech Case.docx | 41 | 1326 | 1327 | 1 | 0 |
| Durable Advantage.docx | 7 | 297 | 307 | 0 | 0 |
| Group Pricing.docx | 8 | 257 | 260 | 0 | 0 |
| Menu Pricing.docx | 7 | 249 | 252 | 0 | 0 |
| Relevant Cost.docx | 11 | 283 | 290 | 0 | 0 |
| Sunk Cost Reasoning.docx | 4 | 172 | 172 | 0 | 0 |
| Supply and Demand Shocks.docx | 8 | 230 | 234 | 0 | 0 |

## Results
- **No text is lost.** Comparing every non-space character of the extracted text with the text inside each document's XML gives an **identical result for all seven files** (for example AuraTech Case: 6,167 characters on both sides). The word counts in the table differ by up to 10 words only because Word stores some words split across several formatting runs, which the raw count treats as separate words.
- **Special characters survive** (curly quotes, en/em dashes, the minus sign in -$36,182): visible in the retrieved passages and in `evidence/ask-tests`.
- **No images, no footnotes or endnotes with text** in any document (AuraTech's footnote and endnote parts are empty), so nothing is silently dropped.
- **Limitation: table structure.** `AuraTech Case.docx` contains one table (regression estimates). Every cell is extracted, but each cell becomes its own line in reading order, so row/column relationships are implied by position, not shown.
  Example of the extracted text: `Intercept (b0)` / `-$36,182` / `[-$42,332, -$30,031]` / `$0`. A retrieval passage that cuts through this table can therefore lose which number belongs to which row. Improvement: render tables as Markdown rows.
- Headings: Word `Heading`/`Title` styles become Markdown headings; none of the documents uses them (they are plain question/answer text), so each becomes one section named after the file.
- Safety limits (unit-tested): files over 5 MB, documents expanding past 20 MB of XML (zip bomb), XML DTD/entity declarations, invalid zip files and missing `word/document.xml` are refused with a clear message.

No PDF support is implemented, so no PDF extraction check applies.
