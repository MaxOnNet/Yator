#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import wraps
import xml.dom.minidom
import os


class Config:
    """
        Класс отвечаюший за сохранение и загрузку конфигурации
    """

    def __init__(self):
        self.xml_file = "{0}/config.xml".format(os.path.abspath(os.path.join(os.path.dirname(
            os.path.realpath(__file__)), '..')))
        self.xml = xml.dom.minidom.parse(self.xml_file)
        self.configuration = self.xml.getElementsByTagName("configuration")[0]


    def fix_parms(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            value_o = str(fn(*args, **kwargs))
            value_n = ""

            value_n = str.replace(value_o, "$path", str(os.path.abspath(os.path.join(os.path.dirname(
                os.path.realpath(__file__)), '..'))))

            return value_n
        return wrapped

    @fix_parms
    def get(self, group, item, attribute, value=""):
        for group in self.configuration.getElementsByTagName(group):
            if item == "":
                if group.hasAttribute(attribute):
                    return group.getAttribute(attribute)
                else:
                    return value
            else:
                for item in group.getElementsByTagName(item):
                    if item.hasAttribute(attribute):
                        return item.getAttribute(attribute)
                    else:
                        return value

    def set(self, group, item, attribute, value):
        if len(self.configuration.getElementsByTagName(group)) == 0:
            self.configuration.appendChild(self.xml.createElement(group))

        for group in self.configuration.getElementsByTagName(group):
            if item == "":
                group.setAttribute(attribute, value)
            else:
                if len(group.getElementsByTagName(item)) == 0:
                    group.appendChild(self.xml.createElement(item))

                for item in group.getElementsByTagName(item):
                    item.setAttribute(attribute, value)

        self.save()

    def remove(self, group, item, attribute):
        for group in self.configuration.getElementsByTagName(group):
            if item == "" and attribute != "":
                if group.hasAttribute(attribute):
                    group.removeAttribute(attribute)

            elif item == "" and attribute == "":
                self.configuration.removeChild(group)

            else:
                for item in group.getElementsByTagName(item):
                    if attribute != "":
                        if item.hasAttribute(attribute):
                            item.removeAttribute(attribute)
                    else:
                        group.removeChild(item)

        self.save()

    def save(self):
        io_writer = open(self.xml_file, "w")
        io_writer.writelines(self.xml.toprettyxml(indent="", newl="", encoding="UTF-8"))
        io_writer.close()

