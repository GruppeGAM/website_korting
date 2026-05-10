#!/usr/bin/env python3
"""
Bildverbesserung – Variante: Maximaler Detailerhalt (HQ-Vorlage)
=================================================================
Unterschied zum Standard-Skript (enhance_image.py):

  Standard:   GaussianBlur  +  fastNlMeansDenoisingColored
              → starke Rausch-/Rasterreduzierung, aber merklicher
                Auflösungsverlust (globales Weichzeichnen)

  Diese HQ-Variante:
              → Bilateral Filter statt Gaußfilter
                Bilateral glättet Rauschen/Raster NUR in gleichmäßigen
                Flächen; Kanten und Feindetails (Gesicht, Haare, Stoff)
                bleiben scharf
              → KEIN fastNlMeansDenoising (zu weichzeichnend)
              → Stärkeres Unsharp Mask zum Ausgleich

Alle Parameter als Konstanten oben – einfach anpassen und neu ausführen.
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

INPUT_PATH   = "images/CCI_000001.jpg"
OUTPUT_PATH  = "images/portrait_hq.jpg"
JPEG_QUALITY = 95          # Höher als Standard → größere Datei, mehr Detail

# ── Bilateral Filter (ersetzt GaussianBlur + NLMeans)
# Funktionsweise: glättet gleichmäßige Flächen (Rauschen/Raster),
# lässt Kanten und Strukturen nahezu unberührt.
#
# d            – Filterdurchmesser in Pixel
#                5–7 = schwach/schnell, 9–11 = mittel, 15+ = stark/langsam
# sigma_color  – Farbtoleranz: größer → mehr Farben werden als "gleich" behandelt
#                Empfehlung: 30–80 (kleiner = kantenschonender)
# sigma_space  – Räumliche Glättung: größer → weiter entfernte Pixel fließen ein
#                Empfehlung: 30–80
#
# Tipp: Mehrere schwache Durchläufe (BILATERAL_PASSES > 1) sind
#       oft besser als ein einziger starker Durchlauf.
BILATERAL_D           = 7
BILATERAL_SIGMA_COLOR = 40
BILATERAL_SIGMA_SPACE = 40
BILATERAL_PASSES      = 2   # Anzahl der Filterdurchläufe

# ── Farbkorrektur (Pillow ImageEnhance.Color)
# 1.0 = unverändert, >1.0 = kräftiger, <1.0 = blasser
COLOR_ENHANCE    = 1.08

# ── Kontrast (Pillow ImageEnhance.Contrast)
CONTRAST_ENHANCE = 1.15

# ── Helligkeit (Pillow ImageEnhance.Brightness)
BRIGHTNESS_ENHANCE = 1.04

# ── Unschärfemaske – etwas aggressiver als Standard, weil kein NLMeans läuft
# radius:    Radius des Halos (px); größer = deutlicherer Schärfeeffekt
# percent:   Stärke in %; 100 = sichtbare Schärfung, 150–200 = deutlich
# threshold: Mindestkontrast zum Schärfen (verhindert Rauschverstärkung)
UNSHARP_RADIUS    = 1.2
UNSHARP_PERCENT   = 150
UNSHARP_THRESHOLD = 4

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

    # 1. Bilateral Filter (Kanten-erhaltende Glättung)
    print(f"Schritt 1/4: Bilateral Filter ({BILATERAL_PASSES}× d={BILATERAL_D}) …")
    for _ in range(BILATERAL_PASSES):
        img_cv = cv2.bilateralFilter(
            img_cv,
            d=BILATERAL_D,
            sigmaColor=BILATERAL_SIGMA_COLOR,
            sigmaSpace=BILATERAL_SIGMA_SPACE,
        )

    # 2. Konvertierung zu Pillow (BGR → RGB)
    img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))

    # 3. Farbkorrektur + Kontrast + Helligkeit
    print("Schritt 2/4: Farbkorrektur & Kontrast …")
    img_pil = ImageEnhance.Color(img_pil).enhance(COLOR_ENHANCE)
    img_pil = ImageEnhance.Contrast(img_pil).enhance(CONTRAST_ENHANCE)
    img_pil = ImageEnhance.Brightness(img_pil).enhance(BRIGHTNESS_ENHANCE)

    # 4. Schärfen
    print("Schritt 3/4: Schärfen …")
    img_pil = img_pil.filter(
        ImageFilter.UnsharpMask(
            radius=UNSHARP_RADIUS,
            percent=UNSHARP_PERCENT,
            threshold=UNSHARP_THRESHOLD,
        )
    )

    # 5. Speichern
    print("Schritt 4/4: Speichern …")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    img_pil.save(OUTPUT_PATH, "JPEG", quality=JPEG_QUALITY, optimize=True)

    size_in  = os.path.getsize(INPUT_PATH)  / 1024
    size_out = os.path.getsize(OUTPUT_PATH) / 1024
    print(f"\nFertig!")
    print(f"  Eingabe:  {INPUT_PATH}  ({size_in:.0f} KB)")
    print(f"  Ausgabe:  {OUTPUT_PATH}  ({size_out:.0f} KB)")
    print(f"\nParameter zum Feinjustieren:")
    print(f"  Bilateral:    BILATERAL_D={BILATERAL_D}, SIGMA_COLOR={BILATERAL_SIGMA_COLOR}, SIGMA_SPACE={BILATERAL_SIGMA_SPACE}, PASSES={BILATERAL_PASSES}")
    print(f"  Farbe:        COLOR_ENHANCE={COLOR_ENHANCE}")
    print(f"  Kontrast:     CONTRAST_ENHANCE={CONTRAST_ENHANCE}")
    print(f"  Helligkeit:   BRIGHTNESS_ENHANCE={BRIGHTNESS_ENHANCE}")
    print(f"  Schärfe:      UNSHARP_RADIUS={UNSHARP_RADIUS}, UNSHARP_PERCENT={UNSHARP_PERCENT}, UNSHARP_THRESHOLD={UNSHARP_THRESHOLD}")

if __name__ == "__main__":
    main()
