'''
Holds all of the functions used by GalaxyClient to handle Docker operations
'''

from subprocess import run


class DockerClient:

    engine = ''

    def __init__(self, user, password, engine):
        self.engine = engine
        run([engine, 'login', '--user', user, '--password', password])

    def pull_image(self, image_name, registry=''):
        '''
        '''
        run([self.engine, 'pull', image_name])


    def tag_image(self, image_name, newtag, version='latest'):
        '''
        '''
        run([self.engine, 'image', 'tag', image_name, f'{newtag}:{version}'])


    def push_image(self, image_tag):
        '''
        Pushes an image
        '''
        run([self.engine, 'push', image_tag])
