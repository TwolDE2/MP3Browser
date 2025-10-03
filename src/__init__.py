from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from gettext import bindtextdomain, dgettext, gettext

PluginLanguageDomain = "MP3Browser"
PluginLanguagePath = "Extensions/MP3Browser/locale"


def localeInit():
	bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	if (translated := dgettext(PluginLanguageDomain, txt)) != txt:
		return translated
	else:
		return gettext(txt)


localeInit()
language.addCallback(localeInit)
