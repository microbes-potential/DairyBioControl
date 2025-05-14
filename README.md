# 🧫 DairyBioControl

**DairyBioControl** is a web-based bioinformatics platform developed with Python and Dash, designed to predict microbial biocontrol potential directly from genome data (e.g., GenBank, antiSMASH, or CSV annotations). The app extracts fermentation- and defense-associated traits and generates a clean, branded PDF report with trait classifications and co-occurrence analysis.

---

## 🔍 Features

- Upload genome files (`.gbk`, `.gbff`, `.csv`, `.json`)
- Automatically detect fermentation or biocontrol traits
- Filter traits by functional category
- Visualize trait co-occurrence networks
- Maintain upload history
- Download PDF reports with detected traits and scores
- Branded with **LaPointes Research Group** logo and layout

---

## 📂 File Types Supported

- `.gbk` / `.gbff`: GenBank-formatted genome files
- `.json`: antiSMASH cluster JSON output
- `.csv`: Annotation files with `gene` or `product` columns

---

## 📊 Scoring Logic

Each detected trait contributes to a cumulative **Biocontrol Score**, based on:
- Number of matched trait-related genes
- Trait detection is keyword-based using a curated JSON database (`dairy_biocontrol_traits.json`)

> **Note:** The app has removed "Acid Tolerance" traits and machine learning scoring logic for simplicity and clarity.

---

## 📁 Directory Structure

```bash
├── app.py                     # Main Dash application
├── pdf_report_generator.py    # PDF generation logic
├── trait_detection_score_based.py  # Trait matching and scoring logic
├── parse_antismash_json.py    # antiSMASH JSON parser
├── db_utils.py                # SQLite logic to store uploads and scores
├── trait_analytics.py         # Co-occurrence network logic
├── dairy_biocontrol_traits.json  # Trait database
├── assets/
│   └── Prof.PNG               # Research group logo

