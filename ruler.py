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
import math as m

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

def createPointGeometry():
    geo = hou.Geometry()
    point = hou.Geometry.createPoint(geo)
    return geo;

def createCircleGeometry():
    geo = hou.Geometry()
    circle_verb = hou.sopNodeTypeCategory().nodeVerb("circle")
    hou.SopVerb.setParms(circle_verb, {
        'type':1, 'divs':12})
    hou.SopVerb.execute(circle_verb, geo, [])
    hou.Geometry.addAttrib(geo, hou.attribType.Point, "Cd", (1, 0, 0))
    return geo

# TODO: Implement a colored background behind the tail and end to 
#       show that it is being axis aligned. maybe highlight geometry in so-
#       me similar way around the spot your measuring from

def makeConcentricDisk(parms):
    r = parms["radius"]
    divs = parms["divs"]
    arcs = parms["arcs"]
    pi = m.pi
    arc_len = 2 * pi / arcs
    div_len = r / float(divs)
    for i in range(divs):
        for j in range(arcs):
            point = hou.Geometry.createPoint(geo)
            pos = hou.Vector3(m.cos(j * arc_len), m.sin(j * arc_len), 0.0) * i * div_len
            hou.Point.setPosition(point, pos)

class DiskMaker(object):
    def __init__(self, radius, divs, arcs, color, gamma):
        self.parms = {"radius": radius, "divs":divs, "arcs":arcs, "geo":None, "color": color, "gamma":gamma}

    def createAttribs(self, geo):
        hou.Geometry.addAttrib(geo, hou.attribType.Point, "Cd", (1.0, 1.0, 1.0))
        hou.Geometry.addAttrib(geo, hou.attribType.Point, "Alpha", 1.0)
        
    def makePoints(self, geo, r, divs, arcs, color, gamma):
        self.createAttribs(geo)
        pi = m.pi
        arc_len = 2 * pi / arcs
        div_len = r / float(divs)
        
        point0 = hou.Geometry.createPoint(geo)
        hou.Point.setAttribValue(point0, "Cd", color)
        hou.Point.setAttribValue(point0, "Alpha", 1.0)
        for i in range(1, divs):
            alpha = pow(1 - (float(i) / divs), gamma)
            for j in range(arcs):
                point = hou.Geometry.createPoint(geo)
                pos = hou.Vector3(m.cos(j * arc_len), m.sin(j * arc_len), 0.0) * i * div_len
                hou.Point.setPosition(point, pos)
                hou.Point.setAttribValue(point, "Cd", color)
                hou.Point.setAttribValue(point, "Alpha", alpha)
                
    def makeFirstRing(self, geo, arcs):
        points = hou.Geometry.points(geo)
        p0 = points[0]
        for i in range(1, arcs):
            prim = hou.Geometry.createPolygon(geo)
            hou.Polygon.addVertex(prim, points[0])
            hou.Polygon.addVertex(prim, points[i])
            hou.Polygon.addVertex(prim, points[i+1])
        prim = hou.Geometry.createPolygon(geo)
        hou.Polygon.addVertex(prim, points[0])
        hou.Polygon.addVertex(prim, points[arcs])
        hou.Polygon.addVertex(prim, points[1])
        
    def makeOtherRings(self, geo, arcs, divs):
        points = hou.Geometry.points(geo)
        for i in range(1, divs - 1):
            for j in range(1, arcs):
                p0 = points[ j + arcs * (i - 1) ]
                p3 = points[ j + 1 + arcs * (i - 1) ]
                p1 = points[ j + arcs * i ]
                p2 = points[ j + 1 + arcs * i ]
                prim = hou.Geometry.createPolygon(geo)
                hou.Polygon.addVertex(prim, p0)
                hou.Polygon.addVertex(prim, p1)
                hou.Polygon.addVertex(prim, p2)
                hou.Polygon.addVertex(prim, p3)
            p0 = points[ arcs + arcs * (i - 1) ]
            p3 = points[ 1 + arcs * (i - 1) ]
            p1 = points[ arcs + arcs * i ]
            p2 = points[ 1 + arcs * i ]
            prim = hou.Geometry.createPolygon(geo)
            hou.Polygon.addVertex(prim, p0)
            hou.Polygon.addVertex(prim, p1)
            hou.Polygon.addVertex(prim, p2)
            hou.Polygon.addVertex(prim, p3)
                
    def makePrims(self, geo, arcs, divs):
        self.makeFirstRing(geo, arcs)
        self.makeOtherRings(geo, arcs, divs)

    def makeDiskImp(self, parms):
        color = parms["color"]
        geo = parms["geo"]
        r = parms["radius"]
        divs = parms["divs"]
        arcs = parms["arcs"]
        gamma = parms["gamma"]
        self.makePoints(geo, r, divs, arcs, color, gamma)
        self.makePrims(geo, arcs, divs)

    def setColor(self, color):
        self.parms["color"] = color
        print color

    def makeDisk(self, direction, color):
        self.setColor(color)
        geo = hou.Geometry()
        self.parms["geo"] = geo
        self.makeDiskImp(self.parms)
        rotate = hou.hmath.buildRotateZToAxis(hou.Vector3(direction))
        hou.Geometry.transform(geo, rotate)
        return geo

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


