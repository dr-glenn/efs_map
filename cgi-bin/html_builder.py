#!/usr/bin/python

__author__="$Author: glenn.d.nelson $"
__date__ ="$LastChangedDate: 2015-09-30 12:39:44 -0700 (Wed, 30 Sep 2015) $"
__version__="$Rev: 39059 $"

# NOTE! Most of this functionality is no longer used (June 2016).
#       Instead of using class HTML to generate pages, we now use jinja2 with template pages.
#       The HTML class methods (designated with 'classmethod') are still used for some common page features.

# Class that generates full HTML pages
import cgi
import Cookie   # not sure I need this import
import efsm_config as config
import logging
logger = logging.getLogger('html_builder')

class HTML:
    # You will insert additional HEAD code in front of this
    headInsertStr = '<!-- HEADINSERT -->'
    # You will insert additional BODY code in front of this
    bodyInsertStr = '<!-- BODYINSERT -->'

    def __init__(self, theCookie, dodClass = "UNCLASSIFIED"):
        '''
        constructor: initializes class that builds head and body of HTML pages.
        Args:
        theCookie - HTTP cookie, can be generated from vv_util.getCookie.
          Used for preventing cached object collisions amongst users.
        dodClass - string that designates DoD classification, will appear at
          top and bottom of pages.
        '''
        self.cookie = theCookie
        self.dodClass = dodClass
        self.pageHTML = []  # will be array of string

        self.createHead()
        self.createBody()
        return

    def output(self):
        '''
        Returns string that represents the complete page, starting and ending with <HTML> tags.
        '''
        # DoD Classification bar must be last thing on page
        self.insertToBody('<div align="center" style="position:relative;clear:both;font-size:10pt;color:white;background-color:green; margin-top:20px" class="scc-unclass">'
                    + self.dodClass + '</div>', before=False)
        allHTML = []
        allHTML.extend( self.pageHTML )
        outStr = '\n'.join( allHTML )
        return outStr

    def createHead(self):
        self.pageHTML.append('Content-type: text/html; charset="UTF-8"')
        if self.cookie:
            self.pageHTML.append(self.cookie.output())
            logger.debug(self.cookie.output())
        self.pageHTML.append('\n')
        # Need DOCTYPE in order for IE8 to properly use CSS positioning
        self.pageHTML.append('<!DOCTYPE html>')
        self.pageHTML.append('<html LANG="en">')
        self.pageHTML.append('<head>')
        self.pageHTML.append('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />')
        # You will insert additional HEAD code in front of this
        self.pageHTML.append(HTML.headInsertStr)
        self.pageHTML.append('</head>')
        return

    def createBody(self):
        # TODO: need better way to add events to body
        #self.pageHTML.append('<body onmousemove="capmouse(event)">')
        self.pageHTML.append('<body>')

        self.pageHTML.append('<div align="center" style="font-size:10pt;color:white;background-color:green;" class="scc-unclass">'
                    + self.dodClass + '</div>')
        # You will insert additional BODY code in front of this
        self.pageHTML.append(HTML.bodyInsertStr)
        self.pageHTML.append('</body>')
        self.pageHTML.append('</html>')
        return

    @classmethod
    def createClassificationBar(cls, classification='UNCLASSIFIED'):
        '''
        Green bar for unclassified. Red bar for classified?
        :param classification:
        :return:
        '''
        class_color = 'green'
        class_class = 'scc-unclass'
        if classification != 'UNCLASSIFIED':
            class_color = 'red'
            class_class = 'scc-class'
        #html = '<div align="center" style="font-size:10pt;color:white;background-color:%s;" class="%s">'+classification+'</div>' %(class_color, class_class)
        html = '<div align="center" style="font-size:10pt;color:white;background-color:{1};" class="{2}">{0}</div>'.format(classification, class_color, class_class)
        return html

    @classmethod
    def createTitleBar(cls, pageTitle):
        '''
        Create the title bar with black background.
        We have two pages: map index and verification graph page.
        :param pageTitle: descriptive title
        :param dateStr: map index shows date of most current XML, graph page has link back to map index.
        :return:
        '''
        # FNMOC Portal Title Bar
        html = []
        html.append('<p>')
        html.append('<noscript>You must enable javascript in your browser</noscript>')
        html.append('<table class="tn_title" width="100%"><tr>')
        html.append('<th><big>'+pageTitle+'</big></th>')
        # target="new" will write to a tab/window labeled "new". If it does not exist, it is created.
        # If it does exist, it is overwritten with new contents.
        html.append('<td><a href="'+config.wxmapRootURL+'" target="new" class="title">WxMap Home</a></td>')
        html.append('<td><a href="/efs_verif/cgi-bin/vv_index.py/" target="new" class="title">Ensemble Model Verification</a></td>')
        html.append('</tr></table>')
        html.append('</p>')
        return '\n'.join(html)

    # Insert block of HTML code in the HEAD
    def insertToHead(self, codeBlock, before=True):
        magicStr = ''
        if before==True: magicStr = HTML.headInsertStr
        else: magicStr = '</head>'
        try:
            # Find the magic string that tells us where to put codeBlock
            idx = self.pageHTML.index( magicStr )
            self.pageHTML.insert( idx, codeBlock )
        except:
            HTML.logger.error('could not insert to HEAD')
        return

    # Insert block of HTML code in the BODY
    def insertToBody(self, codeBlock, before=True):
        magicStr = ''
        if before==True: magicStr = HTML.bodyInsertStr
        else: magicStr = '</body>'
        try:
            # Find the magic string that tells us where to put codeBlock
            idx = self.pageHTML.index( magicStr )
            self.pageHTML.insert( idx, codeBlock )
        except:
            HTML.logger.error('could not insert to BODY')
        return

#..................START EPILOGUE......................................
#
# CONFIGURATION IDENTIFICATION:  @(#)$Id: html_builder.py 39059 2015-09-30 19:39:44Z glenn.d.nelson $
#
# NAME:                          html_builder.py
#
# AUTHOR:                        Glenn Nelson / CSC
#
# DESCRIPTION:                   Used to generate full HTML pages and return string of the page
#
# CONTRACT NUMBER AND TITLE:     n/a
#
# REFERENCES:                    none
#
# CLASSIFICATION:                unclassified
#
# RESTRICTIONS:                  Tested in IE7,9, Firefox 3.5,4,5
#
# FPATH:                         none
#
# USAGE:                         none (file is used by other Python)
#
#...................END EPILOGUE........................................
