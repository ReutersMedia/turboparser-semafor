## Overview

Exposes the CMU [TurboParser](http://www.cs.cmu.edu/~ark/TurboParser/) as a web service, and also passes the items to (SEMAFOR 3.0)[http://www.cs.cmu.edu/~ark/SEMAFOR/] for semantic frame extraction.  It depends on the (docker container)[https://github.com/ReutersMedia/semafor-svr/tree/master/semafor-frameparser] for SEMAFOR.


## Running

A docker-compose YAML file is provided, and is the easiest way to deploy.  Download the file locally and run:

```
docker-compose up -d
```

This will launch two linked containers, one with the API, and one with the frame parser.  To use:

```
curl -X POST -d @myfile "http://localhost:8080/parse/EN"
```

As a convience, you can also pass short text fragments via an HTTP GET:

```
curl "http://localhost:8080/parse/EN?t=The+moon+is+made+of+cheese."
```

## Copyright

Copyright (C) 2017 Thomson Reuters

