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

""" Provides the RepoUpdate class for updating a local Kodi repository from
    a local add-on source directory.

    This can be run as an executable script (repoupdate -h for help with usage)
    or you can import the RepoUpdate class for use from your own python scripts
    
        from repoupdate import RepoUpdate
        
        repo = RepoUpdate('/path/to/repo', '/path/to/addons')
        repo.update()

    Requires Python 3
    No additional dependencies """


import os
import sys
import shutil
import zipfile
import hashlib
import xml.etree.ElementTree as ET
import argparse


def version_parts(version):
    """Convert a version string to a list of integers"""
    return [int(p) for p in version.split(".")]


class Addon:
    """A class representing an add-on in the source directory"""

    EXTS = (".py", ".xml", ".jpg", ".png", ".txt", ".po")

    def __init__(self, xml_file):
        self.tree = ET.parse(xml_file).getroot()
        self.id = self.tree.attrib["id"]
        self.version_str = self.tree.attrib["version"]
        self.version = version_parts(self.version_str)

        self._path = os.path.dirname(xml_file)

    def __str__(self):
        return f"{self.id}-{self.version_str}"

    def _create_zip(self, zip_path):
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(self._path):
                for f in files:
                    if os.path.splitext(f)[1] in self.EXTS:
                        path_orig = os.path.join(root, f)
                        path_zip = os.path.join(self.id, os.path.relpath(root, self._path), f)
                        z.write(path_orig, path_zip)

    def create_release(self, path):
        """Create a release"""
        dest = os.path.join(path, self.id)
        if not os.path.isdir(dest):
            os.makedirs(dest)

        zip_path = os.path.join(dest, str(self)) + ".zip"
        self._create_zip(zip_path)
        print(f"\t- Created {zip_path}.")

        os.chdir(self._path)

        for f in ("addon.xml", "icon.png", "fanart.jpg"):
            try:
                shutil.copy(f, dest)
            except IOError:
                continue
            else:
                print(f"\t- Copied {f}.")

        try:
            shutil.copy("changelog.txt", os.path.join(dest, f"changelog-{self.version_str}.txt"))
        except IOError:
            pass
        else:
            print("\t- Copied changelog.txt")

        os.chdir("..")


class RepoUpdate:
    """The main class which finds add-ons in the source directory and updates
    the repository with the latest version.

    The default source directory is the current directory."""

    def __init__(self, repo_root, source_root=None):
        if source_root is None:
            self.source_root = os.getcwd()
        else:
            self.source_root = os.path.abspath(source_root)
            try:
                os.chdir(source_root)
            except OSError:
                print(f"Source directory does not exist: {source_root}")
                sys.exit(1)

        self.repo_root = os.path.abspath(repo_root)

        xml_path = os.path.join(self.repo_root, "addons.xml")
        try:
            self._xml = ET.parse(xml_path).getroot()
        except IOError:
            self._xml = None

    def _addons(self):
        for root, _, filenames in os.walk(self.source_root):
            if "addon.xml" in filenames and ".repoignore" not in filenames:
                addon_xml = os.path.join(root, "addon.xml")
                try:
                    yield Addon(addon_xml)
                except ET.ParseError:
                    print(f"Skipping invalid addon.xml: {addon_xml}")

    def _needs_update(self, addon_id, version):
        if self._xml is not None:
            xpath = f"addon[@id='{addon_id}']"
            repo_addon = self._xml.find(xpath)
            return repo_addon is None or version_parts(repo_addon.attrib["version"]) < version
        else:
            return True

    def update(self, force_update=False, force_xml=False):
        """Update the repository with the latest versions of the add-ons"""
        update_required = force_xml
        addons = list(self._addons())
        if addons:
            # Build xml tree and create release zip files as necessary
            element = ET.Element("addons")
            for addon in addons:
                print(f"Found {addon.id}")
                element.append(addon.tree)
                # Only update if the add-on has not already been released
                # or the update is forced
                if (
                    self._needs_update(addon.id, addon.version)
                    or force_update is True
                    or force_update == addon.id
                ):
                    update_required = True
                    print(f"Releasing {addon}...")
                    addon.create_release(self.repo_root)

            if update_required:
                # Generate strings
                xml = ET.tostring(element, encoding="utf-8")
                xml_md5 = hashlib.md5(xml).hexdigest().encode("utf-8")

                # Update addons.xml and addons.xml.md5
                for f, content in (("addons.xml", xml), ("addons.xml.md5", xml_md5)):
                    path = os.path.join(self.repo_root, f)
                    open(path, "wb").write(content)
                    print(f"Updated {path}")
            else:
                print("No repo update required.")
        else:
            print("No addons found.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update a local Kodi repository from a local add-on source directory"
    )
    parser.add_argument("repo", help="path to the root of the repository")
    parser.add_argument("-s", "--source", help="path to the root of the add-on source directory")
    parser.add_argument(
        "-f",
        "--force",
        nargs="?",
        const=True,
        default=False,
        metavar="ADDON ID",
        help="force update all add-ons " "or force update only the specified add-on.",
    )
    parser.add_argument(
        "-F", "--force-xml", action="store_true", help="force only the recreation of addons.xml"
    )

    args = parser.parse_args()

    repo = RepoUpdate(args.repo, args.source)
    repo.update(args.force, args.force_xml)
