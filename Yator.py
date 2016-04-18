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
from Queue import Queue
from threading import Thread
from Interfaces.Config import Config
from Interfaces.Transcode import AudioTranscode


class Yator:

    def __init__(self):
        self.config = Config()
        self.queue = Queue()

        self.cache_path = self.config.get("yator", "cache", "path", "")
        self.structure_path = self.config.get("yator", "structure", "path", "")

        self.bitrate = self.config.get("transcode", "", "bitrate", "256")

        self.library = Library(self.config.get("itunes", "", "library", ""))
        self.playlist_re = re.compile("Yator\sCD(?P<disk>\d\d)")

        self.structure_prepare()
        self.queue_prepare()
        self.queue_worker()
        self.song_rebase()


    def structure_prepare(self):
        if not os.path.isdir(self.cache_path):
            os.makedirs(self.cache_path, 0755)

        if not os.path.isdir(self.structure_path):
            os.makedirs(self.structure_path, 0755)

        # Делаем минимальную структуру для работы сд ченжера
        #
        structure_minimal_cd = self.config.get("yator", "structure", "minimal_cd", "6")

        for cd_index in range(1, int(structure_minimal_cd), 1):
            if len(str(cd_index)) == 1:
                cd_index = "0{0}".format(cd_index)

            cd_path = "{0}CD{1}".format(self.structure_path, str(cd_index))

            if not os.path.isdir(cd_path):
                os.makedirs(cd_path, 0755)

    def song_rebase(self):
        playlists = self.library.getPlaylistNames()

        for playlist in playlists:
            playlist_match = self.playlist_re.search(playlist)

            if playlist_match:
                disk_number = playlist_match.group('disk')
                disk_folder = "{0}CD{1}/".format(self.structure_path, disk_number)

                print "Заполняем структуру по плейлисту \'{0}\' как диск {1} с {2} композицией(ями)".format(playlist,
                                                        disk_number, len(self.library.getPlaylist(playlist).tracks))

                if not os.path.isdir(disk_folder):
                    os.makedirs(disk_folder, 0755)
                else:
                    filelist = [f for f in os.listdir(disk_folder) if f.endswith(".mp3")]
                    for f in filelist:
                        os.remove("{0}/{1}".format(disk_folder, f))

                for song in self.library.getPlaylist(playlist).tracks:
                    print "    Перемещаем #{2} [{0} - {1}]".format(song.artist, song.name, song.playlist_order)

                    file_cache = "{0}{1}.mp3".format(self.cache_path, song.track_id)
                    file_name = self.make_safe_filename(
                                             translit("{0}_{1} - {2}.mp3".format(song.playlist_order, song.artist,
                                                                                 song.name),
                                                      language_code="ru", reversed=True))
                    file_structure = "{0}{1}".format(disk_folder, file_name)

                    shutil.copyfile(file_cache, file_structure)

    def queue_prepare(self):
        print 'Подготавливаем очередь для транскодинга...'

        self.library = Library(self.config.get("itunes", "", "library", ""))
        playlists = self.library.getPlaylistNames()

        for playlist in playlists:
            playlist_match = self.playlist_re.search(playlist)

            if playlist_match:
                print "Нашли плейлист \'{0}\' с {1} композицией(ями)".format(playlist,
                                                                        len(self.library.getPlaylist(playlist).tracks))

                for song in self.library.getPlaylist(playlist).tracks:
                    self.queue.put(["/{0}".format(song.location), "{0}{1}.mp3".format(self.cache_path, song.track_id)])

    def queue_worker(self):
        thread_count = self.config.get("transcode", "", "threads", "2")

        print 'Зупускаем {0} транскодеров(а) c битрейтом в {1} килобит в секунду.'.format(thread_count, self.bitrate)

        for thread_index in xrange(0, int(thread_count), 1):
            worker = Thread(target=self.thread_worker, args=(thread_index, self.queue, self.bitrate))
            worker.setDaemon(True)
            worker.start()

        self.queue.join()
        print 'Транскодинг завершен.'

    def thread_worker(self, thread_index, queue, file_bitrate):
        transcode = AudioTranscode()

        while True:
            [file_orig, file_transcoded] = queue.get()
            print '{0}: {1}'.format(thread_index, file_orig)
            transcode.transcode(file_orig, file_transcoded, bitrate=file_bitrate)
            queue.task_done()

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
