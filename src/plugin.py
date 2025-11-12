# Decompiled from: Python 3.10.4 (main, Jun 29 2022, 12:14:53) [GCC 11.2.0]

# This plugin is licensed under the Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
# To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to CreativeCommons, 559 Nathan Abbott Way, Stanford, California 94305, USA

from os import linesep, makedirs, remove, rename, rmdir, statvfs, walk
from os.path import exists, getsize, join, normpath
import datetime, socket, time
import random
from re import findall, search, split, sub, DOTALL

from mutagen.mp3 import MP3, HeaderNotFoundError
from mutagen.id3 import ID3, ID3NoHeaderError, APIC, PictureType
from mutagen.easyid3 import EasyID3
print(f"[mp3browser] ************* {EasyID3.valid_keys.keys()}")

from urllib.parse import unquote_plus
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import parse_qs

#from requests import get
import requests
from requests.exceptions import HTTPError
from twisted.internet.reactor import callInThread

from twisted.web import client, error

from enigma import addFont, eConsoleAppContainer, eListboxPythonMultiContent, ePoint, eServiceReference, eSize, eTimer, getDesktop, gFont, gMainDC, iPlayableService, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, RT_WRAP
from Components.ActionMap import ActionMap
from Components.config import config, configfile, ConfigDirectory, getConfigListEntry, ConfigSelection, ConfigSlider, ConfigSubsection, ConfigText 
from Components.ConfigList import ConfigListScreen
from Components.FileList import FileList
from Components.Harddisk import harddiskmanager
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap, MultiPixmap
from Components.ScrollLabel import ScrollLabel
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Slider import Slider
from Components.Sources.List import List
from Plugins.Plugin import PluginDescriptor
from Screens.ChannelSelection import ChannelSelection
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Setup import Setup
from Screens.Standby import TryQuitMainloop
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Session import SessionObject
from skin import applySkinFactor, fonts, parameters
from Tools.Directories import copyfile, fileExists, fileReadLine, fileReadLines, fileWriteLine, fileWriteLines

def getMountChoices():
	choices = []
	for p in harddiskmanager.getMountedPartitions():
		if exists(p.mountpoint):
			d = normpath(p.mountpoint)
			entry = (p.mountpoint, d)
			if p.mountpoint != "/" and entry not in choices:
				choices.append(entry)
	choices.sort()
	return choices

def getMountDefault(choices):
	choices = {x[1]: x[0] for x in choices}
	default = choices.get("/media/hdd") or choices.get("/media/usb")
	print("[MP3Browser][getMountDefault] default, choices", default, "   ", choices)
	return default

lang = language.getLanguage()[:2]
choices = getMountChoices()
config.plugins.mp3browser = ConfigSubsection()
config.plugins.mp3browser.mp3folder = ConfigSelection(choices=choices, default=getMountDefault(choices))
config.plugins.mp3browser.cachefolder = ConfigSelection(default="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/cache", choices=[("/media/usb/mp3browser/cache", "/media/usb"), ("/media/hdd/mp3browser/cache", "/media/hdd"), ("/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/cache", "Flash")])
config.plugins.mp3browser.DBfolder = ConfigSelection(default="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/database", choices=[("/media/usb/mp3browser/database", "/media/usb"), ("/media/hdd/mp3browser/database", "/media/hdd"), ("/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/database", "Flash")])
config.plugins.mp3browser.language = ConfigSelection(default="en", choices=[("en", "English"), ("de", "German"), ("es", "Spanish")])
config.plugins.mp3browser.background = ConfigSelection(default="background", choices=[("background", "Background"), ("player", "Media Player")])
config.plugins.mp3browser.showtv = ConfigSelection(default="show", choices=[("show", "Show"), ("hide", "Hide")])
config.plugins.mp3browser.sortorder = ConfigSelection(default="artist", choices=[("artist", "MP3 Artist A-Z"), ("artist_reverse", "MP3 Artist Z-A"), ("album", "MP3 Album Title A-Z"), ("album_reverse", "MP3 Album Title Z-A"), ("track", "MP3 Track Title A-Z"), ("track_reverse", "MP3 Track Title Z-A"), ("genre", "MP3 Genre A-Z"), ("genre_reverse", "MP3 Genre Z-A"), ("year", "MP3 Release Date Ascending"), ("year_reverse", "MP3 Release Date Descending"), ("date", "MP3 Creation Date Ascending"), ("date_reverse", "MP3 Creation Date Descending"), ("folder", "MP3 Folder Ascending"), ("folder_reverse", "MP3 Folder Descending"), ("runtime", "MP3 Runtime Ascending"), ("runtime_reverse", "MP3 Runtime Descending")])
config.plugins.mp3browser.shuffle = ConfigSelection(default="no", choices=[("yes", "Automatic"), ("no", "Button 5")])
config.plugins.mp3browser.screensaver = ConfigSelection(default="no", choices=[("yes", "Automatic"), ("no", "Button 2")])
config.plugins.mp3browser.lastmp3 = ConfigSelection(default="yes", choices=[("yes", "Yes"), ("no", "No"), ("folder", "Folder Selection")])
config.plugins.mp3browser.lastfilter = ConfigSelection(default="no", choices=[("no", "No"), ("yes", "Yes")])
config.plugins.mp3browser.showfolder = ConfigSelection(default="no", choices=[("no", "No"), ("yes", "Yes")])
config.plugins.mp3browser.discogs = ConfigSelection(default="show", choices=[("show", "Show"), ("hide", "Hide")])
config.plugins.mp3browser.discogstoken = ConfigText(default=" ", fixed_size=False)
config.plugins.mp3browser.font = ConfigSelection(default="yes", choices=[("yes", "Yes"), ("no", "No")])
config.plugins.mp3browser.showinfo = ConfigSelection(default="info", choices=[("oninfo", "Info Button"), ("info", "Show Info"), ("always", "Show Info & Lyrics")])  # toggle 0,1,2
config.plugins.mp3browser.metrixlist = ConfigSelection(default="all", choices=[("all", "Artist & Track Title"), ("artist", "Artist")])
config.plugins.mp3browser.autocheck = ConfigSelection(default="yes", choices=[("yes", "Yes"), ("no", "No")])
config.plugins.mp3browser.showmenu = ConfigSelection(default="no", choices=[("no", "No"), ("yes", "Yes")])
config.plugins.mp3browser.autoupdate = ConfigSelection(default="no", choices=[("no", "No"), ("yes", "Yes")])
config.plugins.mp3browser.reset = ConfigSelection(default="no", choices=[("no", "No"), ("yes", "Yes")])
config.plugins.mp3browser.style = ConfigSelection(default="coverwall", choices=[("coverwall", "Coverwall"), ("metrix", "Metrix")])
config.plugins.mp3browser.transparency = ConfigSlider(default=255, limits=(100, 255))
config.plugins.mp3browser.hideupdate = ConfigSelection(default="yes", choices=[("yes", "Yes"), ("no", "No")])
config.plugins.mp3browser.cleanup = ConfigSelection(default="no", choices=[("no", "<Cleanup>"), ("no", "<Cleanup>")])
config.plugins.mp3browser.backup = ConfigSelection(default="no", choices=[("no", "<Backup>"), ("no", "<Backup>")])
config.plugins.mp3browser.restore = ConfigSelection(default="no", choices=[("no", "<Restore>"), ("no", "<Restore>")])
config.plugins.mp3browser.color = ConfigSelection(default="#007895BC", choices=[
    ("#007895BC", "Default"),
    ("#00F0A30A", "Amber"),
    ("#00825A2C", "Brown"),
    ("#000050EF", "Cobalt"),
    ("#00911D10", "Crimson"),
    ("#001BA1E2", "Cyan"),
    ("#00008A00", "Emerald"),
    ("#0070AD11", "Green"),
    ("#006A00FF", "Indigo"),
    ("#00A4C400", "Lime"),
    ("#00A61D4D", "Magenta"),
    ("#0076608A", "Mauve"),
    ("#006D8764", "Olive"),
    ("#00C3461B", "Orange"),
    ("#00F472D0", "Pink"),
    ("#00E51400", "Red"),
    ("#007A3B3F", "Sienna"),
    ("#00647687", "Steel"),
    ("#00149BAF", "Teal"),
    ("#004176B6", "Tufts"),
    ("#006C0AAB", "Violet"),
    ("#00BF9217", "Yellow")
])

config.plugins.mp3browser.metrixcolor = ConfigSelection(default="0x00000000", choices=[
    ("0x00000000", "Skin Default"),
    ("0x00F0A30A", "Amber"),
    ("0x007895BC", "Blue"),
    ("0x00825A2C", "Brown"),
    ("0x000050EF", "Cobalt"),
    ("0x00911D10", "Crimson"),
    ("0x001BA1E2", "Cyan"),
    ("0x00008A00", "Emerald"),
    ("0x0070AD11", "Green"),
    ("0x006A00FF", "Indigo"),
    ("0x00BB0048", "Magenta"),
    ("0x0076608A", "Mauve"),
    ("0x006D8764", "Olive"),
    ("0x00C3461B", "Orange"),
    ("0x00F472D0", "Pink"),
    ("0x00E51400", "Red"),
    ("0x007A3B3F", "Sienna"),
    ("0x00647687", "Steel"),
    ("0x00149BAF", "Teal"),
    ("0x004176B6", "Tufts"),
    ("0x006C0AAB", "Violet"),
    ("0x00BF9217", "Yellow")
])
calledBrowser = config.plugins.mp3browser.style.value
default_png = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/browser/default.png"
defaultfolder_png = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/browser/default_folder.png"
  
addFont("/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/font/Sans.ttf", "Sans", 100, False)
addFont("/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/font/MetrixHD.ttf", "Metrix", 100, False)


def threadGetPage(url=None, file=None, key=None, success=None, fail=None, *args, **kwargs):
	print("[MP3Browser][threadGetPage] url, file, key, args, kwargs", url, "   ", file, "   ", key, "   ", args, "   ", kwargs)
	authHeaders = {"User-Agent", "Twisted Client"}
	myheaders = {"User-Agent": "Twisted Client Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",}    
	try:
		response = requests.get(url, headers=myheaders)
		response.raise_for_status()
		if file is None:
			success(response.content)
		elif key is not None:
			success(response.content, file, key)
		else:
			success(response.content, file)
	except HTTPError as httperror:
		print("[MP3Browser][threadGetPage] Http error: ", httperror)
		if fail is not None:
			fail(httperror)
	except Exception as error:
		print("[MP3Browser][threadGetPage] error: ", error)
		if fail is not None:
			fail(error)

			
def threadGetjpg(url=None, artistntrack=None, success=None, fail=None, *args, **kwargs):
	authHeaders = {"User-Agent", "Twisted Client"}
	myheaders = {"User-Agent": "Twisted Client Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",}    
	try:
		response = requests.get(url, headers=myheaders)
		response.raise_for_status()
		success(response.content, artistntrack)
	except HTTPError as httperror:
		print("[MP3Browser][threadGetPage] Http error: ", httperror)
		if fail is not None:
			fail(httperror)
	except Exception as error:
		print("[MP3Browser][threadGetPage] error: ", error)
		if fail is not None:
			fail(error)
	  
  
def skinScale(skin):
	def repl(m):
		factor = getDesktop(0).size().height()/720
		delimiter = ";" if m.group(1) == "font=" else ","
		spl = []
		for x in m.group(2).split(delimiter):
			spl.append(str(int(int(x)*factor)) if x.isdigit() else x)
		return m.group(1) + '"' + delimiter.join(spl) + '"'
	return sub('(position=|size=|font=)\"([^"]+)\"', repl, skin)  

def applySkinVars(skin, dict):
	for key in list(dict.keys()):
		try:
			skin = skin.replace('{' + key + '}', dict[key])
		except Exception as e:
			print(e, '@key=', key)
	return skin

def transHTML(text):
	text = text.replace("&nbsp;", " ").replace("&szlig;", "ss").replace("&quot;", """).replace("&ndash;", "-").replace("&Oslash;", "").replace("&bdquo;", """).replace("&ldquo;", """).replace("&rsquo;", """).replace("&gt;", ">").replace("&lt;", "<")
	text = text.replace("&copy;.*", " ").replace("&amp;", "&").replace("&uuml;", "Ã¼").replace("&auml;", "Ã¤").replace("&ouml;", "Ã¶").replace("&eacute;", "é").replace("&hellip;", "...").replace("&egrave;", "è").replace("&agrave;", "à")
	text = text.replace("&Uuml;", "Ue").replace("&Auml;", "Ae").replace("&Ouml;", "Oe").replace("&#034;", """).replace("&#34;", """).replace("&#38;", "und").replace("&#039;", """).replace("&#39;", """).replace("&#133;", "...").replace("&#196;", "Ã„").replace("&#214;", "Ã–").replace("&#220;", "Ãœ").replace("&#223;", "ÃŸ").replace("&#228;", "Ã¤").replace("&#246;", "Ã¶").replace("&#252;", "Ã¼")
	return text


def transCHARTLYRICS(text):
	text = text.replace(" ", "+").replace("&", "+").replace(".", "+").replace(",", "+").replace(""", "").replace("(", "").replace(")", "").replace("[", "").replace("]", "").replace("!", "").replace(":", "").replace(";", "").replace(""", "").replace("|", "").replace("~", "").replace("?", "").replace("!", "")
	return text


def transLYRICSTIME(text):
	text = text.replace(" ", "-").replace(".", "-").replace(""", "-").replace("&", "and").replace(",", "").replace("(", "").replace(")", "").replace("[", "").replace("]", "").replace("!", "").replace(":", "").replace(";", "").replace(""", "").replace("|", "").replace("~", "").replace("?", "").replace("!", "").replace("---", "-").replace("--", "-")
	return text


def transDISCOGS(text):
	text = text.replace("\\u00a0", " ").replace("\\u0026", "&").replace("\\u003c", "<").replace("\\u003e", ">").replace("\\u00b4", "´").replace("\\u00e9", "e").replace("\\u00e4", "ä").replace("\\u00c4", "Ä").replace("\\u00f6", "ö").replace("\\u00d6", "Ö").replace("\\u00fc", "ü").replace("\\u00dc", "Ü").replace("\\u00df", "ß").replace("\\u20ac", "€").replace("\\u0024", "$").replace("\\u00a3", "£")
	text = text.replace(b"\xa0", " ").replace(b"\xa9", "©").replace(b"\xae", "®").replace(b"\xb7", "\\*").replace("\\u2002", " ").replace("\\u2003", " ").replace("\\u2009", " ").replace("\\u2013", "-").replace("\\u2014", "--").replace("\\u2018", """).replace("\\u2019", """).replace("\\u201c", """).replace("\\u201d", """).replace("\\u2022", "•").replace("\\u2026", "...").replace("\\u2122", "™")
	text = text.replace("[a=", "")
	text = sub("\\[m=[0-9]+\\]", "Album#", text)
	text = sub("\\[.[0-9]+\\]", "Artist#", text)
	text = sub("\\[.*?\\]", "", text)
	text = text.replace("]", "").replace("\\"", """)
	return text

