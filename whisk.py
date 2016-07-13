# This code depends on the command line tool multimarkdown.

from __future__ import unicode_literals
import os, sys, jinja2, subprocess, re, time
from codecs import open
from xml.etree import ElementTree
from textwrap import dedent

MARKDOWN_EXT = '.markdown'
OUTPUT_EXT   = '.html'
TEMPLATE_EXT = '.template'
ROOT_DIR     = '.'
TEMPLATE_DIR = '.'
INDEX_NAME   = 'index'

class Whisk:
    def __init__(self):
        print('Preparing to make whisk...')
        start_time = time.time()

        # Load all markdown files.
        mdbundle = FileLoader(MARKDOWN_EXT, ROOT_DIR, MarkdownFile)

        # Load the templates.
        templates = set(f.metadata['template'] for f in mdbundle.files)
        tt = Templater(TEMPLATE_DIR)
        tt.load_templates(templates)

        # Render each markdown file according to its template & write to file.
        for mdfile in mdbundle.files:
            tt.render_and_write(mdfile)

        # Success message.
        print('Rendered %i markdown files in %f seconds.' \
            % (len(mdbundle.files), time.time() - start_time) )

class File(object):
    # Generic file class.
    def __init__(self, fullpath):
        self.fullpath = fullpath
        self.path, self.name = os.path.split(fullpath)
        self.slug, _         = os.path.splitext(self.name)
        self.id,   self.ext  = os.path.splitext(fullpath)
        self.metadata = {}

    def add_metadata(self, newdict):
        self.metadata.update(newdict)

    def add_data(self, newdict):
        self.__dict__.update(newdict)

    def get_data(self):
        return self.__dict__


class MarkdownFile(File):
    # Markdown file class. Initialization converts the file to HTML.
    def __init__(self, fullpath):
        super(MarkdownFile, self).__init__(fullpath)
        self.url = self.id + OUTPUT_EXT

        # Default metadata.
        self.metadata.update({
            'title': None,
            'author': None,
            'date': None,
            'tags': None,           # tags don't do anything yet.
            'template': 'note'
        })

        # Create the converted HTML. The `-s` forces snippet mode.
        self.html = multimarkdown(fullpath, '-s')

        # And this is the meta content.
        metafields = multimarkdown(fullpath, '-m').split("\n")
        for field in metafields:
            value = multimarkdown(fullpath, '-e %s' % field)
            self.metadata[field] = value


class FileLoader:
    # Loads all files of a certain filetype. This class will become useful
    # when I want to do more processing on the markdown files: collecting and
    # sorting by tags, passing data to templates, etc.
    def __init__(self, file_extension, search_directory, FileClass=File):
        # Traverse the search_directory and load in
        # each .markdown file as a MarkdownFile object.
        self.files = []
        for root, dirs, files in os.walk(search_directory):
            for file in files:
                if file.endswith(file_extension):
                    fullpath = os.path.join(root, file)
                    self.files.append( FileClass(fullpath) )

        # This isn't _too_ hacky.
        self.add_notes_data()

    def add_notes_data(self):
        # Slightly hacky, though. What's a better way?
        noteslist = [f for f in self.files if f.metadata['template'] == 'note']
        noteslist = sort_alphanum(noteslist, lambda f: f.slug, reverse=True)
        for file in self.files:
            if file.slug == INDEX_NAME:
                file.add_data({'notes' : noteslist})


class Templater:
    # Class for loading and rendering templates.
    def __init__(self, directory):
        self.env = jinja2.Environment( \
            loader=jinja2.FileSystemLoader([directory]),
            lstrip_blocks=True,
            trim_blocks=True )
        self.env.filters['dedent'] = dedent
        self.env.filters['inline'] = inner_html
        self.env.filters['mmd']    = multimarkdown_from_str
        self.templates = {}

    def load_templates(self, lst):
        for t in lst:
            self.templates[t] = self.env.get_template(t + TEMPLATE_EXT)

    def render_and_write(self, mdfile):
        t = mdfile.metadata['template']
        html  = self.templates[t].render(mdfile.get_data())
        outfn = mdfile.id + OUTPUT_EXT
        with open(outfn, 'w+', encoding='utf_8_sig', errors='strict') as outf:
            outf.write(html)


def multimarkdown(fullpath, args=''):
    args = ("multimarkdown %s %s" % (args, fullpath)).split()
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    p.wait()
    output = p.stdout.read()
    return output.decode('utf_8').strip()

def multimarkdown_from_str(s):
    if not s:
        return ''

    s = '\n' + s

    # Pipe the string to multimarkdown:
    p1 = subprocess.Popen(("echo", s), stdout=subprocess.PIPE)
    p2 = subprocess.Popen(("multimarkdown", "-s"), \
            stdin=p1.stdout, stdout=subprocess.PIPE, shell=True)
    p1.stdout.close()
    output = p2.communicate()[0]
    return output.encode('utf_8').strip()

def inner_html(html):
    if not html:
        return ''

    # Strips the outer tag of a string of valid XML.
    tree = ElementTree.fromstring(html.decode('utf-8'))
    outhtml = tree.text + ''.join(ElementTree.tostring(e) for e in tree)
    return outhtml.encode('ascii', 'xmlcharrefreplace')

# A function for better (alphanum) sorting. Modified from
#     http://nedbatchelder.com/blog/200712/human_sorting.html#comments
def sort_alphanum(l, key, reverse=False):
    return sorted(l, reverse=reverse, key=lambda a: \
            zip( re.split("(\\d+)", key(a).lower())[0::2], \
                map(int, re.split("(\\d+)", key(a).lower())[1::2])) )


# Whisk away.
if __name__ == "__main__":
    w = Whisk()
