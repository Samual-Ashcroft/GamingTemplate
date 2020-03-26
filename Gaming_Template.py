
from pyglet.gl import *
from pyglet.window import key
from pyglet.gl import GLfloat
from os import listdir
from os.path import isfile, join
import time
import struct
import random

print('KEYBOARD CONTROLS:',
      '\n   W,A,S,D - Directions',
      '\n   Space - Fire/Action',
      '\n   Enter - Pause/Options',
      '\n   ESC - Exit')

ZONEWIDTH = 25
WindowProps = [800, 600]
WINDOW   = WindowProps
INCREMENT = 5
CONTROLZPOSITION = -100
CONTROLSCALER = 0.097
CONTROLSIZE = ZONEWIDTH*CONTROLSCALER
ZSCALER = 10

def wrap180(theta):
    while True:
        if theta > 180:
            theta -= 360
        elif theta < -180:
            theta += 360
        else:
            break
    return theta

def contain(value, upper, lower):
    if value > upper:
        return upper
    elif value < lower:
        return lower
    return value

def STLRead(Models, fileName, ModelID, ColorID = 1, scaler = 1):
    filePipe = open(fileName, 'rb')
    colorcodes = [[.16, .16, .16, 1.0], [.12, .12, .12, 1.0], [.5, 0, 0, 0.1], [.38, .37, .4, 1],[.35, .2, .53, 1]]
    headerLength = 80
    floatLength = 4
    endLength = 2
    header = filePipe.read(headerLength)
    facetNo = struct.unpack('I', filePipe.read(4))[0]
    Models.append( [[ModelID, colorcodes[ColorID]],[]] )
    for data in range(facetNo):
        try:
            Normal = [struct.unpack('f', filePipe.read(floatLength))[0],
                    struct.unpack('f', filePipe.read(floatLength))[0],
                    struct.unpack('f', filePipe.read(floatLength))[0]]
            Vertex1 = [struct.unpack('f', filePipe.read(floatLength))[0]*scaler,
                    struct.unpack('f', filePipe.read(floatLength))[0]*scaler,
                    struct.unpack('f', filePipe.read(floatLength))[0]*scaler]
            Vertex2 = [struct.unpack('f', filePipe.read(floatLength))[0]*scaler,
                    struct.unpack('f', filePipe.read(floatLength))[0]*scaler,
                    struct.unpack('f', filePipe.read(floatLength))[0]*scaler]
            Vertex3 = [struct.unpack('f', filePipe.read(floatLength))[0]*scaler,
                    struct.unpack('f', filePipe.read(floatLength))[0]*scaler,
                    struct.unpack('f', filePipe.read(floatLength))[0]*scaler]
            filePipe.read(endLength)
            Models[-1][1].append([Normal, Vertex1, Vertex2, Vertex3])
        except:
            print("error reading facets")
            break
    filePipe.close()
    return Models

def PopulateModels(fileSets, scaler = 1):
    Models = []
    for iterator1 in range(len(fileSets)):
        for iterator2 in range(len(fileSets[iterator1])):
            try:
                Models = STLRead(Models, fileSets[iterator1][iterator2], iterator1, int(fileSets[iterator1][iterator2][11:14]), scaler)
            except:
                Models = STLRead(Models, fileSets[iterator1][iterator2], iterator1, 1, scaler)
    return Models

def PullFileNames(extension, subFolder):
    ''' Pulls a list of STL files in, provided they start
    with a number 000 up to 010'''
    fileNames = [f for f in listdir(subFolder) if isfile(join(subFolder, f))]
    iterator = 0
    while iterator < len(fileNames):
        if fileNames[iterator].find(extension) == -1:
            del fileNames[iterator]
        else:
            iterator +=1
    fileSets = [[], [], [], [], [], [], [], [], [], [], []]
    for iterator1 in range(len(fileNames)):
        fileSets[int(fileNames[iterator1][:3])].append(subFolder+'/'+fileNames[iterator1])
    return fileSets

