"""
State:          Ruler
State type:     mb::ruler
Description:    For measuring distances on geometry.
Author:         michaelb
Date Created:   March 24, 2020 - 11:28:31
"""

# People are asking for something like this:
# https://forums.odforce.net/topic/39249-ruler-tool-non-procedurally-measure-a-distance/
# https://forums.odforce.net/topic/43048-is-there-any-tool-to-measure-distance-between-two-points-in-viewport/
# https://www.sidefx.com/tutorials/houdini-tutorial-creating-a-measure-distance-tool/
# Have seen Steven Knipping create a make shift measuring line in a tutorial.

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

# TODO: Implement a colored background behind the tail and end to 
#       show that it is being axis aligned. maybe highlight geometry in so-
#       me similar way around the spot your measuring from

class Color(object):
    green = 0
    yellow = 1
    purple = 2
    pink = 3

    colorMap = {
        pink   : (hou.Vector4(1.0, 0.4745, 0.77647, 1),       "#ff79c6"),
        yellow : (hou.Vector4(0.9450, 0.9804, 0.54902, 1),    "#f1fa8c"),
        purple : (hou.Vector4(0.74118, 0.57647, 0.97647, 1),  "#bd93f9"),
        green  : (hou.Vector4(0.31372, 0.980392, 0.48235, 1), "#50fa7b"),
        }

    def __init__(self, color):
        self.vector4, self.hex_str = Color.colorMap[color]

    def getVec(self):
        return self.vector4

    def getHexStr(self):
        return self.hex_str

class Measurement(object):
    default_font_size = 30.0
    default_text = "default text"

    def __init__(self, scene_viewer, color):
        sphere = createSphereGeometry()
        line = createLineGeometry()
        frustum = createFrustumGeometry()
        self.tail_spot_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "tail_spot", frustum)
        self.head_spot_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "head_spot", frustum)
        self.line_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "line", line)
        self.text_drawable = hou.TextDrawable(scene_viewer, "text_drawable")
        self.text_params = {'text': None, 'translate': hou.Vector3(0.0, 0.0, 0.0)}
        self.spot_params = {'color1': color.getVec(), 'fade_factor': 0.5}
        self.line_params = {'line_width': 4.0, 'style': (10.0, 5.0), 'color1': color.getVec(),  'fade_factor':0.3}
        self.tail_pos = hou.Vector3(0.0, 0.0, 0.0)
        self.head_pos = hou.Vector3(0.0, 0.0, 0.0)
        self.spot_size = 0.01
        self.measurement = 0.0
        self.font_size = Measurement.default_font_size
        self.font_color = color.getHexStr()
        self.text = Measurement.default_text
        self.updateTextField()

    def show(self, visible):
        """ Display or hide drawables.
        """
        self.text_drawable.show(visible)
        self.tail_spot_drawable.show(visible)
        self.head_spot_drawable.show(visible)
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

    def updateTextField(self):
        font_string = '<font size="{1}" color="{2}"><b> {0} </b></font>'.format(self.text, self.font_size, self.font_color)
        self.text_params['text'] = font_string

    def draw( self, handle ):
        """ This callback is used for rendering the drawables
        """
        hou.GeometryDrawable.draw(self.line_drawable, handle, self.line_params)
        hou.GeometryDrawable.draw(self.tail_spot_drawable, handle, self.spot_params)
        hou.GeometryDrawable.draw(self.head_spot_drawable, handle, self.spot_params)
        hou.TextDrawable.draw(self.text_drawable, handle, self.text_params)

    def drawInterrupt(self, handle, geometry_viewport):
        screen_pos = hou.GeometryViewport.mapToScreen(geometry_viewport, self.head_pos)
        self.setTextPos(screen_pos[0], screen_pos[1])
        hou.GeometryDrawable.draw(self.line_drawable, handle, self.line_params)
        hou.GeometryDrawable.draw(self.tail_spot_drawable, handle, self.spot_params)
        hou.GeometryDrawable.draw(self.head_spot_drawable, handle, self.spot_params)
        hou.TextDrawable.draw(self.text_drawable, handle, self.text_params)

    def setSpotTransform(self, drawable, model_to_camera, camera_to_ndc):
        initToCurDir = (self.head_pos - self.tail_pos).normalized()
        if (drawable == self.tail_spot_drawable):
            initToCurDir *= -1
            translate = hou.hmath.buildTranslate(self.tail_pos)
        else:
            translate = hou.hmath.buildTranslate(self.head_pos)
        rotate = hou.hmath.buildRotateZToAxis(initToCurDir)
        model_to_ndc = translate * model_to_camera * camera_to_ndc
        w = model_to_ndc.at(3, 3)
        if (w == 1): # this checks for orthogonality of the matrix. does not feel very robust tho...
            w = 2 / abs(camera_to_ndc.at(0,0)) #scale ~* orthowidth
        w *= self.spot_size
        scale = hou.hmath.buildScale(w, w, w)
        transfrom = rotate * scale * translate
        hou.GeometryDrawable.setTransform(drawable, transfrom)

    def setLineTransform(self, drawable):
        initToCurDir = (self.head_pos - self.tail_pos).normalized()
        rotate = hou.hmath.buildRotateZToAxis(initToCurDir)
        translate = hou.hmath.buildTranslate(self.tail_pos)
        scale = hou.hmath.buildScale(self.measurement, self.measurement, self.measurement)
        transform = rotate * scale * translate
        hou.GeometryDrawable.setTransform(drawable, transform)

    def setTailPos(self, pos):
        self.tail_pos = pos

    def updateHeadPos(self, pos):
        self.head_pos = pos 
        self.measurement = (pos - self.tail_pos).length()

    def updateText(self, screen_pos):
        self.setTextPos(screen_pos[0], screen_pos[1])
        self.setText(str(self.measurement))

    def updateDrawables(self, model_to_camera, camera_to_ndc):
        self.setSpotTransform(self.tail_spot_drawable, model_to_camera, camera_to_ndc)
        self.setSpotTransform(self.head_spot_drawable, model_to_camera, camera_to_ndc)
        self.setLineTransform(self.line_drawable)

    def update(self, intersection_pos, screen_pos, model_to_camera, camera_to_ndc):
        self.updateHeadPos(intersection_pos)
        self.updateText(screen_pos)
        self.updateDrawables(model_to_camera, camera_to_ndc)

