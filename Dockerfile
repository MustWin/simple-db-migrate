FROM mikejihbe/sqlplus:latest

RUN mkdir /simple-db-migrate
ADD requirements.txt /simple-db-migrate/requirements.txt
WORKDIR /simple-db-migrate
RUN pip install --upgrade pip && pip install -r requirements.txt
ADD . /simple-db-migrate
RUN python ./setup.py install

WORKDIR /db
ENTRYPOINT ["db-migrate"]
