FROM python:3.6.9-slim
 
# Set the working directory to /app
WORKDIR /app
 
# Copy the current directory contents into the container at /app
COPY . /app

RUN mkdir -p /data/FY4A/

RUN mkdir -p /data/FY4A-NC/
 
# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt && \
	 apt-get -y update && apt-get install -y gfortran


# Make port 80 available to the world outside this container
#EXPOSE 80
 
# Define environment variable
#ENV NAME World

CMD ["python","a0_ll2lc_fy4a.py"]
 
CMD ["f2py","-m","index2data","-c","index2data.f90"]

# Run app.py when the container launches
#CMD ["python", "main_decode_python.py"]

#CMD ["python", "app.py"]


#docker build -t fy4a .

#docker run --rm -v /home/shixiutong/data/FY4A:/data/FY4A/ -v /home/shixiutong/data/FY4A-NC:/data/FY4A-NC/ -v /home/shixiutong/fy4a:/app fy4a

#docker rmi fy4a

#docker run -p 4000:80 fy4a