class MeasurementContainer(object):
    colors = (
            Color(Color.green), Color(Color.yellow),
            Color(Color.pink), Color(Color.purple))

    def __init__(self):
        self.measurements = []

    def showAll(self):
        for m in self.measurements: 
            m.show(True)

    def hideAll(self):
        for m in self.measurements: 
            m.show(False)

    def count(self):
        return len(self.measurements)

    def addMeasurement(self, scene_viewer):
        colorIndex = self.count() % len(MeasurementContainer.colors)
        self.measurements.append(Measurement(scene_viewer, MeasurementContainer.colors[colorIndex]))
        self.measurements[-1].show(False)

    def draw(self, handle):
        for m in self.measurements:
            m.draw(handle)

    def drawInterrupt(self, handle, geometry_viewport):
        for m in self.measurements:
            m.drawInterrupt(handle, geometry_viewport)

    def current(self):
        if self.count() < 1: 
            raise hou.Error("No measurements available!") #this check is for debugging. we should never be in this place if things work correctly.
        return self.measurements[-1]

    def setCurrentTailPos(self, pos):
        self.current().setTailPos(pos)

    def updateCurrent(self, intersection_pos, screen_pos, model_to_camera, camera_to_ndc):
        self.current().update(intersection_pos, screen_pos, model_to_camera, camera_to_ndc)

