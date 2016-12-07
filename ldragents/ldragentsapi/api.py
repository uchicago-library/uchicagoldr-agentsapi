from flask import g, jsonify, Blueprint, request, send_file, make_response
from flask_restful import Resource, Api, reqparse
from os import scandir
from os.path import join
import re
from uuid import uuid4
#from werkzeug.utils import secure_filename

from ldrpremisbuilding.utils import *
from uchicagoldrapicore.responses.apiresponse import APIResponse
from uchicagoldrapicore.responses.apiresponse import APIResponse
from uchicagoldrapicore.lib.apiexceptionhandler import APIExceptionHandler

__AUTHOR__ = "Tyler Danstrom"
__EMAIL__ = "tdanstrom@uchicago.edu"
__VERSION__ = "1.0.0"
__DESCRIPTION__ = "a restful application to enable getting and posting PREMIS agent data over the web"
__COPYRIGHT__ = "University of Chicago, 2016"

_EXCEPTION_HANDLER = APIExceptionHandler()

def get_current_agents():
    from flask import current_app
    def build_a_generator(path):
        for n_entry in scandir(path):
            if n_entry.is_dir():
                yield from build_a_generator(n_entry.path)
            elif n_entry.path.endswith("agent.xml"):
                yield extract_core_information_agent_record(n_entry.path)
    return build_a_generator(current_app.config["AGENTS_PATH"])

def expand_agents_list(term=None, identifier=None):
    print(identifier)
    a_generator = get_current_agents()
    tally = 1
    output = {}
    for n_item in a_generator:
        row_dict = {'name':n_item.name, 'type':n_item.type,
                    'identifier':n_item.identifier, 'events':n_item.events}
        if term and isinstance(term, str):
            if term in n_item.name:
                output[tally] = row_dict
        elif identifier:
            if n_item.identifier.strip() == identifier.strip():
                output[tally] = row_dict
                break
        else:
            output[tally] = row_dict
        tally += 1
    return output

def is_there_a_result(api_category, a_dict):
    if a_dict.keys() == 0:
        return APIResponse("fail", data={api_category: "no results"})
    else:
        if api_category == "agent":
            return APIResponse("success", data={api_category: a_dict[list(a_dict.keys())[0]]})
        else:
            return APIResponse("success", data={api_category: a_dict})

def evaluate_input(a_dict):
    from flask import current_app
    assert isinstance(a_dict, dict)
    for key, value in a_dict.items():
        if key not in current_app.config["VALID_KEYS"]:
            return (False, "{} is not a legal key")
        elif not re.compile(current_app.config[key.upper()]).match(value):
            return (False, "{} does not match required ".format(value) +\
                    "specification for key {}".format(key))
    return True

class AllAgents(Resource):
    def get(self):
        try:
            query = request.args.get("term")
            answer = expand_agents_list(term=query)
            resp = is_there_a_result("agents", answer)
            return jsonify(resp.dictify())
        except Exception as error:
            return jsonify(_EXCEPTION_HANDLER.handle(error).dictify())

    def post(self):
        from flask import current_app
        try:
            data = request.get_json(force=True)
            dto = namedtuple("adto", "edit_fields identifier root " + \
                             ' '.join(data.get("fields")))(data.get("fields"), None,
                             current_app.config["AGENTS_PATH"], *[data.get(x) for x in data.get("fields")])
            was_it_made = create_or_edit_an_agent_record(dto)
            if was_it_made[0]:
                resp = APIResponse("success", data={'agents':{'result':'new', 'identifier': was_it_made[1]}})
            else:
                resp = APIResponse("fail", errors=["could not create a new agent record"])
            return jsonify(resp.dictify())
        except Exception as error:
            return jsonify(_EXCEPTION_HANDLER.handle(error).dictify())

class ASpecificAgent(Resource):
    def get(self, premisid):
        try:
            answer = expand_agents_list(identifier=premisid)
            resp = is_there_a_result("agent", answer)
            return jsonify(resp.dictify())
        except Exception as error:
            return jsonify(_EXCEPTION_HANDLER.handle(error).dictify())

    def post(self, premisid):
        from flask import current_app
        try:
            data = request.get_json(force=True)
            dto = namedtuple("adto", "edit_fields identifier root " + \
                             ' '.join(data.get("fields")))(data.get("fields"), premisid,
                             current_app.config["AGENTS_PATH"], *[data.get(x) for x in data.get("fields")])
            was_it_made = create_or_edit_an_agent_record(dto)
            if was_it_made[0]:
                resp = APIResponse("success", data={'agents':{'result':'new', 'identifier': was_it_made[1]}})
            else:
                resp = APIResponse("fail", errors=["could not create a new agent record"])
            return jsonify(resp.dictify())
        except Exception as error:
            return jsonify(_EXCEPTION_HANDLER.handle(error).dictify())

class AgentEvents(Resource):
    def get(self, premisid):
        try:
            answer = expand_agents_list(identifier=premisid)
            tally = 1
            if len(list(answer.keys())) == 1:
                resp = APIResponse("success", data={"agent events": self._populate_output(answer)})
            else:
                resp = APIResponse("fail", data={"agent events": "no results"})
            return jsonify(resp.dictify())
        except Exception as error:
            return jsonify(_EXCEPTION_HANDLER.handle(error).dictify())

    def post(self, premisid):
        from flask import current_app
        try:
            data = request.get_json(force=True)
            dto = namedtuple("edto", "identifier root event")\
                            (premisid, current_app.config["AGENTS_PATH"], data.get("event"))
            was_it_added = add_event_to_a_premis_agent(dto)
            if was_it_added:
                resp  = APIResponse("success",
                                    data={"agent event": {"result":"added event",
                                                          "identifier": premisid,
                                                          "new_event":data.get("eventid")}})
            else:
                resp = APIResponse("fail", errors=["could not attach event {} to {}".format(data.get("linkedevent"), premisid)])
            return jsonify(resp.dictify())
        except Exception as error:
            return jsonify(_EXCEPTION_HANDLER.handle(error).dictify())

    def _populate_output(self, answer_dict):
        keynum = list(answer_dict.keys())[0]
        out = {'agent': answer_dict.get(keynum).get("identifier"), "events":[]}
        for n_event in answer_dict.get(keynum).get("events"):
            out['events'].append(n_event.get("identifier"))
        return out

# Create our app, hook the API to it, and add our resources
BP = Blueprint("ldragentsapi", __name__)
API = Api(BP)

# file retrieval endpoints
API.add_resource(AllAgents, "/agents")
API.add_resource(ASpecificAgent, "/agents/<string:premisid>")
API.add_resource(AgentEvents, "/agents/<string:premisid>/events")
