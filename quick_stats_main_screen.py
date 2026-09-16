import json
import time

from aqt import mw

from . import getUserOption

FONT_STACK = '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, Helvetica, Arial, sans-serif'

PERIODS = ['today', 'month', 'year', 'lifetime']
PERIOD_LABELS = {
	'today': 'Today',
	'month': 'Last month',
	'year': 'Last year',
	'lifetime': 'Lifetime',
}
PERIOD_SPAN_DAYS = {
	'today': 1,
	'month': 30,
	'year': 365,
}

STAT_CONFIG = [
	('stat_cards', 'qsCards', 'Cards'),
	('stat_time', 'qsTime', 'Time'),
	('stat_per_card', 'qsPerCard', 'Per card'),
	('stat_new', 'qsNew', 'New'),
	('stat_retention', 'qsRetention', 'Retention'),
]


def _format_number(n):
	sep = getUserOption('thousand_separator', ',')
	return '{:,}'.format(int(n)).replace(',', sep)


def _day_cutoff():
	sched = mw.col.sched
	if hasattr(sched, 'day_cutoff'):
		return sched.day_cutoff
	# fallback for schedulers that don't expose day_cutoff directly:
	# rebuild the rollover-hour boundary ourselves
	rollover = mw.col.conf.get('rollover', 4)
	now = time.localtime()
	cutoff = time.mktime((now.tm_year, now.tm_mon, now.tm_mday, rollover, 0, 0, 0, 0, -1))
	if time.time() >= cutoff:
		cutoff += 86400
	return int(cutoff)


def _period_stats(start_ms, end_ms):
	if start_ms is None:
		bounds, params = "id < ?", (end_ms,)
	else:
		bounds, params = "id >= ? and id < ?", (start_ms, end_ms)

	cards = mw.col.db.scalar(f"select count(*) from revlog where {bounds} and type != 4", *params) or 0
	time_ms = mw.col.db.scalar(f"select sum(time) from revlog where {bounds} and type != 4", *params) or 0
	new_cards = mw.col.db.scalar(f"select count(distinct cid) from revlog where {bounds} and type = 0", *params) or 0
	correct = mw.col.db.scalar(f"select count(*) from revlog where {bounds} and type != 4 and ease > 1", *params) or 0

	minutes = time_ms / 60000
	seconds_per_card = (time_ms / 1000 / cards) if cards else 0
	retention = (correct / cards * 100) if cards else 0
	return {
		'cards': cards,
		'minutes': round(minutes, 1),
		'spc': round(seconds_per_card, 1),
		'new_cards': new_cards,
		'retention': round(retention, 1),
	}


def _all_period_stats():
	cutoff = _day_cutoff()
	end_ms = cutoff * 1000
	stats = {}
	for period in PERIODS:
		if period == 'lifetime':
			stats[period] = _period_stats(None, end_ms)
		else:
			start_ms = end_ms - PERIOD_SPAN_DAYS[period] * 86400 * 1000
			stats[period] = _period_stats(start_ms, end_ms)
	return stats


def _daily_load():
	# mirrors Anki's own calculation (rslib/src/stats/graphs/future_due.rs):
	# sum of 1 / max(interval, 1) over all cards that aren't new or suspended
	# (buried cards still count), truncated to an integer.
	result = mw.col.db.scalar(
		"select sum(1.0 / max(ivl, 1)) from cards where type != 0 and queue != -1"
	)
	return int(result or 0)


