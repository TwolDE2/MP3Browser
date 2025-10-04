DESCRIPTION = "Create playable library of MP3 files and their associated information/backgrounds"
MAINTAINER = "TwolDE -  original code @kashmir "

require conf/license/license-gplv2.inc
require conf/python/python3-compileall.inc
inherit gitpkgv allarch gettext setuptools3-openplugins

PV = "3.01+git"
PKGV = "3.01+git${GITPKGV}"

SRCREV = "${AUTOREV}"

SRC_URI = "git://github.com/TwolDE2/MP3Browser.git;protocol=https;branch=main"