def vec(*args):
    return (GLfloat * len(args))(*args)

class Entity:
    def __init__(self, stlID, x, y, z=0, xr=0, yr=0, zr=0, dx=0, dy=0, dz=0, dxr=0, dyr=0, dzr=0):
        self._stlID = stlID
        self.x = x
        self.y = y
        self.z = z
        self.xr = xr
        self.yr = yr
        self.zr = zr
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.dxr = dxr
        self.dyr = dyr
        self.dzr = dzr

    def spin(self, dxr=0, dyr=0, dzr=0):
        self.dxr = dxr
        self.dyr = dyr
        self.dzr = dzr

    def move(self, dx, dy, dz):
        self.dx = dx
        self.dy = dy
        self.dz = dz
    
    def iterate(self):
        self.x += self.dx
        self.y += self.dy
        self.z += self.dz
        self.xr = wrap180(self.xr + self.dxr)
        self.yr = wrap180(self.yr + self.dyr)
        self.zr = wrap180(self.zr + self.dzr)

class EntityGroup:
    def __init__(self, stlID, x, y, z=0, spacing = 15, xNo=range(0,1,1), yNo=range(0,1,1), zNo=range(0,1,1)):
        self._container = []
        self._stlID = stlID
        self.x = x
        self.y = y
        self.z = z
        for _xNo in xNo:
            for _yNo in yNo:
                for _zNo in zNo:
                    self._container.append(Entity(stlID, x+spacing*_xNo, y+spacing*_yNo, z+spacing*_zNo))