class Plane:
    X, Y, Z = range(0, 3)

class Measurement(object):
    default_font_size = 30.0
    default_text = "default text"
    disk_maker = DiskMaker(10, 8, 20, (1.0, 1.0, 1.0), 3)

    def __init__(self, scene_viewer, color):
        sphere = createSphereGeometry()
        line = createLineGeometry()
        frustum = createFrustumGeometry()
        point = createPointGeometry()
        circle = createCircleGeometry()
        self.disk_x = Measurement.disk_maker.makeDisk((1, 0, 0), (.7, .2, .2))
        self.disk_y = Measurement.disk_maker.makeDisk((0, 1, 0), (.2, .7, .2))
        self.disk_z = Measurement.disk_maker.makeDisk((0, 0, 1), (.2, .2, .7))
        self.scene_viewer = scene_viewer
        self.tail_spot_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "tail_spot", frustum)
        self.head_spot_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "head_spot", frustum)
        self.line_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "line", line)
        self.point_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Point, "point", point)
        self.tail_disk_drawable = None
        self.head_disk_drawable = None
        self.text_drawable = hou.TextDrawable(scene_viewer, "text_drawable")
        self.text_params = {'text': None, 'translate': hou.Vector3(0.0, 0.0, 0.0)}
        self.spot_params = {'color1': color.getVec(), 'fade_factor': 0.5}
        self.line_params = {'line_width': 4.0, 'style': (10.0, 5.0), 'color1': color.getVec(),  'fade_factor':0.3}
        self.point_params = {'style': hou.drawableGeometryPointStyle.LinearCircle, 'radius': 25.5}
        self.tail_pos = hou.Vector3(0.0, 0.0, 0.0)
        self.head_pos = hou.Vector3(0.0, 0.0, 0.0)
        self.spot_size = 0.01
        self.measurement = 0.0
        self.font_size = Measurement.default_font_size
        self.font_color = color.getHexStr()
        self.text = Measurement.default_text
        self.curPlane = None
        self.angle_snapping = False
        self.updateTextField()

    def getLength(self):
        return self.measurement

    def getTailPos(self):
        return self.tail_pos

    def getDir(self):
        return hou.Vector3.normalized(self.head_pos - self.tail_pos)

    def show(self, visible):
        """ Display or hide drawables.
        """
        self.text_drawable.show(visible)
        self.tail_spot_drawable.show(visible)
        self.head_spot_drawable.show(visible)
        self.line_drawable.show(visible)
        self.point_drawable.show(visible)
        if self.tail_disk_drawable != None:
            self.tail_disk_drawable.show(visible)
        if self.head_disk_drawable != None:
            self.head_disk_drawable.show(visible)

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
        if self.tail_disk_drawable != None:
            hou.GeometryDrawable.draw(self.tail_disk_drawable, handle)
        if self.head_disk_drawable != None:
            hou.GeometryDrawable.draw(self.head_disk_drawable, handle)
        hou.GeometryDrawable.draw(self.line_drawable, handle, self.line_params)
        hou.GeometryDrawable.draw(self.tail_spot_drawable, handle, self.spot_params)
        hou.GeometryDrawable.draw(self.head_spot_drawable, handle, self.spot_params)
        hou.TextDrawable.draw(self.text_drawable, handle, self.text_params)

    def drawInterrupt(self, handle, geometry_viewport):
        screen_pos = hou.GeometryViewport.mapToScreen(geometry_viewport, self.head_pos)
        self.setTextPos(screen_pos[0], screen_pos[1])
        if self.tail_disk_drawable != None:
            hou.GeometryDrawable.draw(self.tail_disk_drawable, handle)
        if self.head_disk_drawable != None:
            hou.GeometryDrawable.draw(self.head_disk_drawable, handle)
        hou.GeometryDrawable.draw(self.line_drawable, handle, self.line_params)
        hou.GeometryDrawable.draw(self.tail_spot_drawable, handle, self.spot_params)
        hou.GeometryDrawable.draw(self.head_spot_drawable, handle, self.spot_params)
        hou.TextDrawable.draw(self.text_drawable, handle, self.text_params)

    def getCameraCancellingScale(self, translate, model_to_camera, camera_to_ndc):
        model_to_ndc = translate * model_to_camera * camera_to_ndc
        w = model_to_ndc.at(3, 3)
        if (w == 1): # this checks for orthogonality of the matrix. does not feel very robust tho...
            w = 2 / abs(camera_to_ndc.at(0,0)) #scale ~* orthowidth
        w *= self.spot_size
        scale = hou.hmath.buildScale(w, w, w)
        return scale

    def setPlane(self, plane):
        self.curPlane = plane

    def angleSnapping(self, yes):
        if (yes):
            self.angle_snapping = True
            print "Angle snapping on"
        else:
            self.angle_snapping = False
            print "Angle snapping off"

    def setSpotTransform(self, drawable, model_to_camera, camera_to_ndc):
        initToCurDir = (self.head_pos - self.tail_pos).normalized()
        if (drawable == self.tail_spot_drawable):
            initToCurDir *= -1
            translate = hou.hmath.buildTranslate(self.tail_pos)
        else:
            translate = hou.hmath.buildTranslate(self.head_pos)
        rotate = hou.hmath.buildRotateZToAxis(initToCurDir)
        scale = self.getCameraCancellingScale(translate, model_to_camera, camera_to_ndc)
        transform = rotate * scale * translate
        hou.GeometryDrawable.setTransform(drawable, transform)

    def setPointTransform(self, pos):
        translate = hou.hmath.buildTranslate(pos)
        hou.GeometryDrawable.setTransform(self.point_drawable, translate)

    def setDiskTransform(self, disk, pos, model_to_camera, camera_to_ndc):
        translate = hou.hmath.buildTranslate(pos)
        scale = self.getCameraCancellingScale(translate, model_to_camera, camera_to_ndc)
        transform = scale * translate
        hou.GeometryDrawable.setTransform(disk, transform)

    def setLineTransform(self, drawable):
        initToCurDir = (self.head_pos - self.tail_pos).normalized()
        rotate = hou.hmath.buildRotateZToAxis(initToCurDir)
        translate = hou.hmath.buildTranslate(self.tail_pos)
        scale = hou.hmath.buildScale(self.measurement, self.measurement, self.measurement)
        transform = rotate * scale * translate
        hou.GeometryDrawable.setTransform(drawable, transform)

    def setTailPos(self, pos):
        self.tail_pos = pos

    def setTailDisk(self, plane, scene_viewer,  model_to_camera, camera_to_ndc):
        if plane == Plane.X: self.tail_disk_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "circle", self.disk_x)
        if plane == Plane.Y: self.tail_disk_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "circle", self.disk_y)
        if plane == Plane.Z: self.tail_disk_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "circle", self.disk_z)
        self.setDiskTransform(self.tail_disk_drawable, self.tail_pos, model_to_camera, camera_to_ndc)

    def setHeadDisk(self, plane, scene_viewer):
        if plane == Plane.X: 
            self.head_disk_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "circle", self.disk_x)
        elif plane == Plane.Y: 
            self.head_disk_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "circle", self.disk_y)
        elif plane == Plane.Z: 
            self.head_disk_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "circle", self.disk_z)
        else:
            print "Should not be called"

    def updateHeadPos(self, pos):
        self.head_pos = pos 
        self.measurement = (pos - self.tail_pos).length()

    def updateText(self, screen_pos):
        self.setTextPos(screen_pos[0], screen_pos[1])
        self.setText(str(self.measurement))

    def updateDrawables(self, model_to_camera, camera_to_ndc, plane, scene_viewer):
        self.setSpotTransform(self.tail_spot_drawable, model_to_camera, camera_to_ndc)
        self.setSpotTransform(self.head_spot_drawable, model_to_camera, camera_to_ndc)
        self.setLineTransform(self.line_drawable)
        self.setPointTransform(self.tail_pos)
        if (plane == None):
            self.head_disk_drawable = None
            return