class State(object):
    msg = "Click and drag on the geometry to measure it."
    planes = (hou.Vector3(1, 0, 0), hou.Vector3(0, 1, 0), hou.Vector3(0, 0, 1))

    def __init__(self, state_name, scene_viewer):
        self.state_name = state_name
        self.scene_viewer = scene_viewer
        self.geometry_viewport = hou.SceneViewer.curViewport(self.scene_viewer)
        self.geo_intersector = None
        self.geometry = None
        self.measurements = MeasurementContainer()
        self.current_node = None
        self.show(False)
                
    def show(self, visible):
        """ Display or hide drawables.
        """
        if visible: 
            self.measurements.showAll()
        else:
            self.measurements.hideAll()

    def getMousePos(self, ui_event):
        device = hou.UIEvent.device(ui_event)
        return device.mouseX(), device.mouseY()

    def findBestPlane(self, ray):
        ray = (abs(ray[0]), abs(ray[1]), abs(ray[2]))
        index = ray.index(max(ray))
        return State.planes[index]

    def intersectWithPlane(self, origin, ray):
        plane = self.findBestPlane(ray)
        return hou.hmath.intersectPlane(hou.Vector3(0, 0, 0), plane, origin, ray)
        
    def getIntersectionPos(self, ui_event):
        (origin, ray) = hou.ViewerEvent.ray(ui_event)
        if self.geo_intersector.intersect(origin, ray):
            if self.geo_intersector.snapped:
                return self.geo_intersector.snapped_position
            else:
                return self.geo_intersector.position
        else:
            return self.intersectWithPlane(origin, ray)

    def worldToScreen(self, pos):
        return hou.GeometryViewport.mapToScreen(self.geometry_viewport, pos)

    def getModelToNDC(self):
        model_to_camera = hou.GeometryViewport.cameraToModelTransform(self.geometry_viewport).inverted()
        camera_to_ndc = hou.GeometryViewport.ndcToCameraTransform(self.geometry_viewport).inverted()
        return model_to_camera * camera_to_ndc

    def getModelToCamera(self):
        model_to_camera = hou.GeometryViewport.cameraToModelTransform(self.geometry_viewport).inverted()
        return model_to_camera

    def getCameraToNDC(self):
        camera_to_ndc = hou.GeometryViewport.ndcToCameraTransform(self.geometry_viewport).inverted()
        return camera_to_ndc

    def onGenerate(self, kwargs):
        """ Assign the geometry to drawabled
        """
        self.measurement = 0.0;
        self.scene_viewer.setPromptMessage( State.msg )
        self.current_node = hou.SceneViewer.currentNode(self.scene_viewer)
        self.geometry = hou.SopNode.geometry(self.current_node)
        self.geo_intersector = su.GeometryIntersector(self.geometry, self.scene_viewer)

    def onResume(self, kwargs):
        self.scene_viewer.setPromptMessage( State.msg )
        self.current_node = hou.SceneViewer.currentNode(self.scene_viewer)
        self.geometry = hou.SopNode.geometry(self.current_node)
        self.geo_intersector = su.GeometryIntersector(self.geometry, self.scene_viewer)

    def onExit(self, kwargs):
        hou.SceneViewer.clearPromptMessage(self.scene_viewer)
        self.show(False)

    def onInterrupt(self,kwargs):
        pass

    def onMouseActive(self, ui_event):
        print "Intersector snap mode"
        print self.geo_intersector.snap_mode
        world_pos = self.getIntersectionPos(ui_event)
        screen_pos = self.worldToScreen(world_pos)
        self.measurements.updateCurrent(world_pos, screen_pos, self.getModelToCamera(), self.getCameraToNDC())
        self.show(True)

    def onMouseStart(self, ui_event):
        self.measurements.addMeasurement(self.scene_viewer)
        intersection_pos = self.getIntersectionPos(ui_event)
        self.measurements.setCurrentTailPos(intersection_pos)

    def onMouseEvent(self, kwargs):
        ui_event = kwargs["ui_event"]
        reason = hou.UIEvent.reason(ui_event)
        if (reason == hou.uiEventReason.Start):
            self.onMouseStart(ui_event)
        elif (reason == hou.uiEventReason.Active):
            self.onMouseActive(ui_event)
#        else:
#            self.show(False)

    def onDraw( self, kwargs ):
        """ This callback is used for rendering the drawables
        """
        handle = kwargs["draw_handle"]
        self.measurements.draw(handle)

    def onDrawInterrupt(self, kwargs):
        handle = kwargs["draw_handle"]
        self.measurements.drawInterrupt(handle, self.geometry_viewport)

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
