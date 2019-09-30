import setuptools

with open("README.md", "r") as fh:
	description = fh.read()

setuptools.setup(
  name             = "pyfgc",
  version          = "1.1.2",
  author           = "Carlos Ghabrous Larrea, Nuno Laurentino Mendes",
  author_email     = "carlos.ghabrous@cern.ch, nuno.laurentino.mendes@cern.ch",
  description      = description,
  url              = "https://gitlab.cern.ch/ccs/fgc/tree/master/sw/clients/python/pyfgc",
  python_requires  = ">=3.6",
  install_requires = ["pyfgc_rbac>=1.0", "pyfgc_name>=1.0", "pyserial>=3.4"],
  packages         = setuptools.find_packages(),
)
