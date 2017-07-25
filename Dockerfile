FROM mikejihbe/sqlplus:latest

RUN pip install --upgrade pip && pip install cx_Oracle

ADD . /simple-db-migrate
RUN cd /simple-db-migrate && python ./setup.py install

ENTRYPOINT ["db-migrate"]
