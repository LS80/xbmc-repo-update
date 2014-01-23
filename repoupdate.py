#! /usr/bin/python

#  Copyright 2013 Lee Smith <lee@lee-smith.me.uk>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

""" Provides the RepoUpdate class for updating a local xbmc repository from 
    a local add-on source directory.

    This can be run as an executable script (repoupdate -h for help with usage)
    or you can import the RepoUpdate class for use from your own python scripts
    
        from repoupdate import RepoUpdate
        
        repo = RepoUpdate('/path/to/addons', '/path/to/Dropbox/Public/Repo')
        repo.update()

    If you don't yet have a Dropbox account yet then sign up via this referral
    link and we'll both get more free space - http://db.tt/btOEa2SW

    Cross-platform (tested on Linux and Windows)
    Requires Python 2.7
    No additional dependencies """

from __future__ import print_function

import os
import sys
import shutil
import zipfile
import hashlib
import xml.etree.ElementTree as ET
import argparse

def version_parts(version):
    return [int(p) for p in version.split('.')]

class Addon(object):
    """ A class representing an add-on in the source directory """

    EXTS = ('.py', '.xml', '.jpg', '.png', '.txt')
    
    def __init__(self, xml_file):
        self.tree = ET.parse(xml_file).getroot()
        self.id = self.tree.attrib['id']
        self.version_str = self.tree.attrib['version']
        self.version = version_parts(self.version_str)
        
        self._path = os.path.dirname(xml_file)
    
    def __str__(self):
        return '{}-{}'.format(self.id, self.version_str)
    
    def _create_zip(self, zip_path):
        z = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(self._path):
            for f in files:
                if os.path.splitext(f)[1] in self.EXTS:
                    path_orig = os.path.join(root, f)
                    path_zip = os.path.join(self.id, os.path.relpath(root, self._path), f)
                    z.write(path_orig, path_zip)
        z.close()
        
    def create_release(self, path):
        dest = os.path.join(path, self.id)
        if not os.path.isdir(dest):
            os.makedirs(dest)

        zip_path = os.path.join(dest, str(self)) + '.zip'
        self._create_zip(zip_path)
        print("\t- Created {}.".format(zip_path))

        os.chdir(self._path)

        for f in ('addon.xml', 'icon.png', 'fanart.jpg'):
            try:
                shutil.copy(f, dest)
            except IOError:
                continue
            else:
                print("\t- Copied {}.".format(f))

        try:
            shutil.copy('changelog.txt',
                        os.path.join(dest,
                                     'changelog-{}.txt'.format(self.version_str)))
        except IOError:
            pass
        else:
            print("\t- Copied changelog.txt".format())

        os.chdir('..')

    
class RepoUpdate(object):
    """ The main class which finds add-ons in the source directory and updates
        the repository with the latest version.
        
        The default repository is a directory called Repo in your Dropbox
        Public folder.
        
        The default source directory is the current directory. """

    def __init__(self, source_root=None, repo_root=None):
        if source_root is None:
            self.source_root = os.getcwd()
        else:
            self.source_root = os.path.abspath(source_root)
            try:
                os.chdir(source_root)
            except OSError:
                print("Source directory does not exist: {}".format(source_root))
                sys.exit(1) 	
        
        if repo_root is None:
            self.repo_root = os.path.join(os.path.expanduser('~'),
                                          'Dropbox', 'Public', 'Repo')
        else:
            self.repo_root = os.path.abspath(repo_root)
          
        xml_path = os.path.join(self.repo_root, 'addons.xml')  
        try:
            self._xml = ET.parse(xml_path).getroot()
        except IOError:
            self._xml = None
        
    def _addons(self):
        for root, dirs, filenames in os.walk(self.source_root):
            if 'addon.xml' in filenames and '.repoignore' not in filenames:
                addon_xml = os.path.join(root, 'addon.xml')
                try:
                    yield Addon(addon_xml)
                except ET.ParseError:
                    print("Skipping invalid addon.xml: {}".format(addon_xml))

    def _needs_update(self, addon_id, version):
        if self._xml is not None:
            xpath = "addon[@id='{}']".format(addon_id, version)
            repo_addon = self._xml.find(xpath)
            return (repo_addon is None or
                    version_parts(repo_addon.attrib['version']) < version)
        else:
            return True

    def update(self, force_update=False, force_xml=False):
        update_required = force_xml
        addons = list(self._addons())
        if addons: 
            # Build xml tree and create release zip files as necessary
            element = ET.Element('addons')
            for addon in addons:
                print("Found {}".format(addon.id))
                element.append(addon.tree)
                # Only update if the add-on has not already been released
                # or the update is forced
                if (self._needs_update(addon.id, addon.version) or 
                    force_update is True or
                    force_update == addon.id):
                    update_required = True
                    print("Releasing {}...".format(addon))
                    addon.create_release(self.repo_root)

            if update_required:
                # Generate strings
                xml = ET.tostring(element, encoding='UTF-8')
                xml_md5 = hashlib.md5(xml).hexdigest()
                
                # Update addons.xml and addons.xml.md5
                for f, content in (('addons.xml', xml),
                                   ('addons.xml.md5', xml_md5)):
                    path = os.path.join(self.repo_root, f)
                    open(path, 'w').write(content)
                    print("Updated {}".format(path))
            else:
                print("No repo update required.")
        else:
            print("No addons found.")


if __name__ == '__main__':
    txt = "Update a local xbmc repository from a local add-on source directory"
    parser = argparse.ArgumentParser(description=txt)
    parser.add_argument('-s', '--source',
                        help="path to the root of the add-on source directory")
    parser.add_argument('-r', '--repo',
                        help="path to the root of the repository")
    parser.add_argument('-f', '--force', nargs='?', const=True, default=False,
                        metavar='ADDON ID',
                        help="force update all add-ons "
                             "or force update only the specified add-on.")
    parser.add_argument('-F', '--force-xml', action='store_true',
                        help="force only the recreation of addons.xml")
    
    args = parser.parse_args()

    repo = RepoUpdate(args.source, args.repo)
    repo.update(args.force, args.force_xml)
