# Available Endpoints

### /agents

#### Methods

##### GET

This will return the records for all agents in the system

output

~~~
{
  "data": {
    "agents": {
      "1": {
        "events": [],
        "identifier": "534562be67dd4b75984b68665ced14fb",
        "name": "test user",
        "type": "person"
      },
      "2": {
        "events": [
          "foo"
        ],
        "identifier": "ce8cc475f8254281918e610ba474c81e",
        "name": "john doe",
        "type": "person"
      }
    }
  },
  "errors": null,
  "status": "success"
}
~~~

##### POST

post data required

~~~
{"fields":["name","type"], "name":"john doe", "type":"person"}
~~~

### /agents/[agent id]

#### Methods

##### GET 

This will return either a "no results" or a single record for the agent with identifier that matches the string [agent id].

output 

~~~
{
  "data": {
    "agent": {
      "events": [],
      "identifier": "534562be67dd4b75984b68665ced14fb",
      "name": "test user",
      "type": "person"
    }
  },
  "errors": null,
  "status": "success"
}
~~~

##### POST

post data required

~~~
{"fields":["name","type"], "name":"jane doe"}
~~~


### /agents/[agent id\/events

#### Methods

##### GET 

This will return a list of event identifiers linked to the agent with identifier that matches the string [agent id].

output

~~~
{
  "data": {
    "agent events": {
      "agent": "534562be67dd4b75984b68665ced14fb",
      "events": []
    }
  },
  "errors": null,
  "status": "success"
}
~~~

##### POST

post data required

~~~~
{"event":"abcdefghijk"}
~~~~
