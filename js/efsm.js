/**
 * Created by nelsong on 2/26/16.
 */

// Must load jquery before this file

// f_str: Input float number as string
// ndec: number of decimal places desired for display
// return: string representing floating point number
function f_format(f_str,ndec) {
    var x = (new Number(f_str).toFixed(ndec));
    return x;
}

var busyMillisec;
var busyTimer = null;
function loadBusy(where) {
    // where - ID for object where you want to overlay the busy image
    busyMillisec = 30000;   // longest time to leave busy timer on screen
    var that = jQuery(where).busy();    // makes 'busy' display visible at position 'where'
    busyTimer = setTimeout( function(){that.busy("hide");}, busyMillisec ); // hide 'busy' after delay
}

function loadNotBusy(where) {
    // hide the 'busy' timer display
    jQuery(where).busy("hide");
}

// Changes the URL in browser address bar - allows people to bookmark a particular display.
// Note: requires HTML5 browser.
function updateAddressBar( theScript ) {
    var form_args = $('#param_sel_form').serialize();
    var url = theScript + '?' + form_args;
    //alert(url);
    window.history.pushState('page-push-2', 'New Title', url);
}


// from http://stackoverflow.com/questions/1409355/finding-the-offset-client-position-of-an-element
// Finds element offsets, even if window is scrolled, by recursively visiting parent elements.
function getOffsetSum(elem) {
    var top=0, left=0;
    //alert('elem: '+elem);
    while(elem) {
        top = top + elem.offsetTop;
        left = left + elem.offsetLeft;
        elem = elem.offsetParent;
    }
    return {top: top, left: left};
}

// User double-clicks map to zoom into selected location.
function map_zoom(thisObj,ev) {
    // fetch display window size
    // compute display coords of mouse
    // compute new zoom ratio
    // Nothing to be done on server side?
    // Compute origin of map_img to copy into map_canvas
    // Compute xsize,ysize for map_img within map_canvas
}

// Handles user click in client area.
// Sends XY coords off to server so that Python matplotlib can derive longitude-latitude
// from the mouse click.
// TODO: not used with OL3, but should be used as handler for 'map.on("click")'
function map_click(thisObj,ev) {
    var clientX, clientY;
    var screenX, screenY;
    var img_scale = parseInt(document.getElementById('img_scale').value);
    if (!ev){var ev = window.event;}
    //var parentOffset = $(this).parent().offset();
    // clientXY has origin at upper-left of map image: thisObj.offset
    //var parentOffset = thisObj.offset();
    var parentOffset = getOffsetSum(thisObj[0]);
    var top  = window.pageYOffset || document.documentElement.scrollTop,
        left = window.pageXOffset || document.documentElement.scrollLeft;
    clientX = ev.clientX - parentOffset.left; clientY = ev.clientY - parentOffset.top;
    screenX = ev.screenX - parentOffset.left; screenY = ev.screenY - parentOffset.top;
    msg = "<p>map_click: JS</p>";
    msg += "<ul>"
    msg += "<li>parent offset: "+parentOffset.left.toFixed(0)+", "+parentOffset.top.toFixed(0);
    msg += "</li><li>scroll: "+left+", "+top;
    msg += "</li><li>client: "+clientX.toFixed(0)+", "+clientY.toFixed(0);
    msg += "</li><li>"+"screen: "+screenX.toFixed(0)+", "+screenY.toFixed(0);
    msg += '</li><li>obj size: ('+thisObj.width()+','+thisObj.height()+')';
    msg += "</li><li>disp: "+img_scale*(clientX+left)+", "+img_scale*(thisObj.height()-(clientY+top));
    msg += "</li></ul>";

    // Now ask python/matplotlib to convert back to lon-lat
    // clientX is relative to left edge of map image (including labeled axes)
    // clientY is relative to top edge of map image, but want bottom edge: (thisObj.height() - clientY)
    // Must adjust by scrollbar amount, usually (0,0)
    // Pass these numbers to python server and use matplotlib transforms to get mouse click relative to map axes.
    var qargs = 'action=map_click&x='+img_scale*(clientX+left)+'&y='+img_scale*(thisObj.height()-(clientY+top));
    //alert(qargs);
    var x_proj,y_proj;
    // Ajax returns more than just lon-lat, but other numbers are only used for debugging.
    // When value is returned, we call plume_click to display the plume graph.
    $.ajax( {url:"/efs_map/cgi-bin/efsm_query.py", data:qargs, type:"POST", dataType:"json",
        success: function(resp){
            msg += "<p>Compute in Python</p>";
            msg += "<ul>";

            x_proj = f_format(resp['x_proj'],1);
            y_proj = f_format(resp['y_proj'],1);
            msg += "<li>proj: "+x_proj+", "+y_proj;

            x_axis = f_format(resp['x_ax'],2);
            y_axis = f_format(resp['y_ax'],2);
            msg += "<li>axis: "+x_axis+", "+y_axis;

            lon = f_format(resp['lon'],2);
            lat = f_format(resp['lat'],2);
            msg += "</li><li>ll: "+lon+", "+lat;

            msg += "</li></ul>";
            $("#xy_dbg").html(msg);
            plume_click(lon,lat);
        },
        error: function(xhr,status) {alert('mouse click: '+status);}
    });

    // NOTE: AJAX is asynchronous and map_mark will be called before ajax call above has completed.
    //map_mark(clientX+left,(clientY+top));   // put a marker on the map
}

