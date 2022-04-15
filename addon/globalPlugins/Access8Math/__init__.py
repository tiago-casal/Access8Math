"""# Access8Math: Allows access math content written by MathML and write math as MathML
# Copyright (C) 2017-2022 Tseng Woody <tsengwoody.tw@gmail.com>
# This file is covered by the GNU General Public License.
# See the file COPYING.txt for more details."""
# coding: utf-8

import os
import sys
import shutil

import addonHandler
import api
import config
import buildVersion
import controlTypes
import globalPluginHandler
import globalVars
import gui
from languageHandler import getWindowsLanguage
from logHandler import log
import mathPres
from mathPres.mathPlayer import MathPlayer
from NVDAObjects.IAccessible import IAccessible
from scriptHandler import script
import textInfos
import tones
import ui

import wx


insert_path_count = 0
# BASE_DIR = os.path.dirname(os.path.dirname(__file__))
# sys.path.insert(0, BASE_DIR)

PATH = os.path.dirname(__file__)

PYTHON_PATH = os.path.join(PATH, 'python')
sys.path.insert(0, PYTHON_PATH)
insert_path_count += 1

PACKAGE_PATH = os.path.join(PATH, 'package')
sys.path.insert(0, PACKAGE_PATH)
insert_path_count += 1

sys.path.insert(0, PATH)
insert_path_count += 1

# python xml import
import python.xml as xml
sys.modules['xml'] = xml

config.conf.spec["Access8Math"] = {
	"settings": {
		"language": "string(default=Windows)",
		"braille_language": "string(default=en)",
		"item_interval_time": "integer(default=50,min=0,max=100)",
		"interaction_frame_show": "boolean(default=false)",
		"analyze_math_meaning": "boolean(default=true)",
		"auto_generate": "boolean(default=false)",
		"dictionary_generate": "boolean(default=true)",
		"no_move_beep": "boolean(default=true)",
		"command_mode": "boolean(default=false)",
		"navigate_mode": "boolean(default=false)",
		"shortcut_mode": "boolean(default=false)",
		"writeNavAudioIndication": "boolean(default=true)",
		"writeNavAcrossLine": "boolean(default=true)",
		"HTML_document_display": "string(default=markdown)",
		"HTML_math_display": "string(default=block)",
		"LaTeX_delimiter": "string(default=bracket)",
		"speech_source": "string(default=Access8Math)",
		"braille_source": "string(default=Access8Math)",
		"interact_source": "string(default=Access8Math)",
	},
	"rules": {
		"SingleMsubsupType": "boolean(default=true)",
		"SingleMsubType": "boolean(default=true)",
		"SingleMsupType": "boolean(default=true)",
		"SingleMunderoverType": "boolean(default=true)",
		"SingleMunderType": "boolean(default=true)",
		"SingleMoverType": "boolean(default=true)",
		"SingleFractionType": "boolean(default=true)",
		"SingleSqrtType": "boolean(default=true)",
		"PowerType": "boolean(default=true)",
		"SquarePowerType": "boolean(default=true)",
		"CubePowerType": "boolean(default=true)",
		"SetType": "boolean(default=true)",
		"AbsoluteType": "boolean(default=true)",
		"MatrixType": "boolean(default=true)",
		"DeterminantType": "boolean(default=true)",
		"AddIntegerFractionType": "boolean(default=true)",
	}
}

import A8M_PM
from dialogs import ReadingSettingsDialog, WritingSettingsDialog, RuleSettingsDialog, NewLanguageAddingDialog, UnicodeDicDialog, MathRuleDialog
from editor import EditorFrame
from interaction import A8MProvider, A8MInteraction
from writer import TextMathEditField

# for i in range(insert_path_count):
	# del sys.path[0]

addonHandler.initTranslation()
ADDON_SUMMARY = addonHandler.getCodeAddon().manifest["summary"]
ADDON_VERSION = addonHandler.getCodeAddon().manifest["version"]

aboutMessage = _("""Access8Math
Version: {addonVersion}
URL: https://addons.nvda-project.org/addons/access8math.en.html
Copyright (C) {copyrightFirstYear}-{copyrightLastYear} Access8Math Contributors
Access8Math is covered by the GNU General Public License (Version 2). You are free to share or change this software in any way you like as long as it is accompanied by the license and you make all source code available to anyone who wants it. This applies to both original and modified copies of this software, plus any derivative works.
It can be viewed online at: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
Access8Math has been sponsored by "Taiwan Visually Impaired People Association"(accessibility@twvip.org) in 2018~2019, hereby express our sincere appreciation.
If you feel this add-on is helpful, please don't hesitate to give support to "Taiwan Visually Impaired People Association" and authors.""").format(
	addonVersion=ADDON_VERSION,
	copyrightFirstYear=2017,
	copyrightLastYear=2022,
)

if buildVersion.version_year >= 2022:
	ROLE_WINDOW = controlTypes.Role.WINDOW
	ROLE_EDITABLETEXT = controlTypes.Role.EDITABLETEXT
