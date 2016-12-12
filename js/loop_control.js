/* 
 * This holds the tau buttons (FNMOC calls them "piano keys"),
 * the player controls (play, stop, forward, back)
 * and the speed control slider.
 */
var LoopControlsJS = {
    init: function( ids, images ) {
        this.tauButtons = null;
        var currentTau = 0;
        this.buttonIds = [];
        this.buttonImages = [];
        // copy values to new Array
        for (i=0; i < ids.length; i++) {
            this.buttonIds[i] = ids[i];
            this.buttonImages[i]  = images[i];
        }
    },
    click: function(button_value) {
        // click any play bar button.
        // send value of button to tauButtons.
        if (this.tauButtons != null) {
            //alert('button='+button_value);
            this.tauButtons.control(button_value);
        }
    },
    attachToTauButtons: function(tb, animSpeedCtrl) {
        // the tau_button bar. Button events in this loop_control will be sent to 'tauButtons''
        this.tauButtons = tb;
        tb.speedCtrl = animSpeedCtrl;
    }
}



