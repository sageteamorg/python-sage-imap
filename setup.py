from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="python_sage_imap",
    version="0.4.0",
    author="Sepehr Akbarzadeh",
    author_email="info@sageteam.org",
    description="Managing IMAP connections and performing various email operations.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sageteamorg/python-sage-imap",
    projcet_urls={
        "Documentation": "https://python-sage-imap.readthedocs.io/en/latest/",
        "Source Code": "https://github.com/sageteamorg/python-sage-imap",
        "Issues": "https://github.com/sageteamorg/python-sage-imap/issues",
    },
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
    ],
    python_requires=">=3.11",
)
