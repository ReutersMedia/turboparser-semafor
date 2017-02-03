FROM ubuntu:14.04
MAINTAINER kenneth.ellis@thomsonreuters.com

RUN apt-get update && \
    apt-get -y install build-essential curl cython automake autoconf python-pip python-numpy \
                       uwsgi uwsgi-plugin-python nginx jq supervisor && \
    pip install regex nltk Flask python-logstash && \
    curl -L https://github.com/andre-martins/TurboParser/archive/master.tar.gz | tar xz -C / && \
    cd /TurboParser-master && \
    ./install-ubuntu.sh && \
    python -m nltk.downloader -d /usr/share/nltk_data punkt && \
    cd /TurboParser-master/python && \
    ./install_wrapper.sh && \
    mkdir /usr/local/lib/turboparser && \
    cp build/lib.linux-x86_64-2.7/turboparser.so /usr/local/lib/turboparser && \
    cp -R ../deps/local/lib/* /usr/local/lib/turboparser && \
    cp ../libturboparser/libturboparser.so /usr/local/lib/turboparser && \
    python setup.py install && \
    addgroup nginx && \
    adduser --system --disabled-password --no-create-home --disabled-login nginx && \
    apt-get -y remove build-essential automake autoconf && \
    apt-get -y autoremove && \
    apt-get clean && \
    rm -rf /TurboParser-master && \
    rm -rf /opt/Turboparser
    
ENV LD_LIBRARY_PATH=/usr/local/lib/turboparser \
    FRAMESERVER_PORT=8085 \
    FRAMESERVER_HOST=localhost

COPY src /tmp/src
COPY conf /tmp/conf

RUN cd /tmp/src && \
    python setup.py install --root / && \
    head -n -1 /root/.bashrc > /root/.bashrc && \
    cp /tmp/conf/uwsgi.ini /root/uwsgi.ini && \
    cp /tmp/conf/supervisord.conf /etc/supervisord.conf && \
    cp /tmp/conf/nginx.conf /etc/nginx/nginx.conf && \
    cp /tmp/conf/uwsgi_params /root/uwsgi_params && \
    cp /tmp/conf/run.sh /root/run.sh && \
    cp /tmp/conf/nlp_pipeline.config /nlp_pipeline.config && \
    cd / && \
    rm -rf /tmp/conf && \
    rm -rf /tmp/src
    
CMD ["/root/run.sh"]


