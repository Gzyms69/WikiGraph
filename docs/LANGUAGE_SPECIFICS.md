# WikiGraph Language Specifics

This document tracks the unique characteristics, data oddities, and processing rules for each supported Wikipedia language.

## 🇵🇱 Polish (pl)
*   **Status:** Fully Supported (Phase 4 Complete).
*   **Character Set:** UTF-8 (Latin Extended-A: ą, ć, ę, ł, ń, ó, ś, ź, ż).
*   **Namespaces:**
    *   Category: `Kategoria:`
    *   File: `Plik:` or `Grafika:`
    *   Template: `Szablon:`
*   **Redirects:** Handled via `#REDIRECT`, `#PATRZ`, `#PRZEKIERUJ`.
*   **Date Format:** `DD month YYYY` (e.g., `14 stycznia 2026`).

## 🇩🇪 German (de)
*   **Status:** In Progress (Phase 4A).
*   **Character Set:** UTF-8 (Latin-1 Supplement: ä, ö, ü, ß).
    *   *Note:* `ß` (Eszett) requires special handling in lowercasing (becomes `ss`).
*   **Namespaces:**
    *   Category: `Kategorie:`
    *   File: `Datei:` or `Bild:`
    *   Template: `Vorlage:`
*   **Redirects:** `#WEITERLEITUNG`.
*   **Quirks:**
    *   **Stable Versions:** German Wikipedia has a strict "Sighted revisions" system. We should use `latest` dumps but be aware flags might differ.
    *   **Person Data:** Often uses `{{Personendaten}}` template which is highly structured.
    *   **Dates:** `D. Month YYYY` (e.g., `14. Januar 2026`). Note the dot.

## 🇺🇸 English (en)
*   **Status:** Planned.
*   **Scale:** Massive (~6.8M articles). Will require significantly more disk space (~100GB for graph).
*   **Quirks:**
    *   "The" prefixes often stripped in sorting but kept in titles.
