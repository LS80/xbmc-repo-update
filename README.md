xbmc-repo-update
================

repoupdate.py provides the RepoUpdate class for updating a local xbmc add-on repository from a local add-on source directory. The repository path defaults to a folder in your Dropbox Public folder called 'Repo' which can then serve as an xbmc repository at dl.dropboxusercontent.com/u/\<userid\>/Repo/.

This has been tested on Linux and Windows. Python 2.7 is the only requirement.

If you don't yet have a Dropbox account to use as an add-on repository then sign up via this referral link and we'll both get more free space - http://db.tt/btOEa2SW.

To enable a Dropbox Public folder go to https://www.dropbox.com/enable_public_folder.

Usage
--------

repoupdate.py can be run as an executable script.

    usage: repoupdate.py [-h] [-s SOURCE] [-r REPO]

    Update a local xbmc repository from a local add-on source directory

    optional arguments:
      -h, --help            show this help message and exit
      -s SOURCE, --source SOURCE
                            path to the root of the add-on source directory
      -r REPO, --repo REPO  path to the root of the repository


Or you can import the RepoUpdate class.
    
    from repoupdate import RepoUpdate
        
    repo = RepoUpdate('/path/to/addons', '/path/to/Dropbox/Public/Repo')
    repo.update()
