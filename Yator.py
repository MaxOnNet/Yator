#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

reload(sys)
sys.setdefaultencoding('utf8')

import os
import re
import shutil
import string

from pyItunes import *

from transliterate import translit

from Interfaces.Config import Config
from Interfaces.Transcode import AudioTranscode


class Yator:
    playlist_re = re.compile('Yator\sCD(?P<disk>\d\d)')

    def __init__(self):
        self.config = Config()
        transcode = AudioTranscode()

        cache_path = self.config.get("yator", "cache", "path", "")
        structure_path = self.config.get("yator", "structure", "path", "")

        if not os.path.isdir(cache_path):
            os.makedirs(cache_path, 0755)

        if not os.path.isdir(structure_path):
            os.makedirs(structure_path, 0755)

        # Делаем минимальную структуру для работы сд ченжера
        #
        structure_minimal_cd = self.config.get("yator", "structure", "minimal_cd", "6")

        for cd_index in range(1, int(structure_minimal_cd), 1):
            if len(str(cd_index)) == 1:
                cd_index = "0{0}".format(cd_index)

            cd_path = "{0}CD{1}".format(structure_path, str(cd_index))

            if not os.path.isdir(cd_path):
                os.makedirs(cd_path, 0755)

        library = Library(self.config.get("itunes", "", "library", ""))
        playlists = library.getPlaylistNames()

        for playlist in playlists:
            playlist_match = self.playlist_re.search(playlist)

            if playlist_match:
                disk_number = playlist_match.group('disk')
                disk_folder = "{0}CD{1}/".format(structure_path, disk_number)

                print "Find Yator playlist \'{0}\' at disk {1} with {2} songs".format(playlist, disk_number,
                                                                        len(library.getPlaylist(playlist).tracks))

                if not os.path.isdir(disk_folder):
                    os.makedirs(disk_folder, 0755)
                else:
                    filelist = [f for f in os.listdir(disk_folder) if f.endswith(".mp3")]
                    for f in filelist:
                        os.remove("{0}/{1}".format(disk_folder, f))

                for song in library.getPlaylist(playlist).tracks:
                    print "    Prepare #{2} [{0} - {1}]".format(song.artist, song.name, song.playlist_order)

                    file_cache = "{0}{1}.mp3".format(cache_path, song.track_id)
                    file_name = self.make_safe_filename(
                                             translit("{0}_{1} - {2}.mp3".format(song.playlist_order, song.artist,
                                                                                 song.name),
                                                      language_code="ru", reversed=True))
                    file_structure = "{0}{1}".format(disk_folder, file_name)

                    if not os.path.exists(file_cache):
                        transcode.transcode("/{0}".format(song.location), file_cache, bitrate=256)

                    shutil.copyfile(file_cache, file_structure)

    @staticmethod
    def make_safe_filename(filename):
        try:
            safechars = string.letters + string.digits + " -_."
            return filter(lambda c: c in safechars, filename)
        except:
            return ""
        pass


if __name__ == "__main__":
    Yator()
