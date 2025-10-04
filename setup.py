from setuptools import setup
import setup_translate

pkg = "Extensions.MP3Browser"
setup(
    name="enigma2-plugin-extensions-mp3browser",
    version="3.01",
    author="TwolDE -  original code @kashmir",
    description="Create playable library of MP3 files and their associated information/backgrounds",
    package_dir={pkg: "src"},
    packages=[pkg],
    package_data={pkg: ["db/filter", "db/last", "db/cache/*.png", "font/*.ttf", "pics/browser/*.png",
        "pics/buttons/*.png", "pics/setup/*.png", "*.png", "*.xml", "locale/*/LC_MESSAGES/*.mo"]},
    cmdclass=setup_translate.cmdclass,  # for translation
)
