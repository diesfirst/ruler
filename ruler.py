"""
State:          Ruler
State type:     mb::ruler
Description:    For measuring distances on geometry.
Author:         michaelb
Date Created:   March 24, 2020 - 11:28:31
"""

# Usage: This sample draws highlights when hovering over geometry polygons.
# Make sure to add an input on the node, connect a polygon mesh geometry and
# hit enter in the viewer.

import hou
import viewerstate.utils as su

def createSphereGeometry():
    geo = hou.Geometry()
    sphere_verb = hou.sopNodeTypeCategory().nodeVerb("sphere")
    hou.SopVerb.setParms(sphere_verb, {'type':2, 'rows':30, 't':(0,0,1)})
    hou.SopVerb.execute(sphere_verb, geo, [])
    return geo

def createLineGeometry():
    geo = hou.Geometry()
    line_verb = hou.sopNodeTypeCategory().nodeVerb("line")
    hou.SopVerb.setParms(line_verb, {'dir': (0, 0, 1)})
    hou.SopVerb.execute(line_verb, geo, [])
    return geo

def createFrustumGeometry():
    geo = hou.Geometry()
    tube_verb = hou.sopNodeTypeCategory().nodeVerb("tube")
    hou.SopVerb.setParms(tube_verb, {
                'type':1, 'cap':1, 'vertexnormals':1, 't':(0,0,0.25), 
                'r':(-90, 0, 0), 'rad': (0.5, 1), 'height':0.5, 'cols':10})
    hou.SopVerb.execute(tube_verb, geo, [])
    return geo

class State(object):
    msg = "Click and drag on the geometry to measure it."
    default_font_size = 30.0
    default_text = "default text"
    pink = hou.Vector4(1.0, 0.4745, 0.77647, 1)
    yellow = hou.Vector4(0.9450, 0.9804, 0.54902, 1)
    purple = hou.Vector4(0.74118, 0.57647, 0.97647, 1)
    green = hou.Vector4(0.31372, 0.980392, 0.48235, 1)

    def __init__(self, state_name, scene_viewer):
        self.state_name = state_name
        self.scene_viewer = scene_viewer
        sphere = createSphereGeometry()
        line = createLineGeometry()
        frustum = createFrustumGeometry()
        self.initial_spot_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "initial_spot", frustum)
        self.current_spot_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "current_spot", frustum)
        self.line_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "line", line)
        self.text_drawable = hou.TextDrawable(scene_viewer, "text_drawable")
        self.text_params = {'text': None, 'translate': hou.Vector3(0.0, 0.0, 0.0)}
        self.spot_params = {'color1': State.yellow, 'fade_factor': 0.5}
        self.line_params = {'line_width': 4.0, 'style': (10.0, 5.0), 'color1': State.yellow,  'fade_factor':0.3}
        self.initial_pos = hou.Vector3(0.0, 0.0, 0.0)
        self.current_pos = hou.Vector3(0.0, 0.0, 0.0)
        self.spot_size = 0.01
        self.measurement = 0.0
        self.geometry = None
        self.current_node = None
        self.font_size = State.default_font_size
        self.font_color = "#50fa7b"
