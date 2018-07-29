from logging import basicConfig, getLogger, DEBUG, INFO
import os, sys, json
from SimpleHTTPServer import SimpleHTTPRequestHandler
import SocketServer
import gitlab

basicConfig(level=DEBUG)
getLogger('urllib3').setLevel(INFO)
logger = getLogger(__name__)

# ---------------------------
# Gitlab service
# ---------------------------

class GitlabService(object):

  def __init__(self, gitlab_url, oauth2_token):
    self.service = gitlab.Gitlab(gitlab_url, oauth_token=oauth2_token)

  def find_project(self, project_id):
    try:
      return self.service.projects.get(project_id)
    except gitlab.exceptions.GitlabGetError as e:
      logger.warn("Failed to find project (project_id=%d): %s", project_id, e)
      return None

  def can_access_project_repository(self, project_id):
    try:
      # try to get repository
      self.service.projects.get(project_id).repository_tree()
      return True
    except gitlab.exceptions.GitlabGetError as e:
      logger.warn("Failed to access repository (project_id=%d): %s", project_id, e)
      return False

# ---------------------------
# web app
# ---------------------------

class GitlabAccessControllHandler(SimpleHTTPRequestHandler):
  GITLAB_SERVER = None
  PROJECT_INFO_FILENAME = '.gitlab-info.json'

  def do_FORBIDDEN(self, message = ''):
    self.send_response(403, "forbidden")
    self.send_header('Content-type', 'text/html')
    self.send_header('Content-Length', len(message))
    self.end_headers()
    self.wfile.write(message)
    self.wfile.close()

  #Handler for the GET requests
  def do_GET(self):
    logger.info("Request Headers: %s", self.headers)
    token = self.headers['X-Forwarded-Access-Token']
    email = self.headers['X-Forwarded-Email']
    base_dir = self.headers.get('X-Document-Base-Dir')
    logger.debug("email: %s, token: %s", email, token)

    if base_dir:
        self.path = base_dir + self.path

    request_path = self.path.split('?', 2)[0]

    project_info = self.get_project_info(request_path)
    if project_info is None or project_info.get('project_id') is None:
      self.do_FORBIDDEN(
          "Access Denied. .gitlab-info.json is not found or invalid")
      return

    if not self.allows_access(token,
        project_info.get('project_id'),
        project_info.get('requires_access_to_code', False)):
      self.do_FORBIDDEN(
          "Access Denied. project: %s, user: %s" % (project_info.get('project_id'), email))
      return

    return SimpleHTTPRequestHandler.do_GET(self)

  def get_project_info(self, request_path):
    if not request_path.endswith('/'):
      request_path = request_path + "/"
    paths = request_path.split('/')
    paths = ['/'.join(paths[0:-i]) for i in range(1, len(paths))]

    proj_filepath = None
    for path in paths:
      proj_filepath = self.translate_path(path + '/' + self.PROJECT_INFO_FILENAME)
      if os.path.isfile(proj_filepath):
        break
    else:
      return None

    try:
      with open(proj_filepath, 'r') as f:
        return json.load(f)
    except (IOError, ValueError):
      logger.exception('Project info file is invalid: %s', proj_filepath)
      return None

  def allows_access(self, token, project_id, requires_access_to_code):
    service = GitlabService(self.GITLAB_SERVER, token)

    project = service.find_project(project_id)
    # the user have no access to this project
    if project is None:
      return False

    # the user requires access to project code
    if requires_access_to_code:
      return service.can_access_project_repository(project_id)

    return True

# Start application
def main():
  if (len(sys.argv) < 3):
    print 'Usage: # python %s PORT GITLAB_URL' % sys.argv[0]
    quit()

  port = int(sys.argv[1], 10)
  GitlabAccessControllHandler.GITLAB_SERVER = sys.argv[2]

  try:
    SocketServer.TCPServer.allow_reuse_address = True
    server = SocketServer.TCPServer(('', port), GitlabAccessControllHandler)
    logger.info('Started httpserver on port %d', port)

    server.serve_forever()

  except KeyboardInterrupt:
    logger.info('^C received, shutting down the web server')
    server.socket.close()

if __name__ == '__main__':
  main()

