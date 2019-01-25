from contextlib import contextmanager
from flexx.pyscript import py2js
import inspect
import re
import os

global_html = ''

def helper_linux_name(fn): return f'/{fn}'.replace('\\', '/').replace(':', '').replace('//', '/')

def content(txt):global global_html; global_html += txt

def css_content(txt):global global_css; global_css += txt

def html_pretify(h):
    from lxml import etree
    parser = etree.XMLParser(remove_blank_text=True)
    xml = etree.fromstring(h, parser=parser)
    return etree.tostring(xml, encoding='unicode', pretty_print=True, method='xml')

def parse_args(**kwargs):
    html_args = " ".join(["=".join([k, '"'+v+'"']) for k, v in kwargs.items()])
    html_args = html_args.replace('css_class', 'class').replace("__","-").replace("for_", "for").replace('class_', 'class').replace('if_', 'if')
    if len(html_args) > 0: html_args = ' '+ html_args 
    return html_args

class Rtag(object):
    def __init__(self, tagname, content='', **kwargs):
        self.tag = tagname
        self.kwargs = kwargs
        self.content = content
    
    def __enter__(self):
        global global_html   
        global_html += '<%s%s>%s'%(self.tag, parse_args(**self.kwargs), self.content)
    
    def __call__(self):
        global global_html
        global_html += '<%s%s>%s'%(self.tag, parse_args(**self.kwargs), self.content) + '</%s>'%(self.tag)
        
    def __exit__(self, type, value, traceback):
        global global_html   
        global_html += '</%s>'%(self.tag)

#template for generating all HTML tags...
html_tags_template1 = '''class __tagname__(object):
    def __init__(self, content='', **kwargs):
        self.tag = self.__class__.__name__
        self.kwargs = kwargs
        self.content = content

    def __enter__(self):
        global global_html   
        global_html += '<%s%s>%s'%(self.tag, parse_args(**self.kwargs), self.content)
    
    def __call__(self):
        global global_html
        global_html += '<%s%s>%s'%(self.tag, parse_args(**self.kwargs), self.content) + '</%s>'%(self.tag)
        
    def __exit__(self, type, value, traceback):
        global global_html   
        global_html += '</%s>'%(self.tag)
'''
        
html_tags = 'A ABBR ACRONYM ADDRESS APPLET AREA BASE BASEFONT BIG BLINK BLOCKQUOTE BODY BR CANVAS B BUTTON CAPTION CENTER CITE CODE COL DFN DIR DIV DL DT DD EM FONT FORM H1 H2 H3 H4 H5 H6 HEAD HR HTML IMG INPUT ISINDEX I KBD LINK LI MAP MARQUEE MENU META OL OPTION PARAM PRE P Q SAMP SCRIPT SELECT SMALL SPAN Strikeout STRONG STYLE SUB SUP TABLE TD TEXTAREA TH TBODY THEAD TFOOT LABEL TITLE TR TT UL U VAR NAV'
html_tags = html_tags.split(' ') + html_tags.lower().split(' ')
for t in html_tags:
    exec(html_tags_template1.replace('__tagname__',t))


materialize_tags_template = '''
class __tagname__(object):
    def __init__(self, css_class='', **kwargs):
        self.materialize_class = self.__class__.__name__
        self.kwargs = kwargs
        self.css_class = self.__class__.__name__ + " " +css_class

    def __enter__(self):
        global global_html   
        global_html += '<div class="%s" %s>'%(self.css_class, parse_args(**self.kwargs))
    
        
    def __exit__(self, type, value, traceback):
        global global_html   
        global_html += '</div>'
'''
materialize_tags = 'row col collection container progress'.split(' ')
for t in materialize_tags:
    exec(materialize_tags_template.replace('__tagname__',t))

def css(item, **kwargs):
    assert len(item) > 0, 'Assertion error: you must provide css item (element, class, id)' 
    assert len(kwargs.items()) > 0, 'Assertion error: you must provide css definitions' 
    global global_css; 
    if len(global_css)>0: global_css += '\n'
    cssdef = " ".join(['%s:%s;'%(k.replace("_", '-'),v) for k,v in kwargs.items()])
    global_css += "%s {%s}"%(item, cssdef)

def add_unique_decorators(py):
    #replace the decorators with relevant code to transform into javascript, referring to self...
    pattern = re.findall('@make_self\ndef (.+)\(', py)
    if len(pattern)>0:
        py = py.replace("@make_self\n", "") #remove the original decorator
        for ref in pattern:
            py += "\nself.%s = %s"%(ref, ref) #add ref to the decorator in the beginning.

    pattern = re.findall('@on\("(.+)"\)\s+def (.+)\(', py)
    if len(pattern)>0:
        for event_name, func_name in pattern:
            py = py.replace('@on("%s")\n'%(event_name), '')
            py += "\nself.on('%s', %s)"%(event_name, func_name)

    pattern = re.findall("@on\('(.+)'\)\s+def (.+)\(", py)
    if len(pattern)>0:
        for event_name, func_name in pattern:
            py = py.replace("@on('%s')\n"%(event_name), '')
            py += "\nself.on('%s', %s)"%(event_name, func_name)
    
    #these post and get pattens are not right yet - you need to put the jquery call after the function and not at the end!.
    pattern = re.findall('@get\("(.+)"\)\ndef (.+)\(', py)
    if len(pattern)>0:
        for url_name, func_name in pattern:
            py = py.replace('@get("%s")\n'%(url_name), "\njQuery.get('%s', %s)"%(url_name, func_name))

    pattern = re.findall('@get_json\("(.+)"\)\ndef (.+)\(', py)
    if len(pattern)>0:
        for url_name, func_name in pattern:
            py = py.replace('@get_json("%s")\n'%(url_name), "\njQuery.getJSON('%s', %s)"%(url_name, func_name))
    
    pattern = re.findall('@post\("(.+), (.+)"\)\ndef (.+)\(', py)
    if len(pattern)>0:
        for url_name, json_data, func_name in pattern:
            py = py.replace('@post("%s", "%s")\n'%(url_name, json_data), "\njQuery.post('%s', %s, %s)"%(url_name, json_data, func_name))

    pattern = re.findall('@post_json\("(.+), (.+)"\)\ndef (.+)\(', py)
    if len(pattern)>0:
        for url_name, json_data, func_name in pattern:
            py = py.replace('@post_json("%s", "%s")\n'%(url_name, json_data), "\njQuery.post('%s', %s, %s, 'json')"%(url_name, json_data, func_name))

    return py
    