def databaseUpdate_core(MP3Database):
	print(f"[MP3Browser][databaseUpdate_core] entered MP3Database:{MP3Database}")
	nameList = []
	mp3List = []
	dateList = []
	artistList = []
	albumList = []
	numberList = []
	trackList = []
	yearList = []
	runtimeList = []
	bitrateList = []
	genreList = []
	posterList = []
	orphaned = 0
	lastArtist = ""
	lastPoster = ""
	lastPosterUrl = ""
	pngjpeg = ""
	mp3browserData = fileReadLine(MP3Database)
	inputMP3files = ":::"
	folder = config.plugins.mp3browser.mp3folder.value
	for root, dirs, files in walk(folder, topdown=False, onerror=None, followlinks=True):
		for name in files:
			if name.lower().endswith(".mp3"):
				# print(f"[MP3Browser][databaseUpdate_core] mp3 name:{name}")
				if search(r"[\uD800-\uDFFF]", name) is not None:
					name = name.encode("utf-8").decode("latin-1").encode("utf-8").decode("utf-8")	
				filename = join(root, name)
				inputMP3files = inputMP3files + filename + ":::"
				mp3 = sub("\\(|\\)|\\[|\\]|\\+|\\?", ".", name)
				if search(mp3, mp3browserData) is None:				 # do we have this name in MP3browser database?
					if name.lower().endswith(".mp3"):		 # if not is it mp3?
						mp3List.append(filename)		 # file name in input source DB, add to output mp3list
						dateList.append(str(datetime.datetime.now()))
						name = sub("\\.mp3|\\.MP3", "", name)
						nameList.append(name)
						tag = None
						artist = album = number = track = year = genre = runtime = bitrate = " "
						print(f"[MP3Browser][databaseUpdate_core] mp3 name:{name} filename:{filename}")
						try:
							tag = MP3(filename, ID3=EasyID3)
							if tag is not None:
								album = tag.get("album", ["n/a"])[0]
								artist = tag.get("artist", ["n/a"])[0]
								number = tag.get("tracknumber", ["n/a"])[0].split("/")[0]
								track = tag.get("title", [name])[0]
								genre = tag.get("genre", ["n/a"])[0]
								year = tag.get("date", ["n/a"])[0]
								runtime = str(datetime.timedelta(seconds=int(tag.info.length)))
								bitrate = str(tag.info.bitrate // 1000)
								bitrate = bitrate + " kbit/s"
						except (HeaderNotFoundError, ID3NoHeaderError) as e:
							print(f"[MP3Browser][databaseUpdate_core] HeaderNotFoundError ID3NoHeaderError:{e}")
							artist = name
							track = "Missing ID3 Header"
							album = "Missing ID3 Header"
							genre = "Missing ID3 Header"
						albumList.append(album)
						artistList.append(artist)
						numberList.append(number)
						trackList.append(track)
						genreList.append(genre)
						yearList.append(year)
						runtimeList.append(runtime)
						bitrateList.append(bitrate)
						artistntrack = transLYRICSTIME(artist + "-" + track)
						artistntrack = artistntrack.replace("/", "-")                            
						print(f"[MP3Browser][databaseUpdate_core] artist:{artist} artistntrack:{artistntrack} album:{album}")
						poster = join(config.plugins.mp3browser.cachefolder.value, artistntrack + ".jpg")

						if fileExists(poster):
							print(f"[MP3Browser][databaseUpdate_core] found poster:{poster}")
							posterurl = poster
							with open(poster, "rb") as fd:
								binData = fd.read()
							apic = APIC(data=binData,
        						encoding=0, # 3 is for utf-8
								type=PictureType.COVER_FRONT,
								desc="cover",
								mime="image/jpeg")
							tag = ID3(filename)
							if tag is not None:
								print("[MP3Browser][databaseUpdate_core] found poster .... adding tag filename:{filename}")
								try:
									tag["apic"] = apic
									tag.save()
								except Exception as e:
									print(f"[MP3Browser][databaseUpdate_core]2a artistntrack:{artistntrack} filename:{filename} poster:{poster}, length poster:{len(poster)}")
									print("[MP3Browser][databaseUpdate_core]2a exception writing tag.add artist", e)
						else:                                                             
							posterurl = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/default.png"
							try:
								tag = ID3(filename)
								poster = tag.getall("APIC")
								print(f"[MP3Browser][databaseUpdate_core]1b ID3 filename:{filename} length poster:{len(poster)}")
							except (HeaderNotFoundError, ID3NoHeaderError) as e:
								print("[MP3Browser][databaseUpdate_core]1b ID3 Header notfound",  e)
							print(f"[MP3Browser][databaseUpdate_core] ID3 artist:{artist} poster:{poster}")
							if len(poster) > 0:
								print(f"[MP3Browser][databaseUpdate_core] ID3 have poster for artist:{artist} poster:{poster} poster[0]:{poster[0]}")
								try:
									mime = poster[0].mime
									if mime.lower().endswith('png'):
										ext = '.png'
									else:
										ext = '.jpg'
								except Exception as err:
									print(f"[MP3Browser][databaseUpdate_core] no mime err:{err}")
									pass										
								print(f"[MP3Browser][databaseUpdate_core] mime:{mime} artist:{artist}")
								artistTrue = artist.split("/")[0]
								if not exists("config.plugins.mp3browser.cachefolder.value + '/' + artistTrue"):
									makedirs("config.plugins.mp3browser.cachefolder.value + '/' + artistTrue")
								posterurl = config.plugins.mp3browser.cachefolder.value + '/' + artistntrack + ext
								try:
									with open(posterurl, 'wb')as fd:
										fd.write(poster[0].data)
								except Exception as error:
									print(f"[MP3Browser][databaseUpdate_core] file write crash as {error}")	
								lastArtist = artist
								lastPoster = poster[0].data
								lastPosterUrl = posterurl
								pngjpeg = mime 
							else:
								print(f"[MP3Browser][databaseUpdate_core] no poster try last artist is same {artist}")							
								if artist == lastArtist:
									posterurl = lastPosterUrl
									apic = APIC(data=lastPoster,
										encoding=0, # 3 is for utf-8
										type=PictureType.COVER_FRONT,
										desc="cover",
										mime=pngjpeg)
									try:
										tag  = EasyID3(filename)
									except Exception as error:
										print(f"[MP3Browser][databaseUpdate_core] tag error as {error}")									
										tag = mutagen.File(path, easy=True)
										tag.add_tags()
									try:
										tag["apic"] = apic
										tag.save()
										print(f"[MP3Browser][databaseUpdate_core]1b success writing tag.add artist:{artist}")                                         
									except Exception as error:
										print(f"[MP3Browser][databaseUpdate_core]1b exception writing tag.add artist-> {error}")
										pass                
						posterList.append(posterurl)
	# print(f"[MP3Browser][databaseUpdate_core] inputMP3files:{inputMP3files}")
	mp3browserDBlist = fileReadLines(MP3Database)
	for folder in mp3browserData.split("\n"):
		mp3line = folder.split(":::")
		mp3Filename = ""
		if mp3line == " " or len(mp3line) < 5:
			continue     
		mp3Filename = mp3line[1]	# location of filename in mp3browser database folder
		mp3Filename = sub("\\(|\\)|\\[|\\]|\\+|\\?", ".", mp3Filename)
		mp3FilenameSearch = mp3Filename.replace(".mp3", "").replace(".MP3", "")
		xx = search(mp3FilenameSearch, inputMP3files)
		if search(mp3FilenameSearch, inputMP3files) is None:	# search for database folder filename in input files
			print(f"[MP3Browser][databaseUpdate_core] mp3browser orphaned database mp3Filename:{mp3Filename} xx:{xx}")
			orphaned += 1
			try:
				mp3browserDBlist.remove(folder)							# - so remove folder in mp3browser database
			except Exception as error:
				print(f"[MP3Browser][databaseUpdate_core] unable to delete folder {folder} from database {error}")
		else:
			continue	# if not orphaned
	if orphaned != 0:
		fileWriteLines(MP3Database, mp3browserDBlist)
	del mp3browserDBlist
	del mp3browserData
	del inputMP3files
	dbcount = 0
	dbcountmax = len(mp3List)-1
	print(f"[MP3Browser][databaseUpdate_core] orphaned:{orphaned} dbcountmax:{dbcountmax+1}")	
	if len(mp3List) == 0:			# no new db folders's
		databaseSort(MP3Database)	
		return(False, orphaned, 0)
	else:
		dbcount = 0
		dbcountmax = len(mp3List)
		print(f"[MP3Browser][databaseUpdate_core] orphaned:{orphaned} dbcountmax:{dbcountmax+1}")
		f = open(MP3Database, "a")		# open mp3browser database at end of database file
		while dbcount < dbcountmax:
			try:
				print(f"[MP3Browser][databaseUpdate_core] 2 dbcount:{dbcount} dbcountmax:{dbcountmax} nameList[(dbcount)]:{nameList[(dbcount)]} mp3List[(dbcount)]:{mp3List[(dbcount)]}")
				data = nameList[(dbcount)] + ":::" + mp3List[(dbcount)] + ":::" + dateList[(dbcount)] + ":::" + artistList[(dbcount)] + ":::" + albumList[(dbcount)] + ":::" + numberList[(dbcount )] + ":::" + trackList[(dbcount)] + ":::" + yearList[(dbcount )] + ":::" + genreList[(dbcount)] + ":::" + runtimeList[(dbcount)] + ":::" + bitrateList[(dbcount)] + ":::" + posterList[(dbcount)] + ":::\n"
				f.write(data)			# write new data at end of database file
			except IndexError as error:
				print(f"[MP3Browser][databaseUpdate_core][write database]2 Indexerror {error}")
			dbcount += 1
		print(f"[MP3Browser][databaseUpdate_core] 3 dbcount:{dbcount} dbcountmax:{dbcountmax}")
		f.close()
		databaseSort(MP3Database)
		dbcountmax +=1
		return(True, orphaned, dbcountmax)

def databaseSort(database):
	sortorder = config.plugins.mp3browser.sortorder.value
	lines = fileReadLines(database)
	print(f"[MP3Browser][databaseSort] sortorder:{sortorder}, database:{database} lengthlines:{len(lines)}")
	if len(lines) != 0:
		if sortorder == "artist":
			newLinesSorted = sorted(lines, key=lambda line: line.split(":::")[3].replace("The ", "").replace("Der ", "").replace("Die ", "").replace("Das ", "").lower())
		elif sortorder == "artist_reverse":
			 newLinesSorted = sorted(lines, key=lambda line: line.split(":::")[3].replace("The ", "").replace("Der ", "").replace("Die ", "").replace("Das ", "").lower(), reverse=True)
		elif sortorder == "album":
			 newLinesSort = sorted(lines, key=lambda line: line.split(":::")[5].zfill(2))
			 newLinesSorted = sorted(newLinesSort, key=lambda line: line.split(":::")[4].replace("The ", "").replace("Der ", "").replace("Die ", "").replace("Das ", "").lower())
		elif sortorder == "album_reverse":
			 newLinesSort = sorted(lines, key=lambda line: line.split(":::")[5].zfill(2))
			 newLinesSorted = sorted(newLinesSort, key=lambda line: line.split(":::")[4].replace("The ", "").replace("Der ", "").replace("Die ", "").replace("Das ", "").lower(), reverse=True)
		elif sortorder == "track":
			 newLinesSorted = sorted(lines, key=lambda line: line.split(":::")[6].replace("The ", "").replace("Der ", "").replace("Die ", "").replace("Das ", "").lower())
		elif sortorder == "track_reverse":
			 newLinesSorted = sorted(lines, key=lambda line: line.split(":::")[6].replace("The ", "").replace("Der ", "").replace("Die ", "").replace("Das ", "").lower(), reverse=True)
		elif sortorder == "genre":
			 newLinesSorted = sorted(lines, key=lambda line: line.split(":::")[8])
		elif sortorder == "genre_reverse":
			 newLinesSorted = sorted(lines, key=lambda line: line.split(":::")[8], reverse=True)
		elif sortorder == "year":
			 newLinesSorted = sorted(lines, key=lambda line: line.split(":::")[7])
		elif sortorder == "year_reverse":
			 newLinesSorted = sorted(lines, key=lambda line: line.split(":::")[7], reverse=True)
		elif sortorder == "date":
			 newLinesSorted = sorted(lines, key=lambda line: line.split(":::")[2])
		elif sortorder == "date_reverse":
			 newLinesSorted = sorted(lines, key=lambda line: line.split(":::")[2], reverse=True)
		elif sortorder == "folder":
			 newLinesSorted = sorted(lines, key=lambda line: line.split(":::")[1])
		elif sortorder == "folder_reverse":
			 newLinesSorted = sorted(lines, key=lambda line: line.split(":::")[1], reverse=True)
		elif sortorder == "runtime":
			 newLinesSorted = sorted(lines, key=lambda line: line.split(":::")[9])
		elif sortorder == "runtime_reverse":
			 newLinesSorted = sorted(lines, key=lambda line: line.split(":::")[9], reverse=True)
		fileWriteLines(database + ".sorted", newLinesSorted)
		# copyfile(database + ".sorted", database)
		# remove(database + ".sorted")
		rename(database + ".sorted", database)	
		print(f"[MP3Browser][databaseSort] 2 database.sorted:")

def filterFolderSetup():
	max = 25
	folder = config.plugins.mp3browser.mp3folder.value
	folders = []
	folders.append(folder[:-1])
	for root, dirs, files in walk(folder, topdown=False, onerror=None, followlinks=True):
		for name in dirs:
			folder = join(root, name)
			folders.append(folder)
			if len(folder) > max:
				max = len(folder)
	folders.sort()
	return folders, max	
	
def filterSetup(database, sequence):
	names = ""
	lines = fileReadLines(database)
	max = 25
	for line in lines:
		mp3line = line.split(":::")
		try:
			name = mp3line[sequence]
		except IndexError as e:
			name = " "
		if name != " ":
			names = names + name + ":::"

	selfnames = [ i for i in names.split(":::") ]
	selfnames.sort()
	selfnames.pop(0)
	try:
		last = selfnames[(-1)]
		for i in range(len(selfnames) - 2, -1, -1):
			if last == selfnames[i]:
				del selfnames[i]
			else:
				last = selfnames[i]
				if len(last) > max:
					max = len(last)
	except IndexError as e:
		print("[MP3Browser][filterSetup] selfnames Indexerror",  e)
	return selfnames, max
	
class mp3BrowserMetrix(Screen):
	skin = """
	<screen position="center,center" size="1280,720" flags="wfNoBorder" title="  " >
		<widget name="metrixback" position="40,25" size="620,670" alphatest="blend" transparent="1" zPosition="-1" />
		<widget name="metrixback2" position="660,40" size="570,640" alphatest="blend" transparent="1" zPosition="-1" />
		<widget render="Label" source="global.CurrentTime" position="1088,43" size="140,60" font="Metrix;50" foregroundColor="#FFFFFF" halign="left" transparent="1" zPosition="3">
	        <convert type="ClockToText">Default</convert>
		</widget>
		<widget render="Label" source="global.CurrentTime" position="916,54" size="161,27" font="{font};15" foregroundColor="#BBBBBB" halign="right" transparent="1" zPosition="3">
	        <convert type="ClockToText">Format:%A</convert>
		</widget>
		<widget render="Label" source="global.CurrentTime" position="916,81" size="161,29" font="{font};16" foregroundColor="#BBBBBB" halign="right" transparent="1" zPosition="3">
	        <convert type="ClockToText">Format:%e. %B</convert>
		</widget>
		<widget name="menu" position="579,655" size="81,40" alphatest="blend" transparent="1" zPosition="4" />
		<widget name="info" position="1149,640" size="81,40" alphatest="blend" transparent="1" zPosition="4" />
		<widget name="help" position="50,655" size="30,29" alphatest="blend" transparent="1" zPosition="4" />
		<widget name="pvr" position="240,655" size="30,29" alphatest="blend" transparent="1" zPosition="4" />
		<widget name="text" position="430,655" size="30,29" alphatest="blend" transparent="1" zPosition="4" />
		<widget name="text1" position="85,654" size="150,30" font="Metrix;22" transparent="1" zPosition="4" />
		<widget name="text2" position="275,654" size="150,30" font="Metrix;22" transparent="1" zPosition="4" />
		<widget name="text3" position="465,654" size="150,30" font="Metrix;22" transparent="1" zPosition="4" />
		<widget name="label" position="80,47" size="540,43" font="Metrix;35" foregroundColor="#FFFFFF" valign="center" transparent="1" zPosition="4" />
		<widget name="label2" position="80,90" size="540,30" font="Metrix;22" foregroundColor="#BBBBBB" valign="center" transparent="1" zPosition="4" />
		<widget name="label3" position="80,620" size="320,30" font="Metrix;22" foregroundColor="#BBBBBB" valign="center" transparent="1" zPosition="4" />
		<widget name="list" position="80,125" size="540,490" transparent="1" zPosition="4" />
		<widget name="yellow" position="50,649" size="30,46" alphatest="blend" transparent="1" zPosition="4" />
		<widget name="red" position="240,649" size="30,46" alphatest="blend" transparent="1" zPosition="4" />
		<widget name="green" position="430,649" size="30,46" alphatest="blend" transparent="1" zPosition="4" />
		<widget name="discogsartist" position="70,55" size="560,35" font="Metrix;28" foregroundColor="#FFFFFF" valign="center" transparent="1" zPosition="22" />
		<widget name="discogs" position="70,100" size="590,540" font="Metrix;22" foregroundColor="#FFFFFF" transparent="1" zPosition="22" />
		<widget name="googlePoster" position="675,166" size="540,405" alphatest="blend" transparent="1" zPosition="22" />
		<widget name="poster" position="722,247" size="150,150" zPosition="23" transparent="1" alphatest="blend" scaleFlags="scaleKeepAspect" />
		<widget name="posterback" position="675,200" size="245,245" zPosition="22" transparent="1" alphatest="on" scaleFlags="scaleKeepAspect" />
		<widget name="name" position="675,120" size="540,70" font="Metrix;28" foregroundColor="#FFFFFF" valign="center" transparent="1" zPosition="5" />
		<widget name="Artist" position="950,210" size="125,30" font="Metrix;22" foregroundColor="#BBBBBB" transparent="1" zPosition="6" />
		<widget name="artist" position="950,240" size="255,30" font="Metrix;22" foregroundColor="#FFFFFF" transparent="1" zPosition="7" />
		<widget name="Album" position="950,280" size="125,30" font="Metrix;22" foregroundColor="#BBBBBB" transparent="1" zPosition="8" />
		<widget name="album" position="950,310" size="255,30" font="Metrix;22" foregroundColor="#FFFFFF" transparent="1" zPosition="9" />
		<widget name="Year" position="950,350" size="100,30" font="Metrix;22" foregroundColor="#BBBBBB" transparent="1" zPosition="10" />
		<widget name="year" position="950,380" size="100,30" font="Metrix;22" foregroundColor="#FFFFFF" transparent="1" zPosition="11" />
		<widget name="Bitrate" position="1050,350" size="125,30" font="Metrix;22" foregroundColor="#BBBBBB" transparent="1" zPosition="12" />
		<widget name="bitrate" position="1050,380" size="125,30" font="Metrix;22" foregroundColor="#FFFFFF" transparent="1" zPosition="13" />
		<widget name="Runtime" position="950,420" size="125,30" font="Metrix;22" foregroundColor="#BBBBBB" transparent="1" zPosition="14" />
		<widget name="runtime" position="950,450" size="125,30" font="Metrix;22" foregroundColor="#FFFFFF" transparent="1" zPosition="15" />
		<widget name="Number" position="675,490" size="100,30" font="Metrix;22" foregroundColor="#BBBBBB" transparent="1" zPosition="16" />
		<widget name="number" position="675,520" size="100,30" font="Metrix;22" foregroundColor="#FFFFFF" transparent="1" zPosition="17" />
		<widget name="Track" position="775,490" size="125,30" font="Metrix;22" foregroundColor="#BBBBBB" transparent="1" zPosition="18" />
		<widget name="track" position="775,520" size="440,30" font="Metrix;22" foregroundColor="#FFFFFF" transparent="1" zPosition="19" />
		<widget name="Genre" position="675,560" size="125,30" font="Metrix;22" foregroundColor="#BBBBBB" transparent="1" zPosition="20" />
		<widget name="genre" position="675,590" size="540,30" font="Metrix;22" foregroundColor="#FFFFFF" transparent="1" zPosition="21" />
	</screen>"""

	def __init__(self, session, index, filter):
		print("[MP3BrowserMetrix][mp3BrowserMetrix] ")
		font = "Sans" if config.plugins.mp3browser.font.value == "yes" else "Regular"
		self.dict = {"font": font}
		self.skin = skinScale(applySkinVars(mp3BrowserMetrix.skin, self.dict))
		Screen.__init__(self, session)
		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.toogleHelp = self.session.instantiateDialog(helpScreen)
		self.showhelp = False
		self.hideflag = True
		self.fav = False
		self.ready = False		# config defined
		self.reset = False		# databse initialised
		self.autoupdate = False
		self.filter = filter
		self.index = index
		self.toggle = 0
		self.move = False if config.plugins.mp3browser.screensaver.value == "no" else True
		self.random = False if config.plugins.mp3browser.shuffle.value == "no" else True
		self.background = False if config.plugins.mp3browser.background.value == "player" else True
		self.showfolder = False if config.plugins.mp3browser.showfolder.value == "no" else True # default is No
		self.lang = config.plugins.mp3browser.language.value
		self.playready = False
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={iPlayableService.evEOF: self.nextMP3})
		self.ABC = "ABC"
		self.artist = ""
		self.artistold = ""
		self.artistdisco = ""
		self.track = ""
		self.trackold = ""
		self.profile = ""
		self.lyrics = ""
		self.lastArtistdisco = ""
		self.lastArtist = ""
		self.lastPoster = ""
		self.namelist = []
		self.mp3list = []
		self.datelist = []
		self.artistlist = []
		self.albumlist = []
		self.numberlist = []
		self.tracklist = []
		self.yearlist = []
		self.runtimelist = []
		self.bitratelist = []
		self.genrelist = []
		self.posterlist = []
		self["Artist"] = Label(_("Artist:"))
		self["Number"] = Label(_("Track#:"))
		self["Track"] = Label(_("Track:"))
		self["Year"] = Label(_("Year:"))
		self["Runtime"] = Label(_("Runtime:"))
		self["Album"] = Label(_("Album:"))
		self["Bitrate"] = Label(_("Bitrate:"))
		self["Genre"] = Label(_("Genre:"))
		self["name"] = Label()
		self["artist"] = Label()
		self["album"] = Label()
		self["number"] = Label()
		self["track"] = Label()
		self["year"] = Label()
		self["runtime"] = Label()
		self["bitrate"] = Label()
		self["genre"] = Label()
		self["text1"] = Label(_("Help"))
		self["text2"] = Label(_("Update"))
		self["text3"] = Label(_("Edit"))
		self["metrixback"] = Pixmap()
		self["metrixback2"] = Pixmap()
		self["poster"] = Pixmap()
		self["posterback"] = Pixmap()
		self["menu"] = Pixmap()
		self["info"] = Pixmap()
		self["help"] = Pixmap()
		self["pvr"] = Pixmap()
		self["text"] = Pixmap()
		self["discogsartist"] = Label()
		self["discogs"] = ScrollLabel()
		self["googlePoster"] = Pixmap()
		self.DiscogsNotBusy = True
		self["yellow"] = Pixmap()
		self["red"] = Pixmap()
		self["green"] = Pixmap()
		self["label"] = Label()
		self["label2"] = Label()
		self["label3"] = Label()
		self["list"] = ItemList([])
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActions", "ChannelSelectBaseActions", "HelpActions", "InfobarActions", "InfobarTeletextActions", "MovieSelectionActions", "MoviePlayerActions", "InfobarEPGActions", "NumberActions"], {"ok": self.ok, 
			"cancel": self.exit, 
			"right": self.rightDown, 
			"left": self.leftUp, 
			"down": self.down, 
			"up": self.up, 
			"nextBouquet": self.zap, 
			"prevBouquet": self.zap, 
			"nextMarker": self.gotoABC, 
			"prevMarker": self.gotoXYZ, 
			"red": self.switchStyle, 
			"yellow": self.config, 
			"green": self.showMP3, 
			"blue": self.hideScreen, 
			"contextMenu": self.config, 
			"showEventInfo": self.toggleInfo, 
			"EPGPressed": self.toggleInfo, 
			"startTeletext": self.databaseEdit, 
			"showMovies": self.databaseUpdate, 
			"showRadio": self.deleteMP3, 
			"leavePlayer": self.stop, 
			"1": self.showMP3, 
			"2": self.moveCovers, 
			"3": self.makeFav, 
			"4": self.showMP3, 
			"5": self.shuffleMP3, 
			"6": self.filterFolder, 
			"7": self.filterArtist, 
			"8": self.filterAlbum, 
			"9": self.filterGenre, 
			"0": self.gotoEnd, 
			"bluelong": self.showHelp, 
			"displayHelp": self.showHelp}, -1)
		self.movie_stop = config.usage.on_movie_stop.value
		self.movie_eof = config.usage.on_movie_eof.value
		config.usage.on_movie_stop.value = "quit"
		config.usage.on_movie_eof.value = "quit"
		self.database = config.plugins.mp3browser.DBfolder.value
		self.favorites = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/favorites"
		self.lastfilter = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/filter"
		self.lastfile = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/last"
		print(f"[onLayoutFinished] database:{config.plugins.mp3browser.DBfolder.value} mp3folder:{config.plugins.mp3browser.mp3folder.value}")
		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		print("[MP3Browser][databaseInitialisation] **** possible return from Browser setup or Initialisation")
		self.version = "2.0py3"
		if fileExists(self.database):
			size = getsize(self.database)
			if size < 10:
				remove(self.database)
		if config.plugins.mp3browser.metrixcolor.value == "0x00000000":
			self.backcolor = False
		else:
			self.backcolor = True
			self.back_color = int(config.plugins.mp3browser.metrixcolor.value, 16)
		self.metrixBackPNG = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/browser/metrix_back.png"
		self.metrixBack2PNG = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/browser/metrix_back2.png"
		if fileExists(self.metrixBackPNG) and fileExists(self.metrixBack2PNG):
			self["metrixback"].instance.setPixmapFromFile(self.metrixBackPNG)
			self["metrixback2"].instance.setPixmapFromFile(self.metrixBack2PNG)
			self["metrixback"].show()
			self["metrixback2"].show()
		posterback = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/browser/metrix_posterback.png"
		self["posterback"].instance.setPixmapFromFile(posterback)
		self["posterback"].show()
		key_menu = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/browser/key_menu.png"
		key_info = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/browser/key_info.png"
		key_help = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/browser/key_help.png"
		key_pvr = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/browser/key_pvr.png"
		key_text = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/browser/key_text.png"
		key_yellow = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/browser/key_yellow.png"
		key_red = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/browser/key_red.png"
		key_green = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/browser/key_green.png"
		self["menu"].instance.setPixmapFromFile(key_menu)
		self["info"].instance.setPixmapFromFile(key_info)
		self["help"].instance.setPixmapFromFile(key_help)
		self["pvr"].instance.setPixmapFromFile(key_pvr)
		self["text"].instance.setPixmapFromFile(key_text)
		self["yellow"].instance.setPixmapFromFile(key_yellow)
		self["red"].instance.setPixmapFromFile(key_red)
		self["green"].instance.setPixmapFromFile(key_green)
		self["yellow"].show()
		self["red"].hide()
		self["green"].hide()
		if config.plugins.mp3browser.showtv.value == "hide":
			self.session.nav.stopService()
		self.coverTimer = eTimer()
		self.coverTimer.callback.append(self.startMoveCovers)
		if fileExists(self.database):
			if self.index == 0:
				if config.plugins.mp3browser.lastfilter.value == "yes":
					self.filter = fileReadLine(self.lastfilter)
				if config.plugins.mp3browser.lastmp3.value == "yes":
					mp3 = fileReadLine(self.lastfile)
					if mp3.endswith("..."):
						self.index = -1
					else:
						mp3 = sub("\\(|\\)|\\[|\\]|\\+|\\?", ".", mp3)
						data = fileReadLine(self.database)
						count = 0
						for line in data.split("\n"):
							if self.filter in line:
								if search(mp3, line) is not None:
									self.index = count
									break
								count += 1

				elif config.plugins.mp3browser.lastmp3.value == "folder" and self.showfolder == True:
					self.index = -1
			self.reset = False
			self.makeMP3BrowserTimer = eTimer()
			print(f"[onLayoutFinished] mp3folder is :{config.plugins.mp3browser.mp3folder.value}")
			if config.plugins.mp3browser.autoupdate.value == "yes" and exists(config.plugins.mp3browser.mp3folder.value):
				self.autoupdate = True
				self.makeMP3BrowserTimer.callback.append(self.databaseUpdate_queryreturn(True))
			else:
				self.makeMP3BrowserTimer.callback.append(self.makeMP3(self.filter))
			self.makeMP3BrowserTimer.start(500, True)
		else:
			self.openTimer = eTimer()
			self.openTimer.callback.append(self.openInfo)
			self.openTimer.start(500, True)
		return

	def config(self):
		print(f"[MP3BrowserMetrix][config] **** self.ready:{self.ready}")	
		if self.ready == True:
			config.usage.on_movie_stop.value = self.movie_stop
			config.usage.on_movie_eof.value = self.movie_eof
			self.session.openWithCallback(self.checkConfig, mp3BrowserConfig)

	def openInfo(self):
		print("[MP3BrowserMetrix][checkDB] **** openInfo entered")	
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/reset"):
			self.session.openWithCallback(self.databaseInitialisation_queryreturn, MessageBox, _("The MP3 Browser Database will be build now. Depending on the number of your mp3s this can take several minutes.\n\nBuild MP3 Browser Database now?"), MessageBox.TYPE_YESNO)
		else:
			self.session.openWithCallback(self.databaseInitialisation, MessageBox, _("Before the Database will be build, check your settings in the setup of the plugin:\n\n- Check the path to the MP3 Folder\n- Change the Cache Folder to your hard disk drive or usb stick."), MessageBox.TYPE_YESNO)

	def checkConfig(self):
		print("[MP3BrowserMetrix][checkConfig] **** return from Browser setup")	
		global calledBrowser
		if config.plugins.mp3browser.style.value != calledBrowser:
			calledBrowser = config.plugins.mp3browser.style.value 
			if config.plugins.mp3browser.style.value == "metrix":
				self.session.openWithCallback(self.close, mp3BrowserMetrix, 0, ":::")
			else:
				self.session.openWithCallback(self.close, mp3Browser, 0, ":::")
		else:
			self.ready = True
			self.databaseUpdate()	

	def checkDB(self):
		print("[MP3BrowserMetrix][checkDB] **** return from Browser setup")	
		global calledBrowser
		if config.plugins.mp3browser.style.value != calledBrowser:
			calledBrowser = config.plugins.mp3browser.style.value 
			if config.plugins.mp3browser.style.value == "metrix":
				self.session.openWithCallback(self.close, mp3BrowserMetrix, 0, ":::")
			else:
				self.session.openWithCallback(self.close, mp3Browser, 0, ":::")
		else:
			self.ready = True
			self.databaseUpdate()	

	def databaseInitialisation(self, answer):
		print(f"[MP3BrowserMetrix][databaseInitialisation] **** entered answer:{answer}")	
		open("/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/reset", "w").close()
		config.usage.on_movie_stop.value = self.movie_stop
		config.usage.on_movie_eof.value = self.movie_eof
		print("[MP3BrowserMetrix][databaseInitialisation] **** entry to Browser setup")		
		if answer is True:
			self.session.openWithCallback(self.checkDB, mp3BrowserConfig)
		else:
			self.databaseInitialisation_queryreturn(True)

	def databaseInitialisation_queryreturn(self, answer):
		print(f"[MP3BrowserMetrix][databaseInitialisation_return] **** entered answer:{answer}")
		if answer is True:
			self.reset = True
			if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/reset"):
				remove("/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/reset")
			open(self.database, "w").close()
			self.makeMP3BrowserTimer = eTimer()
			self.resetTimer = eTimer()
			self.resetTimer.callback.append(self.databaseUpdate_queryreturn(True))
			self.resetTimer.start(500, True)


	def databaseUpdate(self):
		print(f"[MP3BrowserMetrix][databaseUpdate] **** entered")
		if self.ready == True:
			if exists(config.plugins.mp3browser.mp3folder.value) and exists(config.plugins.mp3browser.cachefolder.value):
				self.session.openWithCallback(self.databaseUpdate_queryreturn, MessageBox, _("\nUpdate MP3 Browser Database?"), MessageBox.TYPE_YESNO)
			elif exists(config.plugins.mp3browser.cachefolder.value):
				self.session.open(MessageBox, _("\nMP3 Folder %s not reachable:\nMP3 Browser Database Update canceled.") % str(config.plugins.mp3browser.mp3folder.value), MessageBox.TYPE_ERROR)
			else:
				self.session.open(MessageBox, _("\nCache Folder %s not reachable:\nMP3 Browser Database Update canceled.") % str(config.plugins.mp3browser.cachefolder.value), MessageBox.TYPE_ERROR)

	def databaseUpdate_queryreturn(self, answer):
		print(f"[MP3BrowserMetrix][databaseUpdate_queryreturn] **** entered answer:{answer} self.ready:{self.ready}")
		print(f"[MP3BrowserMetrix][databaseUpdate_queryreturn] **** self.database:{self.database}") 
		if answer is True:
			self.ready = False
			if self.mp3list:
				mp3 = self.mp3list[self.index]
				fileWriteLine(self.lastfile, mp3)
			if not fileExists(self.database):
				open(self.database, "w").close()
			if fileExists(self.database):
				self.runTimer = eTimer()
				self.runTimer.callback.append(self.databaseUpdate_run)
				self.runTimer.start(500, True)

	def databaseUpdate_run(self):
		print(f"[MP3BrowserMetrix][databaseUpdate_run] entered")
		if config.plugins.mp3browser.hideupdate.value == "yes":
			self.hideScreen()
		if self.fav == True:
			self.fav = False
			self.database = config.plugins.mp3browser.DBfolder.value
		returnValue, orphaned, dbcountmax = databaseUpdate_core(self.database)
		if not returnValue:		
			self.databaseUpdate_finished(False, orphaned, dbcountmax)
		else:
			if self.reset == True:
				if config.plugins.mp3browser.hideupdate.value == "yes" and self.hideflag == False:
					self.hideScreen()
				self.session.openWithCallback(self.exit, mp3BrowserMetrix, 0, ":::")
			else:
				self.databaseUpdate_finished(True, orphaned, dbcountmax)
		return

	def databaseUpdate_finished(self, found, orphaned, dbcountmax):
		print(f"[MP3BrowserMetrix][databaseUpdate_finished] ***** found:{found}, orphaned:{orphaned}, dbcountmax:{dbcountmax} filter:{self.filter} self.lastfile:{self.lastfile}")     
		if config.plugins.mp3browser.hideupdate.value == "yes" and self.hideflag == False:
			self.hideScreen()
		mp3 = fileReadLine(self.lastfile)
		mp3 = sub("\\(|\\)|\\[|\\]|\\+|\\?", ".", mp3)
		data = fileReadLine(self.database)
		count = 0
		for line in data.split("\n"):
			if self.filter in line:
				if search(mp3, line) is not None:
					self.index = count
					break
				count += 1
		if self.autoupdate == True:
			self.autoupdate = False
			self.makeMP3BrowserTimer.callback.append(self.makeMP3(self.filter))
		elif found == False and orphaned == 0:
			self.session.open(MessageBox, _("\nNo new mp3's found:\nYour Database is up to date."), MessageBox.TYPE_INFO)
			self.makeMP3(self.filter)
		elif found == False and orphaned != 0:
			self.session.open(MessageBox, _("\nNo new mp3's found.\n%s orphaned Database Entries deleted.") % str(orphaned), MessageBox.TYPE_INFO)
			self.makeMP3(self.filter)
		elif orphaned == 0:
			self.session.open(MessageBox, _("\n%s mp3's imported into Database.") % str(dbcountmax), MessageBox.TYPE_INFO)
			self.makeMP3(self.filter)
		else:
			self.session.open(MessageBox, _("\n%s mp3's imported into Database.\n%s orphaned Database Entries deleted.") % (str(dbcountmax), str(orphaned)), MessageBox.TYPE_INFO)
			self.makeMP3(self.filter)
		return

	def makeMP3(self, filter):
		self.namelist = []
		self.mp3list = []
		self.datelist = []
		self.artistlist = []
		self.albumlist = []
		self.numberlist = []
		self.tracklist = []
		self.yearlist = []
		self.runtimelist = []
		self.bitratelist = []
		self.genrelist = []
		self.posterlist = []
		self.filter = filter
		if fileExists(self.database):
			lines = fileReadLines(self.database)
			for line in lines:
				if filter in line:
					try:           
						name = filename = date = artist = album = number = track = year = genre = runtime = bitrate = " "                
						poster = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/default.png"
						mp3line = line.split(":::")
						if mp3line == " " or len(mp3line)  < 2:
							continue
						else:
							name = mp3line[0]
							filename = mp3line[1]
							date = mp3line[2]
							artist = mp3line[3]
							album = mp3line[4]
							number = mp3line[5]
							track = mp3line[6]
							year = mp3line[7]
							genre = mp3line[8]
							runtime = mp3line[9]
							bitrate = mp3line[10]
							poster = mp3line[11]
					except IndexError as e:
						print("[MP3Browser][makeMP3] index error", e)
					self.namelist.append(name)
					self.mp3list.append(filename)
					self.datelist.append(date)
					self.artistlist.append(artist)
					self.albumlist.append(album)
					self.numberlist.append(number)
					self.tracklist.append(track)
					self.yearlist.append(year)
					self.genrelist.append(genre)
					self.runtimelist.append(runtime)
					self.bitratelist.append(bitrate)
					self.posterlist.append(poster)
			if self.showfolder == True:
				self.namelist.append(_("<List of MP3 Folder>"))
				self.mp3list.append(config.plugins.mp3browser.mp3folder.value + "...")
				self.datelist.append("")
				self.artistlist.append("")
				self.albumlist.append("")
				self.numberlist.append("")
				self.tracklist.append("")
				self.yearlist.append("")
				self.genrelist.append("")
				self.runtimelist.append("")
				self.bitratelist.append("")
				self.posterlist.append("/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/default_folder.png")
			self.maxentry = len(self.namelist)
			self.makeList()
			if self.ready == True:
				self.makePoster()
				self.makeInfo()

	def nextMP3(self):				# called at end of current playing mp3
		print("[MP3BrowserMetrix][nextMP3] Index, toggle",  self.index, "   ", self.toggle)
		print("[MP3BrowserMetrix][nextMP3] self.playready",  self.playready)    
		if self.playready == True:
			if self.random == False:
				self.index += 1
			else:
				self.index = random.randint(0, self.maxentry)
			if self.index == self.maxentry:
				self.index = 0
			self.ok()
			try:
				self["label3"].setText("Item %s/%s" % (str(self.index + 1), str(self.totalItem)))
				self["list"].moveToIndex(self.index)
			except IndexError as e:
				print("[MP3BrowserMetrix][nextMP3] Indexerror",  e)
			self.makePoster()
			self.makeInfo()
			
