
# Simplified summarization for popular science article generation
Scientific publications are a vital tool for spreading knowledge, but their complexity often limits accessibility for the general public. As research advances, simplified content becomes increasingly important for informed decision-making in fields like medicine and technology.



## Tech Stack

This project is built using the following technologies:


[![technologies.png](https://i.postimg.cc/SRfJW6C8/image.png)](https://postimg.cc/jnCxTJ8d)


## Run Locally

Clone the project

```bash
  git clone https://github.com/tomernetzer14/article-simplify.git
```

Go to the project directory

```bash
   cd article-simplify
```

Install dependencies

```bash
  npm install

  pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download en_core_web_sm
```

Start the server

```bash
  ng serve -o
```

Go to the backend directory

```bash
   cd backend
```

download and copy files to MODEL/t5-custom directory

```bash
   https://drive.google.com/drive/folders/1wgOcnw6ATNhSRgtv29fRhbLKwrDpDm3A?usp=sharing
```


Start the server

```bash
  python customApp.py
```

## Run using docker

Go to the project directory

```bash
   cd article-simplify
```

Build the project

```bash
    docker-compose build
```

Run the docker

```bash
    docker-compose up
```

you can also run it on cuda, changing the YML file of the docker.
## Running Tests

To run tests, run the following command

for Fronend:

```bash
ng test
```

for Backend:

```bash
cd backend
```
```bash
pytest tests/ -v
```

## Authors

- [@tomernetzer14](https://www.github.com/tomernetzer14)
- [@neriala](https://www.github.com/neriala)
- [@yossiii050](https://www.github.com/yossiii050)


## Support

For support, email tomerne@ac.sce.ac.il 


## Feedback

If you have any feedback, please reach out to us at yossiyo2@ac.sce.ac.il

