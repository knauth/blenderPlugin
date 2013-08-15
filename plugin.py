import bpy
import math
import mathutils
import os
import yaml
#TODO: shader selection inside blender?

#TODO:
#currently using rough heuristics for ScreenWindow (sun shadows) and light intensity. Improve

# be able to add materials to it
# click and have all the scripts built
# one proxy object per type in a data column
# one script that prepares for cluster
# one script that does one frame for you

# TODO: currently all objects represented by one proxy must have the SAME GEOMETRY
# eg. sphere radius 3, cannot also have spheres of radius 2
#
#OTHER NEEDED/WANTED INFO:
# camera loc, filepath, scaling factor, frame range, data file

#TODO: actually take input from blender for the export (a menu or something) colors and textures
#TODO: seclecting which proxys and which objs from a blender menu
#TODO: Why is renderman's window larger than blender's for rendering
#some of the files
#TODO: prman has holes in the bottom of the cylinders, aqsis doesn't. Why?

#TODO: intensity level somehow
#TODO: shadows!
#TODO: shadows currently take objects with colors and shaders, kill this and save time!
#TODO: renderman multiple cores (qsub vs -p:16) vs renderman one instance per core
#TODO: shadow_pass .shd file is the same for all frames. Fix somehow

#TODO/CHECKLIST: make file format (pos, rot, geom type, dimensions, group, velocity, pressure
# in bitbucket 
# render the file. in blender(headless?), then using renderman 
# full animation
# fancier stuff (moving camra/lights or fancy materials (shadows, reflection, ambient and global illumination)


# Converts to video
# ffmpeg -f image2 -r 2 -i out.%01d.tif -c:v libx264  test.mp4

#Resolution and shading rate affect time and quality of render

bl_info = {
        "name": "Chrono::Render plugin",
        "description": "Allows for easy graphical manipulation of simulated data before rendering with a powerful renderman renderer",
        "author": "Daniel <Daphron> Kaczmarek",
        "version": (0, 7),
        "blender": (2, 67, 1), #TODO: find minimum version
        "location": "File > Import > Import Chrono::Engine",
        "warning": "",
        "wiki_url": "TODO",
        "tracker_url":"TODO",
        "category": "Import-Export"}

DEFAULT_COLOR = (0.4, 0.4, 0.6)

fin = ""
objects = ""
proxyObjects = ""
# max_dimensions = (0, 0, 0, 0, 0, 0) #x_min, x_max, y_min, y_max, z_min, z_max
max_dim = 1
min_dim = 1

class AmbientLightProxy:
    def __init__(self):
        self.material = self.create_material()
        self.obj = None

    def update(self):
        """Grabs stuff like color, texture and stores them"""
        #Color can be diffuse, specular, mirror, and subsurface scattering
        if self.obj.active_material is None:
            self.obj = bpy.context.scene.objects['Ambient Light Proxy']
        self.color = (self.obj.active_material.diffuse_color[0], self.obj.active_material.diffuse_color[1], self.obj.active_material.diffuse_color[2])

    def create_material(self):
        mat = bpy.data.materials.new("Ambient light proxy material")
        mat.diffuse_color = (0,0,0)
        mat.diffuse_shader = 'LAMBERT'
        mat.diffuse_intensity = 1.0
        mat.specular_color = (1.0, 1.0, 1.0)
        mat.specular_shader = 'COOKTORR'
        mat.specular_intensity = 0.5
        mat.alpha = 1.0
        mat.ambient = 1
        return mat

    def addToBlender(self):
        bpy.ops.mesh.primitive_monkey_add(location=(6, 6, 6))
        bpy.context.active_object.name = "Ambient Light Proxy"
        bpy.context.active_object.active_material = self.material
        self.obj = bpy.context.active_object
        
