FROM python:latest

RUN apt-get -y update && apt-get install -y apt-utils && apt-get -y upgrade
RUN apt-get install -y libgl1-mesa-glx ffmpeg libsm6 libxext6 


COPY ./ /app
WORKDIR /app

RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 9084

ENTRYPOINT ["python"]
CMD ["server.py"]
