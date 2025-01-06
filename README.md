kodi-repo-update
================

**repoupdate.py updates a local Kodi add-on repository from a local add-on source directory. It will find all the add-ons in the source directory which are newer than in the repository, then create all the required files, and update the addons.xml file accordingly.**

Python 3 is the only requirement.

Usage
--------

repoupdate.py can be run as an executable script.

  usage: repoupdate.py [-h] [-s SOURCE] [-f [ADDON ID]] [-F] repo

  Update a local Kodi repository from a local add-on source directory

  positional arguments:
    repo                  path to the root of the repository

  options:
    -h, --help            show this help message and exit
    -s SOURCE, --source SOURCE
                          path to the root of the add-on source directory
    -f [ADDON ID], --force [ADDON ID]
                          force update all add-ons or force update only the specified add-on.
    -F, --force-xml       force only the recreation of addons.xml


Or you can import the RepoUpdate class.
    
    from repoupdate import RepoUpdate
        
    repo = RepoUpdate('/path/to/addons', '/path/to/Dropbox/Public/Repo')
    repo.update()
