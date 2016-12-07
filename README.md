# Available Endpoints

### /agents

#### Methods

##### GET

This will return the records for all agents in the system

##### POST

post data required

~~~
{"fields":["name","type"], "name":"john doe", "type":"person"}
~~~

### /agents/[agent id]

#### Methods

##### GET 

This will return either a "no results" or a single record for the agent with identifier that matches the string [agent id].

##### POST

post data required

~~~
{"fields":["name","type"], "name":"jane doe"}
~~~


### /agents/[agent id\/events

#### Methods

##### GET 

This will return a list of event identifiers linked to the agent with identifier that matches the string [agent id].

##### POST

post data required

~~~~
{"event":"abcdefghijk"}
~~~~
