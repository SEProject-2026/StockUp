# 🧾 Receipt Scanner Tests

This directory contains the automated test suite and the testing fixtures for the StockUp Receipt Scanner module. 
The tests evaluate the robustness and accuracy of the parsing algorithms (the logic that extracts the actual products, barcodes, and quantities from OCR text outputs).

## 📂 Directory Structure

*   📷 `results/receipts/`: Stores the original receipt media (images or PDFs). This folder is used to **categorize test cases** for the final report. You should move the test media files into one of these subdirectories:
    *   📁 `digital/` - For digital PDF documents.
    *   📁 `physical/` - For regular physical receipts in good photo conditions.
    *   📁 `complicated/` - For physical receipts in bad, crumpled, or fading conditions.
    *   *Note: Files left in the root directory will be categorized as "General".*
*   📄 `results/raw/`: Contains the flat raw text strings extracted from the receipts (via Google Vision OCR or native PDF text). The tests directly use this text instead of making real API calls, ensuring tests are fast, deterministic, and free.
*   ✅ `results/expected/`: Contains the flat expected, ground-truth JSON outputs corresponding to each raw text file. If the barcode parsing logic changes, the tests evaluate its outputs against these expected JSON files.
*   📊 `scanner_test_report.txt`: An automatically generated summary file created after running the `pytest` suite. It lists parser performance broken down by each receipt, summarizes the category metrics (including the number of receipts processed per category), and calculates a global overall success score.

## 🛠️ Adding New Test Cases

If you encounter a receipt that is parsed incorrectly and want to add it as a new test case, use the CLI utility located in this directory.

Open your terminal in the `backend` folder and run:
```bash
python tests/unit/scanner/generate_test_fixture.py "path/to/your/receipt.jpg"
```
*(For panoramic receipts composed of multiple images, simply append paths sequentially in the same command).*

Under the hood, this sets `ENABLE_DEBUG=True`, invoking `test_recorder.py`. The mechanism automatically creates the `raw/` text, populates the `expected/` JSON (summing multi-quantities correctly), and copies the referenced image or PDF into the root `results/receipts/` directory.

> [!IMPORTANT]
> **After generation, categorize the receipt!** Move the newly created image/PDF from the root `receipts/` directory into `digital/`, `physical/`, or `complicated/`. Keep the newly created files in `raw/` and `expected/` exactly where they are.

## 🚀 Running the Tests

To evaluate the parser logic against the existing fixtures, activate your virtual environment `(.venv)` in the `backend` folder and run:

```bash
pytest tests/unit/scanner/test_scanner_logic.py -v
```

### 📈 Performance Metrics

The tests measure logic regressions and improvements based on a Composite Score (out of 100). The scores are provided on an individual case basis, a per-category basis, and a global basis, using these metrics:
1.  🎯 **Barcode Identification Rate:** (70% Weight) Measures how many expected products were successfully identified.
2.  ⚖️ **Quantity Accuracy Rate:** (30% Weight) Of the successfully identified products, measures if the quantity extracted is precise.
3.  🚫 **False Positives (Noise penalty):** Subtracts heavily from the composite score for every incorrect barcode guessed that didn't exist in the actual receipt (e.g. interpreting a loyal club number as a product).
