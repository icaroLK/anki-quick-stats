from aqt import mw
from aqt.qt import (
	QCheckBox,
	QComboBox,
	QDialog,
	QDialogButtonBox,
	QHBoxLayout,
	QLabel,
	QVBoxLayout,
	QWidget,
)

from . import getUserOption, setUserOption

SEPARATOR_OPTIONS = [
	(",", "Comma   (1,000)"),
	(".", "Period   (1.000)"),
	(" ", "Space   (1 000)"),
	("", "None   (1000)"),
]

STAT_TOGGLES = [
	("stat_cards", "Cards studied"),
	("stat_time", "Time studied"),
	("stat_per_card", "Time per card"),
	("stat_new", "New cards"),
	("stat_retention", "Retention"),
]

DEFAULTS = {
	'show_total_lifetime': False,
	'show_today_stats': True,
	'show_future_stats': False,
	'show_default_anki_stats': False,
	'thousand_separator': ',',
	'stat_cards': True,
	'stat_time': True,
	'stat_per_card': True,
	'stat_new': True,
	'stat_retention': True,
}


class QuickStatsSettings(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent or mw)
		self.setWindowTitle("📊 Quick Stats (Main Screen) Settings")
		self.setMinimumWidth(360)

		layout = QVBoxLayout(self)

		self.show_total_cb = QCheckBox("Show total reviews (lifetime)")
		self.show_total_cb.setChecked(bool(getUserOption('show_total_lifetime', DEFAULTS['show_total_lifetime'])))
		layout.addWidget(self.show_total_cb)

		self.show_today_cb = QCheckBox("Show a stats row for a selected period (Today / Last month / Last year / Lifetime)")
		self.show_today_cb.setChecked(bool(getUserOption('show_today_stats', DEFAULTS['show_today_stats'])))
		self.show_today_cb.toggled.connect(self._update_stat_toggles_visibility)
		layout.addWidget(self.show_today_cb)

		self.stat_container = QWidget()
		stat_layout = QVBoxLayout(self.stat_container)
		stat_layout.setContentsMargins(24, 4, 0, 4)
		self.stat_checkboxes = {}
		for key, label in STAT_TOGGLES:
			cb = QCheckBox(label)
			cb.setChecked(bool(getUserOption(key, DEFAULTS[key])))
			stat_layout.addWidget(cb)
			self.stat_checkboxes[key] = cb
		layout.addWidget(self.stat_container)

		self.show_future_cb = QCheckBox("Show future daily load")
		self.show_future_cb.setChecked(bool(getUserOption('show_future_stats', DEFAULTS['show_future_stats'])))
		layout.addWidget(self.show_future_cb)

		self.show_default_cb = QCheckBox('Show Anki\'s default "Studied X cards..." line')
		self.show_default_cb.setChecked(bool(getUserOption('show_default_anki_stats', DEFAULTS['show_default_anki_stats'])))
		layout.addWidget(self.show_default_cb)

		sep_row = QHBoxLayout()
		sep_row.addWidget(QLabel("Thousands separator:"))
		self.sep_combo = QComboBox()
		current_sep = getUserOption('thousand_separator', DEFAULTS['thousand_separator'])
		for value, label in SEPARATOR_OPTIONS:
			self.sep_combo.addItem(label, value)
		idx = next((i for i, (v, _) in enumerate(SEPARATOR_OPTIONS) if v == current_sep), 0)
		self.sep_combo.setCurrentIndex(idx)
		sep_row.addWidget(self.sep_combo)
		layout.addLayout(sep_row)

		buttons = QDialogButtonBox(
			QDialogButtonBox.StandardButton.Ok
			| QDialogButtonBox.StandardButton.Cancel
			| QDialogButtonBox.StandardButton.RestoreDefaults
		)
		buttons.accepted.connect(self.on_accept)
		buttons.rejected.connect(self.reject)
		buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self.on_restore_defaults)
		layout.addWidget(buttons)

		self._update_stat_toggles_visibility(self.show_today_cb.isChecked())

	def _update_stat_toggles_visibility(self, checked):
		self.stat_container.setVisible(checked)

	def on_restore_defaults(self):
		self.show_total_cb.setChecked(DEFAULTS['show_total_lifetime'])
		self.show_today_cb.setChecked(DEFAULTS['show_today_stats'])
		self.show_future_cb.setChecked(DEFAULTS['show_future_stats'])
		self.show_default_cb.setChecked(DEFAULTS['show_default_anki_stats'])
		for key, cb in self.stat_checkboxes.items():
			cb.setChecked(DEFAULTS[key])
		idx = next((i for i, (v, _) in enumerate(SEPARATOR_OPTIONS) if v == DEFAULTS['thousand_separator']), 0)
		self.sep_combo.setCurrentIndex(idx)

	def on_accept(self):
		setUserOption('show_total_lifetime', self.show_total_cb.isChecked())
		setUserOption('show_today_stats', self.show_today_cb.isChecked())
		setUserOption('show_future_stats', self.show_future_cb.isChecked())
		setUserOption('show_default_anki_stats', self.show_default_cb.isChecked())
		setUserOption('thousand_separator', self.sep_combo.currentData())
		for key, cb in self.stat_checkboxes.items():
			setUserOption(key, cb.isChecked())
		if mw.state == 'deckBrowser' and mw.deckBrowser:
			mw.deckBrowser.refresh()
		self.accept()


def open_settings():
	QuickStatsSettings(mw).exec()
