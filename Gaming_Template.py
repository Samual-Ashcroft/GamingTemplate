import sys
import ctypes
import copy

import orion5
from orion5.utils.general import *
from orion5.orion5_math import *

from pyglet.gl import *
from pyglet.window import key
from pyglet.gl import GLfloat

print('KEYBOARD CONTROLS:',
      '\n   W,A,S,D - Directions',
      '\n   Space - Fire/Action',
      '\n   Enter - Pause/Options',
      '\n   ESC - Exit')

ZONEWIDTH = 25
WindowProps = [800, 600]
WINDOW   = [WindowProps[0] + 4 * ZONEWIDTH, WindowProps[1] + 2 * ZONEWIDTH]
INCREMENT = 5
CONTROLZPOSITION = -100
CONTROLSCALER = 0.097
CONTROLSIZE = ZONEWIDTH*CONTROLSCALER

seeder = [
    {
        'Trans': {'x': 0, 'y': -700, 'z': 0},
        'Rot': {'x': 0, 'y': 0, 'z': 180}
    }
]

arm = {
    'id': 0,
    'coms': ['COM8'],
    'arms': [
        {
            'arm': None,
            'Trans': {'x': 0, 'y': 0, 'z': 0},
            'Rot': {'x': 0, 'y': 0, 'z': 0}
        }
    ]
}

ORION5 = None
SEQUENCEFOLDER = './sequences/'
SEQUENCEBASENAME = 'Sequence'
SEQUENCEEXTENSION = '.txt'
ZSCALER = 10

def vec(*args):
    return (GLfloat * len(args))(*args)

