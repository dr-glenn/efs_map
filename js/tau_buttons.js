/*
 * Javascript "class" to manage and control a tau button bar.
 * Actually it is a Javascript "object literal".
 * GDN: as defined here, it is normally used as a singleton. However, you can use it:
 * 'tb = clone(TauButtonsJS);'. Unfortunately 'clone' may not work correctly.
 * The best way to make a 'class' might be using 'prototype' keyword as explained
 * in section 1.2 here: http://www.phpied.com/3-ways-to-define-a-javascript-class/
 *
 * The button bar HTML is constructed in tau_buttons.py.
 * A single button is an anchor (HTML:A) containing a div (HTML:DIV),
 * containing a hidden input (HTML:INPUT TYPE="HIDDEN").
 * The anchor recieves events: mouseover, mouseout. The display style is assigned
 * to the DIV. So event handlers have to fetch the child DIV and change the CLASS
 * of the DIV to change the button display. Clear?
 */
var TauButtonsJS = {
    currentTau: 0,
    animateMillisec: 300,
    animateTimer: null,
    animateOn: false,
    imgHolderId: null,  // ID of the HTML object where current tau IMG is displayed
    speedCtrl: null,    // widget that controls animation speed

    init: function( taus, images ) {
        this.tauValues = [];
        this.tauValid  = [];
        this.images    = [];
        this.myButtons = [];
        // copy values to new Array
        var i;
        for (i=0; i < taus.length; i++) {
            this.tauValues[i] = taus[i];
            this.tauValid[i]  = true;
            if (images.length == taus.length)
                this.images[i] = images[i];
            else
                this.images[i] = null;
        }
    },
    click: function() {
        // no use for click in this button bar
    },
    control: function(command) {
        // TODO - should be able to invoke function by name
        if (command=='stop') {
            this.stop();
        }
        else if (command=='play') {
            this.start();
        }
        else if (command=='first') {
            this.first();
        }
        else if (command=='last') {
            this.last();
        }
        else if (command=='prev') {
            this.prevTau();
        }
        else if (command=='next') {
            // 'next' is a keyword in some Javscript libs
            this.nextTau();
        }
    },
    mouseover: function(button) {
        //var insideDiv = (button.getElementsByTagName("div"))[0];
        var tauIdx = (button.getElementsByTagName("input"))[0].value;
        tauIdx = parseInt(tauIdx);
        this.stop();    // just in case animation is running
        //alert('mouseover1='+tauIdx);
        // TODO: might want to fetch insideDiv here and test for disabled state,
        //       and maybe skip calling tauSelect.
        var elemId = 'div_tau_button_' + tauIdx.toString();
        var insideDiv = document.getElementById( elemId );
        if (insideDiv) {
            if ((insideDiv.className == "tau_button_disable")
            ||   insideDiv.getAttribute("class") == "tau_button_disable" ) {
                return;
            }
        }
        this.tauSelect(tauIdx);
    },
    mouseout: function(button) {
        //var insideDiv = (button.getElementsByTagName("div"))[0];
        var tauIdx = (button.getElementsByTagName("input"))[0].value;
        tauIdx = parseInt(tauIdx);
        // GDN - we want buttons to stay depressed until a new button is selected.
        // For example, if mouse moves along button bar, then when new button is
        // selected, the previous should be unselected.
        // But if mouse moves entirely out of the button bar, then the selected
        // button should remain depressed. Thus we do not call tauUnSelect here.
        //this.tauUnSelect(tauIdx);
    },
    getTau: function() { return this.currentTau; },
    setTau: function(tau) { this.currentTau = tau; },
    tauSelectCurrent: function() {
        var tau = this.getTau();
        for (var i=0; i < this.tauValues.length; i++) {
            if (tau == this.tauValues[i]) {
                this.tauSelect(i);
                break;
            }
        }
    },
    tauSelect: function(tauIdx) {
        // changes button state and stores new value
        var elemId = 'div_tau_button_' + tauIdx.toString();
        var insideDiv = document.getElementById( elemId );
//        alert('tauSelect 1');
        var newTau = this.tauValues[tauIdx];
//        alert('tauSelect 2');
        var oldTau = this.currentTau;
//        alert('newTau='+newTau);
        // TODO - should saveId be stored in hidden element or just stored in this class object?
        var saveId = document.getElementById( "tau_button_current_id" );
        var oldIdx = saveId.value;
        if (oldIdx != null && oldIdx.length > 0) {
            //alert('tauSelect 3, oldIdx='+oldIdx.toString());
            this.tauUnSelect(+oldIdx);  // change state of old button
        }
        this.currentTau = newTau;
        //alert('tauSelect 4');
        if (insideDiv) {
            insideDiv.className = "tau_button_dwn_holder"; // IE does things different than standard.
            insideDiv.setAttribute( "class", "tau_button_dwn_holder" );
            var lbl = document.getElementById( "tau_label" );
            if (lbl) { lbl.value = newTau; }
            if (saveId) { saveId.value = tauIdx.toString(); }
        }
        var imgFile = this.images[tauIdx];
        //alert('tauSelect 5');

        // change img src, so user sees new image
        var imgElem = document.getElementById ( this.imgHolderId );
        if (imgFile != null && imgElem) {
            //alert('imgFile='+imgFile);
            imgElem.src = imgFile;
        }
        // if you need additional behavior, implement tauSelectEx as global function
        if (typeof tauSelectEx != "undefined") {
            tauSelectEx(insideDiv, newTau);
        }

    },
    tauUnSelect: function(tauIdx) {
        // changes button state, does not change value
        var elemId = 'div_tau_button_' + tauIdx.toString();
        var insideDiv = document.getElementById( elemId );
        //alert('tauUnSelect 1');
        if (insideDiv) {
            if (this.tauValid[tauIdx] == true) {
                insideDiv.className = "tau_button_up_holder";  // IE browser
                insideDiv.setAttribute( "class", "tau_button_up_holder" ); // all other browser
            }
            else {
                insideDiv.className = "tau_button_disable";  // IE browser
                insideDiv.setAttribute( "class", "tau_button_disable" ); // all other browser
            }
        }
        // if you need additional behavior, implement tauUnSelectEx as global function
        //alert('tauUnSelect 2');
        if (typeof tauUnSelectEx != "undefined") {
            tauUnSelectEx(insideDiv);
        }
    },
    tauDisable: function(tauIdx) {
        // changes button state, does not change value
        var elemId = 'div_tau_button_' + tauIdx.toString();
        var insideDiv = document.getElementById( elemId );
        //alert('tauUnSelect 1');
        if (insideDiv) {
            insideDiv.className = "tau_button_disable";  // IE browser
            insideDiv.setAttribute( "class", "tau_button_disable" ); // all other browser
        }
    },
    tauEnable: function(tauIdx) {
        // changes button state, does not change value
        var elemId = 'div_tau_button_' + tauIdx.toString();
        var insideDiv = document.getElementById( elemId );
        //alert('tauUnSelect 1');
        if (insideDiv) {
            insideDiv.className = "tau_button_up_holder";  // IE browser
            insideDiv.setAttribute( "class", "tau_button_up_holder" ); // all other browser
        }
    },
    // should not name it 'next', because that is javascript keyword
    nextTau: function() {
        var saveId = document.getElementById( "tau_button_current_id" );
        var tauIdx = 0;
        if (saveId) {
            // If saveId, then first unselect the current button
            tauIdx = parseInt(saveId.value);
            this.tauUnSelect( tauIdx );
        }
        // Advance to next button and select if enabled
        while (1) {
            ++tauIdx;
            // TODO - GDN - infinite loop is NONE are enabled
            if (tauIdx >= this.tauValues.length) tauIdx = 0;
            if (this.tauValid[tauIdx] == true) {
                saveId.value = tauIdx.toString();
                this.tauSelect( tauIdx );
                break;
            }
        }
    },
    prevTau: function() {
        var saveId = document.getElementById( "tau_button_current_id" );
        var tauIdx = 0;
        if (saveId) {
                // If saveId, then first unselect the current button
                tauIdx = parseInt(saveId.value);
                this.tauUnSelect( tauIdx );
        }
        // Backup to previous button and select if enabled
        while (1) {
            --tauIdx;
            // TODO - GDN - infinite loop is NONE are enabled
            if (tauIdx < 0) tauIdx = this.tauValues.length - 1;
            if (this.tauValid[tauIdx] == true) {
                saveId.value = tauIdx.toString();
                this.tauSelect( tauIdx );
                break;
            }
        }
    },
    start: function() {
        // animate the image display
        if (this.speedCtrl != null) {
            var msec = document.getElementById( this.speedCtrl ).value;
            this.animateMillisec = msec;
        }
        this.animate(this);
    },
    stop: function() {
        // stop the image animation
        this.animateOn = false;
        clearTimeout( this.animateTimer );
    },
    first: function() {
        // select first tau value
        var saveId = document.getElementById( "tau_button_current_id" );
        var tauIdx;
        if (saveId) {
            // If saveId, then first unselect the current button
            tauIdx = parseInt(saveId.value);
            this.tauUnSelect( tauIdx );
        }
        // Now go to begin or first enabled button
        for (tauIdx = 0; tauIdx < this.tauValues.length; tauIdx++) {
            if (this.tauValid[tauIdx] == true) {
                saveId.value = tauIdx.toString();
                this.tauSelect( tauIdx );
                break;
            }
        }
    },
    last: function() {
        // select last tau value
        var saveId = document.getElementById( "tau_button_current_id" );
        var tauIdx;
        if (saveId) {
            // If saveId, then first unselect the current button
            tauIdx = parseInt(saveId.value);
            this.tauUnSelect( tauIdx );
        }
        // Now go to end or last enabled button
        for (tauIdx = this.tauValues.length - 1; tauIdx >= 0; tauIdx--) {
            if (this.tauValid[tauIdx] == true) {
                saveId.value = tauIdx.toString();
                this.tauSelect( tauIdx );
                break;
            }
        }
    },
    animateGraph: function() {
        // continue running animation. This is probably the only way to do it in Javascript.
        if (this.animateOn) {
            this.nextTau();
            if (this.speedCtrl != null) {
                var msec = document.getElementById( this.speedCtrl ).value;
                this.animateMillisec = msec;
            }

            // When timeout is done, animateGraph is called again.
            // To stop the animate loop, "animateTimer" variable is cleared.
            var theObj = this;  // gobbledegook required to pass instance function to global function.
            this.animateTimer = setTimeout( function(){theObj.animateGraph();}, this.animateMillisec );
        }
    },
    animate: function( theButton ) {
        // don't run this if it is already running.
        if (! this.animateOn ) {
            // start running timed animation display
            this.animateOn = true;
            this.animateGraph();
        }
    },
    setImgHolder: function(imgId) {
        // Store the DOM element ID for the IMG tag where main image is displayed.
        this.imgHolderId = imgId;
    },
    enableValidButtons: function(validTimes) {
        for (var tauIdx=0; tauIdx < this.tauValues.length; tauIdx++) {
            tau = this.tauValues[tauIdx];
            var isValid = false;
            for (var key in validTimes) {
                if (tau == validTimes[key]) {
                    isValid = true;
                    this.tauValid[tauIdx] = true;
                    this.tauEnable(tauIdx);
                    break;
                }
            }
            if (!isValid) {
                this.tauValid[tauIdx] = false;
                this.tauDisable(tauIdx);
            }
        }
        this.tauSelectCurrent();
    }

}
