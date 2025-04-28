#!/usr/bin/env python3
import warnings
# unterdrücke genau diesen UserWarning aus pyannote.audio
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module=r"pyannote\.audio\.models\.blocks\.pooling"
)

import argparse
import sys
import os
import AdvancedHTMLParser
from noScribe import App, millisec, html_to_text

def run_headless(args):
    # Instanziiert die App (erstellt alle GUI‑Widgets, aber wir verstecken das Fenster sofort)
    app = App()
    app.withdraw()             # Versteckt das Hauptfenster
    app.update()               # GUI‑State aktualisieren
    app.cancel = False         # sicherheitshalber zurücksetzen

    # 1) Pfade setzen
    app.audio_file = args.audio
    app.transcript_file = args.output

    # 2) Damit save_doc() den richtigen Dateinamen und die Extension benutzt:
    import os
    app.my_transcript_file = args.output
    app.file_ext = os.path.splitext(args.output)[1].lstrip('.')  # 'html', 'txt' oder 'vtt'

    # Start/Stop
    app.entry_start.delete(0, 'end')
    if args.start:
        app.entry_start.insert(0, args.start)
    else:
        app.entry_start.insert(0, '')
    app.entry_stop.delete(0, 'end')
    if args.stop:
        app.entry_stop.insert(0, args.stop)
    else:
        app.entry_stop.insert(0, '')

    # Modell‑Dropdown (z.B. "precise" oder "fast")
    app.option_menu_whisper_model.set(args.model)

    # Sprache (Auto, Multilingual oder z.B. "de", "en")
    app.option_menu_language.set(args.language.capitalize())

    # Sprecherzahl (z.B. "auto", "none" oder "2")
    app.option_menu_speaker.set(str(args.speakers))

    # Checkboxen
    if args.overlap:
        app.check_box_overlapping.select()
    else:
        app.check_box_overlapping.deselect()

    if args.fillers:
        app.check_box_disfluencies.select()
    else:
        app.check_box_disfluencies.deselect()

    if args.timestamps:
        app.check_box_timestamps.select()
    else:
        app.check_box_timestamps.deselect()

    # 4) Ruft die Transkriptions‑Routine auf (anstelle des GUI‑Buttons):
    app.transcription_worker()

def main():
    p = argparse.ArgumentParser(
        description="Headless noScribe – gleiche Optionen wie GUI, aber komplett in der Konsole"
    )
    p.add_argument("-i", "--audio",   required=True, help="Eingabe‑Datei (Audio/Video)")
    p.add_argument("-o", "--output",  required=True, help="Ausgabe‑Transkript (.html, .txt, .vtt)")
    p.add_argument("--start",         help="Startzeit hh:mm:ss (optional)")
    p.add_argument("--stop",          help="Stop-Zeit hh:mm:ss (optional)")
    p.add_argument("-l", "--language",default="Auto",
                   help="Sprache: z.B. Auto, Multilingual, de, en")
    p.add_argument("-m", "--model",   default="precise",
                   help="Modell: precise oder fast (wie in GUI)")
    p.add_argument("-s", "--speakers",default="auto",
                   help="Sprechererkennung: auto, none oder Zahl")
    p.add_argument("--overlap", action="store_true",
                   help="Überlappende Sprache markieren")
    p.add_argument("--fillers", action="store_true",
                   help="Füllwörter beibehalten")
    p.add_argument("--timestamps", action="store_true",
                   help="Zeitmarken einfügen")
    args = p.parse_args()

    # Validierung
    if not args.audio or not args.output:
        p.error("Bitte mindestens --audio und --output angeben.")

    try:
        # wenn .txt angefragt, erst HTML generieren, dann wie noScribe konvertieren:
        if args.output.lower().endswith('.txt'):
            html_out = args.output[:-4] + '.html'
            args_html = args
            args_html.output = html_out
            run_headless(args_html)

            # HTML → Text konvertieren mit AdvancedHTMLParser + html_to_text()
            parser = AdvancedHTMLParser.AdvancedHTMLParser()
            with open(html_out, 'r', encoding='utf-8') as hf:
                parser.parseStr(hf.read())
            text = html_to_text(parser)
            with open(args.output, 'w', encoding='utf-8') as tf:
                tf.write(text)
            # temporäre HTML wegräumen
            try:
                os.remove(html_out)
            except:
                pass
        else:
            run_headless(args)

    except Exception as e:
        print("Fehler beim Transkribieren:", e, file=sys.stderr)
        sys.exit(1)
    else:
        # lege wenigstens eine leere .txt an, falls sie es trotz allem nicht tut
        if args.output.lower().endswith('.txt') and os.path.exists(args.output) and os.path.getsize(args.output) == 0:
            open(args.output, 'w', encoding='utf-8').close()

if __name__ == "__main__":
    main()
