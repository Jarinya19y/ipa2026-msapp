FROM python
WORKDIR /home/myapp
COPY ./templates/* /home/myapp/templates/
COPY ./static/* /home/myapp/static/
COPY ./app.py /home/myapp/
RUN pip install flask
RUN pip install pymongo
CMD ["python", "/home/myapp/app.py"]
EXPOSE 8080