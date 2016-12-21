/**
 * Created by nelsong on 12/19/16.
 */
/* OpenLayers3 functionality

 */
// Here we setup OpenLayers map with a PNG overlay.
// OL can add graticule
// OL mouse position: http://openlayers.org/en/latest/examples/mouse-position.html
var mousePositionControl = new ol.control.MousePosition({
    coordinateFormat: ol.coordinate.createStringXY(1),
    projection: 'EPSG:4326',
    // comment the following two lines to have the mouse position
    // be placed within the map.
    //className: 'custom-mouse-position',
    //target: document.getElementById('mouse-position'),
    undefinedHTML: '&nbsp;'
});

var extent = [0, 0, 1600, 800];
var ll_extent = [-180.0, -90.0, 180.0, 90.0];
//var ll_extent = [0.0, -90.0, 360.0, 90.0];
var marker_layer;

function create_main_map() {
    // OSM is child of ol.source.XYZ and projection = EPSG:3857
    var map = new ol.Map({
        controls: ol.control.defaults({
            attributionOptions: /** @type {olx.control.AttributionOptions} */ ({
                collapsible: false
            })
        }).extend([mousePositionControl,new ol.control.ScaleLine()]),
        target: 'map_div',
        layers: [
            new ol.layer.Tile({source: new ol.source.OSM(), }),
        ],
        view: new ol.View({
            center: ol.proj.fromLonLat([0.0, 0.0]),
            zoom: 2,
            minZoom: 1, maxZoom: 6,
        })
    });
    //console.log('create_main_map: map='+JSON.stringify(3));
    map.on('click', function(evt) {
        var coord = evt.coordinate; // 3857: coordinates in meters
        var ll_coord = ol.proj.transform(coord, 'EPSG:3857', 'EPSG:4326');
        console.log('3857: '+coord+' 4326: '+ll_coord);
        var lon = f_format(ll_coord[0],2);
        var lat = f_format(ll_coord[1],2);
        plume_click(lon,lat);
        //map_mark_overlay(lon,lat);
    });
    //
    var ll_proj = 'EPSG:4326';  // with 3857 the map looks the same, but coords are in meters
    // TODO: can I specify "imageLoadFunction: function(image,src){}"
    // TODO: or just change it so that 'url' references python with args to re-arrange image bounds
    var glob_layer = new ol.layer.Image({title:"Wind 850",
        source: new ol.source.ImageStatic({
            attributions: 'FNMOC Ensemble',
            url: '/efs_map/images/Overlay-180.png',
            projection: ll_proj,
            imageExtent: ll_extent,
        }),
        opacity: 0.5
    });
    //glob_layer.setExtent(bounds);
    map.addLayer(glob_layer);
    marker_layer = new ol.layer.Vector();
    map.addLayer(marker_layer);
    /*
    map_mark_overlay(0,0);   // test that we can place a mark
    */
    return map;
}