# toggle 0,1,2 choices=[(_("oninfo"), _("Info Button")), (_("info"), _("Show Info")), (_("always"), _("Show Info & Lyrics"))
			if self.toggle == 1:
				self.hideList()
				self.getLyrics()
			elif self.toggle == 2:
				self.hideInfo()
				self.getDiscogs()

	def showMP3(self):					# green button or 4 shows list of mp3's
		if self.ready == True:
			mp3s = ""
			if fileExists(self.database):
				lines = fileReadLines(self.database)
				for line in lines:
					if self.filter in line:
						mp3line = line.split(":::")
						try:
							mp3 = mp3line[3] + " - " + mp3line[6]
						except IndexError as e:
							mp3 = " "

						if mp3 != " ":
							mp3s = mp3s + mp3 + ":::"

				if self.showfolder == True:
					mp3s = mp3s + "<List of MP3 Folder>" + ":::"
				self.mp3s = [ i for i in mp3s.split(":::") ]
				self.mp3s.pop()
				self.session.openWithCallback(self.gotoMP3, allMP3List, self.mp3s, self.index)

	def gotoMP3(self, index):				# jump to selected mp3
		print("[MP3BrowserMetrix][gotoMP3] index",  index)
		if index is not None:
			self.index = index
			try:
				self["label3"].setText("Item %s/%s" % (str(self.index + 1), str(self.totalItem)))
				self["list"].moveToIndex(self.index)
			except IndexError as e:
				print("[MP3BrowserMetrix][gotoMP3   ] Indexerror",  e)

			self.makePoster()
			self.makeInfo()
			if self.toggle == 1:
				self.hideList()
				self.getLyrics()
			elif self.toggle == 2:
				self.hideInfo()
				self.getDiscogs()

	def deleteMP3(self):				# show Radio button
		if self.ready == True:
			if self.toggle == 0:
				try:
					name = self.namelist[self.index]
					self.session.openWithCallback(self.deleteMP3_return, MessageBox, _("\nThis will delete %s from the Database and from the MP3 Folder!\n\nDo you want to continue?") % name, MessageBox.TYPE_YESNO)
				except IndexError as e:
					print("[MP3BrowserMetrix][deleteMP3   ] Indexerror",  e)

			elif self.toggle == 1:
				try:
					self.artist = self.artistlist[self.index]
					self.track = self.tracklist[self.index]
					self.session.openWithCallback(self.deleteMP3_return, MessageBox, _("\nThis will delete the Lyrics of %s - %s!\n\nDo you want to continue?") % (self.artist, self.track), MessageBox.TYPE_YESNO)
				except IndexError as e:
					print("[MP3BrowserMetrix][deleteMP3   ] Indexerror",  e)

			elif self.toggle == 2:
				try:
					self.artist = self.artistlist[self.index]
					self.session.openWithCallback(self.deleteMP3_return, MessageBox, _("\nThis will delete the Discogs Information and Google Poster of %s!\n\nDo you want to continue?") % self.artist, MessageBox.TYPE_YESNO)
				except IndexError as e:
					print("[MP3BrowserMetrix][deleteMP3   ] Indexerror",  e)

	def deleteMP3_return(self, answer):
		if answer is True:
			if self.toggle == 0:
				try:
					mp3 = self.mp3list[self.index]
					filename = sub(".*?[/]", "", mp3)
					lyricsfile = join(config.plugins.mp3browser.cachefolder.value, filename)
					lyricsfile = lyricsfile.replace(".MP3", ".lyrics").replace(".mp3", ".lyrics")
					if fileExists(lyricsfile):
						remove(lyricsfile)
					if fileExists(mp3):
						remove(mp3)
					mp3 = sub("\\(|\\)|\\[|\\]|\\+|\\?", ".", mp3)
					data = open(self.database).read()
					for line in data.split("\n"):
						if search(mp3, line) is not None:
							data = data.replace(line + "\n", "")

					fileWriteLine(self.database, data)
					if self.index == self.maxentry - 1:
						self.index -= 1
					self.makeMP3(self.filter)
				except IndexError as e:
					print("[MP3BrowserMetrix][deleteMP3_return   ] Indexerror",  e)
			elif self.toggle == 1:
				try:
					filepath = self.mp3list[self.index]
					filename = sub(".*?[/]", "", filepath)
					lyricsfile = join(config.plugins.mp3browser.cachefolder.value, filename)
					lyricsfile = lyricsfile.replace(".MP3", ".lyrics").replace(".mp3", ".lyrics")
					if fileExists(lyricsfile):
						remove(lyricsfile)
					artist = "%s - %s" % (self.artist, self.track)
					if len(artist) > 35:
						if artist[34:35] == " ":
							artist = artist[0:34]
						else:
							artist = artist[0:35] + "FIN"
							artist = sub(" \\S+FIN", "", artist)
						artist = artist + " ..."
					self["discogsartist"].setText(str(artist))
					self["discogsartist"].show()
					self.lyrics = "ChartLyrics:\nNo Lyrics for %s - %s found." % (self.artist, self.track)
					self["discogs"].setText(self.lyrics)
					self["discogs"].show()
				except IndexError as e:
					print("[MP3BrowserMetrix][deleteMP3_return] Indexerror",  e)
			elif self.toggle == 2:
				discogsfile = join(config.plugins.mp3browser.cachefolder.value, self.artist.replace("/", "_") + ".discogs")
				posterjpeg = discogsfile.replace(".discogs", ".jpeg")
				posterpng = discogsfile.replace(".discogs", ".png")
				posterbmp = discogsfile.replace(".discogs", ".bmp")
				if fileExists(discogsfile):
					remove(discogsfile)
				if fileExists(posterjpeg):
					remove(posterjpeg)
				if fileExists(posterpng):
					remove(posterpng)
				if fileExists(posterbmp):
					remove(posterbmp)
				self["discogsartist"].setText("%s" % self.artist)
				self.profile = "Discogs.com:\nArtist %s not found." % self.artist
				self["discogs"].setText(self.profile)
				self["googlePoster"].hide()
				self.showInfo()
		return

	def shuffleMP3(self):
		if self.ready == True:
			self.ready = False
			if self.random == False:
				self.session.openWithCallback(self.shuffleMP3_return, switchScreen, 2, "shuffle")
			else:
				self.session.openWithCallback(self.shuffleMP3_return, switchScreen, 1, "shuffle")

	def shuffleMP3_return(self, number):
		if number is None:
			self.ready = True
		elif number == 1:
			self.random = False
			self.ready = True
		elif number == 2:
			self.random = True
			self.ready = True
		return

	def makePoster(self):			# develop pictures if possible for Album/Artist
		print("[MP3BrowserMetrix][makPoster] Entry self.index ", self.index)    
		self.artist = self.artistlist[self.index]
		self.track = self.tracklist[self.index]
		self.album = self.albumlist[self.index]
		if self.lastArtist != self.artist:
			self.lastPoster = ""
			self.lastArtist = ""
			self.lastAlbum = ""
		artistntrack = transLYRICSTIME(self.artist + "-" + self.track)
		artistntrack = artistntrack.replace("/", "-")
		album = transLYRICSTIME(self.album) 
		discogsfile = join(config.plugins.mp3browser.cachefolder.value, artistntrack + ".jpg")
		if fileExists(discogsfile):				# have album/artist picture jpg
			self.makePoster2()
		elif self.DiscogsNotBusy:				# No album/artist picture jpg get it from Discogs
			print(f"[MP3BrowserMetrix][makePoster] ******** artist:{self.artist} album:{self.album} track:{self.track} using album im discogs")
			if album and album != "n/a":
				url = f"http://api.discogs.com/database/search?q={self.artist}&album={self.album}&token={config.plugins.mp3browser.discogstoken.value}"
			else:	
				url = f"http://api.discogs.com/database/search?q={self.artist}&title={self.track}&token={config.plugins.mp3browser.discogstoken.value}"
			print(f"[MP3BrowserMetrix][makePoster] ******** url:{url} using token discogs")
			callInThread(threadGetjpg, url=url, artistntrack=artistntrack, success=self.makeJpg1, fail=self.makePoster2)
		else:									# Discogs not available
			self.makePoster2()

	def makePoster2(self, *args, **kwargs):		# make screen poster from available information for Album/Artist
		posterurl = self.posterlist[self.index]
		poster = sub(".*?[/]", "", posterurl)
		poster = join(config.plugins.mp3browser.cachefolder.value, poster)
		# print("[MP3BrowserMetrix][makePoster2]1 Entry -> posterurl, poster",  posterurl, "   ", poster)
		self.artist = self.artistlist[self.index]
		self.track = self.tracklist[self.index]
		if self.lastArtist != self.artist:
			self.lastPoster = ""
			self.lastArtist = ""
		artistntrack = transLYRICSTIME(self.artist + "-" + self.track)
		discogsfile = join(config.plugins.mp3browser.cachefolder.value, artistntrack + ".jpg")
		if fileExists(discogsfile):
			self.posterlist[self.index] = poster = discogsfile
			self.lastPoster = poster
			self.lastArtist = self.artist
		elif "default" in posterurl:
			poster = defaultfolder_png if "default_folder" in posterurl else default_png
		elif search("http", posterurl) is not None:
			callInThread(threadGetPage, url=posterurl, file=poster, success=self.getPoster, fail=self.downloadError)
		else:
			filename = self.mp3list[self.index]
			try:
				tag = ID3(filename)
			except ID3NoHeaderError:
				poster = defaultfolder_png if "default_folder" in posterurl else default_png
				self["poster"].instance.setPixmapFromFile(posterurl)
				return
			poster = tag.getall("APIC")
			if len(poster) > 0:
				f = open(posterurl, "wb")
				f.write(poster[0].data)
				f.close()
				poster = posterurl
			else:    
				poster = defaultfolder_png if "default_folder" in posterurl else default_png
		# print("[MP3BrowserMetrix][makePoster]1 artist, lastArtist, poster, self.lastPoster, posterurl", self.artist, "   ", self.lastArtist, "   ", poster, "   ", self.lastPoster, "   ", posterurl)        
		if "default" in poster and self.artist == self.lastArtist:
				poster = self.lastPoster
		# print("[MP3BrowserMetrix][makePoster]1 artist, lastArtist, poster, posterurl", self.artist, "   ", self.lastArtist, "   ", poster, "   ", posterurl)                
		self["poster"].instance.setPixmapFromFile(poster)
		self["poster"].show
		self.showInfo()

	def getPoster(self, output, poster):
		print("[MP3BrowserMetrix][getPoster]1 found http not default in posterurl",  posterurl)
		f = open(poster, "wb")
		f.write(output)
		f.close()
		if fileExists(poster):
			self["poster"].instance.setPixmapFromFile(poster)

	def makeJpg1(self, output, artistntrack=None, *args, **kwargs):
		output = output.decode()
		print(f"[MP3BrowserMetrix][makeJpg1] discogs output:{output}")		
		artistntrack = artistntrack.replace("/", "-")
		if "thumb" in output:						# if artist/track thumb picture in download from Discogs try download it
			print("[MP3BrowserMetrix][makeJpg1] Entered, output available")
			titleJpeg = output.split("thumb", 1)[1].split("jpeg", 1)[0][4:] + "jpeg"
#			coverJpeg = output.split("cover_image", 1)[1].split("jpeg", 1)[0][4:] + "jpeg"
			callInThread(threadGetjpg, url=titleJpeg, artistntrack=artistntrack, success=self.makeJpg3, fail=self.makeJpgerror)			
		else:										# artist/track not found, lets try artist
			print("[MP3BrowserMetrix][makeJpg1] Left - artist/track not found, lets try artist")
			url = "http://api.discogs.com/database/search?q=%s&token=%s" % (self.artist, config.plugins.mp3browser.discogstoken.value)
			print("[MP3BrowserMetrix][makeJpg1] ******** using token discogs")			
			callInThread(threadGetjpg, url=url, artistntrack=artistntrack, success=self.makeJpg2, fail=self.makePoster2)
			
	def makeJpg2(self, output, artistntrack=None, *args, **kwargs):					# if artist thumb picture in download from Discogs try download it
		output = output.decode()
		if "thumb" in output:
			artistntrack = artistntrack.replace("/", "-")
			print("[MP3BrowserMetrix][makeJpg1] Entered, output available")
			titleJpeg = output.split("thumb", 1)[1].split("jpeg", 1)[0][4:] + "jpeg"
#			coverJpeg = output.split("cover_image", 1)[1].split("jpeg", 1)[0][4:] + "jpeg"
			callInThread(threadGetjpg, url=titleJpeg, artistntrack=artistntrack, success=self.makeJpg3, fail=self.makePoster2)            
		else:
			self.makePoster2()			# go back and create Screen Poster

	def makeJpg3(self, output, artistntrack=None, *args, **kwargs):					# found thumb picture load it
		if output:
			artistntrack = artistntrack.replace("/", "-")
			discogsfile = join(config.plugins.mp3browser.cachefolder.value, artistntrack + ".jpg")
			print("[MP3BrowserMetrix][makeJpg3] Entered, discogsfile  ", discogsfile )
			f = open(discogsfile, "wb")
			f.write(output)
			f.close()
		self.makePoster2()			# go back and create Screen Poster

	def makeJpgerror(self, output, *args, **kwargs):
		self.DiscogsNotBusy = False
		print("[MP3BrowserMetrix][makeJpgerror] Entered, output ", output)            
		self.session.open(MessageBox, _("[MP3Browser][makeJpg] Too many calls to discogs.com."), MessageBox.TYPE_INFO, timeout=20)
		self.makePoster2()

	def getLyrics(self):
		self.ready = False
		try:
			self.artist = self.artistlist[self.index]
			self.track = self.tracklist[self.index]
		except IndexError as e:
				print("[MP3Browser][makeLyrics] Indexerror",  e)
				return            
		if self.artist == self.artistold and self.track == self.trackold:
			artist = "%s - %s" % (self.artist, self.track)
			if len(artist) > 35:
				if artist[34:35] == " ":
					artist = artist[0:34]
				else:
					artist = artist[0:35] + "FIN"
					artist = sub(" \\S+FIN", "", artist)
				artist = artist + " ..."
			self["discogsartist"].setText(str(artist))
			self["discogsartist"].show()
			self["discogs"].setText(self.lyrics)
			self["discogs"].show()
			self.ready = True
		else:
			self.artistold = self.artist
			self.trackold = self.track
			filepath = self.mp3list[self.index]
			filename = sub(".*?[/]", "", filepath)
			lyricsfile = join(config.plugins.mp3browser.cachefolder.value, filename)
			lyricsfile = lyricsfile.replace(".MP3", ".lyrics")
			lyricsfile = lyricsfile.replace(".mp3", ".lyrics")
			if fileExists(lyricsfile):
				self.lyrics = open(lyricsfile).read()
				self.lyrics = transHTML(self.lyrics)
				artist = "%s - %s" % (self.artist, self.track)
				if len(artist) > 35:
					if artist[34:35] == " ":
						artist = artist[0:34]
					else:
						artist = artist[0:35] + "FIN"
						artist = sub(" \\S+FIN", "", artist)
					artist = artist + " ..."
				self["discogsartist"].setText(str(artist))
				self["discogsartist"].show()
				self["discogs"].setText(self.lyrics)
				self["discogs"].show()
				artistntrack = transLYRICSTIME(self.artist + "-" + self.track) 
				discogsfile = join(config.plugins.mp3browser.cachefolder.value, artistntrack + ".jpg")
				if fileExists(discogsfile):
					self["poster"].instance.setPixmapFromFile(discogsfile)
					self["poster"].show()                 
				self.ready = True
			else:
				self["discogsartist"].setText("")
				self["discogs"].setText("")
				artist = transCHARTLYRICS(self.artist.lower())
				track = transCHARTLYRICS(self.track.lower())
				url = "http://api.chartlyrics.com/apiv1.asmx/SearchLyricDirect?artist=%s&song=%s" % (artist, track)
				callInThread(threadGetPage, url=url, success=self.makeLyrics, fail=self.downloadLyricsError)

	def makeLyrics(self, output):
		# print("[MP3Browser][makeLyrics] entered output is  ", output)
		output = output.decode()    
		lyrics = findall("<Lyric>(.*?)</Lyric>", output, flags=DOTALL)
		if lyrics:
			self.lyrics = lyrics[0].replace("amp;", "")
			artist = "%s - %s" % (self.artist, self.track)
			if len(artist) > 35:
				if artist[34:35] == " ":
					artist = artist[0:34]
				else:
					artist = artist[0:35] + "FIN"
					artist = sub(" \\S+FIN", "", artist)
				artist = artist + " ..."
			self["discogsartist"].setText(str(artist))
			self["discogsartist"].show()
			self["discogs"].setText(self.lyrics)
			self["discogs"].show()
			artistntrack = transLYRICSTIME(self.artist + "-" + self.track) 
			discogsfile = join(config.plugins.mp3browser.cachefolder.value, artistntrack + ".jpg")
			if fileExists(discogsfile):
				self["poster"].instance.setPixmapFromFile(discogsfile)
				self["poster"].show()              
			filepath = self.mp3list[self.index]
			filename = sub(".*?[/]", "", filepath)
			lyricsfile = join(config.plugins.mp3browser.cachefolder.value, filename)
			lyricsfile = lyricsfile.replace(".MP3", ".lyrics")
			lyricsfile = lyricsfile.replace(".mp3", ".lyrics")
			f = open(lyricsfile, "w")
			f.write(self.lyrics)
			f.close()
			self.ready = True
		else:
			artist = "%s - %s" % (self.artist, self.track)
			if len(artist) > 35:
				if artist[34:35] == " ":
					artist = artist[0:34]
				else:
					artist = artist[0:35] + "FIN"
					artist = sub(" \\S+FIN", "", artist)
				artist = artist + " ..."
			self["discogsartist"].setText(str(artist))
			self["discogsartist"].show()
			self.lyrics = "ChartLyrics/lyrics.time:\nNo Lyrics for %s - %s found." % (self.artist, self.track)
			self["discogs"].setText(self.lyrics)
			self["discogs"].show()
			self.ready = True

	def downloadLyricsError(self,  *args, **kwargs):
		artist = "%s - %s" % (self.artist, self.track)
		print("[MP3BrowserMetrix][downloadLyricsError] Entered artist", artist)
		if len(artist) == 0:
			return
		else:
			if len(artist) > 35:
				if artist[34:35] == " ":
					artist = artist[0:34]
				else:
					artist = artist[0:35] + "FIN"
					artist = sub(" \\S+FIN", "", artist)
				artist = artist + " ..."
			print("[MP3BrowserMetrix][downloadLyricsError] artist", artist)
			self["discogsartist"].setText(artist)
			self["discogsartist"].show()
			self.lyrics = "ChartLyrics/lyrics.time:\nNo Lyrics for %s - %s found." % (self.artist, self.track)
			self["discogs"].setText(self.lyrics)
			self["discogs"].show()
		self.ready = True

	def renewCover(self):
		return

	def makeFav(self):
		if self.ready == True:
			if self.fav == False:
				artist = self.artistlist[self.index]
				track = self.tracklist[self.index]
				self.session.openWithCallback(self.choiceFavFalse, ChoiceBox, title="MP3 Favourites", list=[("Open Favourites", "open"), ("Edit Favourites", "edit"), ("Add %s to Favourites" % (artist + " - " + track), "add")])
			else:
				self.session.openWithCallback(self.choiceFavTrue, ChoiceBox, title="MP3 Favourites", list=[("Close Favourites", "close"), ("Edit Favourites", "edit")])

	def choiceFavFalse(self, choice):
		choice = choice and choice[1]
		if choice == "open":
			self.fav = True
			self.index = 0
			self.database = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/favorites"
			self.makeMP3(self.filter)
		elif choice == "edit":
			self.session.open(mp3Fav, False)
		else:
			f = open(self.favorites, "a")
			data = self.namelist[self.index] + ":::" + self.mp3list[self.index] + ":::" + self.datelist[self.index] + ":::" + self.artistlist[self.index] + ":::" + self.albumlist[self.index] + ":::" + self.numberlist[self.index] + ":::" + self.tracklist[self.index] + ":::" + self.yearlist[self.index] + ":::" + self.genrelist[self.index] + ":::" + self.runtimelist[self.index] + ":::" + self.bitratelist[self.index] + ":::" + self.posterlist[self.index] + ":::"
			f.write(data)
			f.write(linesep)
			f.close()
			self.session.open(mp3Fav, True)

	def choiceFavTrue(self, choice):
		choice = choice and choice[1]
		if choice == "close":
			self.fav = False
			self.index = 0
			self.database = config.plugins.mp3browser.DBfolder.value
			self.makeMP3(self.filter)
		elif choice == "edit":
			self.session.openWithCallback(self.returnFavEdit, mp3Fav, False)

	def returnFavEdit(self, edit):
		if edit is None:
			pass
		else:
			self.index = 0
			self.makeMP3(self.filter)
		return

	def switchStyle(self):
		if self.ready == True:
			self.ready = False
			self.session.openWithCallback(self.returnStyle, switchScreen, 2, "style")

	def returnStyle(self, number):
		if number is None or number == 1:
			self.ready = True
		elif number == 2:
			if config.plugins.mp3browser.lastmp3.value == "yes":
				try:
					mp3 = self.mp3list[self.index]
					f = open(self.lastfile, "w")
					f.write(mp3)
					f.close()
				except IndexError as e:
					print(f"[MP3Browser][returnStyle] self.index:{self.index}, Indexerror:{e}")

			config.usage.on_movie_stop.value = self.movie_stop
			config.usage.on_movie_eof.value = self.movie_eof
			self.session.openWithCallback(self.close, mp3Browser, self.index, self.filter)
		return

	def startMoveCovers(self):
		try:
			cover = self.posterlist[self.index]
			cover = sub(".*?[/]", "", cover)
			cover = join(config.plugins.mp3browser.cachefolder.value, cover)
			if fileExists(cover):
				self.session.open(moveCover, cover)
		except IndexError as e:
			print("[MP3Browser][startMoveCovers   ] Indexerror",  e)

	def moveCovers(self):
		if self.ready == True:
			self.ready = False
			if self.move == False:
				self.session.openWithCallback(self.returnMoveCovers, switchScreen, 2, "move")
			else:
				self.session.openWithCallback(self.returnMoveCovers, switchScreen, 1, "move")

	def returnMoveCovers(self, number):
		if number is None:
			self.ready = True
		elif number == 1:
			self.move = False
			self.ready = True
		elif number == 2:
			self.move = True
			self.ready = True
			try:
				cover = self.posterlist[self.index]
				cover = sub(".*?[/]", "", cover)
				cover = join(config.plugins.mp3browser.cachefolder.value, cover)
				if fileExists(cover):
					self.session.open(moveCover, cover)
			except IndexError as e:
				print("[MP3Browser][returnMoveCovers] Indexerror",  e)

		return

	def toggleInfo(self):
		if self.ready == True:
			if self.toggle == 0:
				self.toggle = 1
				self.hideList()
				self.getLyrics()
				self["yellow"].show()
				self["red"].show()
				self["green"].show()
				self["text1"].setText(" ")
				self["text2"].setText("Style")
				self["text3"].setText(" ")
			elif self.toggle == 1:
				if config.plugins.mp3browser.discogs.value == "show":
					self.toggle = 2
					self.hideInfo()
					self.getDiscogs()
				else:
					self.toggle = 0
					self.hideDiscogs()
					self.showList()
					self.showInfo()
					self["text1"].setText("Help")
					self["text2"].setText("Update")
					self["text3"].setText("Edit")
			else:
				self.toggle = 0
				self.hideDiscogs()
				self.showList()
				self.showInfo()
				self["text1"].setText("Help")
				self["text2"].setText("Update")
				self["text3"].setText("Edit")

	def showDiscogs(self):
		self["discogs"].show()
		self["discogsartist"].show()
		self["googlePoster"].show()
		self["yellow"].show()
		self["red"].show()
		self["green"].show()

	def showList(self):
		self["label"].show()
		self["label2"].show()
		self["label3"].show()
		self["list"].show()
		self["help"].show()
		self["pvr"].show()
		self["text"].show()

	def showInfo(self):
		self["name"].show()
		self["artist"].show()
		self["Artist"].show()
		self["album"].show()
		self["Album"].show()
		self["number"].show()
		self["Number"].show()
		self["track"].show()
		self["Track"].show()
		self["year"].show()
		self["Year"].show()
		self["runtime"].show()
		self["Runtime"].show()
		self["bitrate"].show()
		self["Bitrate"].show()
		self["genre"].show()
		self["Genre"].show()
		self["poster"].show()
		self["posterback"].show()

	def hideInfo(self):
		self["name"].hide()
		self["artist"].hide()
		self["Artist"].hide()
		self["album"].hide()
		self["Album"].hide()
		self["number"].hide()
		self["Number"].hide()
		self["track"].hide()
		self["Track"].hide()
		self["year"].hide()
		self["Year"].hide()
		self["runtime"].hide()
		self["Runtime"].hide()
		self["bitrate"].hide()
		self["Bitrate"].hide()
		self["genre"].hide()
		self["Genre"].hide()
		self["poster"].hide()
		self["posterback"].hide()

	def hideDiscogs(self):
		self["discogsartist"].hide()
		self["discogs"].hide()
		self["googlePoster"].hide()
		self["yellow"].hide()
		self["red"].hide()
		self["green"].hide()

	def hideList(self):
		self["label"].hide()
		self["label2"].hide()
		self["label3"].hide()
		self["list"].hide()
		self["help"].hide()
		self["pvr"].hide()
		self["text"].hide()

	def makeInfo(self):
		try:
			name = self.artistlist[self.index] + " - " + self.tracklist[self.index]
			if self.showfolder == True and name == " - ":
				self["name"].setText("<List of MP3 Folder>")
				self["name"].show()
				self["Artist"].hide()
				self["artist"].hide()
				self["Album"].hide()
				self["album"].hide()
				self["Number"].hide()
				self["number"].hide()
				self["Track"].hide()
				self["track"].hide()
				self["Year"].hide()
				self["year"].hide()
				self["Runtime"].hide()
				self["runtime"].hide()
				self["Bitrate"].hide()
				self["bitrate"].hide()
				self["Genre"].hide()
				self["genre"].hide()
				return
			if len(name) > 63:
				if name[62:63] == " ":
					name = name[0:62]
				else:
					name = name[0:63] + "FIN"
					name = sub(" \\S+FIN", "", name)
				name = name + "..."
			self["name"].setText(str(name))
			self["name"].show()
			self.setTitle(str(name))
		except IndexError as e:
			self["name"].hide()

		self["Artist"].hide()
		self["artist"].hide()
		self["Album"].hide()
		self["album"].hide()
		self["Number"].hide()
		self["number"].hide()
		self["Track"].hide()
		self["track"].hide()
		self["Year"].hide()
		self["year"].hide()
		self["Runtime"].hide()
		self["runtime"].hide()
		self["Bitrate"].hide()
		self["bitrate"].hide()
		self["Genre"].hide()
		self["genre"].hide()

		try:
			artist = self.artistlist[self.index]
			self["Artist"].show()
			self["artist"].setText(artist)
			self["artist"].show()
			album = self.albumlist[self.index]
			self["Album"].show()
			self["album"].setText(album)
			self["album"].show()
			number = self.numberlist[self.index]
			self["Number"].show()
			self["number"].setText(number)
			self["number"].show()
			track = self.tracklist[self.index]
			self["Track"].show()
			self["track"].setText(track)
			self["track"].show()
			year = self.yearlist[self.index]
			self["Year"].show()
			self["year"].setText(year)
			self["year"].show()
			runtime = self.runtimelist[self.index]
			self["Runtime"].show()
			self["runtime"].setText(runtime)
			self["runtime"].show()
			bitrate = self.bitratelist[self.index]
			self["Bitrate"].show()
			self["bitrate"].setText(bitrate)
			self["bitrate"].show()
			genres = self.genrelist[self.index]
			self["Genre"].show()
			self["genre"].setText(genres)
			self["genre"].show()
		except IndexError as e:
			pass

	def makeList(self):
		print("[MP3BrowserMetrix][makeList]1 entered")    
		lines = fileReadLines(self.database)
		mp3s = []
		if config.plugins.mp3browser.metrixlist.value == "all":
			for line in lines:
				if self.filter in line:
					mp3line = line.split(":::")
					try:
						res = [
						 ""]
						mp3 = mp3line[3] + " - " + mp3line[6]
						if len(mp3) > 47:
							if mp3[46:47] == " ":
								mp3 = mp3[0:46]
							else:
								mp3 = mp3[0:47] + "FIN"
								mp3 = sub(" \\S+FIN", "", mp3)
							mp3 = str(mp3) + " ..."
						if self.backcolor == True:
							res.append(MultiContentEntryText(pos=(0, 0), 
							size=(540, 40), font=26, color=16777215, color_sel=16777215, backcolor_sel=self.back_color, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=mp3))
						else:
							res.append(MultiContentEntryText(pos=(0, 0), 
							size=(540, 40), font=26, color=16777215, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=mp3))
						mp3s.append(res)
					except IndexError as e:
						print("[MP3BrowserMetrix][ makeList1] Indexerror",  e)

		else:
			for line in f:
				if self.filter in line:
					mp3line = line.split(":::")
					try:
						res = [
						 ""]
						mp3 = mp3line[3]
						if self.backcolor == True:
							res.append(MultiContentEntryText(pos=(0, 0), 
							size=(540, 40), font=26, color=16777215, color_sel=16777215, backcolor_sel=self.back_color, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=mp3))
						else:
							res.append(MultiContentEntryText(pos=(0, 0), 
							size=(540, 40), font=26, color=16777215, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=mp3))
						mp3s.append(res)
					except IndexError as e:
						print("[MP3BrowserMetrix][makeList]1 Indexerror",  e)

		if self.showfolder == True:
			res = [
			 ""]
			if self.backcolor == True:
				res.append(MultiContentEntryText(pos=(0, 0), size=(540, 40), font=26, color=16777215, color_sel=16777215, backcolor_sel=self.back_color, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text="<List of MP3 Folder>"))
			else:
				res.append(MultiContentEntryText(pos=(0, 0), size=(540, 40), font=26, color=16777215, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text="<List of MP3 Folder>"))
			mp3s.append(res)
		self["list"].l.setList(mp3s)
		self["list"].l.setFont(26, gFont("Metrix", 26))
		self["list"].l.setItemHeight(35)
		self["list"].moveToIndex(self.index)

