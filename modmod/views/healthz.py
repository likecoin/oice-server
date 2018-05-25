from cornice import Service

healthz = Service(name='healthz', path='/healthz', description="Health check endpoint")

@healthz.get()
def get_info(request):
    return {
      "code": 200,
      "message": "ok",
    }
