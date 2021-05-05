'''
client.py contains the wrapping interface for all the other modules (aside from cli.py)
'''
import requests
import dockerutils


class GalaxyClient:
    '''
    The primary class for the client - this is the authenticated context from
    which all authentication flows.
    '''
    headers = {}
    api_root = ''
    token = ''
    docker_client = None

    def __init__(self, api_root, user='', password='', container_engine='podman'):
        self.api_root = api_root
        if user != '' and password != '':
            self.token = requests.post(
                            api_root + 'automation-hub/v3/auth/token',
                            auth=(user, password)
                            ).json().get('token')
            self.headers = {
                'accept': 'application/json',
                'Authorization': f'Token {self.token}'
                }
            self.docker_client = dockerutils.DockerClient(user, password, container_engine)

    def pull_image(self, image_name):
        ''' pulls an image with the given credentials '''
        self.docker_client.pull_image(image_name)

    def tag_image(self, image_name, newtag, version='latest'):
        ''' tags a pulled image with the given newtag and version '''
        self.docker_client.tag_image(image_name, newtag, version=version)

    def push_image(self, image_tag):
        ''' pushs a image '''
        self.docker_client.push_image(image_tag)