# toggle 0,1,2 choices=[("oninfo", "Info Button"), ("info", "Show Info"), ("always", "Show Info & Lyrics")        
		if self.toggle == 1:
			self.hideList()
			self.getLyrics()
		elif self.toggle == 2:
			self.hideInfo()
			self.getDiscogs()
		self.totalMP3 = len(mp3s)
		self.totalItem = len(mp3s)
		self.ready = True if self.totalMP3 != 0 else False
		print("[MP3BrowserMetrix][makeList] totalMP3, totalItem",  self.totalMP3, "   ", self.totalItem)        
		if self.showfolder == True:
			self.totalMP3 -= 1
		fav = "Favourites"
		free = "free Space"
		folder = "Folder"
		if exists(config.plugins.mp3browser.mp3folder.value):
			stat = statvfs(config.plugins.mp3browser.mp3folder.value)
			freeSize = stat.f_bsize * stat.f_bfree // 1024 // 1024 // 1024
			if self.fav == False:
				titel = "%s MP3s" % str(self.totalMP3)
			else:
				titel = "%s MP3 %s" % (str(self.totalMP3), fav)
			titel2 = "(MP3 %s: %s GB %s)" % (folder, str(freeSize), free)
			self["label"].setText(titel)
			self["label2"].setText(titel2)
			self["label3"].setText("Item %s/%s" % (str(self.index + 1), str(self.totalItem)))
		else:
			if self.fav == False:
				titel = "%s MP3s" % str(self.totalMP3)
			else:
				titel = "%s MP3 %s" % (str(self.totalMP3), fav)
			titel2 = "(MP3 %s offline)" % folder
			self["label"].setText(titel)
			self["label2"].setText(titel2)
			self["label3"].setText("Item %s/%s" % (str(self.index + 1), str(self.totalItem)))

	def getDiscogs(self):
		print("[MP3BrowserMetrix][getDiscogs] Entered")   
		self.ready = True

	def ok(self):
		print("[MP3BrowserMetrix][ok] self.ready",  self.ready)    
		if self.ready == True:
			try:
				filename = self.mp3list[self.index]
				if self.showfolder == True and filename.endswith("..."):
					self.filterFolder()
					return
				sref = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + filename)
				sref.setName(self.artistlist[self.index] + " - " + self.tracklist[self.index])
				if self.background == True:
					self.playready = True
					self.session.nav.stopService()
					self.session.nav.playService(sref)
				else:
					self.playready = True
					self.session.open(MoviePlayer, sref)
				if self.move == True:
					self.coverTimer.stop()
					self.coverTimer.start(500, True)
			except IndexError as e:
				print("[MP3Browser][ok] Indexerror",  e)

	def stop(self):
		self.playready = False
		if self.background == True:
			self.session.nav.stopService()
			self.session.nav.playService(self.oldService)
		if self.move == True:
			self.coverTimer.stop()

	def down(self):
		print("[MP3BrowserMetrix][down] self.ready, self.toggle",  self.ready, "   ", self.toggle)    
		if self.ready == True:
			self["list"].down()
			self.index = self["list"].getSelectedIndex()
			print("[MP3BrowserMetrix][down] self.index",  self.index)
			self["label3"].setText("Item %s/%s" % (str(self.index + 1), str(self.totalItem)))
			self.makePoster()
			self.makeInfo()
			if self.toggle == 1:
				self.hideList()
				self.getLyrics()
			elif self.toggle == 2:
				self.hideInfo()
				self.getDiscogs()

	def up(self):
		print("[MP3BrowserMetrix][up]self.ready , self.toggle",  self.ready, "   ", self.toggle)
		if self.ready == True:
			self["list"].up()
			self.index = self["list"].getSelectedIndex()
			print("[MP3BrowserMetrix][up] self.index",  self.index)
			self["label3"].setText("Item %s/%s" % (str(self.index + 1), str(self.totalItem)))
			self.makePoster()
			self.makeInfo()
			if self.toggle == 1:
				self.hideList()
				self.getLyrics()
			elif self.toggle == 2:
				self.hideInfo()
				self.getDiscogs()

	def rightDown(self):
		print("[MP3BrowserMetrix][rightDown] self.ready, self.toggle",  self.ready, "   ", self.toggle)
		if self.ready == True:
			if self.toggle != 0:
				self["discogs"].pageDown()
			else:
				self["list"].pageDown()
				self.index = self["list"].getSelectedIndex()
				self["label3"].setText("Item %s/%s" % (str(self.index + 1), str(self.totalItem)))
				self.makePoster()
				self.makeInfo()

	def leftUp(self):
		print("[MP3BrowserMetrix][leftUp] self.ready, self.toggle",  self.ready, "   ", self.toggle)
		if self.ready == True:
			if self.toggle != 0:
				self["discogs"].pageUp()
			else:
				self["list"].pageUp()
				self.index = self["list"].getSelectedIndex()
				self["label3"].setText("Item %s/%s" % (str(self.index + 1), str(self.totalItem)))
				self.makePoster()
				self.makeInfo()

	def gotoEnd(self):
		print("[MP3BrowserMetrix][gotoEnd] self.ready, self.index",  self.ready, "   ", self.index)    
		if self.ready == True:
			self.index = self.maxentry - 1
			try:
				self["label3"].setText("Item %s/%s" % (str(self.index + 1), str(self.totalItem)))
				self["list"].moveToIndex(self.index)
			except IndexError as e:
				print("[MP3BrowserMetrix][   ] Indexerror",  e)

			self.makePoster()
			self.makeInfo()
			if self.toggle == 1:
				self.hideList()
				self.getLyrics()
			elif self.toggle == 2:
				self.hideInfo()
				self.getDiscogs()

	def gotoABC(self):
		self.session.openWithCallback(self.enterABC, getABC, self.ABC, False)

	def gotoXYZ(self):
		self.session.openWithCallback(self.enterABC, getABC, self.ABC, True)

	def enterABC(self, ABC):
		if ABC is None:
			pass
		else:
			self.ABC = ABC
			ABC = ABC[0].lower()
			try:
				self.index = next(index for index, value in enumerate(self.artistlist) if value.lower().replace("the ", "").startswith(ABC))
				try:
					self["label3"].setText("Item %s/%s" % (str(self.index + 1), str(self.totalItem)))
					self["list"].moveToIndex(self.index)
				except IndexError as e:
					print("[MP3BrowserMetrix]enterABC Indexerror",  e)

				self.makePoster()
				self.makeInfo()
				if self.toggle == 1:
					self.hideList()
					self.getLyrics()
				elif self.toggle == 2:
					self.hideInfo()
					self.getDiscogs()
			except StopIteration as e:
				print("[MP3BrowserMetrix][enterABC] iteration errors",  e)
		return

	def filterFolder(self):
		if self.ready == True:
			self.folders, max = filterFolderSetup()
			if fileExists(self.database):			
				self.session.openWithCallback(self.filter_return, filterList, self.folders, "MP3 Folder Selection", len(self.folders), max)
		return

	def filterArtist(self):
		if self.ready == True and fileExists(self.database):
			self.artists, max = filterSetup(self.database, 3)
			self.session.openWithCallback(self.filter_return, filterList, self.artists, "Artist Selection", len(self.artists), max)

	def filterAlbum(self):
		if self.ready == True and fileExists(self.database):
			self.albums, max = filterSetup(self.database, 4)
			self.session.openWithCallback(self.filter_return, filterList, self.albums, "Album Selection", len(self.albums), max)

	def filterGenre(self):
		if self.ready == True and fileExists(self.database):
			self.genres, max = filterSetup(self.database, 8)
			self.session.openWithCallback(self.filter_return, filterList, self.genres, "Genre Selection", len(self.genres), max)

	def filter_return(self, filter):
		if filter and filter is not None:
			self.index = 0
			self.makeMP3(filter)
		return

	def databaseEdit(self):				# startTeleText button
		if self.ready == True:
			try:
				mp3 = self.mp3list[self.index]
			except IndexError as e:
				mp3 = "None"

			self.session.openWithCallback(self.databaseEdit_return, mp3DatabaseStart, mp3)

	def databaseEdit_return(self, changed):
		if changed is True:
			mp3 = self.mp3list[self.index]
			mp3 = sub("\\(|\\)|\\[|\\]|\\+|\\?", ".", mp3)
			databaseSort(self.database)
			f = open(self.database, "r")
			count = 0
			for line in f:
				if self.filter in line:
					if mp3 in line:
						self.index = count
						break
					count += 1

			f.close()
			self.makeMP3(self.filter)

	def downloadError(self, output):
		self.ready = True

	def config(self):
		if self.ready == True:
			config.usage.on_movie_stop.value = self.movie_stop
			config.usage.on_movie_eof.value = self.movie_eof
			print("[MP3Browser][databaseInitialisation] **** call to Browser setup or Initialisation")
			self.session.openWithCallback(self.checkDB, mp3BrowserConfig)

	def zap(self):
		servicelist = self.session.instantiateDialog(ChannelSelection)
		self.session.execDialog(servicelist)

	def showHelp(self):
		if self.showhelp == False:
			self.showhelp = True
			self.toogleHelp.show()
		else:
			self.showhelp = False
			self.toogleHelp.hide()

	def infoScreen(self):
		self.session.open(infoScreenMP3Browser, None, True)
		return

	def hideScreen(self):
		if self.hideflag == True:
			self.hideflag = False
			count = 40
			while count > 0:
				count -= 1

		else:
			self.hideflag = True
			count = 0
			while count < 40:
				count += 1

	def exit(self):
		if self.showhelp == True:
			self.showhelp = False
			self.toogleHelp.hide()
		elif self.toggle != 0:
			self.toggle = 0
			self.hideDiscogs()
			self.showList()
			self.showInfo()
			self["text1"].setText("Help")
			self["text2"].setText("Update")
			self["text3"].setText("Edit")
		else:
			self.playready = False
			if self.background == True or config.plugins.mp3browser.showtv.value == "hide":
				self.session.nav.playService(self.oldService)
			if config.plugins.mp3browser.lastmp3.value == "yes":
				try:
					mp3 = self.mp3list[self.index]
					fileWriteLine(self.lastfile, mp3)
				except IndexError as e:
					print("[MP3BrowserMetrix][exit] Indexerror",  e)
			if config.plugins.mp3browser.lastfilter.value == "yes":
				fileWriteLine(self.lastfilter, self.filter)
			self.session.deleteDialog(self.toogleHelp)
			config.usage.on_movie_stop.value = self.movie_stop
			config.usage.on_movie_eof.value = self.movie_eof
			self.close()


class mp3Browser(Screen):

	def __init__(self, session, index, filter):
		print("[MP3Browser][mp3Browser] ")
		self.xd = False
		self.posterX = 9
		self.posterY = 5
		self.posterALL = 45
		self.posterREST = 0
		self.positionlist = []
		skincontent = ""
		numX = -1
		factor = getDesktop(0).size().height()/720
		print(f"[MP3Browser][mp3Browser] factor:{factor}")
		for x in list(range(self.posterALL)):
			numY = x // 9
			numX += 1
			if numX >= 9:
				numX = 0
			posX = 2 + numX * (142)
			posY = 6 + numY * (142)
			self.positionlist.append((posX - 16, posY - 16))
			skincontent += '<widget name="poster' + str(x) + '" position="' + str(posX) + ',' + str(posY) + '" size="140,140" zPosition="-4" transparent="1" alphatest="on" scaleFlags="scaleKeepAspect" />'
			skincontent += '<widget name="poster_back' + str(x) + '" position="' + str(posX) + ',' + str(posY) + '" size="140,140" zPosition="-3" transparent="1" alphatest="blend" scaleFlags="scaleKeepAspect" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/browser/poster_backHD2.png" />'

		skinHD = """
		<screen position="center,center" size="1280,720" flags="wfNoBorder" title="  " >
			<widget name="infoback" position="25,25" size="525,430" alphatest="blend" transparent="1" zPosition="-1" />
			<widget name="name" position="40,30" size="495,70" font="{font};28" foregroundColor="#FFFFFF" valign="center" transparent="1" zPosition="3" />
			<widget name="Artist" position="40,100" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="4" />
			<widget name="artist" position="40,130" size="320,28" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="5" />
			<widget name="Album" position="40,170" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="6" />
			<widget name="album" position="40,200" size="320,28" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="7" />
			<widget name="Year" position="370,170" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="8" />
			<widget name="year" position="370,200" size="125,28" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="9" />
			<widget name="Track" position="40,240" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="10" />
			<widget name="track" position="40,270" size="320,28" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="11" />
			<widget name="Number" position="370,240" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="12" />
			<widget name="number" position="370,270" size="125,28" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="13" />
			<widget name="Runtime" position="40,310" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="14" />
			<widget name="runtime" position="40,340" size="320,28" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="15" />
			<widget name="Bitrate" position="370,310" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="16" />
			<widget name="bitrate" position="370,340" size="125,28" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="17" />
			<widget name="Genre" position="40,380" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="18" />
			<widget name="genre" position="40,410" size="500,28" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="19" />
			<widget name="discogsback" position="730,25" size="525,430" alphatest="blend" transparent="1" zPosition="-1" />
			<widget name="discogs" position="745,40" size="500,400" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="20" />
			<widget name="googlePoster" position="37,53" size="500,375" alphatest="on" transparent="1" zPosition="20" />
			<widget name="frame" position="-11,-7" size="172,172" zPosition="-2" alphatest="on" />"""
		skinHD += skincontent
		skinHD += "</screen>"
		font = "Sans" if config.plugins.mp3browser.font.value == "yes" else "Regular"
		color = config.plugins.mp3browser.color.value
		self.dict = {"font": font, "color": color}
		self.skin = skinScale(applySkinVars(skinHD, self.dict))
		# self.skin = applySkinVars(skinHD, self.dict)
		# print(f"[MP3Browser][mp3Browser] skinHD:{skinHD}")
		print(f"[MP3Browser][mp3Browser] self.skin:{self.skin}")
		Screen.__init__(self, session)
		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.toogleHelp = self.session.instantiateDialog(helpScreen)
		self.showhelp = False
		self.hideflag = True
		self.fav = False
		self.ready = False		# config defined
		self.reset = False		# databse initialised
		self.autoupdate = False
		self.filter = filter
		self.index = index
		self.wallindex = self.index % self.posterALL
		self.pagecount = self.index // self.posterALL + 1
		self.walloldindex = 0
		self.pagemax = 1

