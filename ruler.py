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

class State(object):
    MSG = "Move the mouse over the geometry."

    def __init__(self, state_name, scene_viewer):
        self.state_name = state_name
        self.scene_viewer = scene_viewer

        # A drawable to display the mouse coordinates at the cursor 
        # position.
        # Use su.CursorLabel.setLabel to display a fix label.
        self.cursor = su.CursorLabel(scene_viewer, "cursor")
        
        # Drawable for drawing the polygon under the cursor.
        self.face = hou.GeometryDrawable(self.scene_viewer, 
            hou.drawableGeometryType.Face, 
            "face", 
            params = {
                "style": hou.drawableGeometryFaceStyle.Plain,
                "color1": (0.0,1.0,0.0,1.0) }
        )
                
    def show(self, visible):
        """ Display or hide drawables.
        """
        self.cursor.show(visible)
        self.face.show(visible)

    def onEnter(self, kwargs):
        """ Assign the geometry to drawabled
        """
        node = kwargs["node"]
        self.geometry = node.geometry()
        self.show(True)

        self.scene_viewer.setPromptMessage( State.MSG )

    def onResume(self, kwargs):
        self.show(True)
        self.scene_viewer.setPromptMessage( State.MSG )

    def onInterrupt(self,kwargs):
        self.show(False)

    def onMouseEvent(self, kwargs):
        """ Computes the cursor text position and drawable geometry
        """
        # set the cursor label
        self.cursor.setParams(kwargs)

        # Set the drawable with the polygon under the cursor
        ui_event = kwargs["ui_event"]
        (origin, dir) = ui_event.ray()        
        gi = su.GeometryIntersector(self.geometry)
        gi.intersect(origin, dir, snapping=False)

        if gi.prim_num != -1 and gi.prim_num != self.poly_id:
            self.poly_id = gi.prim_num
    
            # Construct a new geometry
            poly_points = self.geometry.prim(self.poly_id).points()                                                                      
            poly_geo = hou.Geometry()
            poly = poly_geo.createPolygon()
            for pt in poly_points:
                point = poly_geo.createPoint()
                point.setPosition(pt.position())
                poly.addVertex(point)        

            # update the drawable                
            self.face.setGeometry(poly_geo)
            self.show(True)
                
        elif gi.prim_num == -1:
            # no polygon under the cursor
            self.poly_id = -1
            self.poly_geo = None            
            self.face.show(False)

    def onDraw( self, kwargs ):
        """ This callback is used for rendering the drawables
        """
        handle = kwargs["draw_handle"]

        self.face.draw(handle) 
        self.cursor.draw(kwargs)


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
