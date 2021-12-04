from setuptools import find_packages
from setuptools import setup

PACKAGE_NAME = "onetimepass"
SCRIPT_NAME = "otp"

DEPENDENCIES = ["click"]
DEV_DEPENDENCIES = ["pre-commit"]

setup(
    name=PACKAGE_NAME,
    version="0.0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=DEPENDENCIES,
    extras_require={"dev": DEV_DEPENDENCIES},
    entry_points=f"""
        [console_scripts]
        {SCRIPT_NAME}={PACKAGE_NAME}.{SCRIPT_NAME}:otp
    """,
)
