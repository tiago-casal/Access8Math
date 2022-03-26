import tones

import sys
import os
import wx

import addonHandler
import gui

addonHandler.initTranslation()

wildcard = \
	"Text (*.txt)|*.txt|"\
	"All (*.*)|*.*"

class EditorFrame(wx.Frame):
	_instances = []
	@classmethod
	def closeAll(cls):
		for item in cls._instances:
			try:
				item.Destroy()
			except:
				pass

	"""def __new__(cls, *args, **kwargs):
		obj = super().__new__(cls, *args, **kwargs)
		cls._instances.append(obj)
		return obj"""

	def __init__(self, parent, filename=_("new document")):
		style = wx.DEFAULT_FRAME_STYLE & (~wx.CLOSE_BOX)
		super(EditorFrame, self).__init__(parent, size=(400, 300), style=style)
		# cls._instances.append(self)

		self.parent = parent
		self.dirname  = "."
		self.filename = filename
		self.modify = False

		# Simplified init method.	   
		self.CreateInteriorWindowComponents()
		self.CreateExteriorWindowComponents()
		self.CenterOnScreen()

		Hotkey(self)

	def SetTitle(self):
		super(EditorFrame, self).SetTitle(_("%s - Access8Math Editor") % self.filename)

	def CreateInteriorWindowComponents(self):
		self.control = wx.TextCtrl(self, -1, value="", style=wx.TE_MULTILINE)
		self.control.Bind(wx.EVT_TEXT, self.OnTextChanged)

	def CreateExteriorWindowComponents(self):
		self.SetTitle()

		# frameIcon = wx.Icon(os.path.join(self.icons_dir,
			# "icon_wxWidgets.ico"),
			# type=wx.BITMAP_TYPE_ICO)
		# self.SetIcon(frameIcon)

		self.CreateMenu()
		self.CreateStatusBar()
		self.BindEvents()

	def CreateMenu(self):
		menuBar = wx.MenuBar()

		fileMenu = wx.Menu()

		for id, label, helpText, handler in \
			[
			(wx.ID_NEW, _("&New"), _("Open a new editor."), self.OnNew),
			(wx.ID_OPEN, _("&Open..."), _("Open a new file."), self.OnOpen),
			(wx.ID_SAVE, _("&Save"), _("Save the current file."), self.OnSave),
			(wx.ID_SAVEAS, _("Save &As..."), _("Save the file under a different name."), self.OnSaveAs),
			(wx.ID_ANY, _("Re&load from Disk"), _("Reload the file from disk."), self.OnReload),
			(wx.ID_EXIT, _("E&xit"), _("Terminate the program."), self.OnExit)
		]:
			if id == None:
				fileMenu.AppendSeparator()
			else:
				item = fileMenu.Append(id, label, helpText)

				# Bind some events to an events handler.
				self.Bind(wx.EVT_MENU, handler, item)

		# Add the fileMenu to the menuBar.
		menuBar.Append(fileMenu, _("&File"))

		# Add the menuBar to the frame.
		self.SetMenuBar(menuBar)

	def BindEvents(self):
		self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

	def DefaultFileDialogOptions(self):
		return dict(
			defaultFile=self.filename,
			defaultDir=self.dirname,
			wildcard=wildcard,
		)
   
	def AskUserForFilename(self, **dialogOptions):
		with wx.FileDialog(self, **dialogOptions) as dialog:
			if dialog.ShowModal() == wx.ID_OK:
				userProvidedFilename = True
				self.filename = dialog.GetFilename()
				self.dirname = dialog.GetDirectory()
				# Update the window title with the new filename.
				self.SetTitle() 
			else:
				userProvidedFilename = False
		# dialog.Destroy()
		return userProvidedFilename

	def OnNew(self, event):
		frame = self.__class__(parent=self.parent)
		frame.Show(True)

	def OnOpen(self, event):
		if self.AskUserForFilename(message=_("Open file"), style=wx.FD_OPEN, **self.DefaultFileDialogOptions()):
			with open(os.path.join(self.dirname, self.filename), 'r', encoding='utf-8') as file:
				self.control.SetValue(file.read())
			self.modify = False

	def OnSave(self, event):
		if self.dirname  == "." or self.filename == _("new document"):
			if self.AskUserForFilename(message=_("Save file"), style=wx.FD_SAVE, **self.DefaultFileDialogOptions()):
				with open(os.path.join(self.dirname, self.filename), 'w', encoding='utf-8') as file:
					file.write(self.control.GetValue())
				self.modify = False
		else:
			with open(os.path.join(self.dirname, self.filename), 'w', encoding='utf-8') as file:
				file.write(self.control.GetValue())
			self.modify = False

	def OnSaveAs(self, event):
		if self.AskUserForFilename(message=_("Save file"), style=wx.FD_SAVE, **self.DefaultFileDialogOptions()):
			with open(os.path.join(self.dirname, self.filename), 'w', encoding='utf-8') as file:
				file.write(self.control.GetValue())
			self.modify = False

	def OnReload(self, event):
		if self.dirname  == "." or self.filename == _("new document"):
			pass
		else:
			with open(os.path.join(self.dirname, self.filename), 'r', encoding='utf-8') as file:
				self.control.SetValue(file.read())
			self.modify = False

	def OnExit(self, event):
		if self.modify:
			if self.dirname  == "." or self.filename == _("new document"):
				path = ' "' + self.filename + '"'
			else:
				path = ' "' + os.path.join(self.dirname, self.filename) + '"'
			val = gui.messageBox(
				# Translators: The message displayed
				_("Save file{path} ?").format(path=path),
				# Translators: The title of the dialog
				_("Save"),
				wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL | wx.ICON_QUESTION, self
			)
			if val == wx.YES:
				self.OnSave(event)
				if not self.modify:
					self.Destroy()
			elif val == wx.NO:
				self.Destroy()
		else:
			self.Destroy()

	def OnCloseWindow(self, event):
		pass
		# self.Destroy()

	def Destroy(self):
		super().Destroy()
		# self.__class__._instances.remove(self)

	def OnTextChanged(self, event):
		self.modify = True