def generateStats():
	total = mw.col.db.scalar("select count(id) from revlog where type != 4") or 0
	show_total = getUserOption('show_total_lifetime', False)
	show_today = getUserOption('show_today_stats', True)
	show_future = getUserOption('show_future_stats', False)

	style = f"""
	<style>
	.qs-card {{
		font-family: {FONT_STACK};
		max-width: 520px;
		margin: 18px auto 0;
		text-align: center;
		color: inherit;
		position: relative;
	}}
	.qs-total-number {{
		font-size: 2.5em;
		font-weight: 600;
		letter-spacing: -0.02em;
		line-height: 1.15;
	}}
	.qs-total-label {{
		font-size: 0.72em;
		text-transform: uppercase;
		letter-spacing: 0.07em;
		opacity: 0.5;
		margin-top: 2px;
	}}
	.qs-divider {{
		height: 1px;
		background: currentColor;
		opacity: 0.16;
		margin: 14px 0 12px;
	}}
	.qs-section-label {{
		font-size: 0.62em;
		opacity: 0.45;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		margin-bottom: 8px;
	}}
	.qs-period-row {{
		display: flex;
		justify-content: center;
		margin: 0 0 14px;
	}}
	.qs-period-btn {{
		display: inline-block;
		font-family: {FONT_STACK};
		font-size: 0.68em;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: inherit;
		opacity: 0.65;
		background: rgba(127,127,127,0.12);
		border-radius: 999px;
		padding: 4px 12px;
		cursor: pointer;
		user-select: none;
	}}
	.qs-period-btn:hover {{
		opacity: 1;
		background: rgba(127,127,127,0.2);
	}}
	.qs-grid {{
		display: flex;
		flex-wrap: nowrap;
		justify-content: space-between;
	}}
	.qs-stat {{
		flex: 1;
		min-width: 0;
		padding: 0 3px;
	}}
	.qs-value {{
		font-size: 1.05em;
		font-weight: 600;
		letter-spacing: -0.01em;
		white-space: nowrap;
	}}
	.qs-label {{
		font-size: 0.62em;
		opacity: 0.5;
		margin-top: 2px;
		text-transform: uppercase;
		letter-spacing: 0.03em;
		white-space: nowrap;
	}}
	.qs-empty {{
		font-family: {FONT_STACK};
		opacity: 0.5;
		padding: 10px;
	}}
	</style>
	"""

	if total == 0:
		return f'{style}<div class="qs-card"><div class="qs-empty">No reviews done yet</div></div>'

	period_html = ""
	if show_today:
		enabled_stats = [
			(key, elem_id, label)
			for key, elem_id, label in STAT_CONFIG
			if getUserOption(key, True)
		]
		stat_divs = "\n".join(
			f'<div class="qs-stat"><div class="qs-value" id="{elem_id}">-</div>'
			f'<div class="qs-label">{label}</div></div>'
			for key, elem_id, label in enabled_stats
		)
		render_lines = []
		if any(key == 'stat_cards' for key, _, _ in enabled_stats):
			render_lines.append("document.getElementById('qsCards').textContent = fmt(d.cards);")
		if any(key == 'stat_time' for key, _, _ in enabled_stats):
			render_lines.append("document.getElementById('qsTime').textContent = fmtTime(d.minutes);")
		if any(key == 'stat_per_card' for key, _, _ in enabled_stats):
			render_lines.append("document.getElementById('qsPerCard').textContent = d.spc.toFixed(1) + 's';")
		if any(key == 'stat_new' for key, _, _ in enabled_stats):
			render_lines.append("document.getElementById('qsNew').textContent = fmt(d.new_cards);")
		if any(key == 'stat_retention' for key, _, _ in enabled_stats):
			render_lines.append("document.getElementById('qsRetention').textContent = d.retention.toFixed(1) + '%';")
		render_body = "\n\t\t\t\t".join(render_lines)

		data = _all_period_stats()
		sep = getUserOption('thousand_separator', ',')
		period_html = f"""
		<div class="qs-period-row">
			<span class="qs-period-btn" id="qsPeriodBtn" role="button" tabindex="0">Today</span>
		</div>
		<div class="qs-grid">
			{stat_divs}
		</div>
		<script>
		(function() {{
			var data = {json.dumps(data)};
			var labels = {json.dumps(PERIOD_LABELS)};
			var order = {json.dumps(PERIODS)};
			var sep = {json.dumps(sep)};
			function fmt(n) {{
				return Math.round(n).toString().replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, sep);
			}}
			function fmtTime(minutes) {{
				if (minutes >= 60) {{
					return (minutes / 60).toFixed(1) + 'h';
				}}
				return minutes.toFixed(1) + 'm';
			}}
			function render(period) {{
				var d = data[period];
				{render_body}
				document.getElementById('qsPeriodBtn').textContent = labels[period];
			}}
			var saved = null;
			try {{ saved = localStorage.getItem('qs_period'); }} catch (e) {{}}
			var idx = order.indexOf(saved);
			if (idx === -1) idx = 0;
			render(order[idx]);
			document.getElementById('qsPeriodBtn').addEventListener('click', function() {{
				idx = (idx + 1) % order.length;
				try {{ localStorage.setItem('qs_period', order[idx]); }} catch (e) {{}}
				render(order[idx]);
			}});
		}})();
		</script>
		"""

	total_html = ""
	if show_total:
		total_html = f"""
		<div class="qs-total">
			<div class="qs-total-number">{_format_number(total)}</div>
			<div class="qs-total-label">Total reviews in lifetime</div>
		</div>
		"""

	future_html = ""
	if show_future:
		daily_load = _daily_load()
		future_html = f"""
		<div class="qs-section-label">Future</div>
		<div class="qs-grid">
			<div class="qs-stat">
				<div class="qs-value">{_format_number(daily_load)}</div>
				<div class="qs-label">Daily load</div>
			</div>
		</div>
		"""

	sections = [html for html in (total_html, period_html, future_html) if html.strip()]
	card_body = '<div class="qs-divider"></div>'.join(sections)

	return f"""
	{style}
	<div class="qs-card">
		{card_body}
	</div>
	"""


def db_wrc(deck_browser, content):
	if not getUserOption('show_default_anki_stats', False):
		# strip only Anki's own default line, leaving anything other addons
		# have already added to content.stats untouched
		content.stats = content.stats.replace(mw.col.studied_today(), "", 1)
	content.stats += generateStats()


from aqt.gui_hooks import deck_browser_will_render_content

deck_browser_will_render_content.append(db_wrc)
