import flask
from flask import Response, request
import json
from haiku import HaikuDetector

app = flask.Flask(__name__)

class JSONEncoder(json.JSONEncoder):
    """ This encoder will serialize all entities that have a to_dict
    method by calling that method and serializing the result. """

    def encode(self, obj):
        if hasattr(obj, 'to_dict'):
            obj = obj.to_dict()
        return super(JSONEncoder, self).encode(obj)

    def default(self, obj):
        if hasattr(obj, 'as_dict'):
            return obj.as_dict()
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        raise TypeError("%r is not JSON serializable" % obj)


def jsonify(obj, status=200, headers=None):
    """ Custom JSONificaton to support obj.to_dict protocol. """
    jsondata = json.dumps(obj, cls=JSONEncoder)
    if 'callback' in request.args:
        jsondata = '%s(%s)' % (request.args.get('callback'), jsondata)
    return Response(jsondata, headers=headers,
                    status=status, mimetype='application/json')


@app.route("/")

def get_haikus():
  # parse args  
  screen_name = request.args.get('name', None)
  n_pages = int(request.args.get('pages', 10))
  debug = requesr.args.get('debug', False)
  
  h = HaikuDetector(
    screen_name = screen_name,
    n_pages = n_pages,
    debug = debug
  )
  
  haikus =  h.go()

  # return json 
  return jsonify(haikus)

if __name__ == "__main__":
  app.debug = True
  app.run(host='0.0.0.0', port=5000)

