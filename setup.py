
requires = ["pyopenphoto"]
try:
    import argparse
    argparse

except ImportError:
    requires.append('argparse')

try:
    from setuptools import setup
    kw = {
        "entry_points": """
[console_scripts]
    openphoto-downloader = openphoto_utils.downloader:main
    openphoto-shell = openphoto_utils.shell:main
    openphoto-importer = openphoto_utils.importer:main
""",
        "zip_safe": False,
        "install_requires": requires
    }
except ImportError:
    from distutils.core import setup
    kw = {
        "scripts": ['scripts/openphoto-downloader', 'scripts/openphoto-shell',
                    'scripts/openphoto-importer'],
        "requires": "requires"
    }

setup(name="openphoto-utils",
      version="0.1",
      description="Utils for openphoto",
      author="Giacomo Bagnoli",
      author_email="gbagnoli@gmail.com",
      packages=["openphoto_utils"],
      **kw
)



