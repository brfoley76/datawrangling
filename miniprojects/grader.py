import json
import os
import requests
from urlparse import urljoin

from typecheck import is_invalid
from static_grader import SerializedSubmission, SerializedScore

BASE_URL = "https://www.thedataincubator.com"
GRADER_USER_KEY = "nosession::nouser"
HOME_DIR = os.environ["HOME"]
try:
  with open("{}/.ssh/.grader_url".format(HOME_DIR)) as submission_url_f:
    BASE_URL = submission_url_f.read().strip()
except IOError: # for local dev / general issues
  print "WARNING: You are missing a base URL. Submissions will go to thedataincubator.com."

try:
  # ~/.ssh is safe, hopefully
  with open("{}/.ssh/.grader_secret".format(HOME_DIR)) as secret_f:
    GRADER_USER_KEY = secret_f.read().strip()
except IOError: # for local dev / general issues
  print "WARNING: You are missing a unique key. A score will be returned to you, but it will not be saved."
  print "Please show this message to a TDI staff member."


def test_cases_grading(question_name, func, test_cases):
  res = []
  for test_case in test_cases:
    #test func with params in
    sub_res = func(*test_case['args'], **test_case['kwargs'])
    invalid = is_invalid(sub_res, test_case['type_str'])
    if invalid:
      print(invalid)
      return
    res.append(sub_res)

  # Submission

  submission = SerializedSubmission(question_name=question_name, submission=res)
  r = requests.post(urljoin(BASE_URL, 'submission?api_key=%s' % GRADER_USER_KEY),
                 data={'submission': submission.dumps()})
  print "=================="
  try:
    score = SerializedScore.loads(r.text)
  except Exception as e:
    print "There was an error. Please send this output to a TDI staff member."
    print e
    print "----" * 5
    print r.text
    print "There was an error. Please send this output to a TDI staff member."
    return

  if r.status_code != 200:
    print "Error!"
  else:
    print "Your score: ", score.score
  if score.error_msg:
    print score.error_msg
  print "=================="

def score(question_name, func):
  # Get test cases
  resp = requests.get(urljoin(BASE_URL, 'test_cases/%s?api_key=%s' % (question_name, GRADER_USER_KEY)))
  if resp.status_code != 200:
    print "No question found:", question_name
    return
  test_cases = json.loads(resp.text)
  test_cases_grading(question_name, func, test_cases)


client_mode = os.environ.get("GRADER_CLIENT_MODE", None)
if client_mode == "local":
  from localgrader import score
elif client_mode == "local_gae":
  BASE_URL = "http://localhost:8080"