class Window(pyglet.window.Window):
    _Widgets = {
        'Selected': None,
        'Widgets': []
    }

    _windowConstants = [
        50, -100*ZSCALER, 0.097, None,
        [
            ['Claw', 'Attack Angle', 'X', 'Y', 'Attack Depth', 'Turret'],
            None,
            [
                [0, 0, True, key.MOTION_END_OF_LINE, key.MOTION_NEXT_PAGE],
                [0, 0, True, key.MOTION_PREVIOUS_PAGE, key.MOTION_BEGINNING_OF_LINE],
                [0, 0, False, key.MOTION_LEFT, key.MOTION_RIGHT],
                [0, 0, True, key.MOTION_UP, key.MOTION_DOWN],
                [0, 0, True, key.MOTION_BACKSPACE, key.MOTION_DELETE],
                [0, 0, False, key.MOTION_PREVIOUS_WORD, key.MOTION_NEXT_WORD]
            ]
        ]
    ] 

    _mouseInfo = {'x':None, 'y':None, 'dx':None, 'dy':None, 
                'scroll_x':None, 'scroll_y':None, 
                'button':None, 'modifiers':None, 'widget':None}
    _cameraInfo = {'offset':{'x':160, 'y':-100, 'z':-300*ZSCALER}, 
                    'rotation':{'x':-80, 'y':0, 'z':-150},
                    'XYZscaler': ZSCALER}
    _windowInfo = {}

    _controlState = [-1, -1, -1, False, False, False, False, None, None, None, [0,0], None] #_controlState[11]

    _armConstants = [
        {'Shoulder': 1}, #(1+(52/28)
        [
            {
                'Turret': 100.0,
                'Shoulder': 100.0,
                'Elbow': 100.0,
                'Wrist': 100.0,
                'Claw': 100.0
            },
            ['Turret', 'Shoulder', 'Elbow', 'Wrist', 'Claw']
        ],
        {
            'X lims': [500.0, 1.0, -250.0, False],
            'Z lims': [500.0, 1.0, -250.0, False],
            'Attack Angle lims': [360.0, 1.0, 0.0, True],
            'Attack Depth lims': [500.0, 1.0, -250.0, False],
            'Claw lims': [250.0, 1.0, 20.0, False],
            'Turret lims': [360.0, 1.0, 0.0, True],
            'Shoulder lims': [360.0, 1.0, 0.0, True],
            'Bicep lims': [360.0, 1.0, 0.0, True],
            'Wrist lims': [360.0, 1.0, 0.0, True],
            'Bicep Len': 170.384,
            'Forearm Len': 136.307,
            'Wrist 2 Claw': 85.25,
            'Key IDs': [
                [key.MOTION_END_OF_LINE, 'Claw', True],
                [key.MOTION_NEXT_PAGE, 'Claw', False],
                [key.MOTION_UP, 'Z', True],
                [key.MOTION_DOWN, 'Z', False],
                [key.MOTION_LEFT, 'X', True],
                [key.MOTION_RIGHT, 'X', False],
                [key.MOTION_PREVIOUS_WORD, 'Turret', True],
                [key.MOTION_NEXT_WORD, 'Turret', False],
                [key.MOTION_PREVIOUS_PAGE, 'Attack Angle', True],
                [key.MOTION_BEGINNING_OF_LINE, 'Attack Angle', False],
                [key.MOTION_BACKSPACE, 'Attack Depth', True],
                [key.MOTION_DELETE, 'Attack Depth', False]
            ]
        }
    ] #self._armConstants[2]

    _armVARS = [
        {
            'X': 400.0,
            'Z': 50.0,
            'Attack Angle': 0.0,
            'Attack Depth': 50.0,
            'Wrist Pos': [0.0, 0.0, 0.0],
            'Elbow Pos': [0.0, 0.0, 0.0],
            'Shoulder Pos': [-30.309, 0.0, 53.0],
            'Elbow Angle': 0.0,
            'Turret': 180.0,
            'Shoulder': 0.0,
            'Elbow': 0.0,
            'Wrist': 0.0,
            'Claw': 200.0,
            'OLD': {
                'X': 400.0,
                'Z': 50.0,
                'Attack Angle': 0.0,
                'Attack Depth': 50.0,
                'Wrist Pos': [0.0, 0.0, 0.0],
                'Elbow Pos': [0.0, 0.0, 0.0],
                'Shoulder Pos': [-30.309, 0.0, 53.0],
                'Elbow Angle': 0.0,
                'Turret': 180.0,
                'Shoulder': 0.0,
                'Elbow': 0.0,
                'Wrist': 0.0,
                'Claw': 200.0,
            },
            'Iter': [
                'X',
                'Z',
                'Attack Angle',
                'Attack Depth',
                'Wrist Pos',
                'Elbow Pos',
                'Shoulder Pos',
                'Elbow Angle',
                'Turret',
                'Shoulder',
                'Elbow',
                'Wrist',
                'Claw'
            ]
        }
    ] #_armVARS[arm['id']]

    _armObjects = [[], None, []] #_armObjects[2] #_armObjects
    _sequence = [[[]], -1] #_sequence[1][0]
    _objects = [[], None, [], []]

    def __init__(self, width, height, title=''):
        image = pyglet.image.load('./obj/logo_60x60.png')
        shift = -6
        self.thing = [
            pyglet.text.Label(
                'C\nL\nA\nW\n \nO\nP\nE\nN\nI\nN\nG',
                font_name='ARIAL', font_size=15,
                x=shift, y=0, align = 'center',
                anchor_x='center', anchor_y='center',
                multiline=True, width=1
            ),
            pyglet.text.Label(
                'W\nR\nI\nS\nT\n \nA\nN\nG\nL\nE',
                font_name='ARIAL', font_size=15,
                x=shift, y=0, align = 'center',
                anchor_x='center', anchor_y='center',
                multiline=True, width=1
            ),
            pyglet.text.Label(
                'TOOL RADIUS',
                font_name='ARIAL', font_size=15,
                x=shift, y=0, align = 'center',
                anchor_x='center', anchor_y='center'
            ),
            pyglet.text.Label(
                'T O O L\n \nH E I G H T',
                font_name='ARIAL', font_size=15,
                x=shift, y=0, align = 'center',
                anchor_x='center', anchor_y='center',
                multiline = True, width = 1
            ),
            pyglet.text.Label(
                'T\nO\nO\nL\n \nD\nI\nS\nT\nA\nN\nC\nE',
                font_name='ARIAL', font_size=15,
                x=shift, y=0, align = 'center',
                anchor_x='center', anchor_y='center',
                multiline=True, width=1
            ),
            pyglet.text.Label(
                'TURRET ANGLE',
                font_name='ARIAL', font_size=15,
                x=shift, y=0, align = 'center',
                anchor_x='center', anchor_y='center'
            ),
            pyglet.sprite.Sprite(image, x=0, y=0)
        ]

        global arm
        pyglet.window.Window.__init__(self, width, height, title, resizable=True, style=pyglet.window.Window.WINDOW_STYLE_DEFAULT)

        self._controlState[8] = [WINDOW[0], WINDOW[1]]
        self.set_minimum_size(self._controlState[8][0], self._controlState[8][1])
        self._controlState[9] = [['Claw', [self._controlState[8][0] - self._windowConstants[0],
                                           self._windowConstants[0],
                                           self._controlState[8][0],
                                           self._controlState[8][1]],
                                  [0, 0]],
                                 ['Attack Angle', [self._windowConstants[0],
                                                   2 * self._windowConstants[0],
                                                   2 * self._windowConstants[0],
                                                   self._controlState[8][1]],
                                  [0, 0]],
                                 ['X', [0,
                                        0,
                                        self._controlState[8][0],
                                        self._windowConstants[0]],
                                  [0, 0]],
                                 ['Y', [0,
                                        self._windowConstants[0],
                                        self._windowConstants[0],
                                        self._controlState[8][1]],
                                  [0, 0]],
                                 ['Attack Depth', [self._controlState[8][0] - 2 * self._windowConstants[0],
                                                   2 * self._windowConstants[0],
                                                   self._controlState[8][0] - self._windowConstants[0],
                                                   self._controlState[8][1]],
                                  [0, 0]],
                                 ['Turret', [self._windowConstants[0],
                                             self._windowConstants[0],
                                             self._controlState[8][0] - self._windowConstants[0],
                                             2 * self._windowConstants[0]],
                                  [0, 0]]]
        self._controlState[11] = {'Claw':[(self._controlState[8][0]/2)-self._windowConstants[0]/2,
                                          (self._windowConstants[0] - self._controlState[8][1] / 2) + self._windowConstants[0] / 2,
                                          0,
                                          abs((self._windowConstants[0] - self._controlState[8][1] / 2) + self._windowConstants[0]/2)*2 + self._windowConstants[0],
                                          self._armConstants[2]['Claw lims'][2],
                                          self._armConstants[2]['Claw lims'][0]-self._armConstants[2]['Claw lims'][2],
                                          0],
                                'Attack Angle':[(self._windowConstants[0]-self._controlState[8][0]/2)+self._windowConstants[0]/2,
                                                (2 * self._windowConstants[0] - self._controlState[8][1] / 2) + self._windowConstants[0] / 2,
                                                0,
                                                abs((2 * self._windowConstants[0] - self._controlState[8][1] / 2) + self._windowConstants[0] / 2)*2 + 2 * self._windowConstants[0],
                                                self._armConstants[2]['Attack Angle lims'][2],
                                                self._armConstants[2]['Attack Angle lims'][0] - self._armConstants[2]['Attack Angle lims'][2],
                                                'Attack Angle',
                                                0.5],
                                'X':[(-self._controlState[8][0]/2)+self._windowConstants[0]/2,
                                     (-self._controlState[8][1]/2)+self._windowConstants[0]/2,
                                     abs((-self._controlState[8][0]/2)+self._windowConstants[0]/2)*2,
                                     0,
                                     self._armConstants[2]['X lims'][2],
                                     self._armConstants[2]['X lims'][0] - self._armConstants[2]['X lims'][2],
                                     'X',
                                     0],
                                'Y':[(-self._controlState[8][0]/2)+self._windowConstants[0]/2,
                                     (self._windowConstants[0] - self._controlState[8][1] / 2) + self._windowConstants[0] / 2,
                                     0,
                                     abs((self._windowConstants[0] - self._controlState[8][1] / 2) + self._windowConstants[0] / 2)*2 + self._windowConstants[0],
                                     self._armConstants[2]['Z lims'][2],
                                     self._armConstants[2]['Z lims'][0] - self._armConstants[2]['Z lims'][2],
                                     'Z',
                                     0],
                                'Attack Depth':[(self._controlState[8][0]/2-self._windowConstants[0])-self._windowConstants[0]/2,
                                                (2*self._windowConstants[0]-self._controlState[8][1] / 2) + self._windowConstants[0] / 2,
                                                0,
                                                abs((2*self._windowConstants[0]-self._controlState[8][1] / 2) + self._windowConstants[0] / 2)*2 + 2 * self._windowConstants[0],
                                                self._armConstants[2]['Attack Depth lims'][2],
                                                self._armConstants[2]['Attack Depth lims'][0] - self._armConstants[2]['Attack Depth lims'][2],
                                                'Attack Depth',
                                                0],
                                'Turret':[(self._windowConstants[0]-self._controlState[8][0]/2)+self._windowConstants[0]/2,
                                                (self._windowConstants[0]-self._controlState[8][1]/2)+self._windowConstants[0]/2,
                                                abs((self._windowConstants[0] - self._controlState[8][0] / 2) + self._windowConstants[0] / 2) * 2,
                                                0,
                                                  self._armConstants[2]['Turret lims'][2],
                                                  self._armConstants[2]['Turret lims'][0] - self._armConstants[2]['Turret lims'][2],
                                                'Turret',
                                                0]}
        self._controlState[7] = self._windowConstants[0] * self._windowConstants[2]
        glClearColor(0, 0, 0, 1)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_NORMALIZE)
        factor = [.1,.5,.1]
        glLightfv(GL_LIGHT1, GL_SPECULAR, vec(1.0*factor[1],1.0*factor[1],1.0*factor[1],1.0*factor[1]))
        glEnable(GL_LIGHT1)
        arm['arms'][arm['id']]['arm'] = orion5.Orion5('standalone', arm['coms'][arm['id']], useSimulator=False)
        self.on_text_motion(False)
        self._windowConstants[4][1] = pyglet.graphics.Batch()
        div = 2.2
        vertices = [
            -self._controlState[7] / div, -self._controlState[7] / div, 0,
            self._controlState[7] / div, -self._controlState[7] / div, 0,
            -self._controlState[7] / div, self._controlState[7] / div, 0,
            -self._controlState[7] / div, self._controlState[7] / div, 0,
            self._controlState[7] / div, -self._controlState[7] / div, 0,
            self._controlState[7] / div, self._controlState[7] / div, 0
        ]
        normals = [
            0.0,0.0,1.0,
            0.0,0.0,1.0,
            0.0,0.0,1.0,
            0.0,0.0,1.0,
            0.0,0.0,1.0,
            0.0,0.0,1.0
        ]
        indices = range(6)
        self._windowConstants[4][1].add_indexed(len(vertices) // 3,
                                      GL_TRIANGLES,
                                      None,  # group,
                                      indices,
                                      ('v3f/static', vertices),
                                      ('n3f/static', normals))
        ModelSets = PolyRead('./obj/3dObjects.SAM', self._cameraInfo['XYZscaler'])
        self._armObjects[1] = len(ModelSets)
        for iterator1 in range(self._armObjects[1]):
            self._armObjects[2].append(ModelSets[iterator1][0][0])
            self._armObjects[0].append(
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
            self._armObjects[0][-1][0].add_indexed(
                len(vertices) // 3,
                GL_TRIANGLES,
                None,  # group,
                indices,
                ('v3f/static', vertices),
                ('n3f/static', normals)
            )

        pyglet.clock.schedule_interval(self.update, 1 / 20.0)
        Offsets = [[0.0, 0.0, 0.0], [200.0, 200.0, 200.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0],
                   [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
        Rotations = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0],
                     [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]

        ModelSets = PopulateModels(PullFileNames('stl', './obj/'), self._cameraInfo['XYZscaler'])
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
            self._objects[2].append(ModelSets[iterator1][0][0])
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

        for item1 in self._windowConstants[4][2]:
            self.on_text_motion(item1[3])
            self.on_text_motion(item1[4])

    def on_resize(self, width, height):
        # set the Viewport
        glViewport(0, 0, width, height)
        self._controlState[8] = [width, height]
        #self.set_size(width, height)
        self._controlState[7] = self._windowConstants[0] * self._windowConstants[2]
        self._controlState[9] = [['Claw', [self._controlState[8][0] - self._windowConstants[0],
                                 self._windowConstants[0],
                                 self._controlState[8][0],
                                 self._controlState[8][1]],
                        [0, 0]],  # Third Zone Second Left, Claw Open?
                       ['Attack Angle', [self._windowConstants[0],
                                         2 * self._windowConstants[0],
                                         2 * self._windowConstants[0],
                                         self._controlState[8][1]],
                        [0, 0]],  # Fifth Zone Second from Right, Attack Angle
                       ['X', [0,
                              0,
                              self._controlState[8][0],
                              self._windowConstants[0]],
                        [0, 0]],  # Second zone bottom, X Position
                       ['Y', [0,
                              self._windowConstants[0],
                              self._windowConstants[0],
                              self._controlState[8][1]],
                        [0, 0]],  # First Zone Left, Y Position
                       ['Attack Depth', [self._controlState[8][0] - 2 * self._windowConstants[0],
                                         2 * self._windowConstants[0],
                                         self._controlState[8][0] - self._windowConstants[0],
                                         self._controlState[8][1]],
                        [0, 0]],  # Sixth Zone Right, Attack Depth
                       ['Turret', [self._windowConstants[0],
                                   self._windowConstants[0],
                                   self._controlState[8][0] - self._windowConstants[0],
                                   2 * self._windowConstants[0]],
                        [0, 0]]]  # Fourth Zone Second from Bottom, Turret Angle
        self._controlState[11] = {'Claw': [(self._controlState[8][0] / 2) - self._windowConstants[0] / 2,
                                      (self._windowConstants[0] - self._controlState[8][1] / 2) + self._windowConstants[0] / 2,
                                      0,
                                      abs((self._windowConstants[0] - self._controlState[8][
                                          1] / 2) + self._windowConstants[0] / 2) * 2 + self._windowConstants[0],
                                      self._armConstants[2]['Claw lims'][2],
                                      self._armConstants[2]['Claw lims'][0] - self._armConstants[2]['Claw lims'][2],
                                      'Claw',
                                      0],
                             'Attack Angle': [(self._windowConstants[0] - self._controlState[8][0] / 2) + self._windowConstants[0] / 2,
                                              (2 * self._windowConstants[0] - self._controlState[8][1] / 2) + self._windowConstants[0] / 2,
                                              0,
                                              abs((2 * self._windowConstants[0] - self._controlState[8][
                                                  1] / 2) + self._windowConstants[0] / 2) * 2 + 2 * self._windowConstants[0],
                                              self._armConstants[2]['Attack Angle lims'][2],
                                              self._armConstants[2]['Attack Angle lims'][0] - self._armConstants[2]['Attack Angle lims'][
                                                  2],
                                              'Attack Angle',
                                              .5],
                             'X': [(-self._controlState[8][0] / 2) + self._windowConstants[0] / 2,
                                   (-self._controlState[8][1] / 2) + self._windowConstants[0] / 2,
                                   abs((-self._controlState[8][0] / 2) + self._windowConstants[0] / 2) * 2,
                                   0,
                                   self._armConstants[2]['X lims'][2],
                                   self._armConstants[2]['X lims'][0] - self._armConstants[2]['X lims'][2],
                                   'X',
                                   0],
                             'Y': [(-self._controlState[8][0] / 2) + self._windowConstants[0] / 2,
                                   (self._windowConstants[0] - self._controlState[8][1] / 2) + self._windowConstants[0] / 2,
                                   0,
                                   abs((self._windowConstants[0] - self._controlState[8][
                                       1] / 2) + self._windowConstants[0] / 2) * 2 + self._windowConstants[0],
                                   self._armConstants[2]['Z lims'][2],
                                   self._armConstants[2]['Z lims'][0] - self._armConstants[2]['Z lims'][2],
                                   'Z',
                                   0],
                             'Attack Depth': [(self._controlState[8][0] / 2 - self._windowConstants[0]) - self._windowConstants[0] / 2,
                                              (2 * self._windowConstants[0] - self._controlState[8][1] / 2) + self._windowConstants[0] / 2,
                                              0,
                                              abs((2 * self._windowConstants[0] - self._controlState[8][
                                                  1] / 2) + self._windowConstants[0] / 2) * 2 + 2 * self._windowConstants[0],
                                              self._armConstants[2]['Attack Depth lims'][2],
                                              self._armConstants[2]['Attack Depth lims'][0] - self._armConstants[2]['Attack Depth lims'][
                                                  2],
                                              'Attack Depth',
                                              0],
                             'Turret': [(self._windowConstants[0] - self._controlState[8][0] / 2) + self._windowConstants[0] / 2,
                                        (self._windowConstants[0] - self._controlState[8][1] / 2) + self._windowConstants[0] / 2,
                                        abs((self._windowConstants[0] - self._controlState[8][0] / 2) + self._windowConstants[0] / 2) * 2,
                                        0,
                                        self._armConstants[2]['Turret lims'][2],
                                        self._armConstants[2]['Turret lims'][0] - self._armConstants[2]['Turret lims'][2],
                                        'Turret',
                                        0]}
        smaller = width
        if width > height:
            smaller = height
        self._windowConstants[1] = - (100 + ((smaller-650)*.153))

        # using Projection mode
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspectRatio = width / height
        gluPerspective(35, aspectRatio, 1, 20000*self._cameraInfo['XYZscaler'])
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0, 0, -500)

    def on_mouse_motion(x, y, dx, dy):
        #_mouseInfo = {'x':None, 'y':None, 'dx':None, 'dy':None, 'scroll_x':None, 'scroll_y':None, 'button':None, 'modifiers':None}
        pass

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        #_mouseInfo = {'x':None, 'y':None, 'dx':None, 'dy':None, 'scroll_x':None, 'scroll_y':None, 'button':None, 'modifiers':None}
        self._cameraInfo['offset']['z'] += scroll_y*50*self._cameraInfo['XYZscaler']

    def on_mouse_press(self, x, y, button, modifiers):
        #_mouseInfo = {'x':None, 'y':None, 'dx':None, 'dy':None, 'scroll_x':None, 'scroll_y':None, 'button':None, 'modifiers':None}
        self._controlState[0] = button
        self._mouseInfo['modifiers'] = modifiers
        self._controlState[1] = 0#iterator1
        for iterator1 in range(len(self._controlState[9])):
            if ((abs((x - self._controlState[8][0] / 2) * self._windowConstants[2] - self._windowConstants[4][2][iterator1][0]) < (self._windowConstants[0] / 2)*self._windowConstants[2])
                and (abs((y - self._controlState[8][1] / 2) * self._windowConstants[2] - self._windowConstants[4][2][iterator1][1]) < (self._windowConstants[0] / 2)*self._windowConstants[2])):
                self._controlState[1] = iterator1 + 1

    def on_mouse_release(self, x, y, button, modifiers):
        #_mouseInfo = {'x':None, 'y':None, 'dx':None, 'dy':None, 'scroll_x':None, 'scroll_y':None, 'button':None, 'modifiers':None}
        self._controlState[0] = -1
        self._controlState[1] = -1
        self._mouseInfo['modifiers'] = -1
    
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if (buttons == 1
            and self._controlState[1] == 0):
            self._cameraInfo['rotation']['x'] -= dy * 0.25
            if modifiers == 0: #self._mouseInfo['modifiers'] == 0:
                self._cameraInfo['rotation']['y'] += dx * 0.25
            else:
                self._cameraInfo['rotation']['z'] += dx * 0.25
        if (buttons == 4
            and self._controlState[1] == 0):
            self._cameraInfo['offset']['x'] += dx * 1.5 *self._cameraInfo['XYZscaler']
            self._cameraInfo['offset']['y'] += dy * 1.5 *self._cameraInfo['XYZscaler']
        if self._controlState[1] > 0:
            if self._windowConstants[4][2][self._controlState[1] - 1][2]:
                thepercent = (((y - self._controlState[9][self._controlState[1] - 1][1][1]
                                +(self._windowConstants[0]/2)-25)
                               / (self._controlState[9][self._controlState[1] - 1][1][3] - self._controlState[9][self._controlState[1] - 1][1][1]))
                              +  self._controlState[11][self._windowConstants[4][0][self._controlState[1] - 1]][7])
            else:
                thepercent = (((x - self._controlState[9][self._controlState[1] - 1][1][0] + (self._windowConstants[0] / 2))
                              / (self._controlState[9][self._controlState[1] - 1][1][2] - self._controlState[9][self._controlState[1] - 1][1][0]))
                              + self._controlState[11][self._windowConstants[4][0][self._controlState[1] - 1]][7])
            if ((self._controlState[11][self._windowConstants[4][0][self._controlState[1] - 1]][7] != 0) and (thepercent > 1)):
                thepercent -= 1
            self.on_text_motion(self._windowConstants[4][2][self._controlState[1] - 1][3], False,
                                (self._controlState[11][self._windowConstants[4][0][self._controlState[1] - 1]][5]
                                 * thepercent
                                 + self._controlState[11][self._windowConstants[4][0][self._controlState[1] - 1]][4])
                                )

    def on_key_press(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            self._controlState = [-1, -1, -1, False, False, False, False]
            arm['arms'][arm['id']]['arm'].releaseTorque()
            pyglet.app.exit()
        print('yolo')

    def update(self, yoyo):
        print('yolo')

    def on_draw(self):
        global arm
        # Clear the current GL Window
        self.clear()

        for iterator1 in range(self._objects[1]):
            glLoadIdentity()
            glTranslatef(self._cameraInfo['offset']['x'],
                         self._cameraInfo['offset']['y'],
                         self._cameraInfo['offset']['z'] - 650*self._cameraInfo['XYZscaler'])
            glRotatef(self._cameraInfo['rotation']['x'], 1, 0, 0)
            glRotatef(self._cameraInfo['rotation']['y'], 0, 1, 0)
            glRotatef(self._cameraInfo['rotation']['z'], 0, 0, 1)
            glTranslatef(self._objects[3][iterator1]['Trans']['x']*self._cameraInfo['XYZscaler'],
                         self._objects[3][iterator1]['Trans']['y']*self._cameraInfo['XYZscaler'],
                         self._objects[3][iterator1]['Trans']['z']*self._cameraInfo['XYZscaler'])
            glRotatef(self._objects[3][iterator1]['Rot']['x'], 1, 0, 0)
            glRotatef(self._objects[3][iterator1]['Rot']['y'], 0, 1, 0)
            glRotatef(self._objects[3][iterator1]['Rot']['z'], 0, 0, 1)

            # Draw the Thing
            glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
            glEnable(GL_COLOR_MATERIAL)
            glColor3f(self._objects[0][iterator1][1][0],
                      self._objects[0][iterator1][1][1],
                      self._objects[0][iterator1][1][2])
            self._objects[0][iterator1][0].draw()
            glDisable(GL_COLOR_MATERIAL)

        for iterator1 in range(len(self._windowConstants[4][0])):
            for iterator2 in [False, True]:
                glLoadIdentity()
                scaler = 0.5
                if iterator2:
                    scaler = ((self._armVARS[arm['id']][self._controlState[11][self._windowConstants[4][0][iterator1]][6]]
                               - self._controlState[11][self._windowConstants[4][0][iterator1]][4])
                              / self._controlState[11][self._windowConstants[4][0][iterator1]][5]
                              + self._controlState[11][self._windowConstants[4][0][iterator1]][7])
                if scaler > 1:
                    scaler -= 1
                self._windowConstants[4][2][iterator1][0] = ((self._controlState[11][self._windowConstants[4][0][iterator1]][0]
                                                   * self._windowConstants[2])
                                                  + (self._controlState[11][self._windowConstants[4][0][iterator1]][2]
                                                     * self._windowConstants[2]
                                                     * scaler))
                self._windowConstants[4][2][iterator1][1] = ((self._controlState[11][self._windowConstants[4][0][iterator1]][1]
                                                   * self._windowConstants[2])
                                                  + (self._controlState[11][self._windowConstants[4][0][iterator1]][3]
                                                     * self._windowConstants[2]
                                                     * scaler))
                if iterator2:
                    glTranslatef(self._windowConstants[4][2][iterator1][0],
                                 self._windowConstants[4][2][iterator1][1],
                                 self._windowConstants[1])
                    glEnable(GL_COLOR_MATERIAL)
                    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
                    glEnable(GL_BLEND)
                    glColor4f(.6,.6,.6,.5)
                    self._windowConstants[4][1].draw()
                    glDisable(GL_BLEND)
                else:
                    glTranslatef(self._windowConstants[4][2][iterator1][0] * self._cameraInfo['XYZscaler'],
                                 self._windowConstants[4][2][iterator1][1] * self._cameraInfo['XYZscaler'],
                                 self._windowConstants[1] * self._cameraInfo['XYZscaler'])
                    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
                    glEnable(GL_COLOR_MATERIAL)
                    glColor3f(1,1,1)
                    self.thing[iterator1].draw()
                glDisable(GL_COLOR_MATERIAL)

    def on_text_motion(self, motion, BLAH = False, Setting = None):
        pass

def Main():
    global arm
    comObj = ComQuery()
    print(comObj)
    try:
        arm['coms'][arm['id']] = str(comObj.device)
    except:
        pass
    import pyglet
    global ORION5
    ORION5 = Window(WINDOW[0], WINDOW[1], 'Gaming Template')
    icon1 = pyglet.image.load('./obj/logo_512x512.png')
    ORION5.set_icon(icon1)
    ORION5.set_location(50,50)
    pyglet.app.run()

if __name__ == '__main__':
    Main()

for item in arm['arms']:
    item['arm'].exit()