class Object:
    def __init__(self, data):
        # print("DATA:",data)
        self.group = data[0]
        self.index = int(data[1]) #The objects unique ID/index number
        #XYZ locations
        self.x = float(data[2])
        self.y = float(data[3])
        self.z = float(data[4])

        self.quat = mathutils.Quaternion((float(data[5]), float(data[6]), float(data[7]), float(data[8])))
        self.euler = tuple(a for a in self.quat.to_euler())

        self.obj_type = data[9].lower()

        #Extra parameters (specific to each object type)
        # test = []
        # for x in range(10,len(data)):
        #     if data[x] is not '\n':
        #         test.append(float(data[x]))
        self.ep = [float(data[x]) for x in range(10,len(data)) if data[x] is not '\n'] 

        self.color = DEFAULT_COLOR
        self.material = self.create_material()

    def create_material(self):
        mat = bpy.data.materials.new("Object {}'s material".format(self.index))
        mat.diffuse_color = self.color
        mat.diffuse_shader = 'LAMBERT'
        mat.diffuse_intensity = 1.0
        mat.specular_color = (1.0, 1.0, 1.0)
        mat.specular_shader = 'COOKTORR'
        mat.specular_intensity = 0.5
        mat.alpha = 1.0
        mat.ambient = 1
        return mat

    def addToBlender(self):
        # if self.index % 100 == 0:
            # print("index = {}".format(self.index))
        # Cube
        if self.obj_type == "cube":
            #ep[0] = length of one side
            bpy.ops.mesh.primitive_cube_add(radius=self.ep[0], location=(self.x, self.y, self.z), rotation=self.euler)
        #Box
        elif self.obj_type == "box":
            bpy.ops.mesh.primitive_cube_add(radius=1.0, location=(self.x, self.y, self.z))
            bpy.ops.transform.resize(value=(self.ep[0], self.ep[1], self.ep[2]))
            bpy.context.object.rotation_euler = mathutils.Euler(self.euler)
        # Cylinder
        elif self.obj_type == "cylinder":
            # ep[0] = radius of top, ep[1] = depth
            bpy.ops.mesh.primitive_cylinder_add(radius=self.ep[0], depth=self.ep[1], location=(self.x, self.y, self.z), rotation=self.euler)
        # Sphere
        elif self.obj_type == "sphere":
            # ep[0] = radius of the sphere
            # uv sphere looks nicer but icosphere might be the better route
            bpy.ops.mesh.primitive_uv_sphere_add(size=self.ep[0], location=(self.x, self.y, self.z), rotation=self.euler)
        # Ellipsoid
        elif self.obj_type == "ellipsoid":
            #ep[0] is the radius, ep[1] is the length in the direction of rotation
            bpy.ops.mesh.primitive_uv_sphere_add(size=1.0, location=(self.x, self.y, self.z))
            #The right way?
            bpy.ops.transform.resize(value=(self.ep[0],self.ep[1],self.ep[2]))
            bpy.context.object.rotation_euler = mathutils.Euler(self.euler)

        #Cone
        elif self.obj_type == "cone":
            # self.ep[0] = radius of cone bottom, self.ep[1] = height of cone
            bpy.ops.mesh.primitive_cone_add(radius1=self.ep[0], depth=self.ep[1], location=(self.x, self.y, self.z), rotation=self.euler)
        #Torus
        elif self.obj_type == "torus":
            bpy.ops.mesh.primitive_torus_add(rotation=self.euler, location=(self.x, self.y, self.z), major_radius=self.ep[0], minor_radius=self.ep[1])
        else:
            print("Object type {} is not currently supported as a primitive in the blender plugin")
 
        bpy.context.active_object["index"] = self.index
        bpy.context.active_object.name = "Obj # {}".format(self.index)
        bpy.context.active_object.active_material = self.material
        self.obj = bpy.context.active_object
        #object.get("index") to get the value
        #object["index"] doesn't work?

    def update(self):
        """Grabs stuff like color, texture and stores them"""
        try:
            self.obj = bpy.context.scene.objects['Obj # {}'.format(self.index)]
            self.color = (self.obj.active_material.diffuse_color[0], self.obj.active_material.diffuse_color[1], self.obj.active_material.diffuse_color[2])
            self.mat = self.obj.active_material
        except:
            import pdb; pdb.set_trace()

