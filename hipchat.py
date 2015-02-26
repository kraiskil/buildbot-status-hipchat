from buildbot.status.base import StatusReceiverMultiService
from buildbot.status.builder import Results, SUCCESS, EXCEPTION, FAILURE
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
      #Does absolute=True here mean that all source stamps are gotten, not just the 'change sources'?
      #If so, probably overkill, if there is a *lot* of source stamps (i.e. big or old projects)
      #but without this, a ForceScheduler build would show [] as the result
      sourcestamp = build.getSourceStamps(absolute=True)[0]
      message +="<br>Branch: %s, revision: %s" % (sourcestamp.branch.encode('utf-8'), sourcestamp.revision.encode('utf-8'))
      color = "green"
      notify = "0"
    elif result == EXCEPTION:
      color = "purple"
    else:
      color = "red"
      notify = "1"

    if result == FAILURE:
      #TODO: can this be cleaner?
      message +="<br>Blamelist: %s" % (", ".join(build.getResponsibleUsers()).encode('utf-8'))
      sourcestamp = build.getSourceStamps(absolute=True)[0]
      message +="<br>Branch: %s, revision: %s" % (sourcestamp.branch.encode('utf-8'), sourcestamp.revision.encode('utf-8'))
      message +="<br>Failing steps:"
      steps = build.getSteps()
      for step in steps:
        if step.getResults()[0] == FAILURE:
          message +="<br>-%s" % (step.getName() )

    # Yes, we are in Twisted and shouldn't do os.system :)
    os.system('curl -H"Content-Type: application/json" -d \'{"message":"%s","color":"%s"}\' "https://api.hipchat.com/v2/room/%s/notification?auth_token=%s&format=json"' % (message, color, self.room_id, self.api_token))
    #just for when you are debugging hipchat instructions
    #log.msg("Send to Hipchat:"+message)