class Hotkey(object):
	def __init__(self, obj):
		self.obj = obj
		self.obj.control.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
		self.obj.control.Bind(wx.EVT_KEY_UP, self.onKeyUp)

		self.key_down = set([])
		self.key_map_action = [
			{
				'key': [wx.WXK_CONTROL, ord('N')],
				'action': self.OnNew,
			},
			{
				'key': [wx.WXK_CONTROL, ord('O')],
				'action': self.OnOpen,
			},
			{
				'key': [wx.WXK_CONTROL, ord('S')],
				'action': self.OnSave,
			},
			{
				'key': [wx.WXK_CONTROL, ord('W')],
				'action': self.OnExit,
			},
			{
				'key': [wx.WXK_ALT, wx.WXK_F4],
				'action': self.OnExit,
			},
		]

	def OnNew(self, event):
		self.obj.OnNew(event)

	def OnOpen(self, event):
		self.obj.OnOpen(event)

	def OnSave(self, event):
		self.obj.OnSave(event)

	def OnSaveAs(self, event):
		self.obj.OnSaveAs(event)

	def OnReload(self, event):
		self.obj.OnReload(event)

	def OnExit(self, event):
		self.obj.OnExit(event)

	def onKeyDown(self, event):
		keycode = event.GetKeyCode()
		self.key_down.add(keycode)
		action = False
		for item in self.key_map_action:
			if self.key_down == set(item['key']):
				self.key_down.clear()
				item['action'](event)
				action = True
				break
		if not action:
			event.Skip()

	def onKeyUp(self, event):
		keycode = event.GetKeyCode()	
		try:
			self.key_down.remove(keycode)
		except KeyError:
			self.key_down.clear()
		event.Skip()