class Window(pyglet.window.Window):

    _mouseInfo = {'x':None, 'y':None, 'dx':None, 'dy':None, 
                'scroll_x':None, 'scroll_y':None, 
                'button':None, 'modifiers':None, 'widget':None}
    _cameraInfo = {'offset':{'x':0, 'y':-350, 'z':500*ZSCALER, 
                        'min':{'x':-1, 'y':-355, 'z':495*ZSCALER}, 
                        'max':{'x':1, 'y':-345, 'z':505*ZSCALER}}, 
                    'rotation':{'x':-110, 'y':0, 'z':0, 
                        'min':{'x':-115, 'y':-5, 'z':-5}, 
                        'max':{'x':-105, 'y':5, 'z':5}}, 
                    'XYZscaler': ZSCALER}
    _textOverlay = {'score':None, 'lives':None, 'zoom':- (100 + ((WindowProps[1]-650)*.153)) * ZSCALER}

    _objects = [[], None, [], []]

    def __init__(self, width, height, title=''):
        self._textOverlay['score'] = pyglet.text.Label(
                'Score: 000',
                font_name='ARIAL', font_size=25,
                x=-6, y=0, align = 'center',
                anchor_x='center', anchor_y='center'
            )
        self._textOverlay['lives'] = pyglet.text.Label(
                'Lives:                        ',
                font_name='ARIAL', font_size=25,
                x=-6, y=0, align = 'center',
                anchor_x='center', anchor_y='center'
            )

        pyglet.window.Window.__init__(self, width, height, title, resizable=False, style=pyglet.window.Window.WINDOW_STYLE_DEFAULT)

        self.set_minimum_size(WINDOW[0], WINDOW[1])

        glClearColor(0, 0, 0, 1)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_NORMALIZE)
        factor = [.1,.5,.1]
        glLightfv(GL_LIGHT1, GL_SPECULAR, vec(1.0*factor[1],1.0*factor[1],1.0*factor[1],1.0*factor[1]))
        glEnable(GL_LIGHT1)

        pyglet.clock.schedule_interval(self.update, 1 / 20.0)
        Offsets = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0],
                   [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
        Rotations = [[0.0, 0.0, 0.0], [90.0, 10.0, 10.0], [90.0, 0.0, 0.0], [0.0, 90.0, 90.0], [0.0, 0.0, 0.0],
                     [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
        '''
        000_004_solid_virus
        001_002_Hearts
        002_003_Tank
        003_003_Bullet
        '''
        ModelSets = PopulateModels(PullFileNames('stl', './obj/'), self._cameraInfo['XYZscaler']*10/163)
        self._objects[1] = len(ModelSets)
        for iterator1 in range(self._objects[1]):
            self._objects[3].append(
                {
                    'Trans': {
                        'x': Offsets[ModelSets[iterator1][0][0]][0],
                        'y': Offsets[ModelSets[iterator1][0][0]][1],
                        'z': Offsets[ModelSets[iterator1][0][0]][2]
                    },
                    'Rot': {
                        'x': Rotations[ModelSets[iterator1][0][0]][0],
                        'y': Rotations[ModelSets[iterator1][0][0]][1],
                        'z': Rotations[ModelSets[iterator1][0][0]][2]
                    }
                }
            )
            #append the Object id
            self._objects[2].append(ModelSets[iterator1][0][0])
            #append the Objects colour id
            self._objects[0].append(
                [
                    pyglet.graphics.Batch(),
                    [
                        ModelSets[iterator1][0][1][0],
                        ModelSets[iterator1][0][1][1],
                        ModelSets[iterator1][0][1][2],
                        ModelSets[iterator1][0][1][3]
                    ]
                ]
            )

            vertices = []
            normals = []
            for iterator2 in range(len(ModelSets[iterator1][1])):
                for iterator3 in range(1, 4):
                    vertices.extend(ModelSets[iterator1][1][iterator2][iterator3])
                    normals.extend(ModelSets[iterator1][1][iterator2][0])

            # Create a list of triangle indices.
            indices = range(3 * len(ModelSets[iterator1][1]))  # [[3*i, 3*i+1, 3*i+2] for i in xrange(len(facets))]
            self._objects[0][-1][0].add_indexed(
                len(vertices) // 3,
                GL_TRIANGLES,
                None,  # group,
                indices,
                ('v3f/static', vertices),
                ('n3f/static', normals)
            )
        self._entities = {'hearts':None, 'tank':None, 'bullets':None}
        self._entities['hearts'] = EntityGroup(1, 15, 0, -5, 10, range(-2, 3, 1))
        self._entities['tank'] = EntityGroup(2, 0, 0, 10)
        self._entities['tank']._container[0].timeout = 10
        self._entities['bullets'] = EntityGroup(3, 0, 0, 20)
        self._entities['bullets']._container[0].dzr = 5
        self._entities['bullets']._container[0].dz = 5
        '''for item1 in self._entities:
            print(item1)
            for item2 in self._entities[item1]._container:
                print(item2._stlID, item2.x, item2.y, item2.z, item2.xr, item2.yr, item2.zr,
                item2.dxr, item2.dyr, item2.dzr)'''

    def on_resize(self, width, height):
        # set the Viewport
        glViewport(0, 0, width, height)
        # using Projection mode
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspectRatio = width / height
        gluPerspective(35, aspectRatio, 1, 20000*self._cameraInfo['XYZscaler'])
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0, 0, -500)

    def on_mouse_motion(self, x, y, dx, dy):
        
        self._entities['tank']._container[0].x = contain(x*120/800-60, 50, -50)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        '''self._cameraInfo['offset']['z'] += scroll_y*50*self._cameraInfo['XYZscaler']
        if self._cameraInfo['offset']['min']['z'] > self._cameraInfo['offset']['z']:
            self._cameraInfo['offset']['z'] = self._cameraInfo['offset']['min']['z'] + 0
        if self._cameraInfo['offset']['max']['z'] < self._cameraInfo['offset']['z']:
            self._cameraInfo['offset']['z'] = self._cameraInfo['offset']['max']['z'] + 0'''
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        if self._entities['tank']._container[0].timeout == 0:
            self._entities['bullets']._container.append(Entity(3, 
                self._entities['tank']._container[0].x + 0,
                self._entities['tank']._container[0].y + 0,
                20, 0, 0, 1, 0, 0, 1))
            self._entities['tank']._container[0].timeout = 10

    def on_mouse_release(self, x, y, button, modifiers):
        pass
    
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """if buttons == 1:
            self._cameraInfo['rotation']['x'] -= dy * 0.25
            if modifiers == 0:
                self._cameraInfo['rotation']['y'] += dx * 0.25
            else:
                self._cameraInfo['rotation']['z'] += dx * 0.25
            ''' This is spagetti a little hmm...   has to be a more modular way to do this I think with OOP perhaps '''
            if self._cameraInfo['rotation']['min']['x'] > self._cameraInfo['rotation']['x']:
                self._cameraInfo['rotation']['x'] = self._cameraInfo['rotation']['min']['x'] + 0
            if self._cameraInfo['rotation']['max']['x'] < self._cameraInfo['rotation']['x']:
                self._cameraInfo['rotation']['x'] = self._cameraInfo['rotation']['max']['x'] + 0
            if self._cameraInfo['rotation']['min']['y'] > self._cameraInfo['rotation']['y']:
                self._cameraInfo['rotation']['y'] = self._cameraInfo['rotation']['min']['y'] + 0
            if self._cameraInfo['rotation']['max']['y'] < self._cameraInfo['rotation']['y']:
                self._cameraInfo['rotation']['y'] = self._cameraInfo['rotation']['max']['y'] + 0
            if self._cameraInfo['rotation']['min']['z'] > self._cameraInfo['rotation']['z']:
                self._cameraInfo['rotation']['z'] = self._cameraInfo['rotation']['min']['z'] + 0
            if self._cameraInfo['rotation']['max']['z'] < self._cameraInfo['rotation']['z']:
                self._cameraInfo['rotation']['z'] = self._cameraInfo['rotation']['max']['z'] + 0
        elif buttons == 4:
            self._cameraInfo['offset']['x'] += dx * 1.5 *self._cameraInfo['XYZscaler']
            self._cameraInfo['offset']['y'] += dy * 1.5 *self._cameraInfo['XYZscaler']
            ''' This is spagetti a little hmm...   has to be a more modular way to do this I think with OOP perhaps '''
            if self._cameraInfo['offset']['min']['x'] > self._cameraInfo['offset']['x']:
                self._cameraInfo['offset']['x'] = self._cameraInfo['offset']['min']['x'] + 0
            if self._cameraInfo['offset']['max']['x'] < self._cameraInfo['offset']['x']:
                self._cameraInfo['offset']['x'] = self._cameraInfo['offset']['max']['x'] + 0
            if self._cameraInfo['offset']['min']['y'] > self._cameraInfo['offset']['y']:
                self._cameraInfo['offset']['y'] = self._cameraInfo['offset']['min']['y'] + 0
            if self._cameraInfo['offset']['max']['y'] < self._cameraInfo['offset']['y']:
                self._cameraInfo['offset']['y'] = self._cameraInfo['offset']['max']['y'] + 0"""
        pass

    def on_key_press(self, symbol, modifiers):
        increaser = 1
        if symbol == key.ESCAPE:
            pyglet.app.exit()
        elif symbol == key.A:
            self._entities['tank']._container[0].dx -= 1
        elif symbol == key.D:
            self._entities['tank']._container[0].dx += 1
        elif symbol == key.W:
            self._entities['tank']._container[0].dx = 0
        elif symbol == key.SPACE:
            if self._entities['tank']._container[0].timeout == 0:
                self._entities['bullets']._container.append(Entity(3, 
                self._entities['tank']._container[0].x + 0,
                self._entities['tank']._container[0].y + 0,
                20, 0, 0, 1, 0, 0, 1))
                self._entities['tank']._container[0].timeout = 10
        


    def update(self, yoyo):
        upper = 5
        def rotate(item):
            item.yr = wrap180(item.yr + item.dyr)
            #print(item.dyr)

            check1 = random.random()
            check2 = random.randint(-upper, upper)

            if item.dyr == 0:
                item.dyr = check2
            elif item.dyr > 0:
                if check1 < 0.01:
                    item.dyr = check2
                else:
                    item.dyr = check2/2+upper/2
            else:
                if check1 < 0.01:
                    item.dyr = check2
                else:
                    item.dyr = check2/2-upper/2
            pass

        for item1 in self._entities:
            for item2 in self._entities[item1]._container:
                item2.iterate()
        for item in self._entities['hearts']._container:
            rotate(item)
        if len(self._entities['bullets']._container) > 0:
            while True:
                for iterator in range(len(self._entities['bullets']._container)):
                    if self._entities['bullets']._container[iterator].z > 75:
                        del self._entities['bullets']._container[iterator]
                        break
                else:
                    break
        self._entities['tank']._container[0].timeout = contain(self._entities['tank']._container[0].timeout - 1, 100, 0)
        if self._entities['tank']._container[0].x != contain(self._entities['tank']._container[0].x, 50, -50):
            self._entities['tank']._container[0].x = contain(self._entities['tank']._container[0].x, 50, -50)
            self._entities['tank']._container[0].dx = 0

    def on_draw(self):
        global arm
        # Clear the current GL Window
        self.clear()

        for item1 in self._entities:
            #print(item1)
            for item2 in self._entities[item1]._container:
                glLoadIdentity()
                glTranslatef(self._cameraInfo['offset']['x'],
                            self._cameraInfo['offset']['y'],
                            self._cameraInfo['offset']['z'] - 650*self._cameraInfo['XYZscaler'])
                glRotatef(self._cameraInfo['rotation']['x'], 1, 0, 0)
                glRotatef(self._cameraInfo['rotation']['y'], 0, 1, 0)
                glRotatef(self._cameraInfo['rotation']['z'], 0, 0, 1)
                glTranslatef((item2.x+self._objects[3][item2._stlID]['Trans']['x'])*self._cameraInfo['XYZscaler'],
                            (item2.y+self._objects[3][item2._stlID]['Trans']['y'])*self._cameraInfo['XYZscaler'],
                            (item2.z+self._objects[3][item2._stlID]['Trans']['z'])*self._cameraInfo['XYZscaler'])
                glRotatef(wrap180(self._objects[3][item2._stlID]['Rot']['x']+item2.xr), 1, 0, 0)
                glRotatef(wrap180(self._objects[3][item2._stlID]['Rot']['y']+item2.yr), 0, 1, 0)
                glRotatef(wrap180(self._objects[3][item2._stlID]['Rot']['z']+item2.zr), 0, 0, 1)

                # Draw the Thing
                glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
                glEnable(GL_COLOR_MATERIAL)
                glColor3f(self._objects[0][item2._stlID][1][0],
                        self._objects[0][item2._stlID][1][1],
                        self._objects[0][item2._stlID][1][2])
                self._objects[0][item2._stlID][0].draw()
                glDisable(GL_COLOR_MATERIAL)

        '''draw the text overlays'''
        glLoadIdentity()
        glTranslatef(0, 250, self._textOverlay['zoom'])
        glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_COLOR_MATERIAL)
        glColor3f(1,1,1)
        self._textOverlay['score'].draw()
        glDisable(GL_COLOR_MATERIAL)
        glLoadIdentity()
        glTranslatef(0, -250, self._textOverlay['zoom'])
        glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_COLOR_MATERIAL)
        glColor3f(1,1,1)
        self._textOverlay['lives'].draw()
        glDisable(GL_COLOR_MATERIAL)

    def on_text_motion(self, motion, BLAH = False, Setting = None):
        pass

def Main():
    import pyglet
    GAMINGTEMPLATE = Window(WINDOW[0], WINDOW[1], 'Gaming Template')
    icon1 = pyglet.image.load('./obj/logo_512x512.png')
    GAMINGTEMPLATE.set_icon(icon1)
    GAMINGTEMPLATE.set_location(50,50)
    pyglet.app.run()

if __name__ == '__main__':
    Main()
