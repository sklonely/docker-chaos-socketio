FROM continuumio/anaconda3
WORKDIR /app
COPY .  /app
RUN pip install -r requirements.txt
CMD python sever.py
EXPOSE 8080
