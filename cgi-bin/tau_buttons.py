#!/usr/bin/python

__author__="$Author: glenn.d.nelson $"
__date__ ="$LastChangedDate: 2014-12-29 09:55:17 -0800 (Mon, 29 Dec 2014) $"
__version__="$Rev: 36397 $"

from string import Template

'''
Notes:
Need a javascript class for TauButtons. Will hold list of tau values, ordered list
of tau buttons, current value, handle to LoopControl. It will also have mouseover,
mouseout and click handlers.
'''
'''
This file defines a python class 'TauButtons' that builds Javascript, CSS and HTML
for a tau button bar. Placing mouse over a button will display the tau value in a
text box and will also fill a DIV with an image. Typically this kind of button bar
appears in FNMOC WxMap pages and is used to display forecast maps at different tau.
'''

class TauButtons:
    '''
    Builds a button bar for tau (a.k.a. lead-time) values. Moving the mouse over
    a tau button changes the appearance, updates a text box that displays the tau value,
    and updates an image in a DIV, typically a forecast map.

    USAGE: see function 'testCode' in this file for example.
    - create instance of TauButtons as explained in 'init' method.
      tb = TauButtons( [0, 12, 24, 36, 48], [list of image files], "map_img_id" )
    - call 'tb.buildHtmlHead(). Returns a string that you will insert into the HEAD
      of the web page.
    - call 'tb.buildHtmlBody(). Returns a string that you will insert into the BODY
      of the web page. Put into BODY at the position where you want the button bar to display.
    '''
    def __init__(self, values, images, img_target=None):
        '''
        values: list of tau values, e.g., [0,12,24,36,...]
        images: list of images as file pathnames. If None, you must set it later.
        img_target: ID of the HTML IMG tag where images will be displayed.
        '''

        # test for values as strings or integers - we prefer 3 digit strings
        if isinstance(values[0], basestring):
            self.tauValues = values
        else:
            # convert tauValues to 3 digit strings
            self.tauValues = ['%03d'%t for t in values]
        self.images     = images
        self.img_target = img_target
        self.loop_control = None
        return

    def buildHtmlHead(self):
        '''
        Creates javascript and CSS that should be included in html head.
        Returns a single string.
        NOTE: FNMOC Perl implementation of tau_buttons has different button sizes:
           Perl code is "width: 10px; height: 12px"; I make these buttons and tau_label
           a little bit larger.
        '''
        # GDN - TODO - path to CSS and JS should be defined in config file. It is expected to be in common dir.
        html = []
        html.append('<link href="/efs_verif/css/tau_buttons.css" rel="stylesheet" type="text/css"/>')
        html.append('<script src="/efs_verif/js/tau_buttons.js"></script>')
        return '\n'.join(html)

    def buildHtmlBody( self ):
        '''
        Builds FNMOC "piano key" style button bar, similar to the Perl version.
        Builds HTML for tau button bar with text display of current value to the left of buttons.
        Returns a string.
        The entire object is a TABLE.

        Note: buttons are built as 'input' inside of 'div' inside of 'a' (anchor).
        TODO - might want to try using 'input' inside of 'span'.
        '''
        html = []
        html.append('<script type="text/javascript">')
        html.append('tauButtons = TauButtonsJS;')
        html.append('tauButtons.init('+str(self.tauValues)+','+str(self.images)+');')
        if self.img_target is not None:
            html.append('tauButtons.setImgHolder("'+self.img_target+'")')

        html.append('</script>')

        # store the ID of the most recently selected tau button
        html.append('<input type="hidden" id="tau_button_current_id" name="tau_button_current_id" value="0">')
        html.append("<table cellspacing='0px' cellpadding='0px'>")
        html.append("<tr>")
        # First put the text box that shows the currently selected tau value
        valueStr = self.tauValues[0]
        html.append("<td align='center'><input type='text' class='tau_button_label' id='tau_label' value='"+valueStr+"'></td>")

        # Now put buttons (piano key style) for each tau value. Each button in a 'TD'.
        # here is template for a single button. TODO - the name 'tauButtons' should be a variable.
        buttonStr = '''
        <td>
        <a style="font-style: normal; text-decoration: none;" href="javascript:void 0"
            onMouseOver="tauButtons.mouseover(this)"
            onMouseOut="tauButtons.mouseout(this)" >
            <div id="div_tau_button_$index" class="tau_button_up_holder" value="$tau">
                <input type="hidden" value="$index">
            </div>
        </a>
        </td>
        '''
        buttonTemplate = Template(buttonStr)    # we will substitute values of 'index and 'tau'
        # write HTML for each button:
        for index,tau in enumerate(self.tauValues):
            outStr = buttonTemplate.safe_substitute(index=index,tau=tau)
            html.append( outStr )
        html.append("</tr></table>")
        return '\n'.join(html)

