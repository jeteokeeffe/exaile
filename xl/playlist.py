# Playlist
#
# Playlist - essentially an ordered TrackDB
#
# also contains functions for saving and loading various playlist formats.

from xl import trackdb, event
import urllib, random

def save_to_m3u(playlist, path):
    """
        Saves a Playlist to an m3u file
    """
    handle = open(path, "w")

    handle.write("#EXTM3U\n")
    if playlist.get_name() != '':
        handle.write("#PLAYLIST: %s\n" % playlist.get_name())

    for track in playlist:
        leng = track.info['length']
        if leng == 0: 
            leng = -1
        handle.write("#EXTINF:%d,%s\n%s\n" % (leng,
            track['title'], track.get_loc()))

    handle.close()

def import_from_m3u(path):
    # import -1 as 0
    pass

def save_to_pls(playlist, path):
    """
        Saves a Playlist to an pls file
    """
    handle = open(path, "w")
    
    handle.write("[playlist]\n")
    handle.write("NumberOfEntries=%d\n\n" % len(playlist))
    
    count = 1 
    
    for track in playlist:
        handle.write("File%d=%s\n" % (count, track.get_loc()))
        handle.write("Title%d=%s\n" % (count, track['title']))
        if track.info['length'] < 1:
            handel.write("Length%d=%d\n\n" % (count, -1))
        else:
            handle.write("Length%d=%d\n\n" % (count, track.info['length']))
        count += 1
    
    handle.write("Version=2")
    handle.close()

def import_from_pls(path):
    pass
    
def save_to_asx(playlist, path):
    """
        Saves a Playlist to an asx file
    """
    handle = open(path, "w")
    
    handle.write("<asx version=\"3.0\">\n")
    if playlist.get_name() != '':
        name = ''
    else:
        name = playlist.get_name()
    handle.write("  <title>%s</title>\n" % name)
    
    for track in playlist:
        handle.write("<entry>\n")
        handle.write("  <title>%s</title>\n" % track['title'])
        handle.write("  <ref href=\"%s\" />\n" % urllib.quote(track.get_loc()))
        handle.write("</entry\n")
    
    handle.write("</asx>")
    handle.close()
    
def import_from_asx(path):
    # urllib.unquote(string)
    pass

def save_to_xspf(playlist, path):
    """
        Saves a Playlist to a xspf file
    """
    handle = open(path, "w")
    
    handle.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
    handle.write("<playlist version=\"1\" xmlns=\"http://xspf.org/ns/0/\">\n")
    if playlist.get_name() != '':
        handle.write("  <title>%s</title>\n" % playlist.get_name())
    
    handle.write("  <trackList>\n")
    for track in playlist:
        handle.write("    <track>\n")
        handle.write("      <title>%s</title>\n" % track['title'])
        if track.info['length'] > 0:
            handle.write("      <location>file://%s</location>\n" % urllib.quote(track.get_loc()))
        else:
            handle.write("      <location>%s</location>\n" % urllib.quote(track.get_loc()))
        handle.write("    </track>\n")
    
    handle.write("  </trackList>\n")
    handle.write("</playlist>\n")
    handle.close()
    
def import_from_xspf(path):
    # urllib.unquote(string)
    pass

class PlaylistIterator(object):
    def __init__(self, pl):
        self.pos = -1
        self.pl = pl
    def __iter__(self):
        return self
    def next(self):
        self.pos+=1
        try:
            return self.pl.ordered_tracks[self.pos]
        except:
            raise StopIteration


