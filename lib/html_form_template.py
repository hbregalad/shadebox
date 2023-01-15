try:
    from .html_template import *
except:
    from html_template import *
import random
import time
from flask import Flask, request

class DataBuffer:
    def __init__(self, data):
        self.data = data #data may be nested list/dict or anything else that implements __getitem__ and __setitem__
    
    NOT_GIVEN = object()
    def access(self, path, _subvalue = NOT_GIVEN, value=NOT_GIVEN, default=NOT_GIVEN):
        if _subvalue is self.NOT_GIVEN:
            _subvalue = self.data
            
        if len(path) > 1:
            if path[0] in _subvalue:
                return self.access(path[1:], _subvalue[path[0]], value, default)
            else:
                raise KeyError("{} not found in {}".format(path[0] , _subvalue))
        elif len(path):
            #last path
            if path[0] in _subvalue:
                previous = _subvalue[path[0]]
            else:
                previous = default
                
            if value is not NOT_GIVEN:#set operation
                _subvalue[path[0]] = value
            return previous
            #else:#get
                #return previous
        else:
            return _subvalue

    def walk(self, path = tuple(), _subvalue=NOT_GIVEN, values=(str,int,float), collections=(tuple,list,dict)):
        if _subvalue is self.NOT_GIVEN:
            _subvalue = self.access(path)
            if _subvalue is self.NOT_GIVEN:
                raise KeyError("path {} not found in {}".format(path, self.data))

        try:
            d = _subvalue.items()
        except AttributeError:
            try:
                d = {k:_subvalue[k] for k in _subvalue.keys()}.items()
            except AttributeError:
                d = enumerate(_subvalue)

        collection_is_editable = hasattr(_subvalue, '__setitem__')

        fields = {}
        browsable = {}
        other = {}
        for k,v in d:
            if isinstance(v, values):
                fields[k] = v
            elif isinstance(v, collections):
                browsable[k] = v
            else:
                other[k] = v 
        nest_on = list(browsable.keys())

        #give the caller time to see the stuff
        yield path, nest_on, fields, other, collection_is_editable

        if collection_is_editable:
            for k,v in fields.items():
                _subvalue[k] = v

        #nest deeper, if the caller left any keys in nest_on to nest deeper on
        for k in nest_on:
            if k not in browsable: continue#skip junk if they've added any...
            yield from self.walk(path + (k,),
                                 browsable[k],
                                 values, collections)
if __name__=='__main__':
    d=DataBuffer({
        'a':(1,[2],{3:4}),
        'b':[1,(2,),{3:4}],
        })
    for Path, dirs, fields, other, Editable in d.walk():
        print(Editable, Path, dirs, fields, other)

class Form_Session:
    SESSIONS = {}
    def __init__(self, buffer, callback):
        self.buffer = buffer
        id_ = self.id = self.time = time()

        while id_ in self.SESSIONS:
            id_ = self.id = random.randint(2^62)

        self.callback = callback

        self.SESSIONS[id_] = self#save
    def cleanup(self, max=16000, timeout=2*7*24*60*60):#default time out is 2 weeks
        t = time.time() - timeout
        ss = self.SESSIONS
        #find sessions that have timed out
        timed_out = [fs for fs in ss.values()
                     if fs.time < t]
        #remove them
        [ss.pop(fs.id) for fs in timed_out]

        #sort the remaining, 
        s = sorted(self.SESSIONS.values(), key=lambda fs:fs.time)
        #while there are too many, remove the oldest
        while len(self.SESSIONS)>max:
            ss.pop(s.pop(0).id)

_app_registered = []
#register this with flask/bottle app
def event_handler(form_id, action):
    if request.method=='POST':
        print(request.form.items())
    elif request.method=='GET':
        print(request.args.items())
        
    try:
        form_id = int(form_id)
    except ValueError:
        try:
            form_id = float(form_id)
        except ValueError:
            return "Session data corrupted?"

    if form_id not in Form_Session.SESSIONS:
        return "Session expired?"

    fs = Form_Session.SESSIONS[form_id]
    
    fs.callback(action)
    

def mk_form(DataBuffer, app, starting_path=tuple()):
    form = html('form')#, indent='', sub_indent='')
    form(action='/update', method='post')

    in_progress = {tuple(): form}
    #fs = Form_Session(DataBuffer, 
    for Path, dirs, fields, other, Editable in DataBuffer.walk(starting_path):
        
        if Path and Path[:-1] in in_progress:
            outer_table = in_progress[Path[:-1]]
            tr = outer_table.tr
            tr.th.append(str(Path[-1]))
            table = tr.td.table.tbody
        else:
            print(Path)
            table = form.table
            table.thead.tr.th(colspan=2).append(" :: ".join((str(i) for i in Path)))
            table = table.tbody
        
        if not Editable:#not editable, just show values
            for k,v in fields.items():
                tr = table.tr
                tr.th(scope='row').append(str(k))
                tr.td.append(str(v))
        else:
            for k,v in fields.items():
                this_path = Path + (k,)
                assert '::' not in str(Path)
                this_path_str = '::'.join((str(i) for i in this_path))

                tr = table.tr
                tr.th(scope='row').label(_for=this_path_str).append(str(k))
                if '\n' in str(v):
                    tr.td.textarea(id=str(k), name=this_path_str, cols=75,
                                   rows=min(25, len(str(v).split('\n'))+2).append(str(v))                                   
                                   )
                else:
                    tr.td.input(type="text", id=str(k), name=this_path_str, value=str(v))
        in_progress[Path] = table

    if not _app_registered:
        app.route('/form_data', methods = ['POST', 'GET'])(event_handler)
        _app_registered.append(app)
    return form
if __name__=='__main__':
    print(mk_form(d))
