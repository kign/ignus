# Simple URL shortener implementation

Server code is written in Python using `flask` and could be deployed in any compatible container, 
such as [Google App Engine](https://cloud.google.com/appengine) or similar (note that a non-GAE
deployment might need additional logic to handle static content).

[Google Firestore](https://cloud.google.com/firestore/) serves as a convinient NoSQL database backend. 
It is relatively straightforward to add alternative backends by writing a driver class implementation.

Before testing or deployment, you need to 

  1. Edit `web/app.yaml` to add Google and/or Microsoft syndicated login parameters;
     
  2. Create file `web/secrets/firestore-auth.json` with Google Firestore authentication;
     
  3. Run `etc/install.sh`. 
     
Now run `etc/run.sh flask` to start a local server at port `:8081`.  