// Leave a marker on the map when user clicks
function map_mark(x,y) {
    //alert('mapclick');
    var msize = 20;
    c = document.getElementById("map_overlay"); var ctx = c.getContext('2d');
    //ctx.canvas.height = img_y; ctx.canvas.width  = img_x;
    //alert('canvas size: '+ctx.canvas.width+', '+ctx.canvas.height);
    // erase canvas in order to clear previous mark
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    // draw a mark at selected location
    ctx.fillStyle = 'blue';
    ctx.fillRect(x-msize/2,y-msize/2,msize,msize);
}

function map_mark_overlay(lon,lat) {
    // Example from: http://stackoverflow.com/questions/32260021/openlayers-3-drawing-a-polygon-feature-over-the-dateline
    // If you don't parseFloat, then "31.2" is treated as a string!
    var x = parseFloat(lon), y = parseFloat(lat);
    var wgs84Proj = new ol.proj.Projection({ code : "EPSG:4326" });
    var origProj = new ol.proj.Projection({ code : "EPSG:3857" });
    // styling for the markers:
    var _myStroke = new ol.style.Stroke({
       color : 'rgba(0,0,255,1.0)',
       width : 1
    });
    var _myFill = new ol.style.Fill({
       color: 'rgba(255,255,0,0.6)'
    });
    var myStyle = new ol.style.Style({
       stroke : _myStroke,
       fill : _myFill
     });
    marker_layer.setStyle(myStyle);

    // If square straddles the date-line, make sure that logitude increases to the right.
    //var unformattedCoordinates = [[175, 70], [175, 60], [-160, 60], [-160, 70]];
    //var unformattedCoordinates = [[175, 70], [175, 60], [200, 60], [200, 70]];
    // Create square centered on (x,y)
    var unformattedCoordinates = [[x-2, y+2], [x-2, y-2], [x+2, y-2], [x+2, y+2]];
    var convertedCoordinates = [];

    // Convert square from long-lat to map coords
    $(unformattedCoordinates).each(function(index, coordinate){
        var xy = ol.proj.transform(coordinate, 'EPSG:4326', 'EPSG:3857');
        convertedCoordinates.push(xy);
    });

    var polygonGeometry = new ol.geom.Polygon([convertedCoordinates]);
    var polygonFeature = new ol.Feature({ geometry : polygonGeometry });

    // TODO: if I can get source from existing layer, then I can add markers to it,
    var vectorSource = new ol.source.Vector();
    vectorSource.addFeature(polygonFeature);
    marker_layer.setSource(vectorSource);
}

// GDN - TODO: tau_buttons should chain handler functions instead of using this pre-defined function name.
// When user selects a tau button, this functio is called.
// called by tau_buttons.tauSelect()
function tauSelectEx(theButton, tauVal) {
    // don't know if tauVal is str or int
    var val = parseInt(""+tauVal, 10);  // ensures conversion to str, then parseInt to a number, base 10
    jQuery('#myform input[name=tau]').val(""+val); // selector wants int string with no leading 0
    var map_id = '#map_' + ('0000' + val).slice(-4);    // hidden IMG tag with ID of "map_NNNN"
    var url = jQuery(map_id).attr('src');       // retrieve URL of hidden IMG
    jQuery('#map_img').attr('src',url);     // Assign URL to visible "map_img"
    return 0;
}

// Better mouse click example: http://miloq.blogspot.com/2011/05/coordinates-mouse-click-canvas.html

// Create the map legend as a canvas object
function create_legend(cntr_vals) {
    // TODO: color values should be dynamically determined
    // TODO: number of cntr_vals should be dynamic, not fixed at 3
    var colors = ['maroon','seagreen','lightskyblue']; // declared in efsm_isis.py
    var canvas = jQuery('<canvas />').attr({
        id:'legend', width:'80', height:'80',
        style:'border:2px solid #000000;'
    });
    //console.log('create_legend: '+JSON.stringify(cntr_vals));
    //var ctx = $(canvas)[0].getContext('2d');
    var ctx = canvas[0].getContext('2d');
    ctx.font = "18px serif";
    for (i = 0; i < cntr_vals.length; i++) {
        my_value = cntr_vals[i];
        my_color = colors[i % colors.length];
        ctx.fillStyle = 'black';
        ctx.fillText(""+my_value, 10, 20+(i*25));
        ctx.fillStyle = my_color;
        ctx.fillRect(40,10+(i*25), 30,10);
    }

    // TODO: should just return canvas and not place it on page,
    // but this is easier for now.
    var leg_div = jQuery('#legend_div');
    // must clear contents
    leg_div.empty();
    // add new legend to div
    leg_div.append(canvas);
}