class ProxyObject(Object):
    def __init__(self, data, indicies):
        """ data is a line of the input file, indicies is a list of lines 
        from the file that this obj represents whichAttribute is a num which 
        specifies the column of data on the line that decides proxyObjs and 
        group tells the specifica group which this proxyObj is for 
        (sphere, cube...) """
        # print("MAKING PROXY OBJ")

        Object.__init__(self, data)
        self.indicies = indicies
        # print(self.group)
        self.color = DEFAULT_COLOR
        self.material.name = "Group {}'s material".format(self.group)

    def addToBlender(self):
        # print(self.ep)
        bpy.ops.mesh.primitive_monkey_add(radius=self.ep[0], location=(self.x, self.y, self.z))
        bpy.context.active_object["group"] = self.group
        bpy.context.active_object.name = "Proxy " + self.group
        bpy.context.active_object.active_material = self.material
        self.obj = bpy.context.active_object

    def update(self):
        try:
            self.obj = bpy.context.scene.objects['Proxy {}'.format(self.group)]
            self.color = (self.obj.active_material.diffuse_color[0], self.obj.active_material.diffuse_color[1], self.obj.active_material.diffuse_color[2])
            self.mat = self.obj.active_material
        except:
            import pdb; pdb.set_trace()

    # def update(self):
    #     """Grabs stuff like color, texture and stores them"""
    #     #Color can be diffuse, specular, mirror, and subsurface scattering
    #     if self.obj.active_material is not None:
    #         self.color = (self.obj.active_material.diffuse_color[0], self.obj.active_material.diffuse_color[1], self.obj.active_material.diffuse_color[2])
    #         self.mat = self.obj.active_material

def configInitialScene():
    # bpy.ops.object.delete()
    pass

class ImportChronoRender(bpy.types.Operator):
    """Import ChronoRender"""
    bl_idname = "import.import_chrono_render"
    bl_label = "Import ChronoRender"
    filename = bpy.props.StringProperty(subtype='FILE_PATH')
    directory = bpy.props.StringProperty(subtype='DIR_PATH')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def process_max_dimensions(self, data):
        global max_dim
        global min_dim
        max_length = max(float(data[x]) for x in range(10,len(data)) if data[x] is not '\n') 
        for coord in (data[2:5]):
            if float(coord) + max_length > max_dim:
                max_dim = float(coord) + max_length
            if float(coord) - max_length < min_dim:
                min_dim = float(coord) - max_length

    def execute(self, context):
        global fin_name
        global objects
        global proxyObjects
        global ambient_proxy
        # filename = "/home/xeno/repos/blender-plugin/plugins/blender/blender_input_test.dat"
        # individualObjectsIndicies = [1,2,3,4, 5, 6] #LINE NUMBERS

        objects = []
        proxyObjects = []

        fin_name = self.filename
        filepath = os.path.join(self.directory, self.filename)

        fin = open(filepath, "r")

        for i, line in enumerate(fin):
            self.process_max_dimensions(line.split(","))
            if line.split(",")[0].lower() == "individual":
                objects.append(Object(line.split(",")))
                print("Object {}".format(i))

            else:
                data = line.split(",")
                proxyExists = False
                for obj in proxyObjects:
                    if obj.group == data[0]:
                        obj.indicies.append(i+1)
                        proxyExists = True
                if not proxyExists:
                    print("New Proxy line num {}".format(i))
                    proxyObjects.append(ProxyObject(data, [i+1]))

        configInitialScene()

        for obj in objects:
            obj.addToBlender()
        for obj in proxyObjects:
            obj.addToBlender()

        ambient_proxy = AmbientLightProxy()
        ambient_proxy.addToBlender()
        print("objects added")
        return {'FINISHED'}

def add_importChronoRenderButton(self, context):
    self.layout.operator(
            ImportChronoRender.bl_idname,
            text=ImportChronoRender.__doc__,
            icon='PLUGIN')