#        if plane != self.curPlane:
#            self.curPlane = plane
        self.setHeadDisk(plane, scene_viewer)
        self.setDiskTransform(self.head_disk_drawable, self.head_pos, model_to_camera, camera_to_ndc)

    def update(self, intersection, screen_pos, model_to_camera, camera_to_ndc, scene_viewer):
        self.updateHeadPos(intersection.pos)
        self.updateText(screen_pos)
        if (intersection.plane != None):
            self.updateDrawables(model_to_camera, camera_to_ndc, self.curPlane, scene_viewer)
        else:
            self.updateDrawables(model_to_camera, camera_to_ndc, None, scene_viewer)

class MeasurementContainer(object):
    colors = (
            Color(Color.green), Color(Color.yellow),
            Color(Color.pink), Color(Color.purple))

    def __init__(self, viewport):
        self.measurements = []
        self.viewport = viewport

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

    def removeMeasurement(self):
        if self.count() < 1: return
        colorIndex = (self.count() - 1) % len(MeasurementContainer.colors)
        self.current().show(False)
        self.measurements.pop()
        hou.GeometryViewport.draw(self.viewport)

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

    def __getitem__(self, index):
        return self.measurements[index]

class Intersection():
    def __init__(self, pos, plane):
        self.pos = pos
        self.has_plane = (plane != None)
        self.plane = plane