# toggle 0,1,2 choices=[("oninfo", "Info Button"), ("info", "Show Info"), ("always", "Show Info & Lyrics")
		
		if config.plugins.mp3browser.showinfo.value == "always":
			self.infofull = True
			self.toggle = 2
		elif config.plugins.mp3browser.showinfo.value == "info":
				self.infofull = True
				self.toggle = 1
		else:
			   self.infofull = False
			   self.toggle = 0
		self.move = False if config.plugins.mp3browser.screensaver.value == "no" else True
		self.random = False if config.plugins.mp3browser.shuffle.value == "no" else True
		self.background = False if config.plugins.mp3browser.background.value == "player" else True
		self.showfolder = False if config.plugins.mp3browser.showfolder.value == "no" else True # default is No
		self.lang = config.plugins.mp3browser.language.value
		self.playready = False
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={iPlayableService.evEOF: self.nextMP3})
		self.ABC = "ABC"
		self.artist = ""
		self.artistold = ""
		self.artistdisco = ""
		self.track = ""
		self.trackold = ""
		self.profile = ""
		self.lyrics = ""
		self.lastArtistdisco = ""
		self.lastArtist = ""
		self.lastPoster = ""
		self.namelist = []
		self.mp3list = []
		self.datelist = []
		self.artistlist = []
		self.albumlist = []
		self.numberlist = []
		self.tracklist = []
		self.yearlist = []
		self.runtimelist = []
		self.bitratelist = []
		self.genrelist = []
		self.posterlist = []
		self["Artist"] = Label(_)("Artist:")
		self["Number"] = Label(_("Track#:"))
		self["Track"] = Label(_("Track:"))
		self["Year"] = Label(_("Year:"))
		self["Runtime"] = Label(_("Runtime:"))
		self["Album"] = Label(_("Album:"))
		self["Bitrate"] = Label(_("Bitrate:"))
		self["Genre"] = Label(_("Genre:"))
		self["name"] = Label()
		self["artist"] = Label()
		self["album"] = Label()
		self["number"] = Label()
		self["track"] = Label()
		self["year"] = Label()
		self["runtime"] = Label()
		self["bitrate"] = Label()
		self["genre"] = Label()
		self["discogs"] = ScrollLabel()
		self["googlePoster"] = Pixmap()
		self["frame"] = Pixmap()
		self["discogsback"] = Pixmap()
		self["discogsback"].hide()
		self["infoback"] = Pixmap()
		for x in list(range(self.posterALL)):
			self["poster" + str(x)] = Pixmap()
			self["poster_back" + str(x)] = Pixmap()
		self["infoback"].hide()
		self["Artist"].hide()
		self["Number"].hide()
		self["Track"].hide()
		self["Year"].hide()
		self["Runtime"].hide()
		self["Album"].hide()
		self["Bitrate"].hide()
		self["Genre"].hide()
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActions", "ChannelSelectBaseActions", "HelpActions", "InfobarActions", "InfobarTeletextActions", "MovieSelectionActions", "MoviePlayerActions", "InfobarEPGActions", "NumberActions"], {"ok": self.ok, 
			"cancel": self.exit, 
			"right": self.rightDown, 
			"left": self.leftUp, 
			"down": self.down, 
			"up": self.up, 
			"nextBouquet": self.zap, 
			"prevBouquet": self.zap, 
			"nextMarker": self.gotoABC, 
			"prevMarker": self.gotoXYZ, 
			"red": self.switchStyle, 
			"yellow": self.config, 
			"green": self.showMP3, 
			"blue": self.hideScreen, 
			"contextMenu": self.config, 
			"showEventInfo": self.toggleInfo, 
			"EPGPressed": self.toggleInfo, 
			"startTeletext": self.databaseEdit, 
			"showMovies": self.databaseUpdate, 
			"showRadio": self.deleteMP3, 
			"leavePlayer": self.stop, 
			"1": self.showMP3, 
			"2": self.moveCovers, 
			"3": self.makeFav, 
			"4": self.showMP3, 
			"5": self.shuffleMP3, 
			"6": self.filterFolder, 
			"7": self.filterArtist, 
			"8": self.filterAlbum, 
			"9": self.filterGenre, 
			"0": self.gotoEnd, 
			"bluelong": self.showHelp, 
			"displayHelp": self.showHelp}, -1)
		self.movie_stop = config.usage.on_movie_stop.value
		self.movie_eof = config.usage.on_movie_eof.value
		config.usage.on_movie_stop.value = "quit"
		config.usage.on_movie_eof.value = "quit"
		self.database = config.plugins.mp3browser.DBfolder.value
		self.favorites = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/favorites"
		self.lastfilter = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/filter"
		self.lastfile = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/last"
		print(f"[onLayoutFinished] database:{config.plugins.mp3browser.DBfolder.value} mp3folder:{config.plugins.mp3browser.mp3folder.value}")
		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		self.version = "2.0py3"
		if fileExists(self.database):
			size = getsize(self.database)
			if size < 10:
				remove(self.database)
		self.infoBackPNG = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/browser/info_backHD.png"
		if fileExists(self.infoBackPNG):
			self["discogsback"].instance.setPixmapFromFile(self.infoBackPNG)
			self["infoback"].instance.setPixmapFromFile(self.infoBackPNG)
			self["discogsback"].hide()
			self["infoback"].hide()
		if config.plugins.mp3browser.showtv.value == "hide":
			self.session.nav.stopService()
		self.coverTimer = eTimer()
		self.coverTimer.callback.append(self.startMoveCovers)
		if fileExists(self.database):
			if self.index == 0:
				if config.plugins.mp3browser.lastfilter.value == "yes":
					self.filter = fileReadLine(self.lastfilter)
				if config.plugins.mp3browser.lastmp3.value == "yes":
					mp3 = fileReadLine(self.lastfile)
					mp3 = sub("\\(|\\)|\\[|\\]|\\+|\\?", ".", mp3)
					data = open(self.database).read()
					count = 0
					for line in data.split("\n"):
						if self.filter in line:
							if search(mp3, line) is not None:
								self.index = count
								break
							count += 1

					if mp3.endswith("..."):
						self.index = count
					self.wallindex = self.index % self.posterALL
					self.pagecount = self.index // self.posterALL + 1
				elif config.plugins.mp3browser.lastmp3.value == "folder" and self.showfolder == True:
					self.index = sum(1 for line in open(self.database))
					self.wallindex = self.index % self.posterALL
					self.pagecount = self.index // self.posterALL + 1
			self.reset = False
			self.makeMP3BrowserTimer = eTimer()
			print(f"[onLayoutFinished] mp3folder is :{config.plugins.mp3browser.mp3folder}")
			if config.plugins.mp3browser.autoupdate.value == "yes" and exists(config.plugins.mp3browser.mp3folder.value):
				self.autoupdate = True
				self.makeMP3BrowserTimer.callback.append(self.databaseUpdate_queryreturn(True))
			else:
				self.makeMP3BrowserTimer.callback.append(self.makeMP3(self.filter))
			self.makeMP3BrowserTimer.start(500, True)
		else:
			self.openTimer = eTimer()
			self.openTimer.callback.append(self.openInfo)
			self.openTimer.start(500, True)
		return

	def config(self):
		print(f"[MP3Browser][config] **** self.ready:{self.ready}")	
		if self.ready == True:
			config.usage.on_movie_stop.value = self.movie_stop
			config.usage.on_movie_eof.value = self.movie_eof
			self.session.openWithCallback(self.checkConfig, mp3BrowserConfig)

	def openInfo(self):
		print("[MP3Browser][checkDB] **** openInfo entered")	
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/reset"):
			self.session.openWithCallback(self.databaseInitialisation_queryreturn, MessageBox, _("The MP3 Browser Database will be build now. Depending on the number of your mp3s this can take several minutes.\n\nBuild MP3 Browser Database now?"), MessageBox.TYPE_YESNO)
		else:
			self.session.openWithCallback(self.databaseInitialisation, MessageBox, _("Before the Database will be build, check your settings in the setup of the plugin:\n\n- Check the path to the MP3 Folder\n- Change the Cache Folder to your hard disk drive or usb stick."), MessageBox.TYPE_YESNO)

	def checkConfig(self):
		print("[MP3Browser][checkConfig] **** return from Browser setup")	
		global calledBrowser
		if config.plugins.mp3browser.style.value != calledBrowser:
			calledBrowser = config.plugins.mp3browser.style.value 
			if config.plugins.mp3browser.style.value == "metrix":
				self.session.openWithCallback(self.close, mp3BrowserMetrix, 0, ":::")
			else:
				self.session.openWithCallback(self.close, mp3Browser, 0, ":::")
		else:
			self.ready = True
			self.databaseUpdate()	

	def checkDB(self):
		print("[MP3Browser][checkDB] **** return from Browser setup")	
		global calledBrowser
		if config.plugins.mp3browser.style.value != calledBrowser:
			calledBrowser = config.plugins.mp3browser.style.value 
			if config.plugins.mp3browser.style.value == "metrix":
				self.session.openWithCallback(self.close, mp3BrowserMetrix, 0, ":::")
			else:
				self.session.openWithCallback(self.close, mp3Browser, 0, ":::")
		else:
			self.ready = True
			self.databaseUpdate()	

	def databaseInitialisation(self, answer):
		print(f"[MP3Browser][databaseInitialisation] **** entered answer:{answer}")	
		open("/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/reset", "w").close()
		config.usage.on_movie_stop.value = self.movie_stop
		config.usage.on_movie_eof.value = self.movie_eof
		print("[MP3Browser][databaseInitialisation] **** entry to Browser setup")		
		if answer is True:
			self.session.openWithCallback(self.checkDB, mp3BrowserConfig)
		else:
			self.databaseInitialisation_queryreturn(True)

	def databaseInitialisation_queryreturn(self, answer):
		print(f"[MP3Browser][databaseInitialisation_return] **** entered answer:{answer}")
		if answer is True:
			self.reset = True
			if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/reset"):
				remove("/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/reset")
			open(self.database, "w").close()
			self.makeMP3BrowserTimer = eTimer()
			self.resetTimer = eTimer()
			self.resetTimer.callback.append(self.databaseUpdate_queryreturn(True))
			self.resetTimer.start(500, True)


	def databaseUpdate(self):
		print(f"[MP3Browser][databaseUpdate] **** entered")
		if self.ready == True:
			if exists(config.plugins.mp3browser.mp3folder.value) and exists(config.plugins.mp3browser.cachefolder.value):
				self.session.openWithCallback(self.databaseUpdate_queryreturn, MessageBox, _("\nUpdate MP3 Browser Database?"), MessageBox.TYPE_YESNO)
			elif exists(config.plugins.mp3browser.cachefolder.value):
				self.session.open(MessageBox, _("\nMP3 Folder %s not reachable:\nMP3 Browser Database Update canceled.") % str(config.plugins.mp3browser.mp3folder.value), MessageBox.TYPE_ERROR)
			else:
				self.session.open(MessageBox, _("\nCache Folder %s not reachable:\nMP3 Browser Database Update canceled.") % str(config.plugins.mp3browser.cachefolder.value), MessageBox.TYPE_ERROR)

	def databaseUpdate_queryreturn(self, answer):
		if answer is True:
			self.ready = False
			if self.mp3list:
				mp3 = self.mp3list[self.index]
				fileWriteLine(self.lastfile, mp3)
			if fileExists(self.database):
				self.runTimer = eTimer()
				self.runTimer.callback.append(self.databaseUpdate_run)
				self.runTimer.start(500, True)

	def databaseUpdate_run(self):
		if config.plugins.mp3browser.hideupdate.value == "yes":
			self.hideScreen()
		if self.fav == True:
			self.fav = False
			self.database = config.plugins.mp3browser.DBfolder.value
		returnValue, orphaned, dbcountmax = databaseUpdate_core(self.database)
		if not returnValue:		
			self.databaseUpdate_finished(False, 0, 0)
		else:
			if self.reset == True:
				if config.plugins.mp3browser.hideupdate.value == "yes" and self.hideflag == False:
					self.hideScreen()
				self.session.openWithCallback(self.exit, mp3BrowserMetrix, 0, ":::")
			else:
				self.databaseUpdate_finished(True, orphaned, dbcountmax)
		return

	def databaseUpdate_finished(self, found, orphaned, dbcountmax):
		print("[MP3Browser][databaseUpdate_finished]")     
		if config.plugins.mp3browser.hideupdate.value == "yes" and self.hideflag == False:
			self.hideScreen()
		mp3 = fileReadLine(self.lastfile)
		mp3 = sub("\\(|\\)|\\[|\\]|\\+|\\?", ".", mp3)
		data = fileReadLine(self.database)
		count = 0
		for line in data.split("\n"):
			if self.filter in line:
				if search(mp3, line) is not None:
					self.index = count
					break
				count += 1

		if self.autoupdate == True:
			self.autoupdate = False
			self.makeMP3BrowserTimer.callback.append(self.makeMP3(self.filter))
		elif found == False and orphaned == 0:
			self.session.open(MessageBox, _("\nNo new mp3's found:\nYour Database is up to date."), MessageBox.TYPE_INFO)
			self.makeMP3(self.filter)
		elif found == False:
			self.session.open(MessageBox, _("\nNo new mp3's found.\n%s orphaned Database Entries deleted.") % str(orphaned), MessageBox.TYPE_INFO)
			self.makeMP3(self.filter)
		elif orphaned == 0:
			self.session.open(MessageBox, _("\n%s mp3's imported into Database.") % str(self.dbcountmax), MessageBox.TYPE_INFO)
			self.makeMP3(self.filter)
		else:
			self.session.open(MessageBox, _("\n%s mp3's imported into Database.\n%s orphaned Database Entries deleted.") % (str(dbcountmax), str(orphaned)), MessageBox.TYPE_INFO)
			self.makeMP3(self.filter)
		return

	def makeMP3(self, filter):
		self.namelist = []
		self.mp3list = []
		self.datelist = []
		self.artistlist = []
		self.albumlist = []
		self.numberlist = []
		self.tracklist = []
		self.yearlist = []
		self.runtimelist = []
		self.bitratelist = []
		self.genrelist = []
		self.posterlist = []
		self.filter = filter
		if fileExists(self.database):
			lines = fileReadLines(self.database)
			for line in lines:
				if filter in line:
					try:           
						name = filename = date = artist = album = number = track = year = genre = runtime = bitrate = " "                
						poster = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/default.png"
						mp3line = line.split(":::")
						if mp3line == " " or len(mp3line)  < 2:
							continue
						else:
							name = mp3line[0]
							filename = mp3line[1]
							date = mp3line[2]
							artist = mp3line[3]
							album = mp3line[4]
							number = mp3line[5]
							track = mp3line[6]
							year = mp3line[7]
							genre = mp3line[8]
							runtime = mp3line[9]
							bitrate = mp3line[10]
							poster = mp3line[11]
					except IndexError as e:
						print("[MP3Browser][makeMP3] index error", e)
					self.namelist.append(name)
					self.mp3list.append(filename)
					self.datelist.append(date)
					self.artistlist.append(artist)
					self.albumlist.append(album)
					self.numberlist.append(number)
					self.tracklist.append(track)
					self.yearlist.append(year)
					self.genrelist.append(genre)
					self.runtimelist.append(runtime)
					self.bitratelist.append(bitrate)
					self.posterlist.append(poster)
			if self.showfolder == True:
				self.namelist.append("<List of MP3 Folder>")
				self.mp3list.append(config.plugins.mp3browser.mp3folder.value + "...")
				self.datelist.append("")
				self.artistlist.append("")
				self.albumlist.append("")
				self.numberlist.append("")
				self.tracklist.append("")
				self.yearlist.append("")
				self.genrelist.append("")
				self.runtimelist.append("")
				self.bitratelist.append("")
				self.posterlist.append("/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/default_folder.png")
			self.maxentry = len(self.namelist)
			self.posterREST = self.maxentry % self.posterALL
			if self.posterREST == 0:
				self.posterREST = self.posterALL
			self.pagemax = self.maxentry // self.posterALL
			if self.maxentry % self.posterALL > 0:
				self.pagemax += 1
			self.makePoster(self.pagecount - 1)
			self.paintFrame()
			if self.infofull == True:
				try:
					self.makeInfo(self.index)
				except IndexError as e:
					print("[MP3Browser][makeMP3   ] Indexerror",  e)
					
# toggle 0,1,2 choices=[("oninfo", "Info Button"), ("info", "Show Info"), ("always", "Show Info & Lyrics")
			if self.toggle == 2:
				self["discogsback"].show()
				self.getLyrics()
			elif self.toggle == 3:
				self.hideInfo()
				self["infoback"].show()
				self.getDiscogs()
			self.ready = True