class ExportChronoRender(bpy.types.Operator):
    """Exports to Chrono::Render"""
    bl_idname = "export.export_chrono_render"
    bl_label = "Export Chrono::Render"
    filename = bpy.props.StringProperty(subtype='FILE_PATH')
    directory = bpy.props.StringProperty(subtype='DIR_PATH')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def construct_condition(self, indicies):
        """docstring for construct_condition"""
        rtnd = "id == "
        if len(indicies) <= 0:
            raise Exception("No indicies in this proxy object")
        for i in indicies:
            rtnd += str(i) + " or id == "

        return rtnd[:-10] #-10 t remove the trailing or id ==

    def write_object(self, objects, is_proxy=False):
        renderobject = []
        for obj in objects:
            obj.update()
            name = obj.group

            #Start writing
            color = "{} {} {}".format(obj.color[0], obj.color[1], obj.color[2])

            data = dict()
            data["name"] = str(name)

            if is_proxy:
                data["condition"] = self.construct_condition(obj.indicies)

            else:
                maxIndex = obj.index
                minIndex = obj.index
                data["condition"] = "id >= {} and id <= {}".format(minIndex, maxIndex)

            data["color"] = color
            data["geometry"] = [{"type" : obj.obj_type}]
            data["shader"] = [{"name" : "matte.sl"}] #TODO: not hardcoded
            
            if obj.obj_type.lower() == "sphere":
                data["geometry"][0]["radius"] = obj.ep[0]
            elif obj.obj_type.lower() == "cube":
                data["geometry"][0]["side"] = obj.ep[0]
            elif obj.obj_type.lower() == "cone":
                data["geometry"][0]["radius"] = obj.ep[0]
                data["geometry"][0]["height"] = obj.ep[1]
            elif obj.obj_type.lower() == "cylinder":
                data["geometry"][0]["radius"] = obj.ep[0]
                data["geometry"][0]["height"] = obj.ep[1]
            elif obj.obj_type.lower() == "ellipsoid":
                data["geometry"][0]["a"] = obj.ep[0]
                data["geometry"][0]["b"] = obj.ep[1]
                data["geometry"][0]["c"] = obj.ep[2]
            elif obj.obj_type.lower() == "torus":
                data["geometry"][0]["rmajor"] = obj.ep[0]
                data["geometry"][0]["rminor"] = obj.ep[1]
            elif obj.obj_type.lower() == "box":
                data["geometry"][0]["xlength"] = obj.ep[0]
                data["geometry"][0]["ylength"] = obj.ep[1]
                data["geometry"][0]["zlength"] = obj.ep[2]
            else:
                print("Geometry type {} not supported by blender export at this time".format(obj.obj_type))

            if not obj.obj.hide_render:
                renderobject.append(data)

        return renderobject

    def camera_to_renderman(self, context, obj):
        camera_matrix = obj.matrix_world
        camera = obj
        camera_loc = obj.location
        camera_euler = obj.rotation_euler

        fov = None
        try:
            cam_fov = math.degrees(obj.data.angle)
            fov = 360.0*math.atan(16.0/camera.data.lens)/math.pi 
        except AttributeError:
            if hasattr(obj.data, "spot_size"):
                fov = math.degrees(obj.data.spot_size)
            else:
                pass

        out = ''

        if hasattr(obj.data, "type"):
            if obj.data.type == 'SUN':
                out += ('Projection "orthographic"\n')
            else:
                out += ('Projection "perspective" "fov" [{}]\n'.format(fov))
        else:
            out += ('Projection "perspective" "fov" [{}]\n'.format(fov))
            
        out += ("Scale 1 1 -1\n")
        out += ("Rotate {} 1 0 0\n".format(-math.degrees(camera_euler[0])))
        out += ("Rotate {} 0 1 0\n".format(-math.degrees(camera_euler[1])))
        out += ("Rotate {} 0 0 1\n".format(-math.degrees(camera_euler[2])))
        out += ("Translate {} {} {}\n".format(-camera_matrix[0][3],
                                                    -camera_matrix[1][3],
                                                    -camera_matrix[2][3]))
        return out
    
    def write_shadowspot(self, context, renderpasses, light_file, obj, end_x, end_y, end_z, delta_angle, index):
        name = "shadow_" + obj.data.name 
        name = name.replace(".", "_")
        shadowmap_name = name + ".rib"
        shadowmap_file_path = os.path.join(self.directory, shadowmap_name)
        shadowmap_file = open(shadowmap_file_path, 'w')
        shadowmap_file.write(self.camera_to_renderman(context, obj))

        light_string = 'LightSource "shadowspot" {} "intensity" {}  "coneangle" {} "conedeltaangle" {} "lightcolor" [{} {} {}] "from" [{} {} {}] "to" [{} {} {}] "shadowname" ["{}"]\n'.format(index, obj.data.energy*30, obj.data.spot_size/2.0, delta_angle, obj.data.color[0], obj.data.color[1], obj.data.color[2], obj.location.x, obj.location.y, obj.location.z, end_x+obj.location.x, end_y+obj.location.y, end_z+obj.location.z, name+".shd")
        light_file.write(light_string)

        #TODO: heuristic for resolution of pass
        shadowpass = {
                    "name": "shadowpass" + str(index),
                    "type": "shadow",
                    "settings" : {
                        "resolution" : "512 512 1",
                        "shadingrate" : 1.0,
                        "pixelsamples" : "1 1",
                        "shadowfilepath" : "shadow_" + obj.data.name + ".rib",
                        "display" : {"output" : "shadow_" + obj.data.name + ".z",
                                    "outtype" : "zfile",
                                    "mode" : "z"}}}
        renderpasses.append(shadowpass)

    def write_sun(self, context, renderpasses, light_file, obj, end_x, end_y, end_z, index):
        global max_dim
        global min_dim
        name = "shadow_" + obj.data.name 
        name = name.replace(".", "_")
        shadowmap_name = name + ".rib"
        shadowmap_file_path = os.path.join(self.directory, shadowmap_name)
        shadowmap_file = open(shadowmap_file_path, 'w')
        shadowmap_file.write(self.camera_to_renderman(context, obj))
        shadowmap_file.write('ScreenWindow {} {} {} {}'.format(min_dim, max_dim, min_dim, max_dim))

        light_string = 'LightSource "shadowdistant" {} "intensity" {} "lightcolor" [{} {} {}] "from" [{} {} {}] "to" [{} {} {}] "shadowname" ["{}"]\n'.format(index, obj.data.energy, obj.data.color[0], obj.data.color[1], obj.data.color[2], 0, 0, 0, end_x, end_y, end_z, name+".shd")
        light_file.write(light_string)

        shadowpass = {
                    "name": "shadowpass" + str(index),
                    "type": "shadow",
                    "settings" : {
                        "resolution" : "512 512 1",
                        "shadingrate" : 1.0,
                        "pixelsamples" : "1 1",
                        "shadowfilepath" : "shadow_" + obj.data.name + ".rib",
                        "display" : {"output" : "shadow_" + obj.data.name + ".z",
                                    "outtype" : "zfile",
                                    "mode" : "z"}}}
        renderpasses.append(shadowpass)

    def write_shadowpoint(self, context, renderpasses, light_file, obj, index):
        light_string = 'LightSource "shadowpoint" {} "intensity" {} "lightcolor" [{} {} {}] "from" [{} {} {}]'.format(index, obj.data.energy*20.0, obj.data.color[0], obj.data.color[1], obj.data.color[2], obj.location.x, obj.location.y, obj.location.z)

        name = "shadow_" + obj.data.name 
        name = name.replace(".", "_")
        shadowmap_name_base = name + ".rib"

        rotations = {'px': 'Rotate -90.0 0.0 1.0 0.0',
                    'py': 'Rotate 90.0 1.0 0.0 0.0',
                    'pz': 'Rotate 0.0 0.0 1.0 0.0',
                    'nx': 'Rotate 90.0 0.0 1.0 0.0',
                    'ny': 'Rotate -90.0 1.0 0.0 0.0',
                    'nz': 'Rotate 180 0.0 1.0 0.0'}
        for end in ('px', 'py', 'pz', 'nx', 'ny', 'nz'):
            shadowmap_name = end + shadowmap_name_base
            shadowmap_file_path = os.path.join(self.directory, shadowmap_name)
            shadowmap_file = open(shadowmap_file_path, 'w')

            light_string += ' "sf{}" ["{}"]'.format(end, end + "shadow_" + obj.data.name + ".shd")
            
            shadowmap_file.write('Projection "perspective" "fov" [95.0]\n')
            # shadowmap_file.write("Scale 1 1 -1\n")
            shadowmap_file.write(rotations[end] + "\n")
            shadowmap_file.write('Translate {} {} {}\n'.format(-obj.location.x, -obj.location.y, -obj.location.z))

            shadowpass = {
                        "name": "shadowpass" + str(index) + "_" + end,
                        "type": "shadow",
                        "settings" : {
                            "resolution" : "512 512 1",
                            "shadingrate" : 1.0,
                            "pixelsamples" : "1 1",
                            "shadowfilepath" : shadowmap_name,
                            "display" : {"output" : end + "shadow_" + obj.data.name + ".z",
                                        "outtype" : "zfile",
                                        "mode" : "z"}}}

            renderpasses.append(shadowpass)


        light_string += '\n'
        light_file.write(light_string)

    def execute(self, context):
        #TODO: get objects and proxyobject properties from blender
        # into the yaml file
        global fin_name
        global objects
        global proxyObjects
        global ambient_proxy

        renderpasses = [] 

        #TODO: custom_camera only appears in the local folder. Change that!
        filepath = os.path.join(self.directory, self.filename)
        fout = open(filepath, "w")
        print("Export beginning")

        ##############
        #Camera stuff#
        ##############
        cam_file_name = "custom_camera.rib"
        cam_file_path = os.path.join(self.directory, cam_file_name)
        cam_file = open(cam_file_path, 'w')
        cam_file.write(self.camera_to_renderman(context, bpy.data.objects['Camera']))

        cam_file.close()
        #############
        #Light stuff#
        #############
        light_file_name = "custom_lighting.rib"
        light_file_path = os.path.join(self.directory, light_file_name)
        light_file = open(light_file_path, 'w')

        for i, obj in enumerate(bpy.context.scene.objects):
            if obj.type == 'LAMP':
                light_string = None
                
                e = obj.rotation_euler
                M = e.to_matrix()
                v = mathutils.Vector((0,0,-1)) #default direction of light
                # v.rotate(e)
                # end_x, end_y, end_z = v
                end_x, end_y, end_z = M*v

                # x20 for point and spot intensity as a rough heuristic to get them looking the same in blender and renderman(matte shader)
                if obj.data.type == 'SUN':
                    # intensity = obj.data.energy*
                    if obj.data.shadow_method == 'NOSHADOW':
                        light_string = 'LightSource "distantlight" {} "intensity" {} "lightcolor" [{} {} {}] "from" [{} {} {}] "to" [{} {} {}]\n'.format(i, obj.data.energy, obj.data.color[0], obj.data.color[1], obj.data.color[2], 0, 0, 0, end_x, end_y, end_z)
                    else:
                        self.write_sun(context, renderpasses, light_file, obj, end_x, end_y, end_z, i)

                elif obj.data.type == 'POINT':
                    if obj.data.shadow_method == 'NOSHADOW':
                        light_string = 'LightSource "pointlight" {} "intensity" {} "lightcolor" [{} {} {}] "from" [{} {} {}]\n'.format(i, obj.data.energy*20, obj.data.color[0], obj.data.color[1], obj.data.color[2], obj.location.x, obj.location.y, obj.location.z)
                    else:
                        self.write_shadowpoint(context, renderpasses, light_file, obj, i)

                elif obj.data.type == 'SPOT':
                    delta_angle = obj.data.spot_size/2 * obj.data.spot_blend
                    if obj.data.shadow_method == 'NOSHADOW':
                        light_string = 'LightSource "spotlight" {} "intensity" {}  "coneangle" {} "conedeltaangle" {} "lightcolor" [{} {} {}] "from" [{} {} {}] "to" [{} {} {}]\n'.format(i, obj.data.energy*20, obj.data.spot_size/2.0, delta_angle, obj.data.color[0], obj.data.color[1], obj.data.color[2], obj.location.x, obj.location.y, obj.location.z, end_x+obj.location.x, end_y+obj.location.y, end_z+obj.location.z)
                    else:
                        self.write_shadowspot(context, renderpasses, light_file, obj, end_x, end_y, end_z, delta_angle, i)

                if light_string != None:
                    light_file.write(light_string)


        ambient_proxy.update()
        light_string = 'LightSource "ambientlight" {} "intensity" {} "lightcolor" [{} {} {}]\n'.format(i, ambient_proxy.obj.active_material.ambient, bpy.data.worlds["World"].ambient_color[0], bpy.data.worlds["World"].ambient_color[1], bpy.data.worlds["World"].ambient_color[2])
        light_file.write(light_string)
        light_file.close()

        ##########
        #The Rest#
        ##########

        renderobject = self.write_object(objects, is_proxy = False)
        renderobject += self.write_object(proxyObjects, is_proxy = True)

        data_name = "./data/" + "_".join(fin_name.split("_")[:-1]) + "_*.dat"

        resolution = "{} {}".format(bpy.data.scenes["Scene"].render.resolution_x, 
                               bpy.data.scenes["Scene"].render.resolution_y)

        defaultpass = {
                    "name": "defaultpass",
                    "settings" : {
                        "resolution" : resolution,
                        "display" : {"output" : "out.tif"}}}
        renderpasses.append(defaultpass)

        data = {"chronorender" : {
                    "rendersettings" : {"searchpaths" : "./"},
                    "camera" : [{"filename" : cam_file_name}],
                    "lighting" : [{"filename" : "custom_lighting.rib"}],
                    # "scene" : [{"filename" : "default_scene.rib"}],
                    "renderpass" : renderpasses ,
                    "simulation" : {
                        "data" : {
                            "datasource" : [{
                                "type" : "csv",
                                "name" : "defaultdata",
                                "resource" : data_name,
                                "fields" : [
                                    #TODO: ugly hack for ignores
                                    ["group", "string"],
                                    ["id", "integer"],
                                    ["pos_x", "float"],
                                    ["pos_y", "float"],
                                    ["pos_z", "float"],
                                    ["quat_w", "float"],
                                    ["quat_x", "float"],
                                    ["quat_y", "float"],
                                    ["quat_z", "float"],
                                    ["ignore", "string"], #object type
                                    ["ignore", "string"], #extra params
                                    ["ignore", "string"], #any reasonable input will work
                                    ["ignore", "string"],
                                    ["ignore", "string"],
                                    ["ignore", "string"],
                                    ["ignore", "string"],
                                    ["ignore", "string"],
                                    ["ignore", "string"],
                                    ["ignore", "string"],
                                    ["ignore", "string"],
                                    ["ignore", "string"],
                                    ["ignore", "string"],
                                    ["ignore", "string"],
                                    ["ignore", "string"],
                                    ["ignore", "string"],
                                    ["ignore", "string"],
                                    ["ignore", "string"],
                                    ["ignore", "string"]]}]},
                            "renderobject" : renderobject}}}
                            # [{
                            #     "name" : "particle",
                            #     "condition" : "id >= 0",
                            #     "color" : color,
                            #     "geometry" : [{
                            #         "radius" : 0.888,
                            #         "type" : "sphere"}]}]}}}}

        yaml.safe_dump(data, fout)

        print("Export complete! (yes really)")
        return {'FINISHED'}

def add_exportChronoRenderButton(self, context):
    self.layout.operator(
            ExportChronoRender.bl_idname,
            text=ExportChronoRender.__doc__,
            icon='PLUGIN')

def register():
    print("Registering")
    bpy.utils.register_class(ImportChronoRender)
    # bpy.types.INFO_MT_file.append(add_object_button)
    bpy.types.INFO_MT_file_import.append(add_importChronoRenderButton)

    bpy.utils.register_class(ExportChronoRender)
    bpy.types.INFO_MT_file_export.append(add_exportChronoRenderButton)

def unregister():
    print("Unregistering")
    bpy.utils.unregister_class(ImportChronoRender)
    bpy.types.unregister_class(ExportChronoRender)

if __name__ == "__main__":
    register()
