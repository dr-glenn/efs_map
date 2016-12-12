#!/usr/bin/python

# construct main page for efs_map application

import os
import os.path
from jinja2 import Template,FileSystemLoader,Environment
import efsm_config as config
import tau_buttons
import loop_control
import html_builder
import logging
logger = logging.getLogger('efsm_view')

# Sample file: ENSEMBLE:2016012500:global_360x181:wnd_spd:isbr_lvl:08500000:00000000:fcst_et001:0000

def createPlayToolbar2(loopControl):
    '''
    Creates button bar for video player controls (stop/pause/play/forward, etc.).
    This code just creates HTML BUTTON objects.
    createPlayToolJS uses javascript jquery-ui to make these BUTTONs
    appear as video player buttons.
    '''
    s = []
    s.append('<div>')
    if loopControl is not None:
        s.append(loopControl.buildHtmlBody())
    s.append('</div>')
    return '\n'.join(s)

def createPianoSelector2(tauButtons, loopControl):
    html = []
    html.append('<div id="leadSelectGroup">')
    if tauButtons is not None:
        html.append( tauButtons.buildHtmlBody() )
    html.append('</div>')
    # 'video player' button bar
    html.append(createPlayToolbar2(loopControl))
    return '\n'.join(html)

# Put this line into ready?
#      document.getElementById("map_img").addEventListener("onclick",function (){mapclick();},false);

def getValidDTG(grid_dir = '/isis/ops/grid/ENSEMBLE'):
    dtgs = []
    # read directory
    files = os.listdir(grid_dir)
    dirs = [f for f in files if os.path.isdir(grid_dir+'/'+f)]
    # keep only names that begin with '20' and are 10 chars long
    dtgs = [d for d in dirs if d.startswith('20') and len(d) == 10]
    return sorted(dtgs,reverse=True)

# When used a web URL, it enters with "__main__", same as command line entry
if __name__ == '__main__':
    import cgi
    if config.localhost:
        import cgitb    # only for debugging
        cgitb.enable()

    cgiform = cgi.FieldStorage()
    if os.path.exists('/isis/ops/grid/ENSEMBLE'):
        grid_root = '/isis/ops/grid/ENSEMBLE'
    else:
        grid_root = config.wwwRoot+config.appRoot+'/data'

    # setup jinja2 template objects
    loader = FileSystemLoader(config.wwwRoot+config.appRoot+'/templates')
    logger.debug('template loader: %s' %(config.wwwRoot+config.appRoot+'/templates'))
    env = Environment(loader=loader)

    # this is the template for the main web page.
    # later we will create HTML pieces that get inserted into the template.
    page_templ = env.get_template('main_view.html')
    page_templ_args = {}

    page_templ_args['fnmoc_css'] = ""
    dtgs = getValidDTG(grid_root)   # list of DTG available in ISIS for the model (ENSEMBLE)
    page_templ_args['dtgs'] = dtgs
    page_templ_args['taus'] = config.taus

    # Python objects representing a tau button bar and player controls (stop/run/forward/back)
    tauButtons = tau_buttons.TauButtons(config.taus, [], "main_graph")
    loopControl = loop_control.LoopControl()
    page_templ_args['tau_buttons_head'] = tauButtons.buildHtmlHead()    # generate javascript
    page_templ_args['loop_control_head'] = loopControl.buildHtmlHead()  # generate javascript
#    page_templ_args['tau_buttons_head'] = ""   # generate javascript
#    page_templ_args['loop_control_head'] = ""  # generate javascript

    # piano_keys is HTML to insert into main page. These are lean and functional FNMOC style buttons
    piano_keys = createPianoSelector2(tauButtons, loopControl)
    page_templ_args['piano_keys'] = piano_keys
#    page_templ_args['piano_keys'] = ""

    # A separate piece of the main page is a form for generating plume plots
    plume_templ = env.get_template('plume_form.html')
    plume_form = plume_templ.render()   # plume_form is a string of HTML that gets inserted into main page
    page_templ_args['plume_form'] = plume_form

    # build entire page and send to client (web browser)
    #cookie = None

    # FNMOC Portal Title Bar
    title_bar = html_builder.HTML.createTitleBar('Ensemble Spaghetti and Plume Plots')
    page_templ_args['title_bar'] = title_bar
    page_templ_args['classification_bar'] = html_builder.HTML.createClassificationBar('UNCLASSIFIED')

    # finally the HTML page is created with all the pieces of page_templ_args inserted
    page_body = page_templ.render(page_templ_args)

    '''
    logger.debug('PAGE START')
    logger.debug(page_body)
    logger.debug('PAGE END')
    '''

    print "Content-type: text/html\n"
    # print cookie here if we decide to use it
    print page_body


#..................START EPILOGUE......................................
#
# CONFIGURATION IDENTIFICATION:  @(#)$Id$
#
# NAME:                          efsm_view.py
#
# AUTHOR:                        Glenn Nelson / Forward Slope
#
# DESCRIPTION:                   main page for efs_map application
#
# CONTRACT NUMBER AND TITLE:     n/a
#
# REFERENCES:                    none
#
# CLASSIFICATION:                unclassified
#
# RESTRICTIONS:                  Python 2.6+
#
# FPATH:                         none
#
# USAGE:                         none (file is imported by other Python)
#
#...................END EPILOGUE........................................