# toggle 0,1,2 choices=[("oninfo", "Info Button"), ("info", "Show Info"), ("always", "Show Info & Lyrics")

	def nextMP3(self):
		print("[MP3Browser][nextMP3] Index, toggle",  self.index, "   ", self.toggle)    
		if self.playready == True:
			if self.random == False:
				self.index += 1
			else:
				self.index = random.randint(0, self.maxentry)
			if self.index == self.maxentry:
				self.index = 0
			self.ok()
			self.walloldindex = self.wallindex
			self.wallindex += 1
			if self.pagecount == self.pagemax and self.wallindex > self.posterREST - 1:
				self.wallindex = 0
				self.pagecount = 1
				self.makePoster(self.pagecount - 1)
			elif self.wallindex == self.posterALL:
				self.wallindex = 0
				self.pagecount += 1
				self.makePoster(self.pagecount - 1)
			self.paintFrame()
			if self.infofull == True:
				try:
					self.makeInfo(self.index)
				except IndexError as e:
					print("[MP3Browser][ nextMP3  ] Indexerror",  e)

			if self.toggle == 2:
				self.getLyrics()
			elif self.toggle == 3:
				self.hideInfo()
				self["infoback"].show()
				self.getDiscogs()

	def showMP3(self):
		if self.ready == True:
			mp3s = ""
			if fileExists(self.database):
				lines = fileReadLines(self.database)
				for line in lines:
					if self.filter in line:
						mp3line = line.split(":::")
						try:
							mp3 = mp3line[3] + " - " + mp3line[6]
						except IndexError as e:
							mp3 = " "

						if mp3 != " ":
							mp3s = mp3s + mp3 + ":::"

				if self.showfolder == True:
					mp3s = mp3s + "<List of MP3 Folder>" + ":::"
				self.mp3s = [ i for i in mp3s.split(":::") ]
				self.mp3s.pop()
				self.session.openWithCallback(self.gotoMP3, allMP3List, self.mp3s, self.index)

	def gotoMP3(self, index):
		if index is not None:
			self.index = index
			self.walloldindex = self.wallindex
			self.wallindex = self.index % self.posterALL
			self.pagecount = self.index // self.posterALL + 1
			self.makePoster(self.pagecount - 1)
			self.paintFrame()
			if self.infofull == True:
				try:
					self.makeInfo(self.index)
				except IndexError as e:
					print("[MP3Browser][gotoMP3   ] Indexerror",  e)

			if self.toggle == 2:
				self.getLyrics()
			elif self.toggle == 3:
				self.hideInfo()
				self["infoback"].show()
				self.getDiscogs()
		return

	def deleteMP3(self):
		if self.ready == True:
			if self.toggle == 0 or self.toggle == 1:
				try:
					name = self.namelist[self.index]
					self.session.openWithCallback(self.deleteMP3_return, MessageBox, _("\nThis will delete %s from the Database and from the MP3 Folder!\n\nDo you want to continue?") % name, MessageBox.TYPE_YESNO)
				except IndexError as e:
					print("[MP3Browser][deleteMP3   ] Indexerror",  e)

			elif self.toggle == 2:
				try:
					self.artist = self.artistlist[self.index]
					self.track = self.tracklist[self.index]
					self.session.openWithCallback(self.deleteMP3_return, MessageBox, _("\nThis will delete the Lyrics of %s - %s!\n\nDo you want to continue?") % (self.artist, self.track), MessageBox.TYPE_YESNO)
				except IndexError as e:
					print("[MP3Browser][deletMP3   ] Indexerror",  e)

			elif self.toggle == 3:
				try:
					self.artist = self.artistlist[self.index]
					self.session.openWithCallback(self.deleteMP3_return, MessageBox, _("\nThis will delete the Discogs Information and Google Poster of %s!\n\nDo you want to continue?") % self.artist, MessageBox.TYPE_YESNO)
				except IndexError as e:
					print("[MP3Browser][deleteMP3   ] Indexerror",  e)

	def deleteMP3_return(self, answer):
		if answer is True:
			if self.toggle == 0 or self.toggle == 1:
				try:
					mp3 = self.mp3list[self.index]
					filename = sub(".*?[/]", "", mp3)
					lyricsfile = join(config.plugins.mp3browser.cachefolder.value, filename)
					lyricsfile = lyricsfile.replace(".MP3", ".lyrics")
					lyricsfile = lyricsfile.replace(".mp3", ".lyrics")
					if fileExists(lyricsfile):
						remove(lyricsfile)
					if fileExists(mp3):
						remove(mp3)
					mp3 = sub("\\(|\\)|\\[|\\]|\\+|\\?", ".", mp3)
					data = open(self.database).read()
					for line in data.split("\n"):
						if search(mp3, line) is not None:
							data = data.replace(line + "\n", "")

					fileWriteLine(self.database, data)
					if self.index == self.maxentry - 1:
						self.index -= 1
					self.makeMP3(self.filter)
				except IndexError as e:
					print("[MP3Browser][deleteMP3_return   ] Indexerror",  e)

			elif self.toggle == 2:
				try:
					filepath = self.mp3list[self.index]
					filename = sub(".*?[/]", "", filepath)
					lyricsfile = join(config.plugins.mp3browser.cachefolder.value, filename)
					lyricsfile = lyricsfile.replace(".MP3", ".lyrics")
					lyricsfile = lyricsfile.replace(".mp3", ".lyrics")
					if fileExists(lyricsfile):
						remove(lyricsfile)
					self.lyrics = "ChartLyrics:\nNo Lyrics for %s - %s found." % (self.artist, self.track)
					self["discogs"].setText(self.lyrics)
					self["discogs"].show()
				except IndexError as e:
					print("[MP3Browser][deleteMP3_return] Indexerror",  e)

			elif self.toggle == 3:
				discogsfile = join(config.plugins.mp3browser.cachefolder.value, self.artist.replace("/", "_") + ".discogs")
				posterjpeg = discogsfile.replace(".discogs", ".jpeg")
				posterpng = discogsfile.replace(".discogs", ".png")
				posterbmp = discogsfile.replace(".discogs", ".bmp")
				if fileExists(discogsfile):
					remove(discogsfile)
				if fileExists(posterjpeg):
					remove(posterjpeg)
				if fileExists(posterpng):
					remove(posterpng)
				if fileExists(posterbmp):
					remove(posterbmp)
				self.profile = "Discogs.com:\nArtist %s not found." % self.artist
				self["discogs"].setText(self.profile)
				self["googlePoster"].hide()
		return

	def shuffleMP3(self):
		if self.ready == True:
			self.ready = False
			if self.random == False:
				self.session.openWithCallback(self.shuffleMP3_return, switchScreen, 2, "shuffle")
			else:
				self.session.openWithCallback(self.shuffleMP3_return, switchScreen, 1, "shuffle")

	def shuffleMP3_return(self, number):
		if number is None:
			self.ready = True
		elif number == 1:
			self.random = False
			self.ready = True
		elif number == 2:
			self.random = True
			self.ready = True
		return


	def makePoster(self, page):
		for x in list(range(self.posterALL)):       # self.posterALL = 45
			# print(f"[MP3Browser][makePoster]2 range:{list(range(self.posterALL))}")
			index = x + page * self.posterALL
			self.dbcountmax = len(self.mp3list)-1
			# print(f"[MP3Browser][makePoster]2 index:{index}, x:{x}, page:{page}, self.posterALL:{self.posterALL}, self.dbcountmax:{self.dbcountmax}")            
			if index > self.dbcountmax:
				index = self.dbcountmax
			posterurl = self.posterlist[index]
			poster = sub(".*?[/]", "", posterurl)
			poster = join(config.plugins.mp3browser.cachefolder.value, poster)
			# print("[MP3Browser][makePoster]2 posterurl, poster",  posterurl, poster)
			self.artist = self.artistlist[index]
			self.track = self.tracklist[index]
			if self.lastArtist != self.artist:
				self.lastPoster = ""
				self.lastArtist = ""
			artistntrack = transLYRICSTIME(self.artist + "-" + self.track)
			discogsfile = join(config.plugins.mp3browser.cachefolder.value, artistntrack + ".jpg")
			# print("[MP3Browser][makePoster]2 discogsfile",  discogsfile)
			if fileExists(discogsfile):
				poster = discogsfile
				self.lastPoster = poster
				self.lastArtist = self.artist
			elif fileExists(poster) and "default" not in posterurl:
				self[("poster" + str(x))].instance.setPixmapFromFile(poster)
				self[("poster" + str(x))].show()
			elif "default" in posterurl:
				# print("[MP3Browser][makePoster]2 found default in posterurl",  posterurl)
				poster = defaultfolder_png if "default_folder" in posterurl else default_png
			elif search("http", posterurl) is not None:
				# print("[MP3Browser][makePoster]2 found http not default in posterurl",  posterurl)
				callInThread(threadGetPage, url=posterurl, success=self.getPoster, file=poster, key=x, fail=self.downloadError)
			else:
				filename = self.mp3list[index]
				tag = ID3(filename)
				poster = tag.getall("APIC")
				if len(poster) > 0:
					f = open(posterurl, "wb")
					f.write(poster[0].data)
					f.close()
					poster = posterurl
				else:    
					poster = defaultfolder_png if "default_folder" in posterurl else default_png                    
			if "default" in poster and self.artist == self.lastArtist:
					poster = self.lastPoster
			self[("poster" + str(x))].instance.setPixmapFromFile(poster)
			self[("poster" + str(x))].show()
		self[("poster_back" + str(self.wallindex))].hide()


	def getPoster(self, output, poster, x):
		f = open(poster, "wb")
		f.write(output)
		f.close()
		if fileExists(poster):
			self[("poster" + str(x))].instance.setPixmapFromFile(poster)
			self[("poster" + str(x))].show()

	def renewCover(self):
		return

	def makeFav(self):
		if self.ready == True:
			if self.fav == False:
				artist = self.artistlist[self.index]
				track = self.tracklist[self.index]
				self.session.openWithCallback(self.choiceFavFalse, ChoiceBox, title="MP3 Favourites", list=[("Open Favourites", "open"), ("Edit Favourites", "edit"), ("Add %s to Favourites" % (artist + " - " + track), "add")])
			else:
				self.session.openWithCallback(self.choiceFavTrue, ChoiceBox, title="MP3 Favourites", list=[("Close Favourites", "close"), ("Edit Favourites", "edit")])

	def choiceFavFalse(self, choice):
		choice = choice and choice[1]
		if choice == "open":
			self.fav = True
			self.index = 0
			self.walloldindex = 0
			self.wallindex = 0
			self.pagecount = 1
			self.database = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/favorites"
			self.makeMP3(self.filter)
		elif choice == "edit":
			self.session.open(mp3Fav, False)
		else:
			f = open(self.favorites, "a")
			data = self.namelist[self.index] + ":::" + self.mp3list[self.index] + ":::" + self.datelist[self.index] + ":::" + self.artistlist[self.index] + ":::" + self.albumlist[self.index] + ":::" + self.numberlist[self.index] + ":::" + self.tracklist[self.index] + ":::" + self.yearlist[self.index] + ":::" + self.genrelist[self.index] + ":::" + self.runtimelist[self.index] + ":::" + self.bitratelist[self.index] + ":::" + self.posterlist[self.index] + ":::"
			f.write(data)
			f.write(linesep)
			f.close()
			self.session.open(mp3Fav, True)

	def choiceFavTrue(self, choice):
		choice = choice and choice[1]
		if choice == "close":
			self.fav = False
			self.index = 0
			self.walloldindex = 0
			self.wallindex = 0
			self.pagecount = 1
			self.database = config.plugins.mp3browser.DBfolder.value
			self.makeMP3(self.filter)
		elif choice == "edit":
			self.session.openWithCallback(self.returnFavEdit, mp3Fav, False)

	def returnFavEdit(self, edit):
		if edit is None:
			pass
		else:
			self.index = 0
			self.walloldindex = 0
			self.wallindex = 0
			self.pagecount = 1
			self.makeMP3(self.filter)
		return

	def switchStyle(self):
		if self.ready == True:
			self.ready = False
			self.session.openWithCallback(self.returnStyle, switchScreen, 1, "style")

	def returnStyle(self, number):
		if number is None or number == 2:
			self.ready = True
		elif number == 1:
			if config.plugins.mp3browser.lastmp3.value == "yes":
				try:
					mp3 = self.mp3list[self.index]
					fileWriteLine(self.lastfile, mp3)
				except IndexError as e:
					print(f"[MP3Browser][returnStyle] self.index:{self.index}, Indexerror:{e}")

			config.usage.on_movie_stop.value = self.movie_stop
			config.usage.on_movie_eof.value = self.movie_eof
			self.session.openWithCallback(self.close, mp3BrowserMetrix, self.index, self.filter)
		return

	def startMoveCovers(self):
		try:
			cover = self.posterlist[self.index]
			cover = sub(".*?[/]", "", cover)
			cover = join(config.plugins.mp3browser.cachefolder.value, cover)
			if fileExists(cover):
				self.session.open(moveCover, cover)
		except IndexError as e:
			print("[MP3Browser][startMoveCovers   ] Indexerror",  e)

	def moveCovers(self):
		if self.ready == True:
			self.ready = False
			if self.move == False:
				self.session.openWithCallback(self.returnMoveCovers, switchScreen, 2, "move")
			else:
				self.session.openWithCallback(self.returnMoveCovers, switchScreen, 1, "move")

	def returnMoveCovers(self, number):
		if number is None:
			self.ready = True
		elif number == 1:
			self.move = False
			self.ready = True
		elif number == 2:
			self.move = True
			self.ready = True
			try:
				cover = self.posterlist[self.index]
				cover = sub(".*?[/]", "", cover)
				cover = join(config.plugins.mp3browser.cachefolder.value, cover)
				if fileExists(cover):
					self.session.open(moveCover, cover)
			except IndexError as e:
				print("[MP3Browser][returnMoveCovers] Indexerror",  e)

		return

	def toggleInfo(self):
		if self.ready == True:
			if self.toggle == 0:
				self.toggle = 1
				self.infofull = True
				try:
					self.makeInfo(self.index)
				except IndexError as e:
					self.showInfo()

			elif self.toggle == 1:
				self.toggle = 2
				self["discogsback"].show()
				self.getLyrics()
			elif self.toggle == 2:
				if config.plugins.mp3browser.discogs.value == "show":
					self.toggle = 3
					self.hideInfo()
					self["infoback"].show()
					self.getDiscogs()
				else:
					self.toggle = 0
					self.infofull = False
					self.hideInfo()
					self.hideDiscogs()
			else:
				self.toggle = 0
				self.infofull = False
				self.hideInfo()
				self.hideDiscogs()

	def showInfo(self):
		self["name"].show()
		self["artist"].show()
		self["Artist"].show()
		self["album"].show()
		self["Album"].show()
		self["number"].show()
		self["Number"].show()
		self["track"].show()
		self["Track"].show()
		self["year"].show()
		self["Year"].show()
		self["runtime"].show()
		self["Runtime"].show()
		self["bitrate"].show()
		self["Bitrate"].show()
		self["genre"].show()
		self["Genre"].show()
		self["infoback"].show()

	def hideInfo(self):
		self["name"].hide()
		self["artist"].hide()
		self["Artist"].hide()
		self["album"].hide()
		self["Album"].hide()
		self["number"].hide()
		self["Number"].hide()
		self["track"].hide()
		self["Track"].hide()
		self["year"].hide()
		self["Year"].hide()
		self["runtime"].hide()
		self["Runtime"].hide()
		self["bitrate"].hide()
		self["Bitrate"].hide()
		self["genre"].hide()
		self["Genre"].hide()
		self["infoback"].hide()

	def hideDiscogs(self):
		self["discogs"].hide()
		self["googlePoster"].hide()
		self["discogsback"].hide()

	def makeInfo(self, count):
		self["infoback"].show()
		try:
			name = self.artistlist[count] + " - " + self.tracklist[count]
			if self.showfolder == True and name == " - ":
				self["name"].setText("<List of MP3 Folder>")
				self["name"].show()
				self["name"].show()
				self["Artist"].hide()
				self["artist"].hide()
				self["Album"].hide()
				self["album"].hide()
				self["Number"].hide()
				self["number"].hide()
				self["Track"].hide()
				self["track"].hide()
				self["Year"].hide()
				self["year"].hide()
				self["Runtime"].hide()
				self["runtime"].hide()
				self["Bitrate"].hide()
				self["bitrate"].hide()
				self["Genre"].hide()
				self["genre"].hide()
				return
			if len(name) > 63:
				if name[62:63] == " ":
					name = name[0:62]
				else:
					name = name[0:63] + "FIN"
					name = sub(" \\S+FIN", "", name)
				name = name + "..."
			self["name"].setText(str(name))
			self["name"].show()
			self.setTitle(str(name))
		except IndexError as e:
			self["name"].hide()

		self["Artist"].hide()
		self["artist"].hide()
		self["Album"].hide()
		self["album"].hide()
		self["Number"].hide()
		self["number"].hide()
		self["Track"].hide()
		self["track"].hide()
		self["Year"].hide()
		self["year"].hide()
		self["Runtime"].hide()
		self["runtime"].hide()
		self["Bitrate"].hide()
		self["bitrate"].hide()
		self["Genre"].hide()
		self["genre"].hide()

		try:
			artist = self.artistlist[self.index]
			self["Artist"].show()
			self["artist"].setText(artist)
			self["artist"].show()
			album = self.albumlist[self.index]
			self["Album"].show()
			self["album"].setText(album)
			self["album"].show()
			number = self.numberlist[self.index]
			self["Number"].show()
			self["number"].setText(number)
			self["number"].show()
			track = self.tracklist[self.index]
			self["Track"].show()
			self["track"].setText(track)
			self["track"].show()
			year = self.yearlist[self.index]
			self["Year"].show()
			self["year"].setText(year)
			self["year"].show()
			runtime = self.runtimelist[self.index]
			self["Runtime"].show()
			self["runtime"].setText(runtime)
			self["runtime"].show()
			bitrate = self.bitratelist[self.index]
			self["Bitrate"].show()
			self["bitrate"].setText(bitrate)
			self["bitrate"].show()
			genres = self.genrelist[self.index]
			self["Genre"].show()
			self["genre"].setText(genres)
			self["genre"].show()
		except IndexError as e:
			pass

	def getLyrics(self):
		self.ready = False
		# print("[MP3Browser][getLyrics] entered")
		try:
			self.artist = self.artistlist[self.index]
			self.track = self.tracklist[self.index]
		except IndexError as e:
				print("[MP3Browser][makeLyrics] Indexerror",  e)
				return            
		if self.artist == self.artistold and self.track == self.trackold:
			self["discogs"].setText(self.lyrics)
			self["discogs"].show()
			self.ready = True
		else:
			self.artistold = self.artist
			self.trackold = self.track
			filepath = self.mp3list[self.index]
			filename = sub(".*?[/]", "", filepath)
			lyricsfile = join(config.plugins.mp3browser.cachefolder.value, filename)
			lyricsfile = lyricsfile.replace(".MP3", ".lyrics")
			lyricsfile = lyricsfile.replace(".mp3", ".lyrics")
			if fileExists(lyricsfile):
				self.lyrics = open(lyricsfile).read()
				self.lyrics = transHTML(self.lyrics)
				self["discogs"].setText(self.lyrics)
				self["discogs"].show()
				self.ready = True
			else:
				self["discogs"].setText("")
				artist = transCHARTLYRICS(self.artist.lower())
				track = transCHARTLYRICS(self.track.lower())
				url = "http://api.chartlyrics.com/apiv1.asmx/SearchLyricDirect?artist=%s&song=%s" % (artist, track)
				callInThread(threadGetPage, url=url, success=self.makeLyrics, fail=self.downloadLyricsError)

	def makeLyrics(self, output):
		# print("[MP3Browser][makeLyrics] entered output is  ", output)
		output = output.decode()    
		lyrics = findall("<Lyric>(.*?)</Lyric>", output, flags=DOTALL)
		if lyrics:
			self.lyrics = lyrics[0].replace("amp;", "")
			self["discogs"].setText(self.lyrics)
			self["discogs"].show()
			filepath = self.mp3list[self.index]
			filename = sub(".*?[/]", "", filepath)
			lyricsfile = join(config.plugins.mp3browser.cachefolder.value, filename)
			lyricsfile = lyricsfile.replace(".MP3", ".lyrics")
			lyricsfile = lyricsfile.replace(".mp3", ".lyrics")
			f = open(lyricsfile, "w")
			f.write(self.lyrics)
			f.close()
		else:
			self.lyrics = "ChartLyrics/lyrics.time:\nNo Lyrics for %s - %s found." % (self.artist, self.track)
			self["discogs"].setText(self.lyrics)
			self["discogs"].show()
		self.ready = True

	def downloadLyricsError(self, output):
		self.lyrics = "ChartLyrics/lyrics.time:\nNo Lyrics for %s - %s found." % (self.artist, self.track)
		self["discogs"].setText(self.lyrics)
		self["discogs"].show()
		self.ready = True

	def getDiscogs(self):
		self.ready = True

	def paintFrame(self):
		try:
			pos = self.positionlist[self.wallindex]
			self["frame"].instance.move(ePoint(pos[0], pos[1]))
			self[("poster_back" + str(self.walloldindex))].show()
			self[("poster_back" + str(self.wallindex))].hide()
			posterurl = self.posterlist[self.index]
			poster = sub(".*?[/]", "", posterurl)
			poster = join(config.plugins.mp3browser.cachefolder.value, poster)
			if fileExists(poster):
				self["frame"].instance.setPixmapFromFile(poster)
		except IndexError as e:
			print("[MP3Browser][paintFrame] Indexerror",  e)
		return

	def ok(self):
		if self.ready == True:
			try:
				filename = self.mp3list[self.index]
				if self.showfolder == True and filename.endswith("..."):
					self.filterFolder()
					return
				sref = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + filename)
				sref.setName(self.artistlist[self.index] + " - " + self.tracklist[self.index])
				if self.background == True:
					self.playready = True
					self.session.nav.stopService()
					self.session.nav.playService(sref)
				else:
					self.playready = True
					self.session.open(MoviePlayer, sref)
				if self.move == True:
					self.coverTimer.stop()
					self.coverTimer.start(500, True)
			except IndexError as e:
				print("[MP3Browser][ok] Indexerror",  e)

	def stop(self):
		self.playready = False
		if self.background == True:
			self.session.nav.stopService()
			self.session.nav.playService(self.oldService)
		if self.move == True:
			self.coverTimer.stop()

	def down(self):
		if self.ready == True:
			if self.toggle == 2 or self.toggle == 3:
				self["discogs"].pageDown()
			else:
				self.walloldindex = self.wallindex
				self.wallindex += self.posterX
				if self.pagecount == self.pagemax - 1 and self.wallindex > self.posterALL + self.posterREST - 2:
					self.wallindex = self.posterREST - 1
					if self.wallindex < 0:
						self.wallindex = 0
					self.pagecount += 1
					self.makePoster(self.pagecount - 1)
					self.index = self.maxentry - 1
				elif self.pagecount == self.pagemax and self.wallindex > self.posterREST - 1:
					if self.wallindex >= self.posterX:
						self.wallindex = self.wallindex % self.posterX
					self.pagecount = 1
					self.makePoster(self.pagecount - 1)
					if self.wallindex >= self.maxentry % self.posterX:
						self.index = self.index + (self.posterX + self.maxentry % self.posterX)
						if self.index >= self.maxentry:
							self.index = self.index - self.maxentry
					else:
						self.index = self.index + self.maxentry % self.posterX
						if self.index >= self.maxentry:
							self.index = self.index - self.maxentry
				elif self.wallindex > self.posterALL - 1:
					self.wallindex = self.wallindex - self.posterALL
					if self.wallindex < 0:
						self.wallindex = 0
					self.pagecount += 1
					self.makePoster(self.pagecount - 1)
					self.index = self.index + self.posterX
					if self.index >= self.maxentry:
						self.index = self.index - self.maxentry
				else:
					self.index = self.index + self.posterX
					if self.index >= self.maxentry:
						self.index = self.index - self.maxentry
				self.paintFrame()
				if self.infofull == True:
					self.makeInfo(self.index)
				if self.toggle == 2:
					self.getLyrics()
				elif self.toggle == 3:
					self.hideInfo()
					self["infoback"].show()
					self.getDiscogs()

	def up(self):
		if self.ready == True:
			if self.toggle == 2 or self.toggle == 3:
				self["discogs"].pageUp()
			else:
				self.walloldindex = self.wallindex
				self.wallindex -= self.posterX
				if self.wallindex < 0:
					if self.pagecount == 1:
						if self.walloldindex < self.posterREST % self.posterX:
							self.wallindex = self.posterREST // self.posterX * self.posterX + self.walloldindex
							if self.wallindex < 0:
								self.wallindex = 0
							self.index = self.index - self.posterREST % self.posterX
							if self.index < 0:
								self.index = self.maxentry + self.index
						else:
							self.wallindex = self.posterREST - 1
							if self.wallindex < 0:
								self.wallindex = 0
							self.index = self.maxentry - 1
						self.pagecount = self.pagemax
						self.makePoster(self.pagecount - 1)
					else:
						self.wallindex = self.posterALL + self.wallindex
						if self.wallindex < 0:
							self.wallindex = 0
						self.pagecount -= 1
						self.makePoster(self.pagecount - 1)
						self.index = self.index - self.posterX
						if self.index < 0:
							self.index = self.maxentry + self.index
				else:
					self.index = self.index - self.posterX
					if self.index < 0:
						self.index = self.maxentry + self.index
				self.paintFrame()
				if self.infofull == True:
					self.makeInfo(self.index)
				if self.toggle == 2:
					self.getLyrics()
				elif self.toggle == 3:
					self.hideInfo()
					self["infoback"].show()
					self.getDiscogs()

	def rightDown(self):
		if self.ready == True:
			self.walloldindex = self.wallindex
			self.wallindex += 1
			if self.pagecount == self.pagemax and self.wallindex > self.posterREST - 1:
				self.wallindex = 0
				self.pagecount = 1
				self.makePoster(self.pagecount - 1)
			elif self.wallindex == self.posterALL:
				self.wallindex = 0
				self.pagecount += 1
				self.makePoster(self.pagecount - 1)
			self.index += 1
			if self.index == self.maxentry:
				self.index = 0
			self.paintFrame()
			if self.infofull == True:
				self.makeInfo(self.index)
			if self.toggle == 2:
				self.getLyrics()
			elif self.toggle == 3:
				self.hideInfo()
				self["infoback"].show()
				self.getDiscogs()

	def leftUp(self):
		if self.ready == True:
			self.walloldindex = self.wallindex
			self.wallindex -= 1
			if self.wallindex < 0:
				if self.pagecount == 1:
					self.wallindex = self.posterREST - 1
					self.pagecount = self.pagemax
				else:
					self.wallindex = self.posterALL - 1
					self.pagecount -= 1
				if self.wallindex < 0:
					self.wallindex = 0
				self.makePoster(self.pagecount - 1)
			self.index -= 1
			if self.index < 0:
				self.index = self.maxentry - 1
			self.paintFrame()
			if self.infofull == True:
				self.makeInfo(self.index)
			if self.toggle == 2:
				self.getLyrics()
			elif self.toggle == 3:
				self.hideInfo()
				self["infoback"].show()
				self.getDiscogs()

	def PageDown(self):
		if self.ready == True:
			self.walloldindex = self.wallindex
			self.wallindex += self.posterALL
			if self.pagecount == self.pagemax - 1 and self.wallindex > self.posterALL + self.posterREST - 2:
				self.wallindex = self.posterREST - 1
				if self.wallindex < 0:
					self.wallindex = 0
				self.pagecount += 1
				self.makePoster(self.pagecount - 1)
				self.index = self.maxentry - 1
			elif self.pagecount == self.pagemax and self.wallindex > self.posterREST - 1:
				if self.wallindex >= self.posterX:
					self.wallindex = self.wallindex % self.posterX
				self.pagecount = 1
				self.makePoster(self.pagecount - 1)
				if self.wallindex >= self.maxentry % self.posterX:
					self.index = self.wallindex
					if self.index >= self.maxentry:
						self.index = self.index - self.maxentry
				else:
					self.index = self.index + self.maxentry % self.posterX
					if self.index >= self.maxentry:
						self.index = self.index - self.maxentry
			elif self.wallindex > self.posterALL - 1:
				self.wallindex = self.wallindex - self.posterALL
				if self.wallindex < 0:
					self.wallindex = 0
				self.pagecount += 1
				self.makePoster(self.pagecount - 1)
				self.index = self.index + self.posterALL
				if self.index >= self.maxentry:
					self.index = self.index - self.maxentry
			else:
				self.index = self.index + self.posterALL
				if self.index >= self.maxentry:
					self.index = self.index - self.maxentry
			self.paintFrame()
			if self.infofull == True:
				self.makeInfo(self.index)
			if self.toggle == 2:
				self.getLyrics()
			elif self.toggle == 3:
				self.hideInfo()
				self["infoback"].show()
				self.getDiscogs()

	def PageUp(self):
		if self.ready == True:
			self.walloldindex = self.wallindex
			self.wallindex -= self.posterALL
			if self.wallindex < 0:
				if self.pagecount == 1:
					if self.walloldindex < self.posterREST % self.posterX:
						self.wallindex = self.posterREST // self.posterX * self.posterX + self.walloldindex
						if self.wallindex < 0:
							self.wallindex = 0
						self.index = self.index - self.posterREST % self.posterX
						if self.index < 0:
							self.index = self.maxentry + self.index
					else:
						self.wallindex = self.posterREST - 1
						if self.wallindex < 0:
							self.wallindex = 0
						self.index = self.maxentry - 1
					self.pagecount = self.pagemax
					self.makePoster(self.pagecount - 1)
				else:
					self.wallindex = self.posterALL + self.wallindex
					if self.wallindex < 0:
						self.wallindex = 0
					self.pagecount -= 1
					self.makePoster(self.pagecount - 1)
					self.index = self.index - self.posterALL
					if self.index < 0:
						self.index = self.maxentry + self.index
			else:
				self.index = self.index - self.posterALL
				if self.index < 0:
					self.index = self.maxentry + self.index
			self.paintFrame()
			if self.infofull == True:
				self.makeInfo(self.index)
			if self.toggle == 2:
				self.getLyrics()
			elif self.toggle == 3:
				self.hideInfo()
				self["infoback"].show()
				self.getDiscogs()

	def gotoEnd(self):
		if self.ready == True:
			self.walloldindex = self.wallindex
			self.wallindex = self.posterREST - 1
			if self.wallindex < 0:
				self.wallindex = 0
			self.pagecount = self.pagemax
			self.makePoster(self.pagecount - 1)
			self.index = self.maxentry - 1
			self.paintFrame()
			if self.infofull == True:
				self.makeInfo(self.index)

			if self.toggle == 2:
				self.getLyrics()
			elif self.toggle == 3:
				self.hideInfo()
				self["infoback"].show()
				self.getDiscogs()

	def gotoABC(self):
		self.session.openWithCallback(self.enterABC, getABC, self.ABC, False)

	def gotoXYZ(self):
		self.session.openWithCallback(self.enterABC, getABC, self.ABC, True)

	def enterABC(self, ABC):
		if ABC is None:
			pass
		else:
			self.ABC = ABC
			ABC = ABC[0].lower()
			try:
				self.index = next(index for index, value in enumerate(self.artistlist) if value.lower().replace("the ", "").startswith(ABC))
				self.walloldindex = self.wallindex
				self.wallindex = self.index % self.posterALL
				self.pagecount = self.index // self.posterALL + 1
				self.makePoster(self.pagecount - 1)
				self.paintFrame()
				if self.infofull == True:
					try:
						self.makeInfo(self.index)
					except IndexError as e:
						print("[MP3Browser][enterABC] Indexerror",  e)

				if self.toggle == 2:
					self.getLyrics()
				elif self.toggle == 3:
					self.hideInfo()
					self["infoback"].show()
					self.getDiscogs()
			except StopIteration as e:
				print("[MP3Browser][enterABC] iteration errors",  e)

		return

	def filterFolder(self):
		if self.ready == True:
			self.folders, max = filterFolderSetup()
			if fileExists(self.database):			
				self.session.openWithCallback(self.filter_return, filterList, self.folders, "MP3 Folder Selection", len(self.folders), max)
		return

	def filterArtist(self):
		if self.ready == True and fileExists(self.database):
			self.artists, max = filterSetup(self.database, 3)
			self.session.openWithCallback(self.filter_return, filterList, self.artists, "Artist Selection", len(self.artists), max)

	def filterAlbum(self):
		if self.ready == True and fileExists(self.database):
			self.albums, max = filterSetup(self.database, 4)
			self.session.openWithCallback(self.filter_return, filterList, self.albums, "Album Selection", len(self.albums), max)

	def filterGenre(self):
		if self.ready == True and fileExists(self.database):
			self.genres, max = filterSetup(self.database, 8)
			self.session.openWithCallback(self.filter_return, filterList, self.genres, "Genre Selection", len(self.genres), max)

	def filter_return(self, filter):
		if filter and filter is not None:
			self[("poster_back" + str(self.wallindex))].show()
			self.wallindex = 0
			self.pagecount = 1
			self.walloldindex = 0
			self.pagemax = 1
			self.index = 0
			self.makeMP3(filter)
		return

	def databaseEdit(self):
		if self.ready == True:
			try:
				mp3 = self.mp3list[self.index]
			except IndexError as e:
				mp3 = "None"

			self.session.openWithCallback(self.databaseEdit_return, mp3DatabaseStart, mp3)

	def databaseEdit_return(self, changed):
		if changed is True:
			mp3 = self.mp3list[self.index]
			mp3 = sub("\\(|\\)|\\[|\\]|\\+|\\?", ".", mp3)
			databaseSort(self.database)
			f = open(self.database, "r")
			count = 0
			for line in f:
				if self.filter in line:
					if mp3 in line:
						self.index = count
						break
					count += 1

			f.close()
			self.makeMP3(self.filter)

	def showPath(self):
		if self.ready == True:
			self.session.open(MessageBox, _("\nMP3 File:\n%s") % self.mp3list[self.index], MessageBox.TYPE_INFO, close_on_any_key=True)

	def getIndex(self, list):
		return list.getSelectedIndex()

	def download(self, link, name):
		print("[download] link=%s, name =%s" % (link, name))
		callInThread(threadGetPage, url=link, success=name, fail=self.downloadError)

	def downloadError(self, output):
		self.ready = True

	def zap(self):
		servicelist = self.session.instantiateDialog(ChannelSelection)
		self.session.execDialog(servicelist)

	def showHelp(self):
		if self.showhelp == False:
			self.showhelp = True
			self.toogleHelp.show()
		else:
			self.showhelp = False
			self.toogleHelp.hide()

	def infoScreen(self):
		self.session.open(infoScreenMP3Browser, None, True)
		return

	def hideScreen(self):
		if self.hideflag == True:
			self.hideflag = False
			count = 40
			while count > 0:
				count -= 1

		else:
			self.hideflag = True
			count = 0
			while count < 40:
				count += 1

	def exit(self):
		if self.showhelp == True:
			self.showhelp = False
			self.toogleHelp.hide()
		elif config.plugins.mp3browser.showinfo.value == "oninfo" and self.infofull == True:
			self.toggle = 0
			self.infofull = False
			self.hideInfo()
			self.hideDiscogs()
		elif config.plugins.mp3browser.showinfo.value == "info" and self.toggle > 1:
			self.toggle = 1
			self.hideDiscogs()
			try:
				self.makeInfo(self.index)
			except IndexError as e:
				self.showInfo()

		elif config.plugins.mp3browser.showinfo.value == "always" and self.toggle == 3:
			self.toggle = 2
			self["googlePoster"].hide()
			self["discogs"].hide()
			try:
				self.makeInfo(self.index)
			except IndexError as e:
				self.showInfo()

			self.getLyrics()
		else:
			self.playready = False
			if self.background == True or config.plugins.mp3browser.showtv.value == "hide":
				self.session.nav.playService(self.oldService)
			if config.plugins.mp3browser.lastmp3.value == "yes":
				try:
					mp3 = self.mp3list[self.index]
					fileWriteLine(self.lastfile, mp3)
				except IndexError as e:
					print("[MP3Browser][exit] Indexerror",  e)

			if config.plugins.mp3browser.lastfilter.value == "yes":
				fileWriteLine(self.lastfilter, self.filter)
			self.session.deleteDialog(self.toogleHelp)
			config.usage.on_movie_stop.value = self.movie_stop
			config.usage.on_movie_eof.value = self.movie_eof
			self.close()


class mp3DatabaseStart(Screen):
	skin = """
	<screen position="center,center" size="730,300" title=" ">
		<ePixmap position="0,0" size="730,28" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/setup/logo.png" zPosition="1"/>
		<widget name="list" position="10,38" size="710,250" scrollbarMode="showOnDemand" zPosition="1" />
		<widget name="list2" position="10,38" size="710,250" scrollbarMode="showOnDemand" zPosition="1" />
	</screen>"""

	def __init__(self, session, mp3):
		Screen.__init__(self, session)
		print("[MP3Browser][mp3DatabaseStart] ")        
		self.hideflag = True
		self.ready = False
		self.change = False
		self.mp3 = mp3
		self.lang = config.plugins.mp3browser.language.value
		self["list"] = ItemList([])
		self["list2"] = ItemList([])
		self.actlist = "list"
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActions", "ChannelSelectBaseActions", "HelpActions", "NumberActions"], {"ok": self.ok, 
		   "cancel": self.exit, 
		   "right": self.rightDown, 
		   "left": self.leftUp, 
		   "down": self.down, 
		   "up": self.up, 
		   "nextBouquet": self.zap, 
		   "prevBouquet": self.zap, 
		   "red": self.infoScreen, 
		   "yellow": self.infoScreen, 
		   "blue": self.hideScreen, 
		   "0": self.gotoEnd, 
		   "displayHelp": self.infoScreen}, -1)
		self.database = config.plugins.mp3browser.DBfolder.value
		self.onLayoutFinish.append(self.makeList)

	def makeList(self):
		self.mp3list = []
		self.datelist = []
		self.artistlist = []
		self.albumlist = []
		self.numberlist = []
		self.tracklist = []
		self.yearlist = []
		self.runtimelist = []
		self.bitratelist = []
		self.genrelist = []
		self.posterlist = []
		self.list = []
		self.listentries = []
		if fileExists(self.database):
			count = 0
			index = 0
			f = open(self.database, "r")
			for line in f:
				date = artist = album = number = track = year = genre = runtime = bitrate = " "             
				poster = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/default.png"            
				mp3line = line.split(":::")
				try:
					mp3 = mp3line[1]
					if mp3 == self.mp3:
						index = count
				except IndexError as e:
					mp3 = " "

				try:
					date = mp3line[2]
					artist = mp3line[3]
					album = mp3line[4]
					number = mp3line[5]
					track = mp3line[6]
					year = mp3line[7]
					genre = mp3line[8]
					runtime = mp3line[9]
					bitrate = mp3line[10]
					poster = mp3line[11]
				except IndexError as e:
					continue

				self.mp3list.append(mp3)
				self.datelist.append(date)
				self.artistlist.append(artist)
				self.albumlist.append(album)
				self.numberlist.append(number)
				self.tracklist.append(track)
				self.yearlist.append(year)
				self.genrelist.append(genre)
				self.runtimelist.append(runtime)
				self.bitratelist.append(bitrate)
				self.posterlist.append(poster)
				self.list.append(artist + " - " + track)
				count += 1
				res = [""]
				res.append(MultiContentEntryText(pos=(0, 0), size=(710, 25), font=20, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=artist + " - " + track))
				self.listentries.append(res)

			self["list"].l.setList(self.listentries)
			self["list"].moveToIndex(index)
			self.selectList()
			self.ready = True
			totalMP3 = len(self.list)
			database = "Database"
			free = "free Space"
			folder = "Folder"
			if exists(config.plugins.mp3browser.mp3folder.value):
				stat = statvfs(config.plugins.mp3browser.mp3folder.value)
				freeSize = stat.f_bsize * stat.f_bfree // 1024 // 1024 // 1024
				title = "%s Editor: %s MP3s (%s GB %s)" % (database, str(totalMP3), str(freeSize), free)
				self.setTitle(title)
			else:
				title = "%s Editor: %s MP3s (MP3 %s offline)" % (database, str(totalMP3), folder)
				self.setTitle(title)

	def makeList2(self):
		self.list2 = []
		self.list2.append(_("Artist: ") + self.artistlist[self.index])
		self.list2.append(_("Album: ") + self.albumlist[self.index])
		self.list2.append(_("Year: ") + self.yearlist[self.index])
		self.list2.append(_("Track: ") + self.tracklist[self.index])
		self.list2.append(_("Number: ") + self.numberlist[self.index])
		self.list2.append(_("Runtime: ") + self.runtimelist[self.index])
		self.list2.append(_("Bitrate: ") + self.bitratelist[self.index])
		self.list2.append(_("Genre: ") + self.genrelist[self.index])
		self.list2.append(_("Cover: ") + self.posterlist[self.index])
		self.list2entries = []
		idx = 0
		for x in self.list2:
			idx += 1

		for i in list(range(idx)):
			try:
				res = [
				 ""]
				res.append(MultiContentEntryText(pos=(0, 0), size=(710, 25), font=20, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.list2[i]))
				self.list2entries.append(res)
			except IndexError as e:
				print("[MP3Browser][   ] Indexerror",  e)

		self["list2"].l.setList(self.list2entries)
		self.selectList2()

	def ok(self):
		if self.ready == True:
			if self.actlist == "list":
				self.index = self["list"].getSelectedIndex()
				mp3 = self.mp3list[self.index]
				self.mp3 = sub("\\(|\\)|\\[|\\]|\\+|\\?", ".", mp3)
				self.makeList2()
			elif self.actlist == "list2":
				index = self["list2"].getSelectedIndex()
				if index == 0:
					self.data = self.artistlist[self.index]
				elif index == 1:
					self.data = self.albumlist[self.index]
				elif index == 2:
					self.data = self.yearlist[self.index]
				elif index == 3:
					self.data = self.tracklist[self.index]
				elif index == 4:
					self.data = self.numberlist[self.index]
				elif index == 5:
					self.data = self.runtimelist[self.index]
				elif index == 6:
					self.data = self.bitratelist[self.index]
				elif index == 7:
					self.data = self.genrelist[self.index]
				elif index == 8:
					self.data = self.posterlist[self.index]
				self.session.openWithCallback(self.changeData, VirtualKeyBoard, title="Database Editor:", text=self.data)

	def changeData(self, newdata):
		if newdata and newdata != "" and newdata != self.data:
			newdata = ":::" + newdata + ":::"
			olddata = ":::" + self.data + ":::"
			database = open(self.database).read()
			for line in database.split("\n"):
				if search(self.mp3, line) is not None:
					newline = line.replace(olddata, newdata)
					database = database.replace(line, newline)

			f = open(self.database + ".new", "w")
			f.write(database)
			f.close()
			rename(self.database + ".new", self.database)
			self.makeList()
			self.makeList2()
			self.change = True
		return

	def selectList(self):
		self.actlist = "list"
		self["list"].show()
		self["list2"].hide()
		self["list"].selectionEnabled(1)
		self["list2"].selectionEnabled(0)

	def selectList2(self):
		self.actlist = "list2"
		self["list"].hide()
		self["list2"].show()
		self["list"].selectionEnabled(0)
		self["list2"].selectionEnabled(1)

	def up(self):
		self[self.actlist].up()

	def down(self):
		self[self.actlist].down()

	def leftUp(self):
		self[self.actlist].pageUp()

	def rightDown(self):
		self[self.actlist].pageDown()

	def gotoEnd(self):
		end = len(self.list) - 1
		self["list"].moveToIndex(end)

	def zap(self):
		servicelist = self.session.instantiateDialog(ChannelSelection)
		self.session.execDialog(servicelist)

	def infoScreen(self):
		self.session.open(infoScreenMP3Browser, None, True)
		return

	def hideScreen(self):
		if self.hideflag == True:
			self.hideflag = False
			count = 40
			while count > 0:
				count -= 1


		else:
			self.hideflag = True
			count = 0
			while count < 40:
				count += 1


	def exit(self):
		if self.hideflag == False:
			self.hideflag = True

		if self.actlist == "list":
			if self.change == True:
				self.close(True)
			else:
				self.close(False)
		elif self.actlist == "list2":
			self.selectList()