#        self.font_color = "red"
        self.text = State.default_text
        self.updateTextField()
                
    def show(self, visible):
        """ Display or hide drawables.
        """
        self.text_drawable.show(visible)
        self.initial_spot_drawable.show(visible)
        self.current_spot_drawable.show(visible)
        self.line_drawable.show(visible)

    def setText(self, text):
        self.text = text
        self.updateTextField()

    def setFontSize(self, size):
        self.font_size = size
        self.updateTextField()

    def setFontColor(self, color):
        self.font_color = color
        self.updateTextField()

    def setTextPos(self, x, y):
        self.text_params['translate'][0] = x
        self.text_params['translate'][1] = y

    def setSpotTransform(self, drawable, pos, flip):
        initToCurDir = (self.current_pos - self.initial_pos).normalized()
        if (flip): initToCurDir *= -1 
        rotate = hou.hmath.buildRotateZToAxis(initToCurDir)
        translate = hou.hmath.buildTranslate(pos)
        viewer = hou.SceneViewer.curViewport(self.scene_viewer)
        modelToCamera = hou.GeometryViewport.cameraToModelTransform(viewer).inverted()
        cameraToNDC = hou.GeometryViewport.ndcToCameraTransform(viewer).inverted()
        NDC = translate * modelToCamera * cameraToNDC
        w = NDC.at(3, 3)
        w *= self.spot_size
        scale = hou.hmath.buildScale(w, w, w)
        transfrom = rotate * scale * translate
        hou.GeometryDrawable.setTransform(drawable, transfrom)

    def setLineTransform(self, drawable):
        initToCurDir = (self.current_pos - self.initial_pos).normalized()
        rotate = hou.hmath.buildRotateZToAxis(initToCurDir)
        translate = hou.hmath.buildTranslate(self.initial_pos)
        scale = hou.hmath.buildScale(self.measurement, self.measurement, self.measurement)
        transform = rotate * scale * translate
        hou.GeometryDrawable.setTransform(drawable, transform)

    def updateTextField(self):
        font_string = '<font size="{1}" color="{2}"><b> {0} </b></font>'.format(self.text, self.font_size, self.font_color)
        self.text_params['text'] = font_string

    def getMousePos(self, ui_event):
        device = hou.UIEvent.device(ui_event)
        return device.mouseX(), device.mouseY()

    def getIntersectionPos(self, ui_event):
        (origin, ray) = hou.ViewerEvent.ray(ui_event)
        (prim_num, pos, normal, uvw) = su.sopGeometryIntersection(self.geometry, origin, ray)
        return pos

    def onGenerate(self, kwargs):
        """ Assign the geometry to drawabled
        """
        self.measurement = 0.0;
        self.scene_viewer.setPromptMessage( State.msg )
        self.current_node = hou.SceneViewer.currentNode(self.scene_viewer)
        self.geometry = hou.SopNode.geometry(self.current_node)
#        self.enableDrawables(True)

    def onResume(self, kwargs):
        self.scene_viewer.setPromptMessage( State.msg )
        self.current_node = hou.SceneViewer.currentNode(self.scene_viewer)
        self.geometry = hou.SopNode.geometry(self.current_node)
#        self.enableDrawables(True)

    def onExit(self, kwargs):
        hou.SceneViewer.clearPromptMessage(self.scene_viewer)
        self.show(False)
#        self.enableDrawables(False)

    def onInterrupt(self,kwargs):
        self.show(False)
#        self.enableDrawables(False)

    def onMouseActive(self, ui_event):
        (x, y) = self.getMousePos(ui_event)
        self.current_pos = self.getIntersectionPos(ui_event)
        self.measurement = (self.current_pos - self.initial_pos).length()
        self.setText(str(self.measurement))
        self.setTextPos(x, y)
        self.setSpotTransform(self.initial_spot_drawable, self.initial_pos, True)
        self.setSpotTransform(self.current_spot_drawable, self.current_pos, False)
        self.setLineTransform(self.line_drawable)
        self.show(True)

    def onMouseStart(self, ui_event):
        self.initial_pos = self.getIntersectionPos(ui_event)

    def onMouseEvent(self, kwargs):
        ui_event = kwargs["ui_event"]
        reason = hou.UIEvent.reason(ui_event)
        if (reason == hou.uiEventReason.Start):
            self.onMouseStart(ui_event)
        elif (reason == hou.uiEventReason.Active):
            self.onMouseActive(ui_event)
        else:
            self.show(False)

    def onDraw( self, kwargs ):
        """ This callback is used for rendering the drawables
        """
        handle = kwargs["draw_handle"]
        hou.TextDrawable.draw(self.text_drawable, handle, self.text_params)
        hou.GeometryDrawable.draw(self.line_drawable, handle, self.line_params)
        hou.GeometryDrawable.draw(self.initial_spot_drawable, handle, self.spot_params)
        hou.GeometryDrawable.draw(self.current_spot_drawable, handle, self.spot_params)

def createViewerStateTemplate():
    """ Mandatory entry point to create and return the viewer state 
        template to register. """

    state_typename = "mb::ruler"
    state_label = "Ruler"
    state_cat = hou.sopNodeTypeCategory()

    template = hou.ViewerStateTemplate(state_typename, state_label, state_cat)
    template.bindFactory(State)
    template.bindIcon("MISC_python")

    return template
