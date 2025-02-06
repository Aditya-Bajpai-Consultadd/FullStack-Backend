FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir "python-jose[cryptography]" "passlib[bcrypt]"

EXPOSE 8000

ENV SQLALCHEMY_DATABASE_URL=mysql+pymysql://root:consultadd@db/fullstackprj

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]