FROM python:3.13.3

COPY . .
RUN pip install -r requirements.txt

EXPOSE 9998

ENTRYPOINT ["python", "a2a_server_calendar_agent.py"]