class RiotTag(object):
    def __init__(self, content='', **kwargs):
        global global_html, global_css
        prev_global_html = global_html
        global_html = ''; global_css=''
        self.HTML(); self.CSS()
        self.html = global_html; self.css = global_css
        
        #restore global html...
        global_html = prev_global_html

        self.tag_name = self.__class__.__name__
        self.kwargs = kwargs
        self.content = content

        name = self.__class__.__name__
        py = inspect.getsourcelines(self.JS)[0][1:]
        first_ident = len(py[0])-len(py[0].lstrip())
        py = "".join([j[first_ident:] for j in py])
        py = "me = self\n"+py #adding the idea of the "me" to refer to all selfs
        
        py = add_unique_decorators(py)

        js = py2js(py)
        js = '    '+js.replace("\n", '\n    ')
        self.tag = "\n<%s>\n%s\n\n<style>\n%s\n</style>\n\n%s\n\n</%s>"%(name, self.html, self.css, js, name)
        
    #placeholders to take the input from the user.
    def HTML(self):
        pass
    
    def CSS(self):
        pass
        
    def JS(self):
        pass
    
    #replicate general activity of the html tag...
    def __enter__(self):
        global global_html   
        global_html += '<%s%s>%s'%(self.tag_name, parse_args(**self.kwargs), self.content)
    
    def __call__(self):
        global global_html
        global_html += '<%s%s>%s'%(self.tag_name, parse_args(**self.kwargs), self.content) + '</%s>'%(self.tag_name)
        
    def __exit__(self, type, value, traceback):
        global global_html   
        global_html += '</%s>'%(self.tag_name)

def get_tag_name_form_html(tag_html):
    return tag_html.split(">")[0][2:]

def generate_index_html(toptitle='', include_css=[],  include_js=[], tags = [], mount=[], body_style=''):
    global global_html
    global_html = ''
    tags_names = [get_tag_name_form_html(t) for t in tags]
    with html():
        with head():
            title(toptitle)()
            for css_file in include_css: 
                if not css_file.endswith(".ico"):
                    link(href=css_file, rel="stylesheet")()
                else:
                    link(href=css_file, rel="ico")()
            
        with body(style=body_style):
            for js_file in include_js: script(src=js_file)()
            for t in mount: 
                Rtag(t)()
            if len(tags) > 0:
                content("\n\n\n")
                for tag in tags:
                    with script(type="riot/tag"): content(tag)

            with script():
                for t in mount:
                    mountTag(t)
            
    return global_html

def mountTag(tag):
    global global_html
    func =  "var tag_%s = riot.mount('%s');"%(tag, tag)
    global_html += func

#===================================================
#===================================================
#===================================================
class RiotPyApp(object):
    
    #-----------------
    def __init__(self,
                 tags=[],
                 mount=['maintag'],
                 routes=[],
                 blueprints=[],
                 css_includes=["css/materialicons.css", "css/materialize.min.css", "favicon.ico"],
                 js_includes=["js/jquery-3.2.1.min.js", "js/materialize.min.js"],
                               body_style='',
                               toptitle=''):
        
        
        if tags == []:
            #fetch all imported tags if not specifically asked...
            tags = globals()['RiotTag'].__subclasses__()

        js_includes = js_includes + ["js/riot+compiler.js", "js/route.min.js"]
        self.tags = [t().tag for t in tags]
        self.index = generate_index_html(include_css=css_includes, 
                                         include_js=js_includes, 
                                         tags=self.tags,
                                         mount = mount,
                                         body_style=body_style,
                                         toptitle=toptitle)

        self.generate_flask(include_css=css_includes, include_js=js_includes, blueprints=blueprints)
    

    def generate_sec_key(self):
        try:
            with open('cache/.sk', 'r') as f:
                return f.read()
        except:
            import string, random
            secret_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            with open('cache/.sk', 'w') as f:
                f.write(secret_key)
            return secret_key
                

    #-----------------

    def generate_flask(self, include_css=[],  include_js=[], blueprints=[]):
        from flask import Flask, send_file
        self.app = Flask(__name__)
        self.app.secret_key = self.generate_sec_key()
        
        @self.app.route('/')
        def get_index():
            return self.index

        @self.app.route('/<path:path>')
        def get_resource(path):
            if ( path in include_css + include_js):
                return send_file(path, as_attachment=True)
            if path[-3:].lower() in ['svg', 'jpg', 'png', 'ico', 'gif', 'off', 'ff2', 'tif', 'iff']:
                if os.path.isfile(path):
                    return send_file(path, as_attachment=True)
                elif os.path.islink(path):
                        path = os.readlink(path)
                        return send_file(path, as_attachment=True)
                else:
                    fn = helper_linux_name(path)
                    if os.path.isfile(fn):
                        return send_file(fn, as_attachment=True)
                    else:
                        return ''
                    
        for bp in blueprints:
            self.app.register_blueprint(bp)
            
                    
    



