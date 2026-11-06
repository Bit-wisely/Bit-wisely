# Profile card

- `profile-card.svg`  – the card shown by README.md (generated, don't edit by hand)
- `generate_card.py`  – rebuilds it:  `python generate_card.py --defaults`
- `portrait.txt`      – the ASCII portrait (plain text). New photo: `python generate_card.py --image photo.png`
- `fonts/`            – JetBrains Mono subset (OFL), embedded in the SVG so alignment is identical on every device
- `update_profile_stats.py` – pulls live repo count / bio, then rebuilds the card

Tweak size in `generate_card.py`: `FONT_SIZE` (info text), `PORTRAIT_FONT` (portrait detail), `CARD_W` (keep <= ~880).
