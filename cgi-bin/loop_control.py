#!/usr/bin/python

__author__="$Author: glenn.d.nelson $"
__date__ ="$LastChangedDate: 2014-02-11 09:19:34 -0800 (Tue, 11 Feb 2014) $"
__version__="$Rev: 34396 $"

from string import Template

'''
This code is used to build HTML for the HEAD and BODY to create a button bar for
control of image animation. The button bar looks and operates like a CD/DVD player.

A separate file of Javascript (loop_control.js) contains the functionality of this
button bar.

When using this Python code, you will want to set the corrsponding tau_button bar
that is controlled by loop_control.
'''

class LoopControl:
    def __init__(self):
        self.tauButtons = None
        return

    def buildDomClass(self):
        '''
        Defines a DOM class for LoopControls.
        '''
        # GDN - TODO - path to JS should be set in config. JS will ultimately be in common.
        html = []
        html.append('<script src="../js/loop_control.js"></script>')
        return '\n'.join(html)

    def buildHtmlHead(self):
        '''
        Returns a string that should be output to HEAD of the HTML page.
        '''
        html = '''
<style>
button.loop_controls {
    width: 28px;
    height: 24px;
}
</style>
<!-- GDN - disable FNMOC
<script src="/common/js/slider/carpe_common.js"></script>
<script src="/common/js/slider/carpe_slider.js"></script>
<link href="/common/css/carpe_slider.css" rel="stylesheet" type="text/css"/>
-->
<script src="../js/loop_control.js"></script>
<script type="text/javascript">
    var loopControls = LoopControlsJS;
    var loopButtons = ['first','prev','stop','play','next','last'];
    var loopImgs = ['/efs_verif/images/first.gif',
                    '/efs_verif/images/back1.gif',
                    '/efs_verif/images/stop.gif',
                    '/efs_verif/images/start.gif',
                    '/efs_verif/images/next1.gif',
                    '/efs_verif/images/last.gif',
                    ];
    loopControls.init( loopButtons, loopImgs );
</script>
        '''
        return html

    def buildHtmlBody(self):
        '''
        Returns a string that should be output to BODY of the HTML page.
        Ideally this html should be read from a file - if done that way, the same HTML
        could be used by Python, Perl, PHP.
        '''
        # GDN - TODO - button IMG files need path that is set by config.
        html = '''
      <!-- Loop Control Box -->
      <table class='looper' width='160px' style='background: none repeat scroll 0 0 rgb(204,204,255)'><tr><td>
        <input type='hidden' name='select_mode' value='1'>
        <tr>
        <td class='looper' colspan=2>
          <!-- animation control buttons -->
          <table summary='movement' class='noborder' align='center' cellspacing='0px' cellpadding='0px'>
           <tr>
            <td><button class='loop_controls' type='submit' name='button_first' value='first' accesskey='I' onClick='loopControls.click("first")'>
                 <img class='loop_buttons' src='/efs_verif/images/first.gif'/>
                 </button></td>
            <td><button class='loop_controls' type='submit' name='button_prev' value='prev' accesskey='P' onClick='loopControls.click("prev")'>
                 <img class='loop_buttons' src='/efs_verif/images/back1.gif'/>
                </button></td>
            <td><button class='loop_controls' type='submit' name='button_stop' value='stop' accesskey='S' onClick='loopControls.click("stop")'>
                 <img class='loop_buttons' src='/efs_verif/images/stop.gif' />
                 </button> </td>
            <td> <button class='loop_controls' type='submit' name='button_play' value='play' accesskey='F' onClick='loopControls.click("play")'>
                 <img src='/efs_verif/images/start.gif'/>
                 </button> </td>
            <td> <button class='loop_controls' type='submit' name='button_next' value='next' accesskey='N' onClick='loopControls.click("next")'>
                 <img src='/efs_verif/images/next1.gif'/>
                 </button> </td>
            <td> <button class='loop_controls' type='submit' name='button_last' value='last' accesskey='L' onClick='loopControls.click("last")'>
                 <img src='/efs_verif/images/last.gif'/>
                 </button> </td>
           </tr>
          </table>
        </td>

        <!-- animation speed and dwell control sliders.  Dwell has been deactivated. 
             inputs: target is name of form element. value is value of element.
             position is initial location of slider in units relative to length
             of slider. Default length of slider is 100 pixels. Slider minimum
             and maximum values are specified in the intialization script. -->
        </tr>
        <tr>
         <td>Speed</td>
         <td style='border: 0; border-style: solid;'>
             <!--
             <input class="carpe-slider from-2000 to-200 position-55" style="float: left; clear: none;" id="anim_speed" name="anim_speed" type="text" />
             -->
             <input class="carpe-slider" min="200" max="2000" step="20" style="float: left; clear: none; transform: rotateY(180deg)" id="anim_speed" name="anim_speed" type="range" />
         </td>
        </tr>

        <!-- GDN - TODO - I am not using these INPUT, they are legacy of the Perl version -->
        <!-- input_current is the image frame displayed -->
        <input type='hidden' name='input_current' value='1'>

        <!-- input_n_frames is the number of image frames -->
        <input type='hidden' name='input_n_frames'>
      </table>
      <!-- end loop control box -->
        '''
        return html
    

#..................START EPILOGUE......................................
#
# CONFIGURATION IDENTIFICATION:  @(#)$Id: loop_control.py 34396 2014-02-11 17:19:34Z glenn.d.nelson $
#
# NAME:                          loop_control.py
#
# AUTHOR:                        Glenn Nelson / CSC
#
# DESCRIPTION:                   Creates a player bar (forward, back, stop, play)
#                                for controlling tau_buttons.
#                                It recreates the look and feel of animator.pl
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
# USAGE:                         invoke with HTTP
#
#...................END EPILOGUE........................................

