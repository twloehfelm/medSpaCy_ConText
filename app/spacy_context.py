
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from fastapi import FastAPI
from pydantic import BaseModel

from typing import List

import logging

import spacy
from medspacy.context import ConTextComponent
  
class Annotation(BaseModel):
  first_pos: int
  last_pos: int
  is_negated: bool
  is_uncertain: bool
  is_conditional: bool
  is_historic: bool
  subject: str

class Data(BaseModel):
  accnum: str
  report: str
  annotations: List[Annotation]

class Annotations(BaseModel):
  annotations: List[Annotation]

app = FastAPI()
logger = logging.getLogger('spacy_context')
logger.setLevel(logging.INFO)

nlp = spacy.load("en_core_sci_lg")
context = ConTextComponent(nlp)
nlp.add_pipe("medspacy_context")

def find_exact_or_overlap_spacy_ent(ctakes_mention, spacy_ents):
  exact_match = [ent for ent in spacy_ents if ent.start_char == ctakes_mention.first_pos and ent.end_char == ctakes_mention.last_pos]
  if exact_match:
    return exact_match[0]
  else:
    overlapping_match = [ent for ent in spacy_ents if ent.start_char < ctakes_mention.last_pos and ent.end_char > ctakes_mention.first_pos]
    if overlapping_match:
      return overlapping_match[0]
  return None

@app.post("/spacy_context/process")
async def process(data: Data):
  accnum = data.accnum
  report = data.report
  annotations = data.annotations
  doc = nlp(report)
  results = []
  for annotation in annotations:
    spacy_match = find_exact_or_overlap_spacy_ent(annotation, doc.ents)
    if spacy_match:
      anno = Annotation(
        first_pos=annotation.first_pos,
        last_pos=annotation.last_pos,
        is_negated=any([annotation.is_negated, spacy_match._.is_negated]),
        is_uncertain=any([annotation.is_uncertain, spacy_match._.is_uncertain]),
        is_conditional=any([annotation.is_conditional, spacy_match._.is_hypothetical]),
        is_historic=any([annotation.is_historic, spacy_match._.is_historical]),
        subject="family" if spacy_match._.is_family else "patient",
      )
      results.append(anno)
  return Annotations(annotations=results)
