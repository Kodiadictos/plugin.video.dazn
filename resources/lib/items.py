# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from kodi_six.utils import py2_encode

import xbmc
import xbmcgui
import xbmcplugin


class Items:


    def __init__(self, plugin):
        self.cache = True
        self.video = False
        self.plugin = plugin


    def list_items(self, focus=False, upd=False, epg=False):
        if self.video:
            xbmcplugin.setContent(self.plugin.addon_handle, self.plugin.content)
        xbmcplugin.endOfDirectory(self.plugin.addon_handle, cacheToDisc=self.cache, updateListing=upd)

        if self.plugin.force_view:
            view_id = self.plugin.view_id
            if self.video:
                view_id = self.plugin.view_id_videos
            if epg:
                view_id = self.plugin.view_id_epg
            xbmc.executebuiltin('Container.SetViewMode({0})'.format(view_id))

        if focus:
            try:
                wnd = xbmcgui.Window(xbmcgui.getCurrentWindowId())
                wnd.getControl(wnd.getFocusId()).selectItem(focus)
            except:
                pass


    def add_item(self, item):
        verify_age = item.get('verify_age', False)

        data = {
            'mode': item['mode'],
            'title': py2_encode(item['title']),
            'id': item.get('id', ''),
            'params': item.get('params', ''),
            'verify_age': verify_age
        }

        art = {
            'thumb': item.get('thumb', self.plugin.addon_icon),
            'poster': item.get('thumb', self.plugin.addon_icon),
            'fanart': item.get('fanart', self.plugin.addon_fanart)
        }

        labels = {
            'title': item['title'],
            'plot': item.get('plot', item['title']),
            'premiered': item.get('date', ''),
            'episode': item.get('episode', 0)
        }

        if verify_age:
            labels['mpaa'] = 'PG-18'

        listitem = xbmcgui.ListItem(item['title'])
        listitem.setArt(art)
        listitem = self.plugin.set_videoinfo(listitem, labels)

        if 'play' in item['mode']:
            self.cache = False
            self.video = True
            folder = False
            listitem = self.plugin.set_streaminfo(listitem, {'duration': item.get('duration', 0)})
            listitem.setProperty('IsPlayable', item.get('playable', 'false'))
        else:
            folder = True

        if item.get('cm', None):
            listitem.addContextMenuItems(item['cm'])

        xbmcplugin.addDirectoryItem(self.plugin.addon_handle, self.plugin.build_url(data), listitem, folder)


    def play_item(self, item, name, context):
        path = item.ManifestUrl
        resolved = True if path else False
        listitem = xbmcgui.ListItem()
        listitem.setContentLookup(False)
        listitem.setMimeType('application/dash+xml')
        listitem.setProperty('inputstreamaddon' if self.plugin.kodi_version <= 18 else 'inputstream', 'inputstream.adaptive')
        listitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        listitem.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
        listitem.setProperty('inputstream.adaptive.max_bandwidth', self.plugin.max_bw)
        listitem.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
        listitem.setProperty('inputstream.adaptive.license_key', '{0}|authorization=Bearer {1}|R{{SSM}}|'.format(item.LaUrl, self.plugin.get_setting('token')))
        if context and resolved:
            listitem = self.plugin.set_videoinfo(listitem, dict(title=name))
            player = xbmc.Player()
            player.play(path, listitem)
            if 'beginning' in context:
                monitor = xbmc.Monitor()
                while not monitor.abortRequested() and (player.isPlayingVideo() == False or player.getTotalTime() == 0):
                    monitor.waitForAbort(0.1)
                player.seekTime(0)
                del monitor
        else:
            listitem.setPath(path)
            xbmcplugin.setResolvedUrl(self.plugin.addon_handle, resolved, listitem)