class Key():
    copy_to_clip = 113 # q
    undo = 122 # z
    create_line_sops = 97 # a

class State(object):
    msg = "Click and drag on the geometry to measure it."
    planes = (hou.Vector3(1, 0, 0), hou.Vector3(0, 1, 0), hou.Vector3(0, 0, 1))

    def __init__(self, state_name, scene_viewer):
        self.state_name = state_name
        self.scene_viewer = scene_viewer
        self.geometry_viewport = hou.SceneViewer.curViewport(self.scene_viewer)
        self.geo_intersector = None
        self.geometry = None
        self.measurements = MeasurementContainer(self.geometry_viewport)
        self.current_node = None
        self.curPlane = None
        self.show(False)
        self.angle_snapping = False
                
    def show(self, visible):
        """ Display or hide drawables.
        """
        if visible: 
            self.measurements.showAll()
        else:
            self.measurements.hideAll()

    def createSop(self, measurement):
        network = hou.SceneViewer.pwd(self.scene_viewer)
        line_node = hou.Node.createNode(network, "line")
        length_parm = hou.SopNode.parm(line_node, "dist")
        origin_parm = hou.SopNode.parmTuple(line_node, "origin")
        dir_parm = hou.SopNode.parmTuple(line_node, "dir")
        hou.Parm.set(length_parm, measurement.getLength())
        hou.ParmTuple.set(origin_parm, measurement.getTailPos())
        hou.ParmTuple.set(dir_parm, measurement.getDir())
        hou.Node.moveToGoodPosition(line_node)

    def createSops(self):
        for measurement in self.measurements:
            self.createSop(measurement)

    def getMousePos(self, ui_event):
        device = hou.UIEvent.device(ui_event)
        return device.mouseX(), device.mouseY()

    def findBestPlane(self, ray):
        ray = (abs(ray[0]), abs(ray[1]), abs(ray[2]))
        index = ray.index(max(ray))
        return index

    def intersectWithPlane(self, origin, ray):
        return Intersection(hou.hmath.intersectPlane(hou.Vector3(0, 0, 0), State.planes[self.curPlane], origin, ray), self.curPlane)

    def getIntersectionRegular(self, ui_event):
        snapping_dict = hou.ViewerEvent.snappingRay(ui_event)
        origin = snapping_dict["origin_point"]
        ray = snapping_dict["direction"]
        if self.geo_intersector.intersect(origin, ray):
            if self.geo_intersector.snapped:
                return Intersection(self.geo_intersector.snapped_position, None)
            else:
                return Intersection(self.geo_intersector.position, None)
        else:
            return self.intersectWithPlane(origin, ray)

    def getIntersectionAngleSnap(self, ui_event):
        return Intersection(hou.Vector3(0,0,0), None)

    def getIntersection(self, ui_event):
        if self.angle_snapping:
            return self.getIntersectionAngleSnap(ui_event)
        else:
            return self.getIntersectionRegular(ui_event)

    def setMeasurementPlane(self, ui_event):
        snapping_dict = hou.ViewerEvent.snappingRay(ui_event)
        snap_mode = self.scene_viewer.snappingMode()
        cur_viewport = hou.SceneViewer.curViewport(self.scene_viewer)
        vt = hou.GeometryViewport.type(cur_viewport)
        if snap_mode == hou.snappingMode.Grid:
            if vt == hou.geometryViewportType.Perspective or vt == hou.geometryViewportType.Top or vt == hou.geometryViewportType.Bottom:
                plane = Plane.Y
            if vt == hou.geometryViewportType.Front or vt == hou.geometryViewportType.Back:
                plane = Plane.Z
            if vt == hou.geometryViewportType.Left or vt == hou.geometryViewportType.Right:
                plane = Plane.X
        else:
            ray = snapping_dict["direction"]
            plane = self.findBestPlane(ray)
        self.measurements.current().setPlane(plane)
        self.curPlane = plane

    def angleSnapping(self, yes):
        self.measurements.current().angleSnapping(yes)
        self.angle_snapping = yes

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

    def removeMeasurement(self):
        self.measurements.removeMeasurement()

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
        intersection = self.getIntersection(ui_event)
        screen_pos = self.worldToScreen(intersection.pos)
        self.measurements.current().update(intersection, screen_pos, self.getModelToCamera(), self.getCameraToNDC(), self.scene_viewer)
        self.show(True)

    def onMouseStart(self, ui_event):
        self.measurements.addMeasurement(self.scene_viewer)
        self.setMeasurementPlane(ui_event)
        intersection = self.getIntersection(ui_event)
        self.measurements.current().setTailPos(intersection.pos)
        if intersection.plane != None:
            self.measurements.current().setTailDisk(intersection.plane, self.scene_viewer, self.getModelToCamera(), self.getCameraToNDC())

    def onMouseEvent(self, kwargs):
        ui_event = kwargs["ui_event"]
        reason = hou.UIEvent.reason(ui_event)
        if (reason == hou.uiEventReason.Start):
            hou.SceneViewer.beginStateUndo(self.scene_viewer, "foo")
            self.onMouseStart(ui_event)
        elif (reason == hou.uiEventReason.Active):
            self.onMouseActive(ui_event)
        elif (reason == hou.uiEventReason.Changed):
            self.curPlane = None
            hou.SceneViewer.endStateUndo(self.scene_viewer)

    def onKeyEvent(self, kwargs):
        ui_event = kwargs["ui_event"]
        device = ui_event.device()
        if device.isKeyPressed():
            if device.keyValue() == Key.undo:
                self.measurements.removeMeasurement()
                return True
            if device.keyValue() == Key.copy_to_clip:
                m = self.measurements.current().getLength()
                hou.ui.copyTextToClipboard(str(m))
                return True
            if device.keyValue() == Key.create_line_sops:
                self.createSops()
        return False 

    def onKeyTransitEvent(self, kwargs):
        ui_event = kwargs['ui_event']
        dev = ui_event.device()
        if dev.isKeyDown() and dev.isCtrlKey(): 
            self.angleSnapping(True)
        if dev.isKeyUp() and self.angle_snapping: 
            self.angleSnapping(False)
            
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