class filterList(Screen):
	skin = """
	<screen position="center,center" size="{screenwidth},{screenheight}" title=" ">
		<ePixmap position="0,0" size="{screenwidth},28" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/setup/{png}.png" zPosition="1"/>
		<widget name="list" position="10,38" size="{listwidth},{listheight}" scrollbarMode="showOnDemand" zPosition="1" />
	</screen>"""

	def __init__(self, session, list, titel, len, max):
		print("[MP3Browser][filterlist] ")    
		if int(len) < 20:
			listheight = int(len) * 25
			screenheight = listheight + 48
			screenheight = str(screenheight)
			listheight = str(listheight)
		else:
			screenheight = "523"
			listheight = "475"
		if int(max) > 50:
			screenwidth = "720"
			listwidth = "700"
			self.listwidth = 700
			png = "logoFilter4"
		elif int(max) > 35:
			screenwidth = "520"
			listwidth = "500"
			self.listwidth = 500
			png = "logoFilter3"
		elif int(max) > 25:
			screenwidth = "370"
			listwidth = "350"
			self.listwidth = 350
			png = "logoFilter2"
		else:
			screenwidth = "270"
			listwidth = "250"
			self.listwidth = 250
			png = "logoFilter"
		self.dict = {"screenwidth": screenwidth, "screenheight": screenheight, "listwidth": listwidth, "listheight": listheight, "png": png}
		self.skin = applySkinVars(filterList.skin, self.dict)
		Screen.__init__(self, session)
		self.hideflag = True
		self.setTitle(titel)
		self.list = list
		self.listentries = []
		self["list"] = ItemList([])
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActions", "ChannelSelectBaseActions", "HelpActions", "NumberActions"], {"ok": self.ok, 
		   "cancel": self.exit, 
		   "down": self.down, 
		   "up": self.up, 
		   "nextBouquet": self.zap, 
		   "prevBouquet": self.zap, 
		   "red": self.infoScreen, 
		   "yellow": self.infoScreen, 
		   "green": self.infoScreen, 
		   "blue": self.hideScreen, 
		   "6": self.resetFilter, 
		   "7": self.resetFilter, 
		   "8": self.resetFilter, 
		   "9": self.resetFilter, 
		   "0": self.gotoEnd, 
		   "displayHelp": self.infoScreen}, -1)
		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		idx = 0
		for x in self.list:
			idx += 1

		for i in list(range(idx)):
			try:
				res = [
				 ""]
				res.append(MultiContentEntryText(pos=(0, 0), size=(self.listwidth, 25), font=20, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.list[i]))
				self.listentries.append(res)
			except IndexError as e:
				print("[MP3Browser][   ] Indexerror",  e)

		self["list"].l.setList(self.listentries)

	def ok(self):
		index = self["list"].getSelectedIndex()
		current = self.list[index]
		self.close(":::" + current)

	def resetFilter(self):
		self.close(":::")

	def down(self):
		self["list"].down()

	def up(self):
		self["list"].up()

	def gotoEnd(self):
		end = len(self.list) - 1
		self["list"].moveToIndex(end)

	def zap(self):
		servicelist = self.session.instantiateDialog(ChannelSelection)
		self.session.execDialog(servicelist)

	def infoScreen(self):
		self.session.open(infoScreenMP3Browser, None, True)
		return

	def hideScreen(self):
		if self.hideflag == True:
			self.hideflag = False
			count = 40
			while count > 0:
				count -= 1


		else:
			self.hideflag = True
			count = 0
			while count < 40:
				count += 1


	def exit(self):
		self.close(None)
		return


class allMP3List(Screen):
	skin = """
	<screen position="center,center" size="730,523" title=" ">
		<ePixmap position="0,0" size="730,28" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/setup/logo.png" zPosition="1"/>
		<widget name="list" position="10,38" size="710,475" scrollbarMode="showOnDemand" zPosition="1" />
	</screen>"""

	def __init__(self, session, list, index):
		Screen.__init__(self, session)
		print("[MP3Browser][allmp3List] ")        
		self.hideflag = True
		self.index = index
		self.list = list
		self.listentries = []
		self["list"] = ItemList([])
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActions", "ChannelSelectBaseActions", "HelpActions", "NumberActions"], {"ok": self.ok, 
		   "cancel": self.exit, 
		   "down": self.down, 
		   "up": self.up, 
		   "nextBouquet": self.zap, 
		   "prevBouquet": self.zap, 
		   "red": self.infoScreen, 
		   "yellow": self.infoScreen, 
		   "green": self.infoScreen, 
		   "blue": self.hideScreen, 
		   "0": self.gotoEnd, 
		   "displayHelp": self.infoScreen}, -1)
		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		idx = 0
		for x in self.list:
			idx += 1

		for i in list(range(idx)):
			try:
				res = [
				 ""]
				res.append(MultiContentEntryText(pos=(0, 0), size=(710, 25), font=20, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.list[i]))
				self.listentries.append(res)
			except IndexError as e:
				print("[MP3Browser][   ] Indexerror",  e)

		self["list"].l.setList(self.listentries)
		try:
			self["list"].moveToIndex(self.index)
		except IndexError as e:
			print("[MP3Browser][   ] Indexerror",  e)

		totalMP3 = len(self.list)
		if config.plugins.mp3browser.showfolder.value == "yes":
			totalMP3 -= 1
		free = "free Space"
		folder = "Folder"
		if exists(config.plugins.mp3browser.mp3folder.value):
			stat = statvfs(config.plugins.mp3browser.mp3folder.value)
			freeSize = stat.f_bsize * stat.f_bfree // 1024 // 1024 // 1024
			title = "%s MP3s (%s GB %s)" % (str(totalMP3), str(freeSize), free)
			self.setTitle(title)
		else:
			title = "%s MP3s (MP3 %s offline)" % (str(totalMP3), folder)
			self.setTitle(title)

	def ok(self):
		index = self["list"].getSelectedIndex()
		self.close(index)

	def down(self):
		self["list"].down()

	def up(self):
		self["list"].up()

	def gotoEnd(self):
		end = len(self.list) - 1
		self["list"].moveToIndex(end)

	def zap(self):
		servicelist = self.session.instantiateDialog(ChannelSelection)
		self.session.execDialog(servicelist)

	def infoScreen(self):
		self.session.open(infoScreenMP3Browser, None, True)
		return

	def hideScreen(self):
		if self.hideflag == True:
			self.hideflag = False
			count = 40
			while count > 0:
				count -= 1

		else:
			self.hideflag = True
			count = 0
			while count < 40:
				count += 1

	def exit(self):
		self.close(None)
		return


class mp3List(Screen):
	skin = """
	<screen position="center,center" size="730,538" title=" ">
		<ePixmap position="0,0" size="730,28" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/setup/logo.png" zPosition="1"/>
		<widget name="poster1" position="10,33" size="120,120" alphatest="blend" zPosition="1" />
		<widget name="poster2" position="10,158" size="120,120" alphatest="blend" zPosition="1" />
		<widget name="poster3" position="10,283" size="120,120" alphatest="blend" zPosition="1" />
		<widget name="poster4" position="10,408" size="120,120" alphatest="blend" zPosition="1" />
		<widget name="list" position="140,33" size="580,500" scrollbarMode="showOnDemand" zPosition="1" />
	</screen>"""

	def __init__(self, session, poster, titel):
		Screen.__init__(self, session)
		print("[MP3Browser][mp3List] ")        
		self.poster = poster
		self.poster1 = "/tmp/mp3browser1.jpg"
		self.poster2 = "/tmp/mp3browser2.jpg"
		self.poster3 = "/tmp/mp3browser3.jpg"
		self.poster4 = "/tmp/mp3browser4.jpg"
		self["poster1"] = Pixmap()
		self["poster2"] = Pixmap()
		self["poster3"] = Pixmap()
		self["poster4"] = Pixmap()
		self.ready = False
		self.hideflag = True
		self.mp3list = []
		self.setTitle(titel)
		self["list"] = ItemList([])
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActions", "ChannelSelectBaseActions", "HelpActions", "NumberActions"], {"ok": self.ok, 
			"cancel": self.exit, 
			"right": self.rightDown, 
			"left": self.leftUp, 
			"down": self.down, 
			"up": self.up, 
			"nextBouquet": self.zap, 
			"prevBouquet": self.zap, 
			"red": self.infoScreen, 
			"yellow": self.infoScreen, 
			"blue": self.hideScreen, 
			"0": self.gotoEnd, 
			"displayHelp": self.infoScreen}, -1)
		if config.plugins.mp3browser.metrixcolor.value == "0x00000000":
			self.backcolor = False
		else:
			self.backcolor = True
			self.back_color = int(config.plugins.mp3browser.metrixcolor.value, 16)
		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		self["poster1"].hide()
		self["poster2"].hide()
		self["poster3"].hide() 
		self["poster4"].hide()                           
		try:
			poster1 = self.poster[0]
			self.download(poster1, self.getPoster1)
			self["poster1"].show()

			poster2 = self.poster[1]
			self.download(poster2, self.getPoster2)
			self["poster2"].show()

			poster3 = self.poster[2]
			self.download(poster3, self.getPoster3)
			self["poster3"].show()

			poster4 = self.poster[3]
			self.download(poster4, self.getPoster4)
			self["poster4"].show()
		except IndexError as e:
			print("[MP3Browser][onLayoutFinished][posterdisplay] Indexerror",  e)

		idx = 0
		for x in self.poster:
			idx += 1

		for i in list(range(idx)):
			res = [
			 ""]
			try:
				poster = sub(".*?[/]", "", self.poster[i])
				if self.backcolor == True:
					res.append(MultiContentEntryText(pos=(0, 0), size=(580, 125), font=26, backcolor_sel=self.back_color, flags=RT_HALIGN_LEFT, text=""))
				res.append(MultiContentEntryText(pos=(5, 5), size=(570, 115), font=26, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text=poster))
			except IndexError as e:
				print("[MP3Browser][onLayoutFinished   ] Indexerror",  e)

			self.mp3list.append(res)

		self["list"].l.setList(self.mp3list)
		self["list"].l.setItemHeight(125)
		self.ready = True

	def ok(self):
		if self.ready == True:
			if fileExists(self.poster1):
				remove(self.poster1)
			if fileExists(self.poster2):
				remove(self.poster2)
			if fileExists(self.poster3):
				remove(self.poster3)
			if fileExists(self.poster4):
				remove(self.poster4)
			c = self["list"].getSelectedIndex()
			current = self.poster[c]
			self.close(current)

	def gotoEnd(self):
		if self.ready == True:
			end = len(self.poster) - 1
			if end > 4:
				self["list"].moveToIndex(end)
				self.leftUp()
				self.rightDown()

	def down(self):
		if self.ready == True:
			try:
				c = self["list"].getSelectedIndex()
			except IndexError as e:
				print("[MP3Browser][down] Indexerror",  e)            
				return

			self["list"].down()
			if c + 1 == len(self.poster):
				self["poster1"].hide()
				self["poster2"].hide()
				self["poster3"].hide() 
				self["poster4"].hide()
				try:
					poster1 = self.poster[0]
					self.download(poster1, self.getPoster1)
					self["poster1"].show()

					poster2 = self.poster[1]
					self.download(poster2, self.getPoster2)
					self["poster2"].show()

					poster3 = self.poster[2]
					self.download(poster3, self.getPoster3)
					self["poster3"].show()

					poster4 = self.poster[3]
					self.download(poster4, self.getPoster4)
					self["poster4"].show()
				except IndexError as e:
					print("[MP3Browser][down]c + 1 Indexerror",  e)                
					self["poster4"].hide()

			elif c % 4 == 3:
				self["poster1"].hide()
				self["poster2"].hide()
				self["poster3"].hide() 
				self["poster4"].hide()            
				try:
					poster1 = self.poster[(c + 1)]
					self.download(poster1, self.getPoster1)
					self["poster1"].show()

					poster2 = self.poster[(c + 2)]
					self.download(poster2, self.getPoster2)
					self["poster2"].show()

					poster3 = self.poster[(c + 3)]
					self.download(poster3, self.getPoster3)
					self["poster3"].show()

					poster4 = self.poster[(c + 4)]
					self.download(poster4, self.getPoster4)
					self["poster4"].show()
				except IndexError as e:
					print("[MP3Browser][down]c % 4 Indexerror",  e)

	def up(self):
		if self.ready == True:
			try:
				c = self["list"].getSelectedIndex()
			except IndexError as e:
				print("[MP3Browser][up Indexerror",  e)            
				return

			self["list"].up()
			if c == 0:
				l = len(self.poster)
				d = l % 4
				if d == 0:
					d = 4
				self["poster1"].hide()
				self["poster2"].hide()
				self["poster3"].hide() 
				self["poster4"].hide() 
				try:
					poster1 = self.poster[(l - d)]
					self.download(poster1, self.getPoster1)
					self["poster1"].show()

					poster2 = self.poster[(l - d + 1)]
					self.download(poster2, self.getPoster2)
					self["poster2"].show()

					poster3 = self.poster[(l - d + 2)]
					self.download(poster3, self.getPoster3)
					self["poster3"].show()

					poster4 = self.poster[(l - d + 3)]
					self.download(poster4, self.getPoster4)
					self["poster4"].show()
				except IndexError as e:
					print("[MP3Browser][up]c = 0 Indexerror",  e)

			elif c % 4 == 0:
				self["poster1"].hide()
				self["poster2"].hide()
				self["poster3"].hide() 
				self["poster4"].hide()             
				try:
					poster1 = self.poster[(c - 4)]
					self.download(poster1, self.getPoster1)
					self["poster1"].show()

					poster2 = self.poster[(c - 3)]
					self.download(poster2, self.getPoster2)
					self["poster2"].show()

					poster3 = self.poster[(c - 2)]
					self.download(poster3, self.getPoster3)
					self["poster3"].show()

					poster4 = self.poster[(c - 1)]
					self.download(poster4, self.getPoster4)
					self["poster4"].show()
				except IndexError as e:
					print("[MP3Browser][up]c % 4 Indexerror",  e)

	def rightDown(self):
		if self.ready == True:
			try:
				c = self["list"].getSelectedIndex()
			except IndexError as e:
				print("[MP3Browser][rightDown] Indexerror C= ",  c, "   ", e)            
				return

			self["list"].pageDown()
			l = len(self.poster)
			d = c % 4
			e = l % 4
			if e == 0:
				e = 4
			if c + e >= l:
				pass

			self["poster1"].hide()
			self["poster2"].hide()
			self["poster3"].hide() 
			self["poster4"].hide()
			try:
				poster1 = self.poster[(c + (4 - d))]
				self.download(poster1, self.getPoster1)
				self["poster1"].show()
				poster2 = self.poster[(c + (5 - d))]
				self.download(poster2, self.getPoster2)
				self["poster2"].show()
				poster3 = self.poster[(c + (6 - d))]
				self.download(poster3, self.getPoster3)
				self["poster3"].show()
				poster4 = self.poster[(c + (7 - d))]
				self.download(poster4, self.getPoster4)
				self["poster4"].show()
			except IndexError as e:
					print("[MP3Browser][rightDown]Indexerror d= ", d,  "   ", e)

	def leftUp(self):
		if self.ready == True:
			try:
				c = self["list"].getSelectedIndex()
			except IndexError as e:
				print("[MP3Browser][leftUp] Indexerrorc = ", c, "   ",  e)            
				return

			self["list"].pageUp()
			d = c % 4
			if c < 4:
				pass

			self["poster1"].hide()
			self["poster2"].hide()
			self["poster3"].hide() 
			self["poster4"].hide()
			try:
				poster1 = self.poster[(c - (4 + d))]
				self.download(poster1, self.getPoster1)
				self["poster1"].show()
				poster2 = self.poster[(c - (3 + d))]
				self.download(poster2, self.getPoster2)
				self["poster2"].show()
				poster3 = self.poster[(c - (2 + d))]
				self.download(poster3, self.getPoster3)
				self["poster3"].show()
				poster4 = self.poster[(c - (1 + d))]
				self.download(poster4, self.getPoster4)
				self["poster4"].show()
			except IndexError as e:
				print("[MP3Browser][leftUp] Indexerror d=",  d, "   ", e)

	def download(self, link, name):
		print("[download] link=%s, name =%s" % (link, name))
		callInThread(threadGetPage, url=link, success=name, fail=self.downloadError)

	def downloadError(self, output):
		print("[MP3Browser][downloadError] ")


	def getPoster1(self, output):
		f = open(self.poster1, "wb")
		f.write(output)
		f.close()
		self.showPoster1(self.poster1)

	def showPoster1(self, poster1):
		if fileExists(poster1):
			self["poster1"].instance.setPixmapFromFileFromFile(poster1)
			self["poster1"].show()
		return

	def getPoster2(self, output):
		f = open(self.poster2, "wb")
		f.write(output)
		f.close()
		self.showPoster2(self.poster2)

	def showPoster2(self, poster2):
		if fileExists(poster2):
			self["poster2"].instance.setPixmapFromFileFromFile(poster2)
			self["poster2"].show()
		return

	def getPoster3(self, output):
		f = open(self.poster3, "wb")
		f.write(output)
		f.close()
		self.showPoster3(self.poster3)

	def showPoster3(self, poster3):
		if fileExists(poster3):
			self["poster3"].instance.setPixmapFromFileFromFile(poster3)
			self["poster3"].show()
		return

	def getPoster4(self, output):
		f = open(self.poster4, "wb")
		f.write(output)
		f.close()
		self.showPoster4(self.poster4)

	def showPoster4(self, poster4):
		if fileExists(poster4):
			self["poster4"].instance.setPixmapFromFileFromFile(poster4)
			self["poster4"].show()       
		return

	def zap(self):
		servicelist = self.session.instantiateDialog(ChannelSelection)
		self.session.execDialog(servicelist)

	def infoScreen(self):
		self.session.open(infoScreenMP3Browser, None, True)
		return

	def hideScreen(self):
		if self.hideflag == True:
			self.hideflag = False
			count = 40
			while count > 0:
				count -= 1

		else:
			self.hideflag = True
			count = 0
			while count < 40:
				count += 1
	def exit(self):
		if fileExists(self.poster1):
			remove(self.poster1)
		if fileExists(self.poster2):
			remove(self.poster2)
		if fileExists(self.poster3):
			remove(self.poster3)
		if fileExists(self.poster4):
			remove(self.poster4)
		self.close(None)
		return


class getABC(Screen):
	skin = """
	<screen position="center,center" size="190,60" backgroundColor="#000000" flags="wfNoBorder" title=" ">
		<widget name="ABC" position="0,0" size="190,60" font="{font};34" halign="center" valign="center" transparent="1" zPosition="1"/>
	</screen>"""

	def __init__(self, session, ABC, XYZ):
		print("[MP3Browser][getABC] ")    
		font = "Sans" if config.plugins.mp3browser.font.value == "yes" else "Regular"
		self.dict = {"font": font}
		self.skin = applySkinVars(getABC.skin, self.dict)
		Screen.__init__(self, session)
		if XYZ == True and ABC == "ABC":
			self.field = "WXYZ"
		else:
			self.field = ABC
		self["ABC"] = Label(self.field)
		self["actions"] = ActionMap(["OkCancelActions", "ChannelSelectBaseActions", "NumberActions"], {"cancel": self.quit, 
			"ok": self.OK, 
			"nextMarker": self.ABC, 
			"prevMarker": self.WXYZ, 
			"2": self._ABC, 
			"3": self._DEF, 
			"4": self._GHI, 
			"5": self._JKL, 
			"6": self._MNO, 
			"7": self._PQRS, 
			"8": self._TUV, 
			"9": self._WXYZ})
		self.Timer = eTimer()
		self.Timer.callback.append(self.returnABC)
		self.Timer.start(2500, True)

	def ABC(self):
		self.Timer.start(2000, True)
		if self.field.startswith("A", "B", "C"):
			self.field = "DEF"
		elif self.field.startswith("D", "E", "F"):
			self.field = "GHI"
		elif self.field.startswith("G", "H", "I"):
			self.field = "JKL"
		elif self.field.startswith("J", "K", "L"):
			self.field = "MNO"
		elif self.field.startswith("M", "N", "O"):
			self.field = "PQRS"
		elif self.field.startswith("P", "Q", "R", "S"):
			self.field = "TUV"
		elif self.field.startswith("T", "U", "V"):
			self.field = "WXYZ"
		elif self.field.startswith("W", "X", "Y", "Z"):
			self.field = "ABC"
		self["ABC"].setText(self.field)

	def WXYZ(self):
		self.Timer.start(2000, True)
		if self.field.startswith("W", "X", "Y", "Z"):
			self.field = "TUV"
		elif self.field.startswith("T", "U", "V"):
			self.field = "PQRS"
		elif self.field.startswith("P", "Q", "S"):
			self.field = "MNO"
		elif self.field.startswith("M", "N", "O"):
			self.field = "JKL"
		elif self.field.startswith("J", "K", "L"):
			self.field = "GHI"
		elif self.field.startswith("G", "H", "I"):
			self.field = "DEF"
		elif self.field.startswith("D", "E", "F"):
			self.field = "ABC"
		elif self.field.startswith("A", "B", "C"):
			self.field = "WXYZ"
		self["ABC"].setText(self.field)

	def _ABC(self):
		self.Timer.start(2000, True)
		if self.field not in ("A", "B", "C"):
			self.field = "A"
		elif self.field == "A":
			self.field = "B"
		elif self.field == "B":
			self.field = "C"
		elif self.field == "C":
			self.field = "A"
		self["ABC"].setText(self.field)

	def _DEF(self):
		self.Timer.start(2000, True)
		if self.field not in ("D", "E", "F"):
			self.field = "D"
		elif self.field == "D":
			self.field = "E"
		elif self.field == "E":
			self.field = "F"
		elif self.field == "F":
			self.field = "D"
		self["ABC"].setText(self.field)

	def _GHI(self):
		self.Timer.start(2000, True)
		if self.field not in ("G", "H", "I"):
			self.field = "G"
		elif self.field == "G":
			self.field = "H"
		elif self.field == "H":
			self.field = "I"
		elif self.field == "I":
			self.field = "G"
		self["ABC"].setText(self.field)

	def _JKL(self):
		self.Timer.start(2000, True)
		if self.field not in ("J", "K", "L"):
			self.field = "J"
		elif self.field == "J":
			self.field = "K"
		elif self.field == "K":
			self.field = "L"
		elif self.field == "L":
			self.field = "J"
		self["ABC"].setText(self.field)

	def _MNO(self):
		self.Timer.start(2000, True)
		if self.field not in ("M", "N", "O"):
			self.field = "M"
		elif self.field == "M":
			self.field = "N"
		elif self.field == "N":
			self.field = "O"
		elif self.field == "O":
			self.field = "M"
		self["ABC"].setText(self.field)

	def _PQRS(self):
		self.Timer.start(2000, True)
		if self.field not in ("P", "Q", "R", "S"):
			self.field = "P"
		elif self.field == "P":
			self.field = "Q"
		elif self.field == "Q":
			self.field = "R"
		elif self.field == "R":
			self.field = "S"
		elif self.field == "S":
			self.field = "P"
		self["ABC"].setText(self.field)

	def _TUV(self):
		self.Timer.start(2000, True)
		if self.field not in ("T", "U", "V"):
			self.field = "T"
		elif self.field == "T":
			self.field = "U"
		elif self.field == "U":
			self.field = "V"
		elif self.field == "V":
			self.field = "T"
		self["ABC"].setText(self.field)

	def _WXYZ(self):
		self.Timer.start(2000, True)
		if self.field not in ("W", "X", "Y", "Z"):
			self.field = "W"
		elif self.field == "W":
			self.field = "X"
		elif self.field == "X":
			self.field = "Y"
		elif self.field == "Y":
			self.field = "Z"
		elif self.field == "Z":
			self.field = "W"
		self["ABC"].setText(self.field)

	def OK(self):
		self.Timer.start(2000, True)
		if self.field == "ABC":
			self.field = "B"
		elif self.field == "B":
			self.field = "C"
		elif self.field == "C":
			self.field = "A"
		elif self.field == "A":
			self.field = "B"
		elif self.field == "DEF":
			self.field = "E"
		elif self.field == "E":
			self.field = "F"
		elif self.field == "F":
			self.field = "D"
		elif self.field == "D":
			self.field = "E"
		elif self.field == "GHI":
			self.field = "H"
		elif self.field == "H":
			self.field = "I"
		elif self.field == "I":
			self.field = "G"
		elif self.field == "G":
			self.field = "H"
		elif self.field == "JKL":
			self.field = "K"
		elif self.field == "K":
			self.field = "L"
		elif self.field == "L":
			self.field = "J"
		elif self.field == "J":
			self.field = "K"
		elif self.field == "MNO":
			self.field = "N"
		elif self.field == "N":
			self.field = "O"
		elif self.field == "O":
			self.field = "M"
		elif self.field == "M":
			self.field = "N"
		elif self.field == "PQRS":
			self.field = "Q"
		elif self.field == "Q":
			self.field = "R"
		elif self.field == "R":
			self.field = "S"
		elif self.field == "S":
			self.field = "P"
		elif self.field == "P":
			self.field = "Q"
		elif self.field == "TUV":
			self.field = "U"
		elif self.field == "U":
			self.field = "V"
		elif self.field == "V":
			self.field = "T"
		elif self.field == "T":
			self.field = "U"
		elif self.field == "WXYZ":
			self.field = "X"
		elif self.field == "X":
			self.field = "Y"
		elif self.field == "Y":
			self.field = "Z"
		elif self.field == "Z":
			self.field = "W"
		elif self.field == "W":
			self.field = "X"
		self["ABC"].setText(self.field)

	def returnABC(self):
		self.Timer.stop()
		self.close(self.field)

	def quit(self):
		self.Timer.stop()
		self.close(None)
		return