######################### Test Code ######################################################
def testCode():
    '''
    This is the main function for test code.
    If you run from command line "python looper.py", you will get the HTML
    output in the console; but you may need to delete the line for os.environ before running.
    If you call this file with a browser, "http://localhost/looper.py", you will get
    a test display page.
    For web test, this script assumes you are running in a cgi-bin directory in Apache,
    and also assumes there is a 'images' directory that is a sibling of cgi-bin.
    The test creates a number of PNG image files in the 'images' directory.
    '''
    import os
    # matplotlib creates a directory. If running in Apache, you need to set HOME as here ...
    os.environ[ 'HOME' ] = '/tmp/'
    import matplotlib
    matplotlib.use( 'Agg' )  # choose a non-GUI backend
    import matplotlib.pylab as plt
    import matplotlib.font_manager as font_mgr

    taus = [0,12,24,36,48,72,96,120,144]
    files = []
    # create PNG images of each of the taus
    for tau in taus:
        tauStr = '%03d' %tau
        filename = config.appRoot+'/images/'+tauStr+'.png'
        if not os.path.exists(filename):
            fig = plt.figure( figsize=(2.0,0.5) )
            plt.figtext(0.5, 0.5, tauStr, style='italic',
                        size='xx-large',
                        verticalalignment='bottom', horizontalalignment='center',
                        bbox={'facecolor':'lightgrey', 'pad':5})

            plt.savefig( filename, format='png', dpi=100 )
        files.append( filename )

    allHTML = htmlTestPageOut(taus, files)  # generates HTML for entire page
    print allHTML   # send HTML to console or browser
    return

def htmlTestPageOut( tauValues, images ):
    '''
    Builds HTML for test page
    '''
    main_img_id = "tau_img"
    tauButtons = TauButtons(tauValues, images, main_img_id)
    html = []
    html.append('Content-type: text/html; charset="UTF-8"')
    html.append('\n')
    # Need DOCTYPE in order for IE8 to properly use CSS positioning
    html.append('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">')
    html.append('<html LANG="en">')
    html.append('<head>')
    html.append(tauButtons.buildHtmlHead())
    html.append('''
        <script type="text/javascript">
        // GDN - this is just test code, you don't need to implement these functions
        function tauUnSelectEx(button) {
            var outText = document.getElementById("out_text");
            outText.innerHTML = 'out='+button.id;
        }
        function tauSelectEx(button, tauVal) {
            var overText = document.getElementById("over_text");
            overText.innerHTML = 'over='+button.id;
        }
        </script>
        '''
        )
    html.append('</head>')

    html.append('<body>')
    html.append('<h1>Tau Button Test</h1>')
    html.append( tauButtons.buildHtmlBody() )
    html.append('<div class="inline" id="img_div">')
    html.append('<img id="'+main_img_id+'" src="#"/>')
    html.append('</div>')
    html.append('<div class="inline" style="margin:10px" id="over_text">over</div>')
    html.append('<div class="inline" style="margin:10px" id="out_text">out</div>')
    html.append('</body>')
    html.append('</html>')
    return '\n'.join(html)

##########################################################################################
# Start of main

'''
This file is normally imported by others, so main is not run.
You can run this file standalone from the Python interpreter, and then this "main"
clause is executed. Use it for debugging - see logger files for debug output.
Failures will typically result from a package import problem - perhaps the wrong version.
Such failures will not appear in webserver logs - how unfortunate!
'''
if __name__ == '__main__':
    testCode()

#..................START EPILOGUE......................................
#
# CONFIGURATION IDENTIFICATION:  @(#)$Id: tau_buttons.py 36397 2014-12-29 17:55:17Z glenn.d.nelson $
#
# NAME:                          tau_buttons.py
#
# AUTHOR:                        Glenn Nelson / CSC
#
# DESCRIPTION:                   Creates a button bar for displaying images at
#                                different tau values. It recreates the look and feel
#                                of tau_buttons.js and animator.pl
#
# CONTRACT NUMBER AND TITLE:     n/a
#
# REFERENCES:                    none
#
# CLASSIFICATION:                unclassified
#
# RESTRICTIONS:                  Tested in IE7,9, Firefox 10, Chrome
#
# FPATH:                         none
#
# USAGE:                         none (file is called from other Python scripts)
#
#...................END EPILOGUE........................................
