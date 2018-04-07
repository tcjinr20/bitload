#!/usr/bin/env python
# coding:utf-8

from bt.torrent import Torrent
from bt.client import Client

client = Client(Torrent('1.torrent'))
client.start()
# Torrent('1.torrent')