class switchScreen(Screen):
	skin = """
	<screen position="center,center" size="300,200" flags="wfNoBorder" title=" ">
		<widget name="label_1" position="0,0" size="300,100" font="{font};32" halign="center" valign="center" transparent="1" zPosition="1"/>
		<widget name="label_2" position="0,100" size="300,100" font="{font};32" halign="center" valign="center" transparent="1" zPosition="1"/>
		<widget name="label_select_1" position="0,0" size="300,100" font="{font};32" backgroundColor="#D9D9D9" foregroundColor="#000000" halign="center" valign="center" transparent="1" zPosition="1"/>
		<widget name="label_select_2" position="0,100" size="300,100" font="{font};32" backgroundColor="#D9D9D9" foregroundColor="#000000" halign="center" valign="center" transparent="1" zPosition="1"/>
		<widget name="select_1" position="0,0" size="300,100" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/browser/menu_select.png" transparent="1" alphatest="blend" zPosition="-1"/>
		<widget name="select_2" position="0,100" size="300,100" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/browser/menu_select.png" transparent="1" alphatest="blend" zPosition="-1"/>
	</screen>"""

	def __init__(self, session, number, mode):
		print("[MP3Browser][switchScreen] ")    
		font = "Sans" if config.plugins.mp3browser.font.value == "yes" else "Regular"
		self.dict = {"font": font}
		self.skin = applySkinVars(switchScreen.skin, self.dict)
		Screen.__init__(self, session)
		self["select_1"] = Pixmap()
		self["select_2"] = Pixmap()
		self["select_1"].hide()
		self["select_2"].hide()
		if mode == "style":
			self["label_1"] = Label(_("METRIX"))
			self["label_2"] = Label(_("COVERWALL"))
			self["label_select_1"] = Label(_("METRIX"))
			self["label_select_2"] = Label(_("COVERWALL"))
		elif mode == "shuffle":
			self["label_1"] = Label(_("NORMAL"))
			self["label_2"] = Label(_("SHUFFLE"))
			self["label_select_1"] = Label(_("NORMAL"))
			self["label_select_2"] = Label(_("SHUFFLE"))
		else:
			self["label_1"] = Label(_("NORMAL"))
			self["label_2"] = Label(_("SCREENSAVER"))
			self["label_select_1"] = Label(_("NORMAL"))
			self["label_select_2"] = Label(_("SCREENSAVER"))
		self["label_select_1"].hide()
		self["label_select_2"].hide()
		self.number = number
		if self.number == 1:
			self["label_1"].hide()
			self["select_1"].show()
			self["label_select_1"].show()
		elif self.number == 2:
			self["label_2"].hide()
			self["select_2"].show()
			self["label_select_2"].show()
		self["actions"] = ActionMap(["OkCancelActions", "NumberActions", "ColorActions", "DirectionActions"], {"cancel": self.quit, 
		   "down": self.__next__, 
		   "red": self.__next__, 
		   "2": self.__next__, 
		   "5": self.__next__})
		self.Timer = eTimer()
		self.Timer.callback.append(self.returnNumber)
		self.Timer.start(2500, True)

	def __next__(self):
		self.Timer.start(2000, True)
		if self.number == 1:
			self["label_select_1"].hide()
			self["select_1"].hide()
			self["label_1"].show()
			self["label_2"].hide()
			self["select_2"].show()
			self["label_select_2"].show()
			self.number = 2
		elif self.number == 2:
			self["label_select_2"].hide()
			self["select_2"].hide()
			self["label_2"].show()
			self["label_1"].hide()
			self["select_1"].show()
			self["label_select_1"].show()
			self.number = 1

	def returnNumber(self):
		self.Timer.stop()
		self.close(self.number)

	def quit(self):
		self.Timer.stop()
		self.close(None)
		return


class moveCover(Screen):
	skinHD = """
	<screen position="0,0" size="1280,720" flags="wfNoBorder" title=" ">\n
		<widget name="cover" position="0,0" size="200,200" alphatest="blend" transparent="1" zPosition="1"/>
	</screen>"""

	def __init__(self, session, cover):
		font = "Sans" if config.plugins.mp3browser.font.value == "yes" else "Regular"		
		self.dict = {"font": font}
		self.skin = applySkinVars(moveCover.skinHD, self.dict)		
		Screen.__init__(self, session)
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={iPlayableService.evEOF: self.quit})
		self.cover = cover
		self["cover"] = Pixmap()
		self["actions"] = ActionMap(["OkCancelActions", "MoviePlayerActions"], {"cancel": self.quit, 
		   "leavePlayer": self.quit})
		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		print("[MP3Browser][moveCover]")    
		if fileExists(self.cover):
			self["cover"].instance.setPixmapFromFile(self.cover)
		self.Timer = eTimer()
		self.Timer.callback.append(self.move)
		self.Timer.start(2500, True)
		return

	def move(self):
		pos_x = random.randint(0, 1080)
		pos_y = random.randint(0, 520)
		self["cover"].instance.move(ePoint(pos_x, pos_y))
		self.Timer.stop()
		self.Timer.start(2500, True)

	def quit(self):
		self.Timer.stop()
		self.close()


class mp3Fav(Screen):
	skinHD = """
	<screen position="center,center" size="620,590" title=" ">
		<ePixmap position="0,0" size="620,28" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/setup/logoFavHD.png" zPosition="1"/>
		<ePixmap position="10,5" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/buttons/red.png" alphatest="blend" zPosition="2" />
		<widget name="label" position="34,4" size="250,22" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
		<widget name="label2" position="360,4" size="250,22" font="{font};18" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="right" transparent="1" zPosition="2" />
		<widget name="favmenu" position="10,70" size="600,510" scrollbarMode="showOnDemand" zPosition="1" />
	</screen>"""

	def __init__(self, session, newmp3):
		font = "Sans" if config.plugins.mp3browser.font.value == "yes" else "Regular"
		self.dict = {"font": font}
		self.listwidth = 600
		self.font = 24
		self.skin = applySkinVars(mp3Fav.skinHD, self.dict)
		self.session = session
		Screen.__init__(self, session)
		print("[MP3Browser][mp3Fav]")        
		self.newmp3 = newmp3
		self.edit = False
		self.ready = False
		self.hideflag = True
		self.count = 0
		self.favmp3 = []
		self.favlist = []
		self.faventries = []
		self["favmenu"] = ItemList([])
		self["label"] = Label(_("= Remove Favorite"))
		self["label2"] = Label(_("0/1 = Move to End/First"))
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActions", "HelpActions", "NumberActions"], {"ok": self.exit, 
			"cancel": self.exit, 
			"right": self.rightDown, 
			"left": self.leftUp, 
			"down": self.down, 
			"up": self.up, 
			"red": self.red, 
			"yellow": self.infoScreen, 
			"green": self.infoScreen, 
			"blue": self.hideScreen, 
			"0": self.move2end, 
			"1": self.move2first, 
			"displayHelp": self.infoScreen}, -1)
		self.Timer = eTimer()
		self.Timer.callback.append(self.makeFav)
		self.Timer.start(500, True)

	def makeFav(self):
		self.setTitle("MP3 Browser:::Favourites")
		self.favorites = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/favorites"
		self.count = 0
		if fileExists(self.favorites):
			f = open(self.favorites, "r")
			self.count = 0
			for line in f:
				self.count += 1
				favline = line.split(":::")
				titel = str(favline[3] + " - " + favline[6])
				mp3 = favline[1]
				res = [""]
				res.append(MultiContentEntryText(pos=(0, 0), size=(self.listwidth, 30), font=self.font, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=titel))
				self.faventries.append(res)
				self.favlist.append(titel)
				self.favmp3.append(mp3)

			f.close()
			self["favmenu"].l.setList(self.faventries)
			self["favmenu"].l.setItemHeight(30)
			if self.newmp3 == True:
				self.newmp3 = False
				lastindex = len(self.favlist) - 1
				if lastindex > 0:
					try:
						self["favmenu"].moveToIndex(lastindex)
					except IndexError as e:
						print("[MP3Browser][   ] Indexerror",  e)

			self.ready = True

	def red(self):
		if len(self.favlist) > 0:
			try:
				c = self.getIndex(self["favmenu"])
				name = self.favlist[c]
			except IndexError as e:
				name = ""

			self.session.openWithCallback(self.red_return, MessageBox, _("\nDelete MP3 %s from Favourites?") % name, MessageBox.TYPE_YESNO)

	def red_return(self, answer):
		if answer is True:
			self.edit = True
			c = self.getIndex(self["favmenu"])
			try:
				mp3 = self.favmp3[c]
			except IndexError as e:
				mp3 = "NONE"

			data = ""
			f = open(self.favorites, "r")
			for line in f:
				if mp3 not in line and line != "\n":
					data = data + line

			f.close()
			fnew = open(self.favorites + ".new", "w")
			fnew.write(data)
			fnew.close()
			rename(self.favorites + ".new", self.favorites)
			self.favmp3 = []
			self.favlist = []
			self.faventries = []
			self.makeFav()

	def move2first(self):
		try:
			self.edit = True
			c = self.getIndex(self["favmenu"])
			fav = self.favmp3[c]
			f = open(self.favorites, "r")
			for line in f:
				if fav in line:
					favdata = line

			f.close()
			fnew = open(self.favorites + ".new", "w")
			fnew.write(favdata)
			fnew.close()
			data = ""
			f = open(self.favorites, "r")
			for line in f:
				if fav not in line and line != "\n":
					data = data + line

			f.close()
			fnew = open(self.favorites + ".new", "a")
			fnew.write(data)
			fnew.close()
			rename(self.favorites + ".new", self.favorites)
			self.favmp3 = []
			self.favlist = []
			self.faventries = []
			self.makeFav()
		except IndexError as e:
			print("[MP3Browser][   ] Indexerror",  e)

	def move2end(self):
		try:
			self.edit = True
			c = self.getIndex(self["favmenu"])
			fav = self.favmp3[c]
			f = open(self.favorites, "r")
			for line in f:
				if fav in line:
					favdata = line

			f.close()
			data = ""
			f = open(self.favorites, "r")
			for line in f:
				if fav not in line and line != "\n":
					data = data + line

			f.close()
			fnew = open(self.favorites + ".new", "w")
			fnew.write(data)
			fnew.close()
			fnew = open(self.favorites + ".new", "a")
			fnew.write(favdata)
			fnew.close()
			rename(self.favorites + ".new", self.favorites)
			self.favmp3 = []
			self.favlist = []
			self.faventries = []
			self.makeFav()
		except IndexError as e:
			print("[MP3Browser][   ] Indexerror",  e)

	def getIndex(self, list):
		return list.getSelectedIndex()

	def down(self):
		self["favmenu"].down()

	def up(self):
		self["favmenu"].up()

	def rightDown(self):
		self["favmenu"].pageDown()

	def leftUp(self):
		self["favmenu"].pageUp()

	def infoScreen(self):
		self.session.open(infoScreenMP3Browser, None, True)
		return

	def hideScreen(self):
		if self.hideflag == True:
			self.hideflag = False
			count = 40
			while count > 0:
				count -= 1

		else:
			self.hideflag = True
			count = 0
			while count < 40:
				count += 1


	def exit(self):
		if self.edit == True:
			self.close("edit")
		else:
			self.close(None)
		return


class ItemList(MenuList):

	def __init__(self, items, enableWrapAround=True):
		MenuList.__init__(self, items, enableWrapAround, eListboxPythonMultiContent)
		print("[MP3Browser][ItemList]items", items)        
		self.l.setFont(26, gFont("Sans", 26))
		self.l.setFont(24, gFont("Sans", 24))
		self.l.setFont(22, gFont("Sans", 22))
		self.l.setFont(20, gFont("Sans", 20))


class helpScreen(Screen):
	skin = """
	<screen position="center,center" size="512,512" flags="wfNoBorder" title=" " >
		<ePixmap position="0,0" size="515,512" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/setup/help.png" alphatest="on" transparent="0" zPosition="0" />
		<ePixmap position="120,50" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/buttons/yellow.png" alphatest="blend" zPosition="3" />
		<ePixmap position="120,71" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/buttons/green.png" alphatest="blend" zPosition="3" />
		<ePixmap position="120,92" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/buttons/red.png" alphatest="blend" zPosition="3" />
		<ePixmap position="120,113" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/buttons/blue.png" alphatest="blend" zPosition="3" />
		<widget name="label" position="120,48" size="395,420" font="{font};18" transparent="1" zPosition="2" />
	</screen>"""

	def __init__(self, session):
		print("[MP3Browser][helpScreen]")    
		font = "Sans" if config.plugins.mp3browser.font.value == "yes" else "Regular"
		self.dict = {"font": font}
		self.skin = applySkinVars(helpScreen.skin, self.dict)
		Screen.__init__(self, session)
		self.setTitle("MP3 Browser Key Assignment")
		self["label"] = Label(_("     : Change Screen\n     : MP3 List\n     : Browser Setup\n     : \n\nInfo Button: ChartLyrics/Discogs\nVideo Button: Update Database\nText Button: Edit Database\nRadio Button: Delete MP3\\Lyrics\\Discogs\n<- -> Button: Go to first letter\nButton 1: Show list of all MP3s\nButton 2: Screensaver on/off\nButton 3: Favourites\nButton 4: Search Cover on Google\nButton 5: MP3 Shuffle on/off\nButton 6: MP3 Folder Selection\nButton 7: MP3 Artist Selection\nButton 8: MP3 Album Selection\nButton 9: MP3 Genre Selection\nButton 0: Go to end of list"))
		self["actions"] = ActionMap(["OkCancelActions"], 
			{"ok": self.close, 
		   "cancel": self.close}, -1)


class infoScreenMP3Browser(Screen):
	skin = """
	<screen position="center,center" size="512,512" flags="wfNoBorder" title=" " >
		<ePixmap position="0,0" size="515,512" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/setup/help.png" alphatest="on" transparent="0" zPosition="0" />
		<ePixmap position="120,50" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/buttons/yellow.png" alphatest="blend" zPosition="3" />
		<ePixmap position="120,71" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/buttons/green.png" alphatest="blend" zPosition="3" />
		<ePixmap position="120,92" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/buttons/red.png" alphatest="blend" zPosition="3" />
		<ePixmap position="120,113" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/pic/buttons/blue.png" alphatest="blend" zPosition="3" />
		<widget name="label" position="120,48" size="395,420" font="{font};18" transparent="1" zPosition="2" />
	</screen>"""

	def __init__(self, session):
		print("[MP3Browser][helpScreen]")    
		font = "Sans" if config.plugins.mp3browser.font.value == "yes" else "Regular"
		self.dict = {"font": font}
		self.skin = applySkinVars(helpScreen.skin, self.dict)
		Screen.__init__(self, session)
		self.setTitle("MP3 Browser Key Assignment")
		self["label"] = Label(_("     : Change Screen\n     : MP3 List\n     : Browser Setup\n     : \n\nInfo Button: ChartLyrics/Discogs\nVideo Button: Update Database\nText Button: Edit Database\nRadio Button: Delete MP3\\Lyrics\\Discogs\n<- -> Button: Go to first letter\nButton 1: Show list of all MP3s\nButton 2: Screensaver on/off\nButton 3: Favourites\nButton 4: Search Cover on Google\nButton 5: MP3 Shuffle on/off\nButton 6: MP3 Folder Selection\nButton 7: MP3 Artist Selection\nButton 8: MP3 Album Selection\nButton 9: MP3 Genre Selection\nButton 0: Go to end of list"))
		self["actions"] = ActionMap(["OkCancelActions"], 
			{"ok": self.close, 
		   "cancel": self.close}, -1)


class mp3BrowserConfig(Setup):
	def __init__(self, session):
		Setup.__init__(self, session, None)
		self.title = _("MP3Browser Settings")
		self.createSetup()
		
	def createSetup(self):
		print("[MP3Browser][mp3BrowserConfig]createSetup entered")
		self.sortorder = config.plugins.mp3browser.sortorder.value
		self.mp3folder = config.plugins.mp3browser.mp3folder.value
		# if not fileExists(config.plugins.mp3browser.cachefolder.value):
		#	config.plugins.mp3browser.cachefolder.value = "/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/cache"            
		self.cachefolder = config.plugins.mp3browser.cachefolder.value
		self.database = config.plugins.mp3browser.DBfolder.value
		self.lang = config.plugins.mp3browser.language.value
		self.ready = False
		self.list = [
			getConfigListEntry(_("Plugin Style:"), config.plugins.mp3browser.style, _("Configures screen layout browser."))
		]
		self.list.append(getConfigListEntry(_("MP3 Folder:"), config.plugins.mp3browser.mp3folder, _("Configures location of MP3 folders.")))		
		self.list.append(getConfigListEntry(_("Cache Folder:"), config.plugins.mp3browser.cachefolder, _("Configures destination of cache folder.")))
		self.list.append(getConfigListEntry(_("Database Folder:"), config.plugins.mp3browser.DBfolder, _("Configures location of MP3browser database.")))
		self.list.append(getConfigListEntry(_("MP3 Play Mode:"), config.plugins.mp3browser.background, _("Show background or player")))	
		self.list.append(getConfigListEntry(_("Show TV in Background:"), config.plugins.mp3browser.showtv, _("show TV in background.")))
		self.list.append(getConfigListEntry(_("MP3 Sort Order:"), config.plugins.mp3browser.sortorder, _("sort by Artist, Genre, data etc.")))
		self.list.append(getConfigListEntry(_("Shuffle MP3:"), config.plugins.mp3browser.shuffle, _("play sequential or shuffle.")))
		self.list.append(getConfigListEntry(_("Screensaver:"), config.plugins.mp3browser.screensaver, _("Automatic or Yes/No")))
		self.list.append(getConfigListEntry(_("Goto last MP3 on Start:"), config.plugins.mp3browser.lastmp3, _("Yes/No or Folder selection.")))
		self.list.append(getConfigListEntry(_("Load last Filter on Start:"), config.plugins.mp3browser.lastfilter, _("Yes/No.")))
		self.list.append(getConfigListEntry(_("Plugin Transparency:"), config.plugins.mp3browser.transparency, _("Yes/No.")))
		self.list.append(getConfigListEntry(_("Plugin Language:"), config.plugins.mp3browser.language, _("English, German etc")))
		self.list.append(getConfigListEntry(_("Show Discogs Info:"), config.plugins.mp3browser.discogs, _("Discogs Information.")))
		self.list.append(getConfigListEntry(_("Discogs Token:"), config.plugins.mp3browser.discogstoken, _("Discogs search token - MUST HAVE to search.")))
		self.list.append(getConfigListEntry(_("Coverwall Info & Lyrics:"), config.plugins.mp3browser.showinfo, _("Set Info type.")))
		self.list.append(getConfigListEntry(_("Coverwall Headline Color:"), config.plugins.mp3browser.color, _("colour.")))
		self.list.append(getConfigListEntry(_("Metrix List Content:"), config.plugins.mp3browser.metrixlist, _("Artist or Artist & Track Info.")))
		self.list.append(getConfigListEntry(_("Metrix List Selection Color:"), config.plugins.mp3browser.metrixcolor, _("Colour.")))
		self.list.append(getConfigListEntry(_("Show List of MP3 Folder:"), config.plugins.mp3browser.showfolder, _("Yes/No.")))
		self.list.append(getConfigListEntry(_("Plugin in Enigma Menu:"), config.plugins.mp3browser.showmenu, _("Show in Extensions.")))
		self.list.append(getConfigListEntry(_("Plugin Sans Serif Font:"), config.plugins.mp3browser.font, _("Font choice.")))
		self.list.append(getConfigListEntry(_("Update Database at Start:"), config.plugins.mp3browser.autoupdate, _("Database update Yes/No.")))
		self.list.append(getConfigListEntry(_("Hide Plugin during Update:"), config.plugins.mp3browser.hideupdate, _("Yes/No.")))
		self.list.append(getConfigListEntry(_("Plugin Auto Update Check:"), config.plugins.mp3browser.autocheck, _("Auto/No.")))
		self.list.append(getConfigListEntry(_("Cleanup Cache Folder:"), config.plugins.mp3browser.cleanup, _("Cleanup Yes/No.")))
		self.list.append(getConfigListEntry(_("Backup Database:"), config.plugins.mp3browser.backup, _("Backup Yes/No.")))
		self.list.append(getConfigListEntry(_("Restore Database:"), config.plugins.mp3browser.restore, _("Restore Yes/No.")))
		self.list.append(getConfigListEntry(_("Reset Database:"), config.plugins.mp3browser.reset, _("reset MP3Browser Database.")))					
		self["config"].list = self.list

		
	def layoutFinished(self):
		print("[MP3Browser][mp3BrowserConfig]layoutFinished entered")
		Setup.layoutFinished(self)
		self.UpdateComponents()

	def selectionChanged(self):
		print("[MP3Browser][mp3BrowserConfig]selectionChanged entered")
		Setup.selectionChanged(self)
		self.UpdateComponents()

	def changedEntry(self):
		print("[MP3Browser][mp3BrowserConfig]changedEntry entered")
		Setup.changedEntry(self)
		self.UpdateComponents()

	def keyCancel(self):
		print("[MP3Browser][mp3BrowserConfig]keyCancel entered")
		Setup.keyCancel(self)

	def confirm(self, confirmed):
		print("[MP3Browser][mp3BrowserConfig]confirmed entered")
		if not confirmed:
			return
		else:
			Setup.keySave(self)

	def keySave(self):
		current = self["config"].getCurrent()
		print(f"[MP3Browser][mp3BrowserConfig]keySave entered self.ready{self.ready}")
		Setup.keySave(self)
		if self.ready == False:
			self.ready = True
			if current[0] == "MP3 Sort Order:" and fileExists(self.database):
				databaseSort(self.database)
			if config.plugins.mp3browser.reset.value == "yes":
				open("/usr/lib/enigma2/python/Plugins/Extensions/MP3Browser/db/reset", "w").close()
				config.plugins.mp3browser.reset.value = "no"
				config.plugins.mp3browser.reset.save()
			if config.plugins.mp3browser.cachefolder.value != self.cachefolder:
				self.container = eConsoleAppContainer()
				self.container.appClosed.append(self.finished)
				newcache = sub("/cache", "", config.plugins.mp3browser.cachefolder.value)
				self.container.execute("mkdir -p '%s' && cp -r '%s' '%s' && rm -rf '%s'" % (config.plugins.mp3browser.cachefolder.value, self.cachefolder, newcache, self.cachefolder))
				self.cachefolder = config.plugins.mp3browser.cachefolder.value
				config.plugins.mp3browser.cachefolder.save()
			print("[MP3Browser][mp3BrowserConfig]save ---> Setup.keySave entered")

	def UpdateComponents(self):
		current = self["config"].getCurrent()
		print(f"[MP3Browser][mp3BrowserConfig]UpdateComponents ---> entered current:{current} current0:{current[0]}")
		if current[0] == "Goto last MP3 on Start:":
			if config.plugins.mp3browser.showfolder.value == "no" and config.plugins.mp3browser.lastmp3.value == "folder":
				config.plugins.mp3browser.lastmp3.value = "yes"
		elif current[0] == "Backup Database:":
			if exists(self.cachefolder):
				if fileExists(self.database):
					data = fileReadLine(self.database)
					try:
						makedirs(self.cachefolder + "/backup")
					except OSError as e:
						print("[MP3Browser][UpdateComponents] OSEerror",  e)

					fileWriteLine(self.cachefolder + "/backup/database", "data")
					SessionObject().session.open(MessageBox, _("\nDatabase backuped to %s") % str(self.cachefolder + "/backup/database"), MessageBox.TYPE_INFO, close_on_any_key=True)
				else:
					SessionObject().session.open(MessageBox, _("\nDatabase %s not found:\nMP3 Browser Database Backup canceled.") % str(self.database), MessageBox.TYPE_ERROR)
			else:
				SessionObject().session.open(MessageBox, _("\nCache Folder %s not reachable:\nMP3 Browser Database Backup canceled.") % str(self.cachefolder), MessageBox.TYPE_ERROR)
		elif current[0] == "Restore Database:":
			if exists(self.cachefolder):
				if fileExists(self.cachefolder + "/backup/database"):
					data = fileReadLine(self.cachefolder + "/backup/database")
					fileWriteLine(self.database, "data")
					SessionObject().session.open(MessageBox, _("\nDatabase restored from %s") % str(self.cachefolder + "/backup/database"), MessageBox.TYPE_INFO, close_on_any_key=True)
				else:
					SessionObject().session.open(MessageBox, _("\nDatabase Backup %s not found:\nMP3 Browser Database Restore canceled.") % str(self.cachefolder + "/backup/database"), MessageBox.TYPE_ERROR)
			else:
				SessionObject().session.open(MessageBox, ("\nCache Folder %s not reachable:\nMP3 Browser Database Restore canceled.") % str(self.cachefolder), MessageBox.TYPE_ERROR)
		elif current[0] == "Cleanup Cache Folder:":
			if exists(self.cachefolder):
				if fileExists(self.database):
					data = fileReadLine(self.database)
					data = data + ":::default_folder.png:::default.png:::database:::"
					folder = self.cachefolder
					count = 0
					for root, dirs, files in walk(folder, topdown=False, onerror=None):
						for name in files:
							shortname = sub("\\.bmp|\\.gif|\\.jpg|\\.jpeg|\\.png|\\.lyrics|\\.discogs", "", name)
							shortname = sub("\\(|\\)|\\[|\\]", ".", shortname)
							if search(shortname, data) is None:
								filename = join(root, name)
								if fileExists(filename):
									remove(filename)
									count += 1

					del data
					if count == 0:
						SessionObject().session.open(MessageBox, _("\nNo orphaned Covers, Lyrics or Discogs Infos found:\nYour Cache Folder is clean."), MessageBox.TYPE_INFO, close_on_any_key=True)
					else:
						SessionObject().session.open(MessageBox, _("\nCleanup Cache Folder finished:\n%s orphaned Covers, Lyrics or Discogs Infos removed.") % str(count), MessageBox.TYPE_INFO, close_on_any_key=True)
				else:
					SessionObject().session.open(MessageBox, _("\nDatabase %s not found:\nCleanup Cache Folder canceled.") % str(self.database), MessageBox.TYPE_ERROR)
			else:
				SessionObject().session.open(MessageBox, _("\nCache Folder %s not reachable:\nCleanup Cache Folder canceled.") % str(self.cachefolder), MessageBox.TYPE_ERROR)
		return


def main(session, **kwargs):
	if config.plugins.mp3browser.style.value == "metrix":
		session.open(mp3BrowserMetrix, 0, ":::")
	else:
		session.open(mp3Browser, 0, ":::")


def menu(menuid, **kwargs):
	if menuid == "mainmenu":
		return [("MP3 Browser", main, "mp3browser", 43)]
	return []


def Plugins(**kwargs):
	lang = language.getLanguage()[:2]
	plugindesc = "Manage your MP3s"
	if config.plugins.mp3browser.showmenu.value == "no":
		return [
		 PluginDescriptor(name="MP3 Browser", description=plugindesc, where=[PluginDescriptor.WHERE_PLUGINMENU], icon="plugin.png", fnc=main),
		 PluginDescriptor(name="MP3 Browser", description=plugindesc, where=[PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main)]
	else:
		return [PluginDescriptor(name="MP3 Browser", description=plugindesc, where=[PluginDescriptor.WHERE_MENU], fnc=menu),
		 PluginDescriptor(name="MP3 Browser", description=plugindesc, where=[PluginDescriptor.WHERE_PLUGINMENU], icon="plugin.png", fnc=main),
		 PluginDescriptor(name="MP3 Browser", description=plugindesc, where=[PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main)]
