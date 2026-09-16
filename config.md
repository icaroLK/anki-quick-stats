# 📊 Quick Stats (Main Screen)

## Notice

This addon shows a clean stat card on the main screen with your total review count, plus cards studied, time studied, time per card, new cards, and retention for a period you pick (Today / Last month / Last year / Lifetime, via the small button above that row). 
It replaces Anki's default "Studied X cards..." line.

## Options

- `thousand_separator`: Character used to group digits in the total (e.g. `,` for 115,717 or `.` for 115.717).
- `show_total_lifetime`: `True`/`false` (default `false`). → Whether to show the big total-reviews number.
- `show_today_stats`: `True`/`false` → Whether to show the period stats row below the total.
- `show_future_stats`: `True`/`false` (default `false`) → Whether to show a "Future" row with your daily load, matching Anki's own Future Daily Load
- `show_default_anki_stats`: `True`/`false` (default `false`) → Whether to also show Anki's original "Studied X cards in Y minutes today (Zs/card)" line above this card.
- `stat_cards`, `stat_time`, `stat_per_card`, `stat_new`, `stat_retention`: `True`/`false` (default `true`) → which individual stats show up in the period row.

You can also change these from **Tools → Quick Stats Settings...** instead of editing this JSON.

Add-on by Icaro Kuchanovicz