else:
	ROLE_WINDOW = controlTypes.ROLE_WINDOW
	ROLE_EDITABLETEXT = controlTypes.ROLE_EDITABLETEXT

mathPlayer = None
try:
	mathPlayer = MathPlayer()
except:
	config.conf["Access8Math"]["settings"]["speech_source"] = "Access8Math"
	config.conf["Access8Math"]["settings"]["braille_source"] = "Access8Math"
	config.conf["Access8Math"]["settings"]["interact_source"] = "Access8Math"
	log.warning("MathPlayer 4 not available")

reader = A8MProvider()
mathPres.registerProvider(reader, speech=True, braille=True, interaction=True)


class AppWindowRoot(IAccessible):
	def event_focusEntered(self):
		def run():
			parent = api.getFocusObject()
			vw = A8MInteraction(parent=parent)
			vw.set(data=globalVars.mathcontent, name="")
			try:
				vw.setFocus()
			except:
				tones.beep(100, 100)
		wx.CallLater(100, run)


editor_content = ''
editor_dialog = None

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self, *args, **kwargs):
		if config.conf["Access8Math"]["settings"]["language"] == "Windows":
			config.conf["Access8Math"]["settings"]["language"] = getWindowsLanguage()
		from command.latex import initialize
		initialize()
		super().__init__(*args, **kwargs)

		A8M_PM.initialize(config.conf["Access8Math"])

		self.language = config.conf["Access8Math"]["settings"]["language"]
		self.create_menu()

	def terminate(self):
		from command.latex import terminate
		terminate()
		try:
			self.toolsMenu.Remove(self.Access8Math_item)
		except (AttributeError, RuntimeError):
			pass

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		if obj.windowClassName == "wxWindowNR" and obj.role == ROLE_WINDOW and obj.name == _("Access8Math interaction window"):
			clsList.insert(0, AppWindowRoot)
		if obj.windowClassName == "Edit" and obj.role == ROLE_EDITABLETEXT:
			clsList.insert(0, TextMathEditField)

	def create_menu(self):
		self.toolsMenu = gui.mainFrame.sysTrayIcon.toolsMenu
		self.menu = wx.Menu()

		self.editor = self.menu.Append(
			wx.ID_ANY,
			_("&Editor...")
		)
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onEditor, self.editor)

		settingsMenu = wx.Menu()

		self.readingSettings = settingsMenu.Append(
			wx.ID_ANY,
			_("&Reading settings...")
		)
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onReadingSettings, self.readingSettings)

		self.writingSettings = settingsMenu.Append(
			wx.ID_ANY,
			_("&Writing settings...")
		)
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onWritingSettings, self.writingSettings)

		self.ruleSettings = settingsMenu.Append(
			wx.ID_ANY,
			_("Ru&le settings...")
		)
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onRuleSettings, self.ruleSettings)

		self.menu.AppendSubMenu(
			settingsMenu,
			_("&Settings"),
		)

		l10nMenu = wx.Menu()

		self.speechUnicodeDictionary = l10nMenu.Append(
			wx.ID_ANY,
			_("Speech &unicode dictionary...")
		)
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onSpeechUnicodeDictionary, self.speechUnicodeDictionary)

		self.speechMathRule = l10nMenu.Append(
			wx.ID_ANY,
			_("Speech &math rule...")
		)
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onSpeechMathRule, self.speechMathRule)

		self.brailleUnicodeDictionary = l10nMenu.Append(
			wx.ID_ANY,
			_("Braille &unicode dictionary...")
		)
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onBrailleUnicodeDictionary, self.brailleUnicodeDictionary)

		self.brailleMathRule = l10nMenu.Append(
			wx.ID_ANY,
			_("Braille &math rule...")
		)
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onBrailleMathRule, self.brailleMathRule)

		self.newLanguageAdding = l10nMenu.Append(
			wx.ID_ANY,
			_("&New language adding...")
		)
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onNewLanguageAdding, self.newLanguageAdding)

		self.menu.AppendSubMenu(
			l10nMenu,
			_("&Localization"),
		)

		self.cleanWorkspace = self.menu.Append(
			wx.ID_ANY,
			_("&Clean Workspace...")
		)
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onCleanWorkspace, self.cleanWorkspace)

		self.about = self.menu.Append(
			wx.ID_ANY,
			_("&About...")
		)
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onAbout, self.about)

		self.Access8Math_item = self.toolsMenu.AppendSubMenu(self.menu, _("Access8Math"), _("Access8Math"))

	@script(
		description=_("Speech source switch"),
		category=ADDON_SUMMARY,
	)
	def script_speech_source_switch(self, gesture):
		if config.conf["Access8Math"]["settings"]["speech_source"] == "Access8Math" and mathPlayer:
			config.conf["Access8Math"]["settings"]["speech_source"] = "MathPlayer"
		elif config.conf["Access8Math"]["settings"]["speech_source"] == "MathPlayer":
			config.conf["Access8Math"]["settings"]["speech_source"] = "Access8Math"
		else:
			config.conf["Access8Math"]["settings"]["speech_source"] = "Access8Math"
		ui.message(_("MathML speech source switch to %s") % config.conf["Access8Math"]["settings"]["speech_source"])

	@script(
		description=_("Braille source switch"),
		category=ADDON_SUMMARY,
	)
	def script_braille_source_switch(self, gesture):
		if config.conf["Access8Math"]["settings"]["braille_source"] == "Access8Math" and mathPlayer:
			config.conf["Access8Math"]["settings"]["braille_source"] = "MathPlayer"
		elif config.conf["Access8Math"]["settings"]["braille_source"] == "MathPlayer":
			config.conf["Access8Math"]["settings"]["braille_source"] = "Access8Math"
		else:
			config.conf["Access8Math"]["settings"]["braille_source"] = "Access8Math"
		ui.message(_("MathML braille source switch to %s") % config.conf["Access8Math"]["settings"]["braille_source"])

	@script(
		description=_("Interact source switch"),
		category=ADDON_SUMMARY,
	)
	def script_interact_source_switch(self, gesture):
		if config.conf["Access8Math"]["settings"]["interact_source"] == "Access8Math" and mathPlayer:
			config.conf["Access8Math"]["settings"]["interact_source"] = "MathPlayer"
		elif config.conf["Access8Math"]["settings"]["interact_source"] == "MathPlayer":
			config.conf["Access8Math"]["settings"]["interact_source"] = "Access8Math"
		else:
			config.conf["Access8Math"]["settings"]["interact_source"] = "Access8Math"
		ui.message(_("MathML interact source switch to %s") % config.conf["Access8Math"]["settings"]["interact_source"])

	@script(
		description=_("Pop up the editor"),
		category=ADDON_SUMMARY,
		gesture="kb:NVDA+alt+e",
	)
	def script_editor_popup(self, gesture):
		def show():
			obj = api.getFocusObject()
			document = obj.makeTextInfo(textInfos.POSITION_ALL)
			editor_content = document.text
			self.editor_popup(editor_content)
		wx.CallAfter(show)

	def editor_popup(self, editor_content):
		"""global editor_dialog
		if editor_dialog:
			editor_dialog.Raise()
			return"""

		parent = gui.mainFrame
		frame = EditorFrame(parent=parent)
		frame.control.SetValue(editor_content)
		frame.Show(True)

		"""with EditorDialog(parent=parent, value=editor_content) as dialog:
			editor_dialog = dialog
			dialog.ShowModal()
			editor_dialog = None"""

	def onReadingSettings(self, evt):
		gui.mainFrame._popupSettingsDialog(ReadingSettingsDialog, config.conf["Access8Math"])

	def onWritingSettings(self, evt):
		gui.mainFrame._popupSettingsDialog(WritingSettingsDialog, config.conf["Access8Math"])

	def onRuleSettings(self, evt):
		gui.mainFrame._popupSettingsDialog(RuleSettingsDialog, config.conf["Access8Math"])

	def onNewLanguageAdding(self, evt):
		NewLanguageAddingDialog(gui.mainFrame).Show()

	def onSpeechUnicodeDictionary(self, evt):
		gui.mainFrame._popupSettingsDialog(
			UnicodeDicDialog, config.conf["Access8Math"],
			language=config.conf["Access8Math"]["settings"]["language"], category='speech'
		)

	def onSpeechMathRule(self, evt):
		gui.mainFrame._popupSettingsDialog(
			MathRuleDialog, config.conf["Access8Math"],
			language=config.conf["Access8Math"]["settings"]["language"], category='speech'
		)

	def onBrailleUnicodeDictionary(self, evt):
		gui.mainFrame._popupSettingsDialog(
			UnicodeDicDialog, config.conf["Access8Math"],
			language=config.conf["Access8Math"]["settings"]["language"], category='braille'
		)

	def onBrailleMathRule(self, evt):
		gui.mainFrame._popupSettingsDialog(
			MathRuleDialog, config.conf["Access8Math"],
			language=config.conf["Access8Math"]["settings"]["language"], category='braille'
		)

	def onEditor(self, editor_content):
		self.editor_popup("")

	def onCleanWorkspace(self, evt):
		for item in [
			os.path.join(PATH, 'web', 'data'),
			os.path.join(PATH, 'web', 'export'),
			os.path.join(PATH, 'web', 'review'),
		]:
			try:
				shutil.rmtree(item)
			except:
				pass

		locale = os.path.join(PATH, 'locale')
		for dirPath, dirNames, fileNames in os.walk(locale):
			for item in fileNames:
				item = os.path.join(dirPath, item)
				try:
					if os.path.isfile(item) and ('_user.dic' in item or '_user.rule' in item):
						os.remove(item)
				except:
					pass

		gui.messageBox(_("Workspace has already been cleaned"), _("Clean Workspace"), wx.OK)

	def onAbout(self, evt):
		gui.messageBox(aboutMessage, _("About Access8Math"), wx.OK)
