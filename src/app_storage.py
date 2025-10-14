from replit.object_storage import Client

class AppStorage:
  def __init__(self):
    self.client = Client()

  def writedata(self, filname, data):
    self.client.upload_from_text(filname, data)

  def readdata(self, filname):
    if(not self.client.exists(filname)):
      return None
    return self.client.download_as_text(filname)