from flask import Flask, request, jsonify, abort
import sys
import logging
import json
import time
import os
import re
import Queue
import threading
import socket

from turbopy import nlp_pipeline

from logstash.formatter import LogstashFormatterVersion1
from logging.handlers import RotatingFileHandler


_NLP_PIPELINE = None
def get_pipeline():
    global _NLP_PIPELINE
    if _NLP_PIPELINE is None:
        _NLP_PIPELINE = nlp_pipeline.NLPPipeline('/nlp_pipeline.config')
        # warm it up
        _NLP_PIPELINE.parse_conll('The moon is made of cheese','EN')
    return _NLP_PIPELINE


#### LOGGING SETUP ####

class LogstashFormatter(LogstashFormatterVersion1):
    @classmethod
    def serialize(cls,message):
        return json.dumps(message)

log_level = os.getenv("LOG_LEVEL","INFO")
try:
    numeric_level = getattr(logging, log_level)
except:
    print("Invalid log level: {0}".format(log_level))
    numeric_level = logging.INFO

root = logging.getLogger()

root.setLevel(numeric_level)

handler = RotatingFileHandler(os.getenv("PYTHON_LOG_FILE","/var/log/turbopy.log"),
                              mode='ab',
                              maxBytes=1000000,
                              backupCount=2)
handler.setFormatter(LogstashFormatter(tags=['python']))
root.addHandler(handler)



#------------------------------------------------------------------------
# App maintenance -- APP IS STARTED AT THE END OF THE FILE
#------------------------------------------------------------------------

# App instance
application = Flask(__name__)

LOGGER = logging.getLogger(__name__)


def frameparser_sender(s,msg):
    LOGGER.info("Sending {0} bytes to frameparser".format(len(msg)))
    s.sendall(msg)
    s.shutdown(socket.SHUT_WR)

def clean_conll(s):
    # add two fields per line
    return '\n'.join([x+'\t_\t_' for x in s.split('\n') if len(x)>0]) + '\n\n'

def postproc_conll(s):
    lines = [ x.split('\t') for x in s.split('\n') ]
    return [ (x[1],x[4],x[7]) for x in lines if len(x)>=8 ]
    
def proc_input(d,pipeline_name):
    LOGGER.info("Received request for pipeline {0}, size={1}".format(pipeline_name,len(d)))
    tstart = time.time()
    pipe = get_pipeline()
    conll = pipe.parse_conll(d,pipeline_name)
    conll = clean_conll(conll)
    LOGGER.info("TurboParser took {0} sec for {1} bytes".format(time.time()-tstart,len(d)))
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.settimeout(15)
    s.connect((os.getenv("FRAMEPARSER_HOST","localhost"),int(os.getenv("FRAMEPARSER_PORT",8085))))
    chunks = []
    sender = threading.Thread(target=frameparser_sender,args=(s,conll))
    sender.start()
    while True:
        d = s.recv(1000)
        if len(d)==0:
            break
        chunks.append(d)
        LOGGER.info("Received {0} bytes from frame parser".format(len(d)))
    sender.join()
    LOGGER.info("Closing frameparser socket")
    s.close()
    fp_sentences = [json.loads(x) for x in ''.join(chunks).split('\n')[:-1]]
    conll_sentences = conll.split('\n\n')[:-1]
    # should be same count
    if len(fp_sentences) != len(conll_sentences):
        LOGGER.error("FP sentences={0}, CONLL sentences={1}, mismatched.  Discarding CONLL data.".format(len(fp_sentences),len(conll_sentences)))
        conll_sentences = [ None for _ in fp_sentences ]
    else:
        conll_sentences = [ postproc_conll(x) for x in conll_sentences ]
    r = []
    for i in range(len(conll_sentences)):
        r.append({'conll':conll_sentences[i],
                  'frames':fp_sentences[i]})
    return r
    
        
@application.route("/parse/<string:pipeline>",methods=['POST','GET'])
def parse_frames(pipeline):
    if request.method == 'GET':
        # parse from text parameter
        d = request.args.get('t')
        if d == None:
            abort(400)
    else:
        d = request.get_data(as_text=True)
    tstart = time.time()
    try:
        r = proc_input(d,pipeline.upper())
    except:
        LOGGER.exception("Error processing input")
        abort(500)
    return jsonify(r)
        
@application.route("/keepalive",methods=['GET'])
def keepalive():
    proc_input("This is a test.","EN")
    return "OK"


if __name__ == '__main__':
    application.run(debug=True)

