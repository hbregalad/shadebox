class html:
    def __init__(self, identity='html', args=):
        self.identity = identity
        self.args = {}
        self.children = []
    def __call__(self, **kargs={}):
        self.args.update(kargs)
    def __getattr__(self, name):
        self.children.append(html('name'))
    def __str__(self):
        def format_args():
            return ''.join(('{}={} '.format(k,v) for k, v in self.args.items()))

        def format_children():
            return ''.join(('{}'.format(v) for v in self.children()))

        if self.children:
            return '<%s %s />%s<%s>' %
                (identity, format_args(), format_children(),identity)
        else:
            return '<%s %s />' %
                (identity, format_args())
