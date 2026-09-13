FROM python:3.11-slim
WORKDIR /home/myapp
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV NET_TEXTFSM=/usr/local/lib/python3.11/site-packages/ntc_templates/templates
CMD ["python", "worker.py"]