
#set this to True to minimize whitespace and enable other bandwidth control techniques.
MINIFY = True

if MINIFY:
    #saves about 40% data.
    HTML_START_INDENT=''
    HTML_INDENT=''
    MOTOR_START_PATH='m'
else:
    #serves beautified html.
    HTML_START_INDENT = '\n'
    HTML_INDENT='  '
    MOTOR_START_PATH='start'

class html:
    """Simple class for building html templates from code with minimal boilerplating."""
    def __init__(self, identity='html', indent=HTML_START_INDENT):
        self.identity = identity
        self.args = {}
        self.children = []
        self.indent = indent
    def __call__(self, **kargs):
        #print('%s.call(%r)' % (self.identity, kargs))
        self.args.update(kargs)
        return self
    def __getattr__(self, name):
        #print('getattr(%r})'% name)
        ret = html(name, indent=self.indent+HTML_INDENT)
        self.children.append(ret)
        return ret
    def __str__(self):
        prefix = ('<!doctype html>'+HTML_START_INDENT) if self.identity == 'html' else ''

        def format_args():
            ret=' '.join(('{}={}'.format(k,repr(v)) for k, v in self.args.items()))
            return ' '+ret if ret else ''

        def format_children(indent):
            return indent+indent.join(('{}'.format(v) for v in self.children))

        if self.children:
            return '%s<%s%s>%s%s</%s>' % (
                prefix, self.identity, format_args(), format_children(self.indent+HTML_INDENT), self.indent, self.identity
                )
        else:
            return '%s<%s %s />' % (
                prefix, self.identity, format_args()
                )
    def append(self, child):
        self.children.append(child)
        return self

CSS= """
    body {
        background-color: black;
        color: White;
        height: 100%;
    }

    a {
        color: blue;
        padding: 5px;
    }

    a.mode {
        color: green;
        background-color: darkblue;
    }

    table {
        width: 100%;
        height: 100%;
    }

    tr {
        height: 20%;
    }
    tr:nth-child(odd) {
        background-color: #030;
    }

    td {
        width: 12.5%;
        text-align: center;
        height: 20%;
    }

    th {
        background-color: #334;
        height: 20%;
    }"""
ROBOT = "User-agent: *\nAllow: /\nDisallow: /{}/".format(MOTOR_START_PATH)

#prerender these static header tags...
if MINIFY:
    #When the time comes to leave debug mode remove extrainious whitespace.
    CSS=' '.join(CSS.split())#shrink data
    #serve as seperate .css file so that the browser can cache it.
    STYLE = str(html('link')(rel='stylesheet', type='text/css', href='/shadebox.css'))
else:
    STYLE = str(html('style', HTML_START_INDENT+HTML_INDENT+HTML_INDENT).append(CSS))+str()

KEYWORDS = str(html('meta')(name="Keywords", content='motorized,shade,control,automation,RPi.GPIO'))

if __name__ == '__main__':
    """Demo"""
    doc = html()
    print (doc)
    doc.head.title.append('Hello World')
    print (doc)
    doc.body.h1.append('Hello World')
    print (doc)