class Playlist(trackdb.TrackDB):
    """
        Represents a playlist, which is basically just a TrackDB
        with ordering.
    """
    def __init__(self, name="", location=None, pickle_attrs=[]):
        """
            Sets up the Playlist

            args: see TrackDB
        """
        self.ordered_tracks = []
        self.current_pos = -1
        self.current_playing = False
        self.shuffle_enabled = False
        self.random_enabled = False
        pickle_attrs += ['name', 'ordered_tracks', 'current_pos', 
                'current_playing', "shuffle_enabled", "random_enabled"]
        trackdb.TrackDB.__init__(self, name=name, location=location,
                pickle_attrs=pickle_attrs)

    def __len__(self):
        """
            Returns the lengh of the playlist.
        """
        return len(self.ordered_tracks)

    def __iter__(self):
        """
            allows "for song in playlist" synatax

            warning: assumes playlist doesn't change while iterating
        """
        return PlaylistIterator(self)

    def add(self, track, location=None):
        """
            insert the track into the playlist at the specified
            location (default: append)

            track: the track to add [Track]
            location: the index to insert at [int]
        """
        self.add_tracks([track], location)

    def add_tracks(self, tracks, location=None):
        """
            like add(), but takes a list of tracks instead of a single one

            tracks: the tracks to add [list of Track]
            location: the index to insert at [int]
        """
        if location == None:
            self.ordered_tracks.extend(tracks)
        else:
            self.ordered_tracks = self.ordered_tracks[:location] + \
                    tracks + self.ordered_tracks[location:]
        for t in tracks:
            trackdb.TrackDB.add(self, t)
        
        if location >= self.current_pos:
            self.current_pos += len(tracks)

    def remove(self, index):
        """
            removes the track at the specified index from the playlist

            index: the index to remove at [int]
        """
        self.remove_tracks(index, index)

    def remove_tracks(self, start, end):
        """
            remove the specified range of tracks from the playlist

            start: index to start at [int]
            end: index to end at (inclusive) [int]
        """
        end = end + 1
        removed = self.ordered_tracks[start:end]
        self.ordered_tracks = self.ordered_tracks[:start] + \
                self.ordered_tracks[end:]
        for t in removed:
            trackdb.TrackDB.remove(self, t)

        if end < self.current_pos:
            self.current_pos -= len(removed)
        elif start <= self.current_pos <= end:
            self.current_pos = start+1

    def get_tracks(self):
        """
            gets the list of tracks in this playlist, in order

            returns: [list of Track]
        """
        return self.ordered_tracks[:]

    def get_current_pos(self):
        """
            gets current playback position, -1 if not playing

            returns: the position [int]
        """
        return self.current_pos

    def set_current_pos(self, pos):
        if pos < len(self.ordered_tracks):
            self.current_pos = pos
        event.log_event('current_changed', self, pos)

    def get_current(self):
        """
            gets the currently-playing Track, or None if no current

            returns: the current track [Track]
        """
        if self.current_pos >= len(self.ordered_tracks) or \
                self.current_pos == -1:
            return None
        else:
            return self.ordered_tracks[self.current_pos]

    def next(self):
        """
            moves to the next track in the playlist

            returns: the next track [Track], None if no more tracks
        """
        if self.random_enabled:
            if len(self.ordered_tracks) == 1:
                return None
            next = self.current_pos
            while next == self.current_pos:
                next = random.choice(range(len(self.ordered_tracks)))
            self.current_pos = next
        else:
            if len(self.ordered_tracks) == 0:
                return None
            self.current_pos += 1

        if self.current_pos >= len(self.ordered_tracks):
            if self.repeat_enabled:
                self.current_pos = 0
            else:
                self.current_pos = -1

        event.log_event('current_changed', self, self.current_pos)
        return self.get_current()

    def prev(self):
        """
            moves to the previous track in the playlist

            returns: the previous track [Track]
        """
        if self.random_enabled:
            return self.get_current() # cant seek backwards in random mode

        self.current_pos -= 1
        if self.current_pos < 0:
            if self.repeat_enabled:
                self.current_pos = len(self.ordered_tracks) - 1
            else:
                self.current_pos = 0

        event.log_event('current_changed', self, self.current_pos)
        return self.get_current()

    def search(self, phrase, sort_field=None):
        """
            searches the playlist
        """
        tracks = trackdb.TrackDB.search(self, phrase, sort_field)
        if sort_field is None:
            from copy import deepcopy
            new_tracks = []
            for tr in self.ordered_tracks:
                if tr in tracks:
                    new_tracks.append(tr)
            tracks = new_tracks
        return tracks

    def toggle_random(self, mode=None):
        """
            toggle random playback order

            mode: set random to this [bool]
        """
        if mode is not None:
            self.random_enabled = mode
        else:
            self.random_enabled = self.random_enabled == False

    def toggle_repeat(self, mode=None):
        """
            toggle repeat playback

            mode: set repeat to this [bool]
        """
        if mode is not None:
            self.repeat_enabled = mode
        else:
            self.repeat_enabled = self.repeat_enabled == False


