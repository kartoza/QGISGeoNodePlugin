"""Utilities to convert styles between OGC SLD and QGIS QML"""

import typing
import xml.etree.ElementTree as ET
from xml.dom import minidom

import qgis.core
from qgis.PyQt import QtXml


def convert_sld_to_qml(raw_sld: str) -> str:
    """Convert SLD to QGIS QML style.

    This code is an modification of the ``SLD4raster.sld2qml()`` method, as found on the
    SLD4raster QGIS plugin:

    https://github.com/MSBilgin/SLD4raster

    Originally created by Mehmet Selim BILGIN. Original code was published with
    GPL v2 license.

    """

    sld_document = minidom.parseString(raw_sld)
    if len(sld_document.getElementsByTagName("sld:RasterSymbolizer")) > 0:
        ns = "sld:"
    elif len(sld_document.getElementsByTagName("se:RasterSymbolizer")) > 0:
        ns = "se:"
    else:
        ns = ""
    root_el = ET.Element("qgis")
    pipe_el = ET.SubElement(root_el, "pipe")
    raster_renderer_el = ET.SubElement(pipe_el, "rasterrenderer")
    ET.SubElement(raster_renderer_el, "rasterTransparency")
    colormap_el_list = sld_document.getElementsByTagName(f"{ns}ColorMap")
    is_singleband = len(colormap_el_list) > 0
    if is_singleband:
        raster_renderer_el.attrib["type"] = "singlebandpseudocolor"
        raster_renderer_el.attrib["band"] = "1"
        raster_shader_el = ET.SubElement(raster_renderer_el, "rastershader")
        color_ramp_shader_el = ET.SubElement(raster_shader_el, "colorrampshader")
        try:
            # Sometimes "ColorMap" tag does not contain "type" attribute. This means
            # it is a ramp color.
            color_map_el = sld_document.getElementsByTagName(f"{ns}ColorMap")[0]
            sld_color_map_type = color_map_el.attributes.has_key("type")
            # or getting raster map colortype by "type" atribute.
            sld_color_map_type2 = color_map_el.attributes["type"].value
            if sld_color_map_type and sld_color_map_type2 == "intervals":
                color_ramp_shader_el.attrib["colorRampType"] = "DISCRETE"
        except Exception:
            color_ramp_shader_el.attrib["colorRampType"] = "INTERPOLATED"
        for color_map_entry in sld_document.getElementsByTagName(f"{ns}ColorMapEntry"):
            try:
                label = color_map_entry.attributes["label"].value
            except Exception:
                label = color_map_entry.attributes["quantity"].value
            item_el = ET.SubElement(color_ramp_shader_el, "item")
            item_el.attrib["alpha"] = "255"
            item_el.attrib["value"] = color_map_entry.attributes["quantity"].value
            item_el.attrib["label"] = label
            item_el.attrib["color"] = color_map_entry.attributes["color"].value
    else:
        red_channel_el = sld_document.getElementsByTagName(f"{ns}RedChannel")[0]
        red_band = red_channel_el.getElementsByTagName(
            f"{ns}SourceChannelName"
        ).firstChild.nodeValue
        green_channel_el = sld_document.getElementsByTagName(f"{ns}GreenChannel")[0]
        green_band = green_channel_el.getElementsByTagName(
            f"{ns}SourceChannelName"
        ).firstChild.nodeValue
        blue_channel_el = sld_document.getElementsByTagName(f"{ns}BlueChannel")[0]
        blue_band = blue_channel_el.getElementsByTagName(
            f"{ns}SourceChannelName"
        ).firstChild.nodeValue
        raster_renderer_el.attrib["type"] = "multibandcolor"
        raster_renderer_el.attrib["redBand"] = red_band
        raster_renderer_el.attrib["greenBand"] = green_band
        raster_renderer_el.attrib["blueBand"] = blue_band

    try:
        # some SLD documents don't have 'Opacity' tag
        sld_opacity = sld_document.getElementsByTagName(f"{ns}Opacity")[
            0
        ].firstChild.nodeValue
    except Exception:
        sld_opacity = "1"

    raster_renderer_el.attrib["opacity"] = sld_opacity
    ET.SubElement(pipe_el, "brightnesscontrast")
    ET.SubElement(pipe_el, "huesaturation")
    ET.SubElement(pipe_el, "rasterresampler")
    blend_mode_el = ET.SubElement(root_el, "blendMode")
    blend_mode_el.text = "0"
    return ET.tostring(root_el).decode("utf-8")


def get_qml(layer: qgis.core.QgsMapLayer) -> typing.Tuple[str, typing.Optional[str]]:
    qml_document = QtXml.QDomDocument()
    root = qml_document.createElement("SLD4raster")
    qml_document.appendChild(root)
    qgis_node = qml_document.createElement("qgis")
    root.appendChild(qgis_node)
    error_message = None
    context = qgis.core.QgsReadWriteContext()
    layer.writeSymbology(qgis_node, qml_document, error_message, context)
    return qml_document.toString(), error_message


