from flask import g, jsonify, Blueprint, request, send_file, make_response
from flask_restful import Resource, Api, reqparse
from os import scandir
from uuid import uuid4
from werkzeug.utils import secure_filename

from pypremis.lib import PremisRecord
from pypremis.nodes import *
from uchicagoldrapicore.responses.apiresponse import APIResponse
from uchicagoldrapicore.responses.apiresponse import APIResponse
from uchicagoldrapicore.lib.apiexceptionhandler import APIExceptionHandler

__AUTHOR__ = "Tyler Danstrom"
__EMAIL__ = "tdanstrom@uchicago.edu"
__VERSION__ = "1.0.0"
__DESCRIPTION__ = "a restful application to enable getting and posting PREMIS agent data over the web"
__COPYRIGHT__ = "University of Chicago, 2016"

_EXCEPTION_HANDLER = APIExceptionHandler()

class AgentField(object):
    def __init__(self, fieldname, fieldvalue):
        if fieldname in ["name", "type", "event"]:
            self.field = fieldname
            self.value = fieldvalue

    def __str__(self):
        return jsonify({"field": self.field, "value": self.value})

class Agent(object):
    def __init__(self, agent_fields):
        self.fields = agent_fields
        self.identifier = uuid4().hex

    def __str__(self):
        return jsonify({"name": [x.value for x in self.fields if x.field == 'name'][0],
                        "type": [x.value for x in self.fields if x.field == "type"][0],
                        "identifier": self.identifier})

def evaluate_input(a_dict):
    from flask import current_app
    assert isinstance(a_dict, dict)
    for key, value in a_dict.items():
        new_field_object = AgentField(key, value)

def get_current_agents():
    from flask import current_app
    return build_a_generator(current_app.config["AGENTS_PATH"])

def build_a_generator(path):
    for n_entry in scandir(path):
        if n_entry.is_dir():
            yield from build_a_generator(n_entry.path)
        elif n_entry.path.endswith("agent.xml"):
            yield extract_core_information_from_agent_record(n_entry.path)

class AllAgents(Resource):
    def get(self):
        try:
            agents_generator = get_current_agents()
            query = request.args.get("term")
            tally = 1
            answer = {}
            if query:
                # need to return any agent record with word in query variable
                # in the agent name element
                for n_agent in agents_generator:
                    if query in n_agent.name:
                        row_dict = {'agent name':n_agent.name, 'agent role': n_agent.role,
                                    'agent type': n_agent.type}
                        answer[tally] = row_dict
                        tally += 1
            else:
                # need to return a list of all agents in the system
                tally = 1
                for n_agent in agents_generator:
                    row_dict = {'agent name':n_agent.name, 'agent role': n_agent.role,
                                'agent type': n_agent.type}
                    answer[tally] = row_dict
                    tally += 1
            if len(answer.keys()) == 0:
                resp = APIResponse("success", data={"agents": "no results"})
            else:
                resp = APIResponse(answer["status"], data={"agents": answer})
            return jsonify(resp.dictify())
        except Exception as errorrror:
            return jsonify(_EXCEPTION_HANDLER.handle(error).dictify())

    def post(self):
        # need to post a new agent record containing information from post data
        try:
            data = request.get_json(force=True)

            return jsonify(APIResponse("success", data=data).dictify())
        except Exception as errorrror:
            return jsonify(_EXCEPTION_HANDLER.handle(error).dictify())

class ASpecificAgent(Resource):
    def get(self, premisid):
        try:
            agents_generator = get_current_agents()
            answer = None
            for n_agent in agents_generator:
                if n_agent.identifier == premisid:
                    answer = n_agent
            if answer:
                output = {"status":"success", "agent_name":answer.name, "agent_role":answer.role,
                          "agent_type":answer.type, "loc": join("/agent", answer.identifier)}
            else:
                output = {"status":"failure", "error":"no results"}
            resp = APIResponse(output["status"], data=output)
            return jsonify(resp.dictify())
        except Exception as errorrror:
            return jsonify(_EXCEPTION_HANDLER.handle(error).dictify())

    def post(self, premisid):
        # need to post an updated agent record for the agent with premisid
        try:
            agents_generator = get_current_agents()
            answer = None
            for n_agent in agents_generator:
                if n_agent.identifier == premisid:
                    answer = n_agent
            if answer:
                parser = reqparse.RequestParser()
                parser.add_argument("edited_fields", type=EditedField, action='append',
                                    help="A list of key:value pairs of field name " +\
                                         "and values to modify for this agent")
                args = parser.parse_args()
                add_event_to_agent(answer.identifier, args["eventid"])
            else:
                output = {"status":"failure", "error":"no results"}
            return APIResponse(output["status"], data=output)
        except Exception as error:
            return jsonify(_EXCEPTION_HANDLER.handle(error).dictify())

class AgentEvents(Resource):
    def get(premisid):
        # need to get the premisid given, locate the agent with that premisid as its identifier,
        # and retrieve the events associated with that agent. It should then package up those events
        # records into a dictionary for return as an APIResponse
        try:
            agents_generator = get_current_agents()
            answer = None
            for n_agent in agents_generator:
                if n_agent.identifier == premisid:
                    answer = n_agent
            if answer:
                output = {"status":"success", "agent_loc": join("/agents", answer.identifier), "events":[]}
                events_dict = {}
                for n_event in n_agent.events:
                    event_loc = join(n_agent.identiifer, "/events", n_event.identifier)
                    event_dict = {"loc":event_loc}
                    output["events"].append(event_dict)
            else:
                output = {"status":"failure", "error":"no results"}
            resp = APIResponse(output["status"], data=output)
            return jsonify(resp.dictify())
        except Exception as error:
            return jsonify(_EXCEPTION_HANDLER.handle(error).dictify())

    def post(premisid):
        # need to get the premisid id given, locate the agent with that premisid as its identiifier, 
        # and create an premis event out of the data passed in the post data and finally attach that new
        # event to the agent identified.
        try:
            agents_generator = get_current_agents()
            answer = None
            for n_agent in agents_generator:
                if n_agent.identifier == premisid:
                    answer = n_agent
            if answer:
                parser = reqparse.RequestParser()
                parser.add_argument("eventid", type=str, help="An agent's name")
                args = parser.parse_args()
                add_event_to_agent(answer.identifier, args["eventid"])
            else:
                output = {"status":"failure", "error":"no results"}
            return APIResponse(output["status"], data=output)
        except Exception as error:
            return jsonify(_EXCEPTION_HANDLER.handle(error).dictify())

# Create our app, hook the API to it, and add our resources
BP = Blueprint("ldragentsapi", __name__)
API = Api(BP)

# file retrieval endpoints
API.add_resource(AllAgents, "/agents")
API.add_resource(ASpecificAgent, "/agents/<string:premisid>")
API.add_resource(AgentEvents, "/agents/<string:premisid>/events")
