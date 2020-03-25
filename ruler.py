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

class State(object):
    msg = "Click and drag on the geometry to measure it."
    default_font_size = 30.0
    default_color = "green"
    default_text = "default text"

    def __init__(self, state_name, scene_viewer):
        self.state_name = state_name
        self.scene_viewer = scene_viewer
        self.text_drawable = hou.TextDrawable(scene_viewer, "text_drawable")
        self.initial_spot_drawable = hou.SimpleDrawable(scene_viewer, hou.drawablePrimitive.Sphere, "initial_spot")
        self.current_spot_drawable = hou.SimpleDrawable(scene_viewer, hou.drawablePrimitive.Sphere, "current_spot")
        self.initial_spot_drawable.setDisplayMode(hou.drawableDisplayMode.CurrentViewportMode)
        self.current_spot_drawable.setDisplayMode(hou.drawableDisplayMode.CurrentViewportMode)
        self.text_params = {'text': None, 'translate' : hou.Vector3(0.0, 0.0, 0.0)}
        self.initial_pos = hou.Vector3(0.0, 0.0, 0.0)
        self.current_pos = hou.Vector3(0.0, 0.0, 0.0)
        self.measurement = 0.0
        self.geometry = None
        self.current_node = None
        self.font_color = State.default_color
        self.font_size = State.default_font_size
        self.text = State.default_text
        self.updateTextField()
                
    def show(self, visible):
        """ Display or hide drawables.
        """
        self.text_drawable.show(visible)
        self.initial_spot_drawable.show(visible)
        self.current_spot_drawable.show(visible)

    def enableDrawables(self, enable):
        self.initial_spot_drawable.enable(enable)
        self.current_spot_drawable.enable(enable)

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

    def setSpotTransform(self, drawable, pos):
        translate = hou.hmath.buildTranslate(pos)
        viewer = hou.SceneViewer.curViewport(self.scene_viewer)
        modelToCamera = hou.GeometryViewport.cameraToModelTransform(viewer).inverted()
        cameraToNDC = hou.GeometryViewport.ndcToCameraTransform(viewer).inverted()
        NDC = translate * modelToCamera * cameraToNDC
        w = NDC.at(3, 3)
        w *= .01
        print w
        scale = hou.hmath.buildScale(w, w, w)
        transfrom = scale * translate
        hou.SimpleDrawable.setTransform(drawable, transfrom)

    def updateTextField(self):
        font_string = '<font color="{2}" size="{1}"> {0} </font>'.format(self.text, self.font_size, self.font_color)
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
        self.enableDrawables(True)

    def onResume(self, kwargs):
        self.scene_viewer.setPromptMessage( State.msg )
        self.current_node = hou.SceneViewer.currentNode(self.scene_viewer)
        self.geometry = hou.SopNode.geometry(self.current_node)
        self.enableDrawables(True)

    def onExit(self, kwargs):
        hou.SceneViewer.clearPromptMessage(self.scene_viewer)
        self.show(False)
        self.enableDrawables(False)

    def onInterrupt(self,kwargs):
        self.show(False)
        self.enableDrawables(False)

    def onMouseActive(self, ui_event):
        (x, y) = self.getMousePos(ui_event)
        self.current_pos = self.getIntersectionPos(ui_event)
        self.measurement = (self.current_pos - self.initial_pos).length()
        self.setText(str(self.measurement))
        self.setTextPos(x, y)
        self.setSpotTransform(self.current_spot_drawable, self.current_pos)
        self.show(True)

    def onMouseStart(self, ui_event):
        (x, y) = self.getMousePos(ui_event)
        self.initial_pos = self.getIntersectionPos(ui_event)
        self.setText("Start!")
        self.setTextPos(x, y)
        self.setSpotTransform(self.initial_spot_drawable, self.initial_pos)
        self.show(True)

    def onMouseEvent(self, kwargs):
        ui_event = kwargs["ui_event"]
        reason = hou.UIEvent.reason(ui_event)
        if (reason == hou.uiEventReason.Start):
            self.onMouseStart(ui_event)
        if (reason == hou.uiEventReason.Active):
            self.onMouseActive(ui_event)
        if (reason == hou.uiEventReason.Changed):
            self.show(False)

    def onDraw( self, kwargs ):
        """ This callback is used for rendering the drawables
        """
        handle = kwargs["draw_handle"]
        hou.TextDrawable.draw(self.text_drawable, handle, self.text_params)

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