def convert_qml_to_sld(raw_qml: str, sld_name: str) -> str:
    """Convert QGIS QML style to SLD

    This code is an modification of the ``SLD4raster.qml2sld()`` method, as found on the
    SLD4raster QGIS plugin:

    https://github.com/MSBilgin/SLD4raster

    Originally created by Mehmet Selim BILGIN. Original code was published with
    GPL v2 license.

    """

    root_el = ET.Element("sld:StyledLayerDescriptor")
    root_el.attrib["xmlns"] = "http://www.opengis.net/sld"
    root_el.attrib["xmlns:sld"] = "http://www.opengis.net/sld"
    root_el.attrib["xmlns:ogc"] = "http://www.opengis.net/ogc"
    root_el.attrib["xmlns:gml"] = "http://www.opengis.net/gml"
    root_el.attrib["version"] = "1.0.0"
    user_layer_el = ET.SubElement(root_el, "sld:UserLayer")
    layer_feature_constraints_el = ET.SubElement(
        user_layer_el, "sld:LayerFeatureConstraints"
    )
    ET.SubElement(layer_feature_constraints_el, "sld:FeatureTypeConstraint")
    user_style_el = ET.SubElement(user_layer_el, "sld:UserStyle")
    style_name_el = ET.SubElement(user_style_el, "sld:Name")
    style_name_el.text = sld_name
    ET.SubElement(user_style_el, "sld:Title")
    featuretype_style_el = ET.SubElement(user_style_el, "sld:FeatureTypeStyle")
    ET.SubElement(featuretype_style_el, "sld:Name")
    rule_el = ET.SubElement(featuretype_style_el, "sld:Rule")
    raster_symbolizer_el = ET.SubElement(rule_el, "sld:RasterSymbolizer")
    geometry_el = ET.SubElement(raster_symbolizer_el, "sld:Geometry")
    ogc_property_name_el = ET.SubElement(geometry_el, "ogc:PropertyName")
    ogc_property_name_el.text = "grid"
    qml_el = minidom.parseString(raw_qml)
    qml_renderer_el = qml_el.getElementsByTagName("rasterrenderer")[0]
    raster_type = str(qml_renderer_el.attributes["type"].value)
    if raster_type == "multibandcolor":
        raster_symbolizer_el.append(_get_multi_band_channel_selection(qml_el))
    elif "gradient" in qml_renderer_el.attributes.keys():
        raster_symbolizer_el.append(_get_gradient_color_map(qml_el))
    else:  # single band raster
        raster_symbolizer_el.append(_get_singleband_raster_color_map(qml_el))
    opacity_el = ET.SubElement(raster_symbolizer_el, "sld:Opacity")
    opacity_el.text = str(qml_renderer_el.attributes["opacity"].value)
    return ET.tostring(root_el).decode("utf-8")


def _get_multi_band_channel_selection(qml: ET.Element) -> ET.Element:
    qml_renderer_el = qml.getElementsByTagName("rasterrenderer")[0]
    red_band = str(qml_renderer_el.attributes["redBand"].value)
    green_band = str(qml_renderer_el.attributes["greenBand"].value)
    blue_band = str(qml_renderer_el.attributes["blueBand"].value)
    channel_selection_el = ET.Element("sld:ChannelSelection")
    red_channel_el = ET.SubElement(channel_selection_el, "sld:RedChannel")
    red_source_channel_el = ET.SubElement(red_channel_el, "sld:SourceChannelName")
    red_source_channel_el.text = red_band
    green_channel_el = ET.SubElement(channel_selection_el, "sld:GreenChannel")
    green_source_channel_el = ET.SubElement(green_channel_el, "sld:SourceChannelName")
    green_source_channel_el.text = green_band
    blue_channel_el = ET.SubElement(channel_selection_el, "sld:BlueChannel")
    blue_source_channel_el = ET.SubElement(blue_channel_el, "sld:SourceChannelName")
    blue_source_channel_el.text = blue_band
    return channel_selection_el


def _get_gradient_color_map(qml: ET.Element) -> ET.Element:
    min_value = qml.getElementsByTagName("minValue")[0].firstChild.nodeValue
    max_value = qml.getElementsByTagName("maxValue")[0].firstChild.nodeValue
    black = "#000000"
    white = "#FFFFFF"
    opacity = "1.0"
    qml_renderer_el = qml.getElementsByTagName("rasterrenderer")[0]
    if qml_renderer_el.attributes["gradient"].value == "WhiteToBlack":
        min_color, max_color = (white, black)
    else:
        min_color, max_color = (black, white)
    color_map_el = ET.Element("sld:ColorMap")
    min_color_map_entry_el = ET.SubElement(color_map_el, "sld:ColorMapEntry")
    min_color_map_entry_el.attrib["color"] = min_color
    min_color_map_entry_el.attrib["opacity"] = opacity
    min_color_map_entry_el.attrib["quantity"] = min_value
    max_color_map_entry_el = ET.SubElement(color_map_el, "sld:ColorMapEntry")
    max_color_map_entry_el.attrib["color"] = max_color
    max_color_map_entry_el.attrib["opacity"] = opacity
    max_color_map_entry_el.attrib["quantity"] = max_value
    return color_map_el


def _get_singleband_raster_color_map(qml: ET.Element) -> ET.Element:
    color_map_el = ET.Element("sld:ColorMap")
    qml_shader_el = qml.getElementsByTagName("colorrampshader")[0]
    color_type = str(qml_shader_el.attributes["colorRampType"].value)
    if color_type == "DISCRETE":
        color_map_el.attrib["type"] = "intervals"
    for element in qml.getElementsByTagName("item"):
        color_map_entry_el = ET.SubElement(color_map_el, "sld:ColorMapEntry")
        color_map_entry_el.attrib["color"] = element.attributes["color"].value
        color_map_entry_el.attrib["quantity"] = element.attributes["value"].value
        color_map_entry_el.attrib["label"] = element.attributes["label"].value
        color_map_entry_el.attrib["opacity"] = "1.0"
    return color_map_el
