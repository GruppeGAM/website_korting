#!/usr/bin/env python3
"""
Bildverbesserung für gescannte Fotokopie
=========================================
Verarbeitet CCI_000001.jpg (gescannte Fotokopie) und erzeugt
eine qualitativ verbesserte Version als portrait_enhanced.jpg.

Alle Parameter als Konstanten – einfach oben anpassen und neu ausführen.
"""

import sys
import os

# ── Abhängigkeiten prüfen ────────────────────────────────────────────────────
try:
    import cv2
    import numpy as np
    from PIL import Image, ImageEnhance, ImageFilter
except ImportError as e:
    print(f"Fehlende Abhängigkeit: {e}")
    print("Bitte installieren: pip install opencv-python pillow numpy")
    sys.exit(1)

# ── Parameter (hier anpassen) ────────────────────────────────────────────────

INPUT_PATH  = "images/CCI_000001.jpg"
OUTPUT_PATH = "images/portrait_enhanced.jpg"
JPEG_QUALITY = 92          # 1–95, höher = besser aber größere Datei

# Descreening (Halbtonraster entfernen)
# Größerer Kernel = stärkeres Weichzeichnen des Rasters
# Empfehlung: 3 (schwach) bis 7 (stark)
DESCREEN_KERNEL  = 5       # muss ungerade sein
DESCREEN_SIGMA   = 1.0     # Stärke des Gaußfilters

# Rauschreduzierung (fastNlMeansDenoisingColored)
# h/hColor: 1–10; höher = weniger Rauschen, aber weicheres Bild
DENOISE_H        = 6
DENOISE_H_COLOR  = 6
DENOISE_TEMPLATE = 7       # Template-Fenstergröße (ungerade)
DENOISE_SEARCH   = 21      # Suchfenster-Größe (ungerade)

# Farbkorrektur (Pillow ImageEnhance.Color)
# 1.0 = unverändert, >1.0 = kräftiger, <1.0 = blasser
COLOR_ENHANCE    = 1.08

# Kontrast (Pillow ImageEnhance.Contrast)
# 1.0 = unverändert, 1.2 = +20 % Kontrast
CONTRAST_ENHANCE = 1.18

# Helligkeit (Pillow ImageEnhance.Brightness)
# 1.0 = unverändert, 1.05 = leicht heller
BRIGHTNESS_ENHANCE = 1.05

# Unschärfemaske (Schärfe zurückgewinnen nach Weichzeichnung)
# radius: Radius des Unschärfe-Halos (px)
# percent: Stärke der Schärfung in %
# threshold: Mindestunterschied für Schärfung (0–255)
UNSHARP_RADIUS    = 1.5
UNSHARP_PERCENT   = 130
UNSHARP_THRESHOLD = 3

# ── Verarbeitung ─────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(INPUT_PATH):
        print(f"Fehler: Eingabedatei nicht gefunden: {INPUT_PATH}")
        sys.exit(1)

    print(f"Lade Bild: {INPUT_PATH}")
    img_cv = cv2.imread(INPUT_PATH)
    if img_cv is None:
        print("Fehler: Bild konnte nicht geladen werden.")
        sys.exit(1)

    h, w = img_cv.shape[:2]
    print(f"Bildgröße: {w} x {h} px")

    # 1. Descreening – Halbtonraster (Druckpunkte der Fotokopie) entfernen
    print("Schritt 1/5: Descreening (Gaußfilter) …")
    img_cv = cv2.GaussianBlur(img_cv, (DESCREEN_KERNEL, DESCREEN_KERNEL), DESCREEN_SIGMA)

    # 2. Rauschreduzierung
    print("Schritt 2/5: Rauschreduzierung …")
    img_cv = cv2.fastNlMeansDenoisingColored(
        img_cv,
        None,
        h=DENOISE_H,
        hColor=DENOISE_H_COLOR,
        templateWindowSize=DENOISE_TEMPLATE,
        searchWindowSize=DENOISE_SEARCH,
    )

    # 3. Konvertierung zu Pillow (BGR → RGB)
    img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))

    # 4. Farbkorrektur
    print("Schritt 3/5: Farbkorrektur …")
    img_pil = ImageEnhance.Color(img_pil).enhance(COLOR_ENHANCE)

    # 5. Kontrast
    print("Schritt 4/5: Kontrast & Helligkeit …")
    img_pil = ImageEnhance.Contrast(img_pil).enhance(CONTRAST_ENHANCE)
    img_pil = ImageEnhance.Brightness(img_pil).enhance(BRIGHTNESS_ENHANCE)

    # 6. Schärfe zurückgewinnen (Unschärfemaske)
    print("Schritt 5/5: Schärfen …")
    img_pil = img_pil.filter(
        ImageFilter.UnsharpMask(
            radius=UNSHARP_RADIUS,
            percent=UNSHARP_PERCENT,
            threshold=UNSHARP_THRESHOLD,
        )
    )

    # 7. Speichern
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    img_pil.save(OUTPUT_PATH, "JPEG", quality=JPEG_QUALITY, optimize=True)

    size_in  = os.path.getsize(INPUT_PATH)  / 1024
    size_out = os.path.getsize(OUTPUT_PATH) / 1024
    print(f"\nFertig!")
    print(f"  Eingabe:  {INPUT_PATH}  ({size_in:.0f} KB)")
    print(f"  Ausgabe:  {OUTPUT_PATH}  ({size_out:.0f} KB)")
    print(f"\nParameter zum Feinjustieren (oben im Skript):")
    print(f"  Descreening:  DESCREEN_KERNEL={DESCREEN_KERNEL}, DESCREEN_SIGMA={DESCREEN_SIGMA}")
    print(f"  Rauschen:     DENOISE_H={DENOISE_H}, DENOISE_H_COLOR={DENOISE_H_COLOR}")
    print(f"  Farbe:        COLOR_ENHANCE={COLOR_ENHANCE}")
    print(f"  Kontrast:     CONTRAST_ENHANCE={CONTRAST_ENHANCE}")
    print(f"  Helligkeit:   BRIGHTNESS_ENHANCE={BRIGHTNESS_ENHANCE}")
    print(f"  Schärfe:      UNSHARP_RADIUS={UNSHARP_RADIUS}, UNSHARP_PERCENT={UNSHARP_PERCENT}")

if __name__ == "__main__":
    main()
