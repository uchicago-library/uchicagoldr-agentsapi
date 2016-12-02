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

class DataTransferObject(object):
    def __init__(self, agent_name, agent_type):
        self.name = agent_name
        self.type = agent_type

    def __str__(self):
        d = {"name": self.name,
             "type": self.type}
        return jsonify(d)

def evaluate_input(a_dict):
    from flask import current_app
    assert isinstance(a_dict, dict)
    for key, value in a_dict.items():
        if key not in current_app.config["VALID_KEYS"]:
            return (False, "{} is not a legal key")
        elif not re.compile(current_app.config[key.upper()]).match(value):
            return (False, "{} does not match required specification for key {}".\
            format(value, key))
    return True

def get_current_agents():
    from flask import current_app
    return build_a_generator(current_app.config["AGENTS_PATH"])

def build_a_generator(path):
    for n_entry in scandir(path):
        if n_entry.is_dir():
            yield from build_a_generator(n_entry.path)
        elif n_entry.path.endswith("agent.xml"):
            yield extract_core_information_agent_record(n_entry.path)

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
        except Exception as error:
            return jsonify(_EXCEPTION_HANDLER.handle(error).dictify())

    def post(self):
        # need to post a new agent record containing information from post data
        from flask import current_app
        try:
            data = request.get_json(force=True)
            test_result = evaluate_input(data)
            if test_result:
                new_agent = DataTransferObject(data["name"], data["type"])
                new_agent = create_new_premis_agent(current_app.config["AGENTS_PATH"], new_agent)
                resp = APIResponse("success", data={"result":"created", "identifier": new_agent})
            else:
                resp = APIResponse("fail", data={"result": "not created"})
            return jsonify(resp.dictify())
        except Exception as error:
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
                output = {"status":"fail", "error":"no results"}
            resp = APIResponse(output["status"], data=output)
            return jsonify(resp.dictify())
        except Exception as error:
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
                data = request.get_json(force=True)
                test_result = evaluate_input(data)
                if test_result:
                    edited_field_name = data.get("field")
                    edited_field_value = data.get("value")
                    new_agent = create_new_premis_agent(current_app.config["AGENTS_PATH"], new_agent, edit_identifier=answer.identifier)
                    resp = APIResponse("success", data={"field":edited_field, "value":edited_value, "identifier":answer.identifier})
                else:
                    resp = APIResponse("fail", data={"result": test_result[1]})
            else:
                resp = APIResponse("fail", data={"result":"no results"})
            return jsonify(resp.dictify())

        except Exception as error:
            return jsonify(_EXCEPTION_HANDLER.handle(error).dictify())
        except Exception as error:
            return jsonify(_EXCEPTION_HANDLER.handle(error).dictify())

class AgentEvents(Resource):
    def get(self, premisid):
        # need to get the premisid given, locate the agent with that 
        # premisid as its identifier, and retrieve the events associated 
        # with that agent. It should then package up those events records 
        # into a dictionary for return as an APIResponse
        try:
            agents_generator = get_current_agents()
            answer = None
            for n_agent in agents_generator:
                if n_agent.identifier == premisid:
                    answer = n_agent
            if answer:
                output = {"status":"success",
                          "agent_loc": join("/agents", answer.identifier),
                          "events":[]}
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

    def post(self, premisid):
        # need to get the premisid id given, locate the agent with that premisid 
        # as its identiifier, and create an premis event out of the data passed 
        # in the post data and finally attach that new event to the agent identified.
        try:
            agents_generator = get_current_agents()
            answer = None
            for n_agent in agents_generator:
                if n_agent.identifier == premisid:
                    answer = n_agent
            if answer:
                data = request.get_json(force=True)
                test_result = evaluate_input(data)
                if test_result:
                    resp = APIResponse("success", data=data).dictify()
                else:
                    resp = APIResponse("fail", data={"result": test_result[1]})
            else:
                resp = APIResponse("fail", data={"result":"no results"})
            return jsonify(resp.dictify())
        except Exception as error:
            return jsonify(_EXCEPTION_HANDLER.handle(error).dictify())

# Create our app, hook the API to it, and add our resources
BP = Blueprint("ldragentsapi", __name__)
API = Api(BP)

# file retrieval endpoints
API.add_resource(AllAgents, "/agents")
API.add_resource(ASpecificAgent, "/agents/<string:premisid>")
API.add_resource(AgentEvents, "/agents/<string:premisid>/events")
