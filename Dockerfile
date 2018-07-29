FROM nginx

RUN apt-get update \
  && apt-get install -y \
    supervisor \
    curl \
    python-pip \
  && apt-get clean
RUN mkdir -p /var/log/supervisor

# install oauth2_proxy
RUN curl -sSL https://github.com/bitly/oauth2_proxy/releases/download/v2.2/oauth2_proxy-2.2.0.linux-amd64.go1.8.1.tar.gz \
  | tar -zxC /usr/local/bin --strip=1

# install python libraries
RUN pip install python-gitlab

COPY docker /app/docker
RUN ln -s /app/docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY gitlab-access-controlled-server.py /app/gitlab-access-controlled-server.py

ENV DOC_ROOT /srv/nginx/pages
RUN mkdir -p $DOC_ROOT

CMD ["/app/docker/entrypoint.sh"]

