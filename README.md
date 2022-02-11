FastAPI implementation of medSpaCy ConText.

Need to download a model from https://allenai.github.io/scispacy/ and save
the .tar.gz file to ./app/resources/. The app is currently setup to use
en_core_sci_lg model so if using another one modify ./app/spacy_context.py 
line 49 to match the model you are using.
