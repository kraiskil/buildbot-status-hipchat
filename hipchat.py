from buildbot.status.base import StatusReceiverMultiService
from buildbot.status.builder import Results, SUCCESS, EXCEPTION
import os, urllib
#from buildbot.status import base
#from twisted.python import log


class HipChatStatusPush(StatusReceiverMultiService):

  def __init__(self, api_token, room_id, localhost_replace=False, **kwargs):
      StatusReceiverMultiService.__init__(self)

      self.api_token = api_token
      self.room_id = room_id
      self.localhost_replace = localhost_replace

  def setServiceParent(self, parent):
    StatusReceiverMultiService.setServiceParent(self, parent)
    self.master_status = self.parent
    self.master_status.subscribe(self)
    self.master = self.master_status.master

  def disownServiceParent(self):
    self.master_status.unsubscribe(self)
    self.master_status = None
    for w in self.watched:
      w.unsubscribe(self)
    return StatusReceiverMultiService.disownServiceParent(self)

  def builderAdded(self, name, builder):
    return self  # subscribe to this builder

  def buildFinished(self, builderName, build, result):
    url = self.master_status.getURLForThing(build)
    if self.localhost_replace:
      url = url.replace("//localhost", "//%s" % self.localhost_replace)

    message = "<a href='%s'>%s</a> %s" % (url, builderName, Results[result].upper()) 
    if result == SUCCESS:
      color = "green"
      notify = "0"
    elif result == EXCEPTION:
      color = "purple"
    else:
      color = "red"
      notify = "1"

    # Yes, we are in Twisted and shouldn't do os.system :)
    os.system('curl -H"Content-Type: application/json" -d \'{"message":"%s","color":"%s"}\' "https://api.hipchat.com/v2/room/%s/notification?auth_token=%s&format=json"' % (message, color, self.room_id, self.api_token))
    #just for when you are debugging hipchat instructions
    #log.msg("Send to Hipchat:"+message)

