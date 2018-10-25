
import os
import rdflib
from rdflib.plugins.sparql.parser import parseUpdate
from rdflib.plugins.sparql.update import evalUpdate
from rdflib.plugins.sparql.algebra import translateQuery, translateUpdate

from sns_client import SnsClient
from neptune_client import NeptuneClient

def main(event, context):
    # honeybadger_api_key = os.getenv('HONEYBADGER_API_KEY', "12345")
    rialto_sparql_endpoint = os.getenv('RIALTO_SPARQL_ENDPOINT', "localhost:8080")
    rialto_sparql_path = os.getenv('RIALTO_SPARQL_PATH', "/bigdata/namespace/kb/sparql")
    rialto_sns_endpoint = os.getenv('RIALTO_SNS_ENDPOINT', "http://localhost:4575")
    rialto_topic_arn = os.getenv('RIALTO_TOPIC_ARN', "rialto")
    aws_region = os.getenv('AWS_REGION', "us-west-2")

    sns_client = SnsClient(rialto_sns_endpoint, rialto_topic_arn, aws_region)
    neptune_client = NeptuneClient(rialto_sparql_endpoint, rialto_sparql_path)

    response = neptune_client.post(event)

    if response['statusCode'] == 200:
        sns_response = sns_client.publish(formatMessage(event['body']))

    return {
        'message' : response['body'],
        'statusCode' : response['statusCode']
	}

def formatMessage(body):
    subjects = []
    graph = translateUpdate(parseUpdate(body))
    for block in graph:
        for key in block.keys():
            if key in ['delete', 'insert']:
                subjects += getSubjectsFromQuads(block[key]['quads'])
                subjects += getSubjectsFromTriples(block[key]['triples'])
            if key in ['quads']:
                subjects += getSubjectsFromQuads(block['quads'])
            if key in ['triples']:
                subjects += getSubjectsFromTriples(block['triples'])

    return "{'Action': 'touch', 'Entities': %s}" % getUniqueSubjects(subjects)

def getSubjectsFromQuads(block):
    subjects = []
    for key in block.keys():
        for s, _p, _o in block[key]:
            subjects.append(s.toPython())
    
    return subjects

def getSubjectsFromTriples(block):
    subjects = []
    for s, _p, _o in block:
        subjects.append(s.toPython())

    return subjects

def getUniqueSubjects(subjectsList):
    unique_subjects = []
    for subject in subjectsList:
        if subject not in unique_subjects:
            unique_subjects.append(subject)
    
    return unique_subjects
