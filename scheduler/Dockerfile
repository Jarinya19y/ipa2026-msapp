FROM python
WORKDIR /home/myapp
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080
CMD ["python", "scheduler.py"]