class SmartPlaylist(Playlist):
    """ 
        Represents a Smart Playlist.  
        This will query a collection object using a set of parameters
    """
    def __init__(self, location=None, collection=None, pickle_attrs=[]):
        """
            Sets up a smart playlist
            
            collection: a reference to a TrackDB object.
    
            args: See TrackDB
        """
        self.search_params = []
        self.custom_params = []
        self.collection = collection
        self.or_match = False
        pickle_attrs += ['search_params', 'or_match']
        Playlist.__init__(self, location=location,
                pickle_attrs=pickle_attrs)

    def set_collection(self, collection):
        """
            change the collection backing this playlist

            collection: the collection to use [Collection]
        """
        self.collection = collection

    def set_or_match(self, value):
        """
            Set to True to make this an or match: match any of the parameters

            value: True to match any, False to match all params
        """
        self.or_match = value

    def get_or_match(self):
        """
            Return if this is an any or and playlist
        """
        return self.or_match
        
    def add_param(self, field, op, value, index=-1):
        """
            Adds a search parameter.

            field:  The field to operate on. [string]
            op:     The operator.  Valid operators are:
                    >,<,>=,<=,=,!=,==,!==,>< (between) [string]
            value:  The value to match against [string]
            index:  Where to insert the parameter in the search order.  -1 
                    to append [int]
        """
        if index:
            self.search_params.insert(index, [field, op, value])
        else:
            self.search_params.append([field, op, value])

    def set_custom_param(self, param, index=-1):
        """
            Adds an arbitrary search parameter, exposing the full power
            of the new search system to the user.

            param:  the search query to use. [string]
            index:  the index to insert at. default is append [int]
        """
        if index:
            self.search_params.insert(index, param)
        else:
            self.search_params.append(param)
   

    def remove_param(self, index):
        """
            Removes a parameter at the speficied index
        
            index:  the index of the parameter to remove
        """
        return self.search_params.pop(index)

    def update(self, collection=None, clear=True):
        """
            Update internal tracks by querying the collection
            collection: the collection to search (leave none to search
                        internal ref)
            clear:      clear current tracks
        """
        self.remove_tracks(0, len(self))
        if not collection:
            collection = self.collection
        if not collection: #if there wasnt one set we might not have one
            return

        search_string = self._create_search_string()
        self.add_tracks(collection.search(search_string))

    def _create_search_string(self):
        """
            Creates a search string based on the internal params
        """

        params = [] # parameter list

        for param in self.search_params:
            if type(param) == str:
                params += [param]
                continue
            (field, op, value) = param
            s = ""
            if op == ">=" or op == "<=":
                s += '( %(field)s%(op)s%(value)s ' \
                    'OR %(field)s==%(value)s )' % \
                    {
                        'field': field,
                        'value': value,
                        'op':    op[0]
                    }
            elif op == "!=" or op == "!==":
                s += 'NOT %(field)s%(op)s"%(value)s"' % \
                    {
                        'field': field,
                        'value': value,
                        'op':    op[1:]
                    }
            elif op == "><":
                s+= '( %(field)s>%(value1)s AND ' \
                    '%(field)s<%(value2)s )' % \
                    {
                        'field':  field,
                        'value1': value[0],
                        'value2': value[1]
                    }
            else:
                s += '%(field)s%(op)s"%(value)s"' % \
                    {
                        'field': field,
                        'value': value,
                        'op':    op
                    }

            params.append(s)

        if self.or_match:
            return ' OR '.join(params)
        else:
            return ' '.join(params)
