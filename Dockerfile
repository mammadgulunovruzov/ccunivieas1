
# we start from slim python images, which already has all the requirements for python
FROM python:3.8

# this will be working directory inside of the image
WORKDIR /usr/src/app

# copy python library requirements.txt
COPY requirements.txt ./

# instal those requirements
RUN pip install --no-cache-dir -r requirements.txt

# copy source files
COPY . .

EXPOSE 8080

ENV NAME serviceEnv

# execute application
CMD ["python", "